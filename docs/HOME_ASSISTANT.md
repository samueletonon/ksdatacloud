# Home Assistant Integration Guide

This document outlines the steps to integrate KS Data Cloud with Home Assistant.

## Integration Approaches

### Option 1: Command Line Sensor (Easiest)
Use existing scripts with Home Assistant's command line integration.

**Pros:**
- No code changes needed
- Quick to set up
- Uses existing `fetch_stations_api.py`

**Cons:**
- Limited control over polling
- Creates subprocess for each update
- Harder to manage multiple sensors

**Setup:**
```yaml
# configuration.yaml
sensor:
  - platform: command_line
    name: "Solar Station Data"
    command: "cd /path/to/ksdatacloud && /path/to/uv run fetch_stations_api.py --no-stdout"
    value_template: "{{ value_json[0].overview.pv_power }}"
    json_attributes:
      - station_name
      - location
      - overview
    scan_interval: 300  # 5 minutes
```

---

### Option 2: RESTful Sensor (Simple)
Wrap the script in a web service, use Home Assistant's REST integration.

**Pros:**
- Decoupled from Home Assistant
- Can serve multiple consumers
- Better for network-based deployments

**Cons:**
- Requires additional web server
- More infrastructure to maintain

---

### Option 3: MQTT Integration (IoT-friendly)
Publish data to MQTT broker, Home Assistant subscribes.

**Pros:**
- Standard IoT protocol
- Good for distributed systems
- Automatic discovery support

**Cons:**
- Requires MQTT broker
- Additional dependency

---

### Option 4: Custom Component (Full Integration) ⭐ **Recommended**
Build a native Home Assistant integration.

**Pros:**
- Full Home Assistant integration
- UI-based configuration
- Automatic device/entity creation
- Best user experience
- Can be added to HACS

**Cons:**
- Most development work
- Requires Home Assistant API knowledge

---

## Detailed Guide: Custom Component Integration

This is the recommended approach for full Home Assistant compatibility.

### Prerequisites

