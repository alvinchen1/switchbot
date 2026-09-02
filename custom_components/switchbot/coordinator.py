from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

import switchbot

class SwitchbotDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, logger=None, name="switchbot", update_interval=None)
        self.config_entry = entry
        self.device = switchbot.SwitchbotDevice(entry.data["address"])

    async def _async_update_data(self):
        return await self.device.get_basic_info()
