from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import HomeAssistantError

def exception_handler(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as err:
            raise HomeAssistantError(f"An error occurred while performing the action: {err}")
    return wrapper

class SwitchbotEntity(Entity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._address = coordinator.config_entry.data["address"]

    @property
    def parsed_data(self):
        return self.coordinator.data or {}
