"""Async API client for KS Data Cloud."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp

from .const import (
    BASE_URL,
    DEVICE_LOGIC_ENDPOINT,
    DEVICE_NAVIGATION_ENDPOINT,
    FLOW_POWER_ENDPOINT,
    LOGIN_BASIC_AUTH,
    LOGIN_ENDPOINT,
    STATION_INFO_ENDPOINT,
)
from .exceptions import KSDataCloudAuthError, KSDataCloudConnectionError

_LOGGER = logging.getLogger(__name__)


class KSDataCloudAPI:
    """API client for KS Data Cloud."""

    def __init__(
        self, session: aiohttp.ClientSession, username: str, password: str
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._token: str | None = None

    async def _async_unwrap_response(self, response: aiohttp.ClientResponse) -> Any:
        """Unwrap API response."""
        try:
            payload = await response.json()
        except ValueError as err:
            raise KSDataCloudConnectionError(f"Invalid JSON: {err}") from err

        if response.status >= 400:
            raise KSDataCloudConnectionError(
                f"HTTP {response.status}: {payload}"
            )

        if payload.get("code") != 200:
            error_msg = payload.get("msg", "Unknown error")
            if response.status == 401 or "auth" in error_msg.lower():
                raise KSDataCloudAuthError(f"API error: {error_msg}")
            raise KSDataCloudConnectionError(f"API error: {error_msg}")

        return payload.get("data")

    async def async_login(self) -> str:
        """Login and get bearer token."""
        try:
            async with self._session.post(
                LOGIN_ENDPOINT,
                headers={
                    "Authorization": LOGIN_BASIC_AUTH,
                    "Content-Type": "application/json",
                    "Origin": BASE_URL,
                    "Referer": f"{BASE_URL}/login",
                },
                json={"username": self._username, "password": self._password},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                token = await self._async_unwrap_response(response)

        except aiohttp.ClientError as err:
            raise KSDataCloudConnectionError(f"Login failed: {err}") from err

        if not token or not isinstance(token, str):
            raise KSDataCloudAuthError("No bearer token returned")

        self._token = token
        _LOGGER.debug("Successfully authenticated")
        return token

    def _validate_station_id(self, station_id: str) -> None:
        """Validate station ID format to prevent injection attacks."""
        if not station_id or len(station_id) > 100:
            raise ValueError(f"Invalid station ID length: {len(station_id)}")
        # Station IDs should only contain alphanumeric characters, underscores, and hyphens
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', station_id):
            raise ValueError(f"Invalid station ID format: {station_id}")

    def _validate_collect_id(self, collect_id: str) -> None:
        """Validate collect ID format to prevent injection attacks."""
        if not collect_id or len(collect_id) > 100:
            raise ValueError(f"Invalid collect ID length: {len(collect_id)}")
        # Collect IDs should only contain alphanumeric characters, underscores, and hyphens
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', collect_id):
            raise ValueError(f"Invalid collect ID format: {collect_id}")

    async def _async_get_station_info(self, station_id: str) -> dict[str, Any]:
        """Get station information."""
        self._validate_station_id(station_id)

        if not self._token:
            await self.async_login()

        try:
            async with self._session.get(
                STATION_INFO_ENDPOINT,
                params={"stationId": station_id},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                return await self._async_unwrap_response(response)
        except aiohttp.ClientError as err:
            raise KSDataCloudConnectionError(f"Failed to get station info: {err}") from err

    async def _async_get_flow_power(self, station_id: str) -> dict[str, Any]:
        """Get power flow data."""
        self._validate_station_id(station_id)

        if not self._token:
            await self.async_login()

        params = {
            "stationId": station_id,
            "stime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            async with self._session.get(
                FLOW_POWER_ENDPOINT,
                params=params,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                return await self._async_unwrap_response(response)
        except aiohttp.ClientError as err:
            raise KSDataCloudConnectionError(f"Failed to get flow power: {err}") from err

    async def _async_get_device_logic(
        self, collect_id: str, station_id: str
    ) -> dict[str, Any]:
        """Get device logic data."""
        self._validate_collect_id(collect_id)
        self._validate_station_id(station_id)

        if not self._token:
            await self.async_login()

        try:
            async with self._session.get(
                DEVICE_LOGIC_ENDPOINT,
                params={"collectId": collect_id},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                return await self._async_unwrap_response(response)
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to get device logic for %s: %s", collect_id, err)
            return {}

    async def _async_get_device_navigation(
        self, collect_id: str, station_id: str
    ) -> dict[str, Any]:
        """Get device navigation data."""
        self._validate_collect_id(collect_id)
        self._validate_station_id(station_id)

        if not self._token:
            await self.async_login()

        try:
            async with self._session.get(
                DEVICE_NAVIGATION_ENDPOINT,
                params={"collectId": collect_id},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                return await self._async_unwrap_response(response)
        except aiohttp.ClientError as err:
            _LOGGER.warning(
                "Failed to get device navigation for %s: %s", collect_id, err
            )
            return {}

    async def _async_get_device_data(
        self, collect_id: str, station_id: str
    ) -> dict[str, Any]:
        """Get combined device data."""
        logic, navigation = await asyncio.gather(
            self._async_get_device_logic(collect_id, station_id),
            self._async_get_device_navigation(collect_id, station_id),
        )

        return {
            "collect_id": collect_id,
            "name": navigation.get("deviceName"),
            "serial_number": navigation.get("sn"),
            "model": navigation.get("deviceModel"),
            "status": navigation.get("status"),
            "faults": navigation.get("faults"),
            "bind_name": navigation.get("bindName"),
            "is_bound": navigation.get("isbind"),
            "timestamp": navigation.get("saveTime"),
            "metrics": logic,
        }

    def _build_station_report(
        self,
        station_id: str,
        station_info: dict[str, Any],
        flow_power: dict[str, Any],
        devices: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build station report."""
        return {
            "station_id": station_id,
            "station_name": station_info.get("stationName"),
            "location": {
                "address": station_info.get("stationAddress"),
                "country": station_info.get("country"),
                "timezone": station_info.get("timeZone"),
                "latitude": station_info.get("latitude"),
                "longitude": station_info.get("longitude"),
            },
            "owner": {
                "name": station_info.get("ownerName"),
                "email": station_info.get("ownerEmail"),
                "phone": station_info.get("ownerPhone"),
            },
            "station": {
                "installed_capacity": station_info.get("installedCapacity"),
                "electricity_unit": station_info.get("elecUnit"),
                "grid_time": station_info.get("gridTime"),
                "collect_ids": station_info.get("collectList") or [],
            },
            "overview": {
                "timestamp": flow_power.get("saveTime"),
                "pv_power": flow_power.get("pvp", 0),
                "battery_soc": flow_power.get("soc", 0),
                "battery_power": flow_power.get("batcdp", 0),
                "grid_power": flow_power.get("gridmp", 0),
                "load_power": flow_power.get("balp", 0),
                "daily_generation": flow_power.get("dgepv", 0),
                "daily_charge": flow_power.get("batcdelc", 0),
                "daily_discharge": flow_power.get("batdisdelc", 0),
                "daily_consumption": flow_power.get("dbalec", 0),
                "daily_grid_import": flow_power.get("decp", 0),
                "daily_grid_export": flow_power.get("decsell", 0),
            },
            "devices": devices,
        }

    async def async_get_station_data(
        self, station_id: str, _retry: bool = True
    ) -> dict[str, Any]:
        """Get all station data."""
        try:
            # Get station info first (has collect_ids)
            station_info = await self._async_get_station_info(station_id)
            collect_ids = station_info.get("collectList") or []

            # Fetch devices and flow_power in parallel
            device_tasks = [
                self._async_get_device_data(cid, station_id) for cid in collect_ids
            ]

            if device_tasks:
                devices, flow_power = await asyncio.gather(
                    asyncio.gather(*device_tasks),
                    self._async_get_flow_power(station_id),
                )
                devices = list(devices)
            else:
                devices = []
                flow_power = await self._async_get_flow_power(station_id)

            return self._build_station_report(
                station_id, station_info, flow_power, devices
            )

        except KSDataCloudAuthError:
            if not _retry:
                raise
            # Token expired, try to re-login once
            _LOGGER.info("Token expired, re-authenticating")
            await self.async_login()
            return await self.async_get_station_data(station_id, _retry=False)