- Home Assistant installation
- Python 3.9+ (Home Assistant's Python)
- Understanding of Home Assistant's integration structure
- Git for version control

### Architecture Overview

```
custom_components/ksdatacloud/
├── __init__.py          # Integration setup
├── manifest.json        # Integration metadata
├── config_flow.py       # UI configuration
├── const.py            # Constants
├── coordinator.py      # Data update coordinator
├── sensor.py           # Sensor entities
├── api.py              # API client (refactored from fetch_stations_api.py)
└── translations/
    └── en.json         # UI strings
```

### Step 1: Project Setup

Create the custom component structure:

```bash
# In your Home Assistant config directory
mkdir -p custom_components/ksdatacloud
cd custom_components/ksdatacloud
touch __init__.py manifest.json config_flow.py const.py coordinator.py sensor.py api.py
mkdir translations
touch translations/en.json
```

### Step 2: Create manifest.json

Define integration metadata:

```json
{
  "domain": "ksdatacloud",
  "name": "KS Data Cloud",
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/yourusername/ksdatacloud",
  "integration_type": "device",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/yourusername/ksdatacloud/issues",
  "requirements": [
    "requests>=2.32.0",
    "python-dotenv>=1.0.0"
  ],
  "version": "0.1.0"
}
```

### Step 3: Refactor API Client (api.py)

Extract the API logic into a reusable class:

```python
"""KS Data Cloud API client."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://sync.ksdatacloud.com"
LOGIN_ENDPOINT = f"{BASE_URL}/api/oauth/auth/login"
STATION_INFO_ENDPOINT = f"{BASE_URL}/api/web/station/manager/getinfo"
FLOW_POWER_ENDPOINT = f"{BASE_URL}/api/web/residential/station/detail/flow/power"
DEVICE_LOGIC_ENDPOINT = f"{BASE_URL}/api/residential/device/detail/logic"
DEVICE_NAVIGATION_ENDPOINT = f"{BASE_URL}/api/residential/device/detail/navigation/data"
LOGIN_BASIC_AUTH = "Basic a3N0YXI6a3N0YXJTZWNyZXQ="


class KSDataCloudAuthError(Exception):
    """Authentication error."""


class KSDataCloudConnectionError(Exception):
    """Connection error."""


class KSDataCloudAPI:
    """API client for KS Data Cloud."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self.session = self._build_session()
        self._token: str | None = None

    def _build_session(self) -> requests.Session:
        """Build HTTP session."""
        session = requests.Session()
        session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "homeassistant-ksdatacloud/1.0",
        })
        return session

    def _unwrap_response(self, response: requests.Response) -> Any:
        """Unwrap API response."""
        try:
            payload = response.json()
        except ValueError as err:
            raise KSDataCloudConnectionError(f"Invalid JSON: {err}") from err

        if response.status_code >= 400:
            raise KSDataCloudConnectionError(
                f"HTTP {response.status_code}: {payload}"
            )

        if payload.get("code") != 200:
            raise KSDataCloudConnectionError(
                f"API error: {payload.get('msg', 'Unknown error')}"
            )

        return payload.get("data")

    async def async_login(self) -> str:
        """Login and get bearer token."""
        try:
            response = self.session.post(
                LOGIN_ENDPOINT,
                headers={
                    "Authorization": LOGIN_BASIC_AUTH,
                    "Content-Type": "application/json",
                    "Origin": BASE_URL,
                    "Referer": f"{BASE_URL}/login",
                },
                json={"username": self.username, "password": self.password},
                timeout=30,
            )
        except requests.RequestException as err:
            raise KSDataCloudConnectionError(f"Login failed: {err}") from err

        token = self._unwrap_response(response)
        if not token or not isinstance(token, str):
            raise KSDataCloudAuthError("No bearer token returned")

        self._token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        return token

    async def async_get_station_data(self, station_id: str) -> dict[str, Any]:
        """Get station data."""
        if not self._token:
            await self.async_login()

        # Get station info
        station_info = await self._async_get_station_info(station_id)
        collect_ids = station_info.get("collectList") or []

        # Get devices
        devices = []
        for collect_id in collect_ids:
            try:
                logic = await self._async_get_device_logic(collect_id, station_id)
                navigation = await self._async_get_device_navigation(collect_id, station_id)
                devices.append({
                    "collect_id": collect_id,
                    "name": navigation.get("deviceName"),
                    "serial_number": navigation.get("sn"),
                    "model": navigation.get("deviceModel"),
                    "status": navigation.get("status"),
                    "metrics": logic,
                })
            except Exception as err:
                _LOGGER.warning(f"Failed to get device {collect_id}: {err}")

        # Get power flow
        flow_power = await self._async_get_flow_power(station_id)

        return self._build_station_report(station_id, station_info, flow_power, devices)

    async def _async_get_station_info(self, station_id: str) -> dict[str, Any]:
        """Get station information."""
        response = self.session.get(
            STATION_INFO_ENDPOINT,
            params={"stationId": station_id},
            timeout=30,
        )
        return self._unwrap_response(response)

    async def _async_get_flow_power(self, station_id: str) -> dict[str, Any]:
        """Get power flow data."""
        params = {
            "stationId": station_id,
            "stime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.session.get(
            FLOW_POWER_ENDPOINT,
            params=params,
            timeout=30,
        )
        return self._unwrap_response(response)

    async def _async_get_device_logic(self, collect_id: str, station_id: str) -> dict[str, Any]:
        """Get device logic data."""
        response = self.session.get(
            DEVICE_LOGIC_ENDPOINT,
            params={"collectId": collect_id},
            timeout=30,
        )
        return self._unwrap_response(response)

    async def _async_get_device_navigation(self, collect_id: str, station_id: str) -> dict[str, Any]:
        """Get device navigation data."""
        response = self.session.get(
            DEVICE_NAVIGATION_ENDPOINT,
            params={"collectId": collect_id},
            timeout=30,
        )
        return self._unwrap_response(response)

    def _build_station_report(
        self,
        station_id: str,
        station_info: dict,
        flow_power: dict,
        devices: list,
    ) -> dict[str, Any]:
        """Build station report."""
        return {
            "station_id": station_id,
            "station_name": station_info.get("stationName"),
            "location": {
                "address": station_info.get("stationAddress"),
                "country": station_info.get("country"),
                "timezone": station_info.get("timeZone"),
            },
            "overview": {
                "timestamp": flow_power.get("saveTime"),
                "pv_power": flow_power.get("pvp", 0),
                "battery_soc": flow_power.get("soc", 0),
                "battery_power": flow_power.get("batcdp", 0),
                "grid_power": flow_power.get("gridmp", 0),
                "load_power": flow_power.get("balp", 0),
                "daily_generation": flow_power.get("dgepv", 0),
                "daily_consumption": flow_power.get("dbalec", 0),
            },
            "devices": devices,
        }
```

### Step 4: Create Constants (const.py)

```python
"""Constants for KS Data Cloud integration."""
from datetime import timedelta

DOMAIN = "ksdatacloud"

# Configuration
CONF_STATION_ID = "station_id"

# Update interval
UPDATE_INTERVAL = timedelta(minutes=5)

# Sensor keys
SENSOR_PV_POWER = "pv_power"
SENSOR_BATTERY_SOC = "battery_soc"
SENSOR_BATTERY_POWER = "battery_power"
SENSOR_GRID_POWER = "grid_power"
SENSOR_LOAD_POWER = "load_power"
SENSOR_DAILY_GENERATION = "daily_generation"
SENSOR_DAILY_CONSUMPTION = "daily_consumption"
```

### Step 5: Create Data Update Coordinator (coordinator.py)

```python
"""Data update coordinator for KS Data Cloud."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KSDataCloudAPI, KSDataCloudConnectionError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class KSDataCloudCoordinator(DataUpdateCoordinator):
    """Class to manage fetching KS Data Cloud data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: KSDataCloudAPI,
        station_id: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.station_id = station_id

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            return await self.api.async_get_station_data(self.station_id)
        except KSDataCloudConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
```

### Step 6: Create Sensor Platform (sensor.py)

```python
"""Sensor platform for KS Data Cloud."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_BATTERY_POWER,
    SENSOR_BATTERY_SOC,
    SENSOR_DAILY_CONSUMPTION,
    SENSOR_DAILY_GENERATION,
    SENSOR_GRID_POWER,
    SENSOR_LOAD_POWER,
    SENSOR_PV_POWER,
)
from .coordinator import KSDataCloudCoordinator

SENSORS = [
    {
        "key": SENSOR_PV_POWER,
        "name": "PV Power",
        "icon": "mdi:solar-power",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": SENSOR_BATTERY_SOC,
        "name": "Battery State of Charge",
        "icon": "mdi:battery",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": SENSOR_BATTERY_POWER,
        "name": "Battery Power",
        "icon": "mdi:battery-charging",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": SENSOR_GRID_POWER,
        "name": "Grid Power",
        "icon": "mdi:transmission-tower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": SENSOR_LOAD_POWER,
        "name": "Load Power",
        "icon": "mdi:home-lightning-bolt",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": SENSOR_DAILY_GENERATION,
        "name": "Daily Generation",
        "icon": "mdi:solar-power",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    {
        "key": SENSOR_DAILY_CONSUMPTION,
        "name": "Daily Consumption",
        "icon": "mdi:home-lightning-bolt",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KS Data Cloud sensors."""
    coordinator: KSDataCloudCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        KSDataCloudSensor(coordinator, sensor)
        for sensor in SENSORS
    ]

    async_add_entities(entities)


class KSDataCloudSensor(CoordinatorEntity, SensorEntity):
    """Representation of a KS Data Cloud sensor."""

    def __init__(
        self,
        coordinator: KSDataCloudCoordinator,
        sensor_config: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = sensor_config["key"]
        self._attr_name = f"{coordinator.data['station_name']} {sensor_config['name']}"
        self._attr_unique_id = f"{coordinator.station_id}_{self._key}"
        self._attr_icon = sensor_config["icon"]
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data["overview"].get(self._key)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.station_id)},
            "name": self.coordinator.data["station_name"],
            "manufacturer": "KS Data Cloud",
            "model": "Solar Station",
        }
```

### Step 7: Create Config Flow (config_flow.py)

```python
"""Config flow for KS Data Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .api import KSDataCloudAPI, KSDataCloudAuthError, KSDataCloudConnectionError
from .const import CONF_STATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_STATION_ID): str,
})


class KSDataCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KS Data Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate credentials
            api = KSDataCloudAPI(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                await api.async_login()
                await api.async_get_station_data(user_input[CONF_STATION_ID])
            except KSDataCloudAuthError:
                errors["base"] = "invalid_auth"
            except KSDataCloudConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create entry
                return self.async_create_entry(
                    title=f"KS Station {user_input[CONF_STATION_ID]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
```

### Step 8: Create Integration Init (__init__.py)

```python
"""The KS Data Cloud integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api import KSDataCloudAPI
from .const import CONF_STATION_ID, DOMAIN
from .coordinator import KSDataCloudCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KS Data Cloud from a config entry."""
    api = KSDataCloudAPI(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    coordinator = KSDataCloudCoordinator(
        hass,
        api,
        entry.data[CONF_STATION_ID],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
```

### Step 9: Create Translations (translations/en.json)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "KS Data Cloud",
        "description": "Enter your KS Data Cloud credentials",
        "data": {
          "username": "Email",
          "password": "Password",
          "station_id": "Station ID"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid credentials",
      "cannot_connect": "Cannot connect to KS Data Cloud",
      "unknown": "Unknown error occurred"
    }
  }
}
```

### Step 10: Installation

1. Copy the `custom_components/ksdatacloud` directory to your Home Assistant config
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "KS Data Cloud"
5. Enter credentials and station ID

### Step 11: Testing

Test the integration:

```bash
# Check Home Assistant logs
tail -f /config/home-assistant.log | grep ksdatacloud

