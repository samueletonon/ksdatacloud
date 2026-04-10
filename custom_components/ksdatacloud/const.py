"""Constants for KS Data Cloud integration."""
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ksdatacloud"

# Platforms
PLATFORMS: list[Platform] = [Platform.SENSOR]

# Configuration keys
CONF_STATION_ID: Final = "station_id"

# Update interval
UPDATE_INTERVAL: Final = timedelta(minutes=5)

# API endpoints
BASE_URL: Final = "https://sync.ksdatacloud.com"
LOGIN_ENDPOINT: Final = f"{BASE_URL}/api/oauth/auth/login"
STATION_INFO_ENDPOINT: Final = f"{BASE_URL}/api/web/station/manager/getinfo"
FLOW_POWER_ENDPOINT: Final = f"{BASE_URL}/api/web/residential/station/detail/flow/power"
DEVICE_LOGIC_ENDPOINT: Final = f"{BASE_URL}/api/residential/device/detail/logic"
DEVICE_NAVIGATION_ENDPOINT: Final = f"{BASE_URL}/api/residential/device/detail/navigation/data"

# Authentication
LOGIN_BASIC_AUTH: Final = "Basic a3N0YXI6a3N0YXJTZWNyZXQ="

# Sensor keys
SENSOR_PV_POWER: Final = "pv_power"
SENSOR_BATTERY_SOC: Final = "battery_soc"
SENSOR_BATTERY_POWER: Final = "battery_power"
SENSOR_GRID_POWER: Final = "grid_power"
SENSOR_LOAD_POWER: Final = "load_power"
SENSOR_DAILY_GENERATION: Final = "daily_generation"
SENSOR_DAILY_CONSUMPTION: Final = "daily_consumption"
SENSOR_DAILY_CHARGE: Final = "daily_charge"
SENSOR_DAILY_DISCHARGE: Final = "daily_discharge"
SENSOR_DAILY_GRID_IMPORT: Final = "daily_grid_import"
SENSOR_DAILY_GRID_EXPORT: Final = "daily_grid_export"
