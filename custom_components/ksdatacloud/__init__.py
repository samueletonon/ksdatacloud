"""The KS Data Cloud integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KSDataCloudAPI
from .const import CONF_STATION_ID, DOMAIN
from .coordinator import KSDataCloudCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KS Data Cloud from a config entry."""
    # Get aiohttp session from Home Assistant
    session = async_get_clientsession(hass)

    # Create API client
    api = KSDataCloudAPI(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    # Create coordinator
    coordinator = KSDataCloudCoordinator(
        hass,
        api,
        entry.data[CONF_STATION_ID],
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