# Verify sensors are created
# Settings → Devices & Services → KS Data Cloud → Device
```

### Step 12: HACS Distribution (Optional)

To distribute via HACS:

1. Create GitHub repository
2. Add `hacs.json`:
```json
{
  "name": "KS Data Cloud",
  "content_in_root": false,
  "render_readme": true,
  "homeassistant": "2023.1.0"
}
```

3. Tag releases following semver
4. Submit to HACS default repository

---

## Migration from Existing Scripts

### Changes Required:

1. **Make API calls async**
   - Replace `requests` with `aiohttp` or use `asyncio.to_thread()`
   - Current implementation uses sync requests in async context

2. **Add proper error handling**
   - Catch specific exceptions
   - Return meaningful error states

3. **Remove CLI interface**
   - Config comes from Home Assistant UI
   - No argparse needed

4. **Add entity attributes**
   - Device class
   - State class
   - Units of measurement

### Converting Existing Code:

```python
# Before (CLI script)
def main():
    args = parse_args()
    config = parse_key_value_file(args.parameters)
    session = build_session()
    login(session, config["username"], config["password"])
    data = collect_station_data(session, station_id)
    print(json.dumps(data))

# After (Home Assistant)
class KSDataCloudAPI:
    async def async_get_station_data(self, station_id):
        if not self._token:
            await self.async_login()
        return await self._fetch_data(station_id)
