"""Sensor platform for KS Data Cloud."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_BATTERY_POWER,
    SENSOR_BATTERY_SOC,
    SENSOR_DAILY_CHARGE,
    SENSOR_DAILY_CONSUMPTION,
    SENSOR_DAILY_DISCHARGE,
    SENSOR_DAILY_GENERATION,
    SENSOR_DAILY_GRID_EXPORT,
    SENSOR_DAILY_GRID_IMPORT,
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
    {
        "key": SENSOR_DAILY_CHARGE,
        "name": "Daily Battery Charge",
        "icon": "mdi:battery-arrow-up",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    {
        "key": SENSOR_DAILY_DISCHARGE,
        "name": "Daily Battery Discharge",
        "icon": "mdi:battery-arrow-down",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    {
        "key": SENSOR_DAILY_GRID_IMPORT,
        "name": "Daily Grid Import",
        "icon": "mdi:transmission-tower-import",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    {
        "key": SENSOR_DAILY_GRID_EXPORT,
        "name": "Daily Grid Export",
        "icon": "mdi:transmission-tower-export",
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

    entities = [KSDataCloudSensor(coordinator, sensor) for sensor in SENSORS]

    async_add_entities(entities)


class KSDataCloudSensor(CoordinatorEntity[KSDataCloudCoordinator], SensorEntity):
    """Representation of a KS Data Cloud sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KSDataCloudCoordinator,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = sensor_config["key"]
        self._attr_name = sensor_config["name"]
        self._attr_unique_id = f"{coordinator.station_id}_{self._key}"
        self._attr_icon = sensor_config["icon"]
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data["overview"].get(self._key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "station_id": self.coordinator.station_id,
            "last_update": self.coordinator.data["overview"].get("timestamp"),
            "location": self.coordinator.data["location"].get("address"),
            "timezone": self.coordinator.data["location"].get("timezone"),
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.station_id)},
            "name": self.coordinator.data["station_name"],
            "manufacturer": "KS Data Cloud",
            "model": "Solar Station",
            "configuration_url": f"https://sync.ksdatacloud.com/station/{self.coordinator.station_id}/residential/overview",
        }
