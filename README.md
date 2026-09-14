# SwitchBot Curtain 3 Speed for Home Assistant

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)
![HACS](https://img.shields.io/badge/HACS-Custom-orange)

This custom Home Assistant integration adds native cover speed support for
SwitchBot Curtain 3 devices. It exposes the movement profiles supported by the
Curtain 3 through Home Assistant's cover controls instead of requiring a
separate custom service.

## Features

- Native Home Assistant cover speed support.
- `QuietDrift`: ultra-slow, almost silent movement.
- `Silent`: faster than QuietDrift while remaining quieter than normal.
- `Normal`: standard Curtain 3 movement speed.
- Speed selection for opening, closing, and moving to a position.
- Local Bluetooth control through Home Assistant and the SwitchBot integration.

## Requirements

- Home Assistant 2026.9.0 or newer.
- A SwitchBot Curtain 3 with firmware 1.2 or newer.
- A Bluetooth connection to the Curtain 3 through Home Assistant.

This integration sends the Curtain 3 speed command over the local Bluetooth
connection. Curtains available only through a SwitchBot Hub, SwitchBot Cloud,
Matter, or the SwitchBot API cannot use these speed profiles.

## Installation with HACS

1. Open **HACS** in Home Assistant.
2. Open **Integrations**, select the three-dot menu, and choose
   **Custom repositories**.
3. Add `https://github.com/alvinchen1/switchbot` as an **Integration**
   repository.
4. Download **SwitchBot Curtain 3 Speed**.
5. Restart Home Assistant.

After restarting, configure the **SwitchBot** integration normally. If the
standard SwitchBot integration is already configured, its existing config
entry can be retained; restart Home Assistant after installing or upgrading
this custom integration.

## Manual installation

1. Download this repository.
2. Copy `custom_components/switchbot` into the `custom_components` directory
   of your Home Assistant configuration.
3. Restart Home Assistant.

The final directory should contain:

```text
/config/custom_components/switchbot/manifest.json
```

## Using a speed profile

The speed is selected with the native `cover.open_cover`,
`cover.close_cover`, or `cover.set_cover_position` service. The available
values are lowercase:

- `quietdrift`
- `silent`
- `normal`

Example:

```yaml
alias: Open curtains quietly
triggers:
  - trigger: sun
    event: sunrise
actions:
  - action: cover.open_cover
    target:
      entity_id: cover.bedroom_curtain
    data:
      speed: quietdrift
mode: single
```

To move to a position with a selected profile:

```yaml
action: cover.set_cover_position
target:
  entity_id: cover.bedroom_curtain
data:
  position: 100
  speed: silent
```

The speed selector is also available from Home Assistant's cover controls
when the entity reports the `SPEED` feature.

## Troubleshooting

- **No speed selector is shown:** Confirm that the installed integration is
  the custom `switchbot` integration, restart Home Assistant, and verify that
  the device is a Curtain 3.
- **Commands fail:** Confirm that Home Assistant can communicate with the
  curtain over Bluetooth and that the curtain is within range of the adapter
  or Bluetooth proxy.
- **QuietDrift is unavailable:** Update the Curtain 3 firmware to version 1.2
  or newer and confirm that the device is connected locally rather than
  through a hub.

## Credits

The speed command mapping is based on the SwitchBot Curtain 3 QuietDrift
project by [Loweack](https://github.com/Loweack/SwitchBot-Curtain-3-QuietDrift).
