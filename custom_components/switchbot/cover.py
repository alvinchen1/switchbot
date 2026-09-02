import logging
from typing import Any, override

import switchbot

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_SPEED,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
    CoverEntityStateAttribute,
)
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.exceptions import ServiceValidationError

from .const import (
    CONF_CURTAIN_SPEED,
    DEFAULT_CURTAIN_SPEED,
    CURTAIN3_SPEED_QUIETDRIFT,
    CURTAIN3_SPEED_SILENT,
    CURTAIN3_SPEED_NORMAL,
    CURTAIN3_SPEED_TO_MODE,
)
from .coordinator import SwitchbotDataUpdateCoordinator
from .entity import SwitchbotEntity, exception_handler

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    device = coordinator.device

    if isinstance(device, switchbot.SwitchbotCurtain):
        async_add_entities([SwitchBotCurtainEntity(coordinator)])
    else:
        return


class SwitchBotCurtainEntity(SwitchbotEntity, CoverEntity, RestoreEntity):
    _device: switchbot.SwitchbotCurtain
    _attr_device_class = CoverDeviceClass.CURTAIN
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.SPEED
    )
    _attr_translation_key = "cover"
    _attr_name = None

    _attr_supported_speeds = [
        CURTAIN3_SPEED_QUIETDRIFT,
        CURTAIN3_SPEED_SILENT,
        CURTAIN3_SPEED_NORMAL,
    ]

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_is_closed = None

    @callback
    def _validate_speed(self, kwargs: dict[str, Any]) -> None:
        if getattr(self._device, "model", None) != "Curtain 3":
            return
        if ATTR_SPEED not in kwargs:
            return
        if kwargs[ATTR_SPEED] not in self._attr_supported_speeds:
            raise ServiceValidationError("not_valid_speed")

    @callback
    def _motor_speed(self, kwargs: dict[str, Any]) -> int:
        if getattr(self._device, "model", None) == "Curtain 3":
            return CURTAIN3_SPEED_TO_MODE[
                kwargs.get(ATTR_SPEED, CURTAIN3_SPEED_NORMAL)
            ]
        return int(
            self.coordinator.config_entry.options.get(
                CONF_CURTAIN_SPEED, DEFAULT_CURTAIN_SPEED
            )
        )

    @override
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if (
            not last_state
            or CoverEntityStateAttribute.CURRENT_POSITION not in last_state.attributes
        ):
            return
        self._attr_current_cover_position = last_state.attributes.get(
            CoverEntityStateAttribute.CURRENT_POSITION
        )
        self._last_run_success = last_state.attributes.get("last_run_success")
        if self._attr_current_cover_position is not None:
            self._attr_is_closed = self._attr_current_cover_position <= 20

    @exception_handler
    @override
    async def async_open_cover(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        speed = self._motor_speed(kwargs)
        self._last_run_success = bool(await self._device.open(speed))
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_close_cover(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        speed = self._motor_speed(kwargs)
        self._last_run_success = bool(await self._device.close(speed))
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_stop_cover(self, **kwargs: Any) -> None:
        self._last_run_success = bool(await self._device.stop())
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_set_cover_position(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        position = kwargs.get(ATTR_POSITION)
        speed = self._motor_speed(kwargs)
        self._last_run_success = bool(await self._device.set_position(position, speed))
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        self._attr_is_closing = self._device.is_closing()
        self._attr_is_opening = self._device.is_opening()
        self._attr_current_cover_position = self.parsed_data["position"]
        self._attr_is_closed = self.parsed_data["position"] <= 20
        self.async_write_ha_state()
