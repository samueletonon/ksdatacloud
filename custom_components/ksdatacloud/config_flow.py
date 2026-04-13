"""Config flow for KS Data Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KSDataCloudAPI
from .const import CONF_STATION_ID, DOMAIN
from .exceptions import KSDataCloudAuthError, KSDataCloudConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_STATION_ID): str,
    }
)


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
            session = async_get_clientsession(self.hass)
            api = KSDataCloudAPI(
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                # Test login
                await api.async_login()
                # Test station access
                station_data = await api.async_get_station_data(
                    user_input[CONF_STATION_ID]
                )
                station_name = station_data.get("station_name", "Unknown Station")

                # Create unique ID from station ID
                await self.async_set_unique_id(user_input[CONF_STATION_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=station_name,
                    data=user_input,
                )

            except KSDataCloudAuthError:
                errors["base"] = "invalid_auth"
            except KSDataCloudConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
