# ha-remocon

**Unofficial Home Assistant integration for Elco heat pumps and oil/gas boilers via the Remocon-Net cloud service.**

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=macschlingel&repository=ha-remocon&category=integration)

Control and monitor your Elco heat pump (e.g. Aerotop SPK) through the Remocon-Net cloud API — directly in Home Assistant, no MQTT or AppDaemon needed.

> **Disclaimer:** This is an unofficial community project. It is not endorsed by or affiliated with Elco or the Ariston Thermo Group.

## Features

- **Oil / gas boiler support** — Choose the system type (heat pump or oil/gas boiler) during setup; cooling and heat pump entities are hidden for boilers and the API requests are adapted to boilers
- **Binary sensors** — Burner running (flame detected, boilers only)
- **Hot water** — Water heater entity with tank temperature, comfort setpoint and operation mode (on / off)
- **Mode buttons** — Auto / Comfort (day) / Reduced (night) / Off (frost protection) in one tap, the active mode is shown by the button icon
- **Sensors** — Operating mode (Auto / Comfort / Reduced / Off)
- **Update interval** — Number entity to set how often the cloud is polled, in minutes (1 to 1440), also available in the integration options
- **Manual refresh** — "Refresh now" button to fetch the data immediately, without waiting for the interval
- **Robust connection** — Tries both Remocon-Net data endpoints, shows the server's reply on errors, and an optional data call that fails no longer breaks the setup
- **CLI tool** — `remocon.py` accepts `--system-type boiler` (or `"system_type": "boiler"` in `config.json`)
- **Translations** — French added; English and German completed

## Requirements

- Elco heat pump **or oil/gas boiler** with a Remocon-Net gateway (connected to the internet)
- Remocon-Net account ([remocon-net.remotethermo.com](https://www.remocon-net.remotethermo.com))
- Home Assistant >= 2025.2.0
- [HACS](https://hacs.xyz/) installed

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. **≡ Menu** → **Custom Repositories**
3. Add:
   - **URL:** `https://github.com/macschlingel/ha-remocon`
   - **Category:** Integration
4. Search for **"Remocon-Net"** in HACS and install
5. Restart Home Assistant

### Manual

```bash
cd /path/to/homeassistant/config/custom_components/
git clone https://github.com/macschlingel/ha-remocon.git elco_remocon_temp
cp -r elco_remocon_temp/custom_components/elco_remocon ./
rm -rf elco_remocon_temp
```

Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **"Remocon-Net"**
3. Enter your credentials:
   - **Email:** Your Remocon-Net login email
   - **Password:** Your Remocon-Net login password
   - **Gateway ID:** Your system's gateway ID (see below)
   - **Zone:** Heating zone (default: 1)
  - **System type:** `Heat pump` or `Oil / gas boiler`

### Finding your Gateway ID

1. Log in at [remocon-net.remotethermo.com](https://www.remocon-net.remotethermo.com)
2. The gateway ID is shown in the URL, e.g. `A1B2C3D4E5F6` in:
   ```
   https://www.remocon-net.remotethermo.com/R2/Plant/Index/A1B2C3D4E5F6
   ```

## Entities

After setup, the following entities are created:

| Entity | Type | Description |
|--------|------|-------------|
| `climate.remocon_net_heat_pump` | Climate | Temperature control, mode, presets |
| `sensor.outside_temperature` | Sensor | Outside temperature |
| `sensor.desired_temperature` | Sensor | Current target temperature |
| `sensor.reduced_temperature` | Sensor | Reduced setpoint temperature |
| `sensor.flow_temperature` | Sensor | Flow temperature |
| `sensor.system_pressure` | Sensor | System pressure (bar) |
| `binary_sensor.heating_active` | Binary | Heating is active |
| `binary_sensor.cooling_active` | Binary | Cooling is active |
| `binary_sensor.heat_pump_on` | Binary | Heat pump is running |

### Climate entity

The climate entity supports:

- **HVAC modes:** `Heat` (Comfort), `Auto` (time program), `Off` (frost protection)
- **Presets:** `Comfort`, `Reduced`
- **Temperature:** Adjustable within the range configured on the heat pump

## CLI Tool

A standalone CLI tool is included for testing and debugging:

```bash
pip install -r requirements.txt

# Create config
cp config.example.json config.json
# Edit config.json with your email, password and gateway ID

# Check status
python3 remocon.py --config-file config.json status

# Set temperature
python3 remocon.py --config-file config.json set-temp --comfort 22.0

# Change mode
python3 remocon.py --config-file config.json set-mode comfort

# Raw API response (debug)
python3 remocon.py --config-file config.json raw-get

# JSON output (for scripting)
python3 remocon.py --config-file config.json status --json
```

## Oil / gas boilers

Select **Oil / gas boiler** as *System type* during setup. The integration then:

- sends the boiler feature flags (`convBoiler`) to the Remocon-Net API instead of the heat-pump ones,
- hides the *cooling active* and *heat pump running* entities,
- adds `binary_sensor.burner_running` (based on the flame sensor reported by the gateway).

For the CLI, set `"system_type": "boiler"` in `config.json` (or use `--system-type boiler`).

> **Experimental:** the boiler mode has not been verified against a real oil boiler yet. Please run
> `python3 remocon.py --config-file config.json --system-type boiler raw-get` and attach the output to an issue if some
> values (flow temperature, pressure, burner) are missing — data point IDs can differ between boiler models.
> Existing installations keep working unchanged (the default system type is *Heat pump*).

## Hot water, mode buttons and update interval

- **Hot water:** a `water_heater` entity (*Hot water*) shows the tank temperature, sets the comfort setpoint and switches the DHW operation mode. The available modes come from your system (usually `off` / `on`).
- **Mode buttons:** `Auto`, `Comfort (day)`, `Reduced (night)` and `Off (frost protection)` buttons switch the heating mode in one tap. The `Operating mode` sensor shows which one is active.
- **Update interval:** an `Update interval` number entity (in the *Configuration* section of the device page, and usable in dashboards) sets how often the cloud is polled, in minutes (1 to 1440, e.g. `60` for once an hour). The same value is available under *Settings → Devices & Services → Remocon-Net → Configure*. Changing it reloads the integration once. Commands you send (temperature, mode) always trigger a refresh.
- **Manual refresh:** the `Refresh now` button fetches fresh data from Remocon-Net immediately, without waiting for the update interval.
- **Button state "Unknown":** in Home Assistant a button's state is the time of its last press, so it reads *Unknown* until pressed once. This cannot be changed by an integration. The active mode is shown by the button icon (filled circle) and by the `Operating mode` sensor; hide the state in a tile card with `hide_state: true`.

> Hot-water writes use the same Remocon-Net endpoints as the web app; they are untested on oil boilers. Please open an issue with the log line if a command fails.

## Known limitations

- **Cloud-dependent:** Control goes through the Remocon-Net cloud. No control possible during internet outages.
- **Polling:** Data is fetched every 2 minutes by default (configurable, see above; no real-time streaming).
- **No room sensor:** If no room thermostat is connected, `current_temperature` shows the target value.

## Technical details

The integration uses the same API as the Elco Remocon-Net web app:

- **Login:** Cookie-based authentication via `/R2/Account/Login`
- **Data:** R2 Web API (`/R2/PlantHomeBsb/GetData/`) + v2 REST API (`/api/v2/remote/dataItems/`)
- **Control:** v2 REST API (`/api/v2/remote/bsbZones/`, `/api/v2/remote/bsbPlantData/`)
- **Platform:** remotethermo.com (Ariston Thermo Group)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT
