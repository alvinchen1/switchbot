import logging
from typing import Any, Optional, override

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_SPEED,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
    CoverEntityStateAttribute,
)
from homeassistant.core import callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import SwitchbotEntity
from .coordinator import SwitchbotDataUpdateCoordinator
from .const import CONF_CURTAIN_SPEED, DEFAULT_CURTAIN_SPEED

from .switchbot import (
    PatchedSwitchbotCurtain,
    CURTAIN3_SPEED_QUIETDRIFT,
    CURTAIN3_SPEED_SILENT,
    CURTAIN3_SPEED_NORMAL,
    is_curtain3,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


CURTAIN3_SPEED_MAP = {
    "quietdrift": CURTAIN3_SPEED_QUIETDRIFT,
    "silent": CURTAIN3_SPEED_SILENT,
    "normal": CURTAIN3_SPEED_NORMAL,
}


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Register entities for this config entry.

    We only override Curtain 3 behavior. All other SwitchBot entities
    are handled by the other platform files in this integration.
    """
    coordinator: SwitchbotDataUpdateCoordinator = entry.runtime_data
    device = coordinator.device

    if isinstance(device, PatchedSwitchbotCurtain):
        async_add_entities([SwitchBotCurtainEntity(coordinator)])
        return

    # Other cover types (Blind Tilt, Roller Shade, etc.)
    # are handled by HA's original cover.py logic,
    # which remains in your repo unchanged.
    return


class SwitchBotCurtainEntity(SwitchbotEntity, CoverEntity, RestoreEntity):
    """Curtain 3 entity with motor speed support."""

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

    _attr_supported_speeds = list(CURTAIN3_SPEED_MAP.keys())

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._device: PatchedSwitchbotCurtain = coordinator.device
        self._attr_is_closed = None

    @callback
    def _validate_speed(self, kwargs: dict[str, Any]) -> None:
        if not is_curtain3(self._device):
            return
        if ATTR_SPEED not in kwargs:
            return
        if kwargs[ATTR_SPEED] not in self._attr_supported_speeds:
            raise ServiceValidationError("not_valid_speed")

    @callback
    def _motor_mode(self, kwargs: dict[str, Any]) -> Optional[int]:
        if is_curtain3(self._device):
            speed = kwargs.get(ATTR_SPEED, "normal")
            return CURTAIN3_SPEED_MAP.get(speed, CURTAIN3_SPEED_NORMAL)

        # Non‑Curtain 3: fall back to legacy HA speed option
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

    @override
    async def async_open_cover(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        mode = self._motor_mode(kwargs)
        self._last_run_success = bool(self._device.open(mode))
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @override
    async def async_close_cover(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        mode = self._motor_mode(kwargs)
        self._last_run_success = bool(self._device.close(mode))
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @override
    async def async_stop_cover(self, **kwargs: Any) -> None:
        self._last_run_success = bool(self._device.stop())
        self._attr_is_opening = self._device.is_opening()
        self._attr_is_closing = self._device.is_closing()
        self.async_write_ha_state()

    @override
    async def async_set_cover_position(self, **kwargs: Any) -> None:
        self._validate_speed(kwargs)
        position = kwargs.get(ATTR_POSITION)
        mode = self._motor_mode(kwargs)
        self._last_run_success = bool(self._device.set_position(position, mode))
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
