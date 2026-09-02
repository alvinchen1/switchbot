import logging
from typing import Optional

import switchbot  # Home Assistant's bundled pySwitchbot

_LOGGER = logging.getLogger(__name__)

# Motor mode bytes for Curtain 3
CURTAIN3_SPEED_QUIETDRIFT = 1
CURTAIN3_SPEED_SILENT = 2
CURTAIN3_SPEED_NORMAL = 255


def is_curtain3(device) -> bool:
    """Detect Curtain 3 by model name."""
    return getattr(device, "model", None) == "Curtain 3"


class PatchedSwitchbotCurtain(switchbot.SwitchbotCurtain):
    """
    A patched Curtain 3 class that adds motor speed support.

    This class wraps the underlying pySwitchbot Curtain implementation
    but adds a mode byte to the BLE payload for Curtain 3 devices.
    """

    def _send_mode_command(self, base_cmd: str, mode: Optional[int]) -> bool:
        """
        Send a BLE command with an optional motor mode byte.

        base_cmd: "01" (open), "02" (close), "06" (set position)
        mode:     Curtain 3 motor mode byte (1, 2, 255)
        """
        if mode is None:
            # Fall back to original behavior
            return bool(super()._send_command(base_cmd))

        # Append mode byte to payload
        payload = base_cmd + f"{mode:02x}"
        _LOGGER.debug("Sending Curtain 3 command: %s", payload)
        return bool(super()._send_command(payload))

    def open(self, mode: Optional[int] = None) -> bool:
        """Open curtain with optional motor mode."""
        return self._send_mode_command("01", mode)

    def close(self, mode: Optional[int] = None) -> bool:
        """Close curtain with optional motor mode."""
        return self._send_mode_command("02", mode)

    def set_position(self, position: int, mode: Optional[int] = None) -> bool:
        """
        Set curtain position with optional motor mode.

        If mode is None, fall back to the original pySwitchbot behavior.
        """
        if mode is None:
            return bool(super().set_position(position))

        # "06" = set position
        return self._send_mode_command("06", mode)
