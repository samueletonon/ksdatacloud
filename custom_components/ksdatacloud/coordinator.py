"""Data update coordinator for KS Data Cloud."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KSDataCloudAPI
from .const import DOMAIN, UPDATE_INTERVAL
from .exceptions import KSDataCloudAuthError, KSDataCloudConnectionError

_LOGGER = logging.getLogger(__name__)


class KSDataCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching KS Data Cloud data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: KSDataCloudAPI,
        station_id: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.station_id = station_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = await self.api.async_get_station_data(self.station_id)
            _LOGGER.debug("Successfully updated station data for %s", self.station_id)
            return data
        except (KSDataCloudConnectionError, KSDataCloudAuthError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