```

---

## Testing Checklist

- [ ] Integration appears in Add Integration dialog
- [ ] Config flow validates credentials
- [ ] Sensors are created with correct names
- [ ] Sensor values update every 5 minutes
- [ ] Device page shows all sensors
- [ ] Errors are logged appropriately
- [ ] Integration can be removed cleanly
- [ ] Multiple stations can be configured
- [ ] Sensors have correct units and icons
- [ ] Energy dashboard shows daily generation/consumption

---

## Additional Features to Consider

1. **Services**
   - `ksdatacloud.refresh_data` - Manual refresh
   - `ksdatacloud.get_historical` - Historical data

2. **Diagnostics**
   - Add diagnostic data for troubleshooting
   - Redact sensitive information

3. **Options Flow**
   - Change polling interval
   - Select which sensors to create

4. **Binary Sensors**
   - Grid connected status
   - Battery charging/discharging

5. **Energy Dashboard Integration**
   - Configure sensors for energy dashboard
   - Track import/export

6. **Lovelace Card**
   - Custom card for solar flow visualization
   - Real-time power flow diagram

---

## Resources

- [Home Assistant Integration Development](https://developers.home-assistant.io/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index/)
- [HACS Documentation](https://hacs.xyz/)
- [Example Integrations](https://github.com/home-assistant/example-custom-config)
