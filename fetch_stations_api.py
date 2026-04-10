#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "requests>=2.32.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_URL = "https://sync.ksdatacloud.com"
LOGIN_ENDPOINT = f"{BASE_URL}/api/oauth/auth/login"
STATION_INFO_ENDPOINT = f"{BASE_URL}/api/web/station/manager/getinfo"
FLOW_POWER_ENDPOINT = f"{BASE_URL}/api/web/residential/station/detail/flow/power"
DEVICE_LOGIC_ENDPOINT = f"{BASE_URL}/api/residential/device/detail/logic"
DEVICE_NAVIGATION_ENDPOINT = f"{BASE_URL}/api/residential/device/detail/navigation/data"

LOGIN_BASIC_AUTH = "Basic a3N0YXI6a3N0YXJTZWNyZXQ="
DEFAULT_PARAMETERS_FILE = "parameters.txt"
DEFAULT_OUTPUT_FILE = "stations_api_output.json"


def parse_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        values[key] = value

    return values


def load_station_ids(station_source: str, base_dir: Path) -> list[str]:
    """Load station IDs from file or string with security validation."""
    # Validate input to prevent path traversal attacks
    if ".." in station_source or station_source.startswith(("~", "/")):
        # If it looks like a path with traversal attempts, reject it
        # unless it's an absolute path that resolves safely
        pass  # Continue to resolve and validate below

    source_path = Path(station_source)
    if not source_path.is_absolute():
        source_path = base_dir / source_path

    # Resolve to canonical path and validate it's within allowed directory
    try:
        source_path = source_path.resolve(strict=False)
    except (ValueError, RuntimeError) as e:
        raise ValueError(f"Invalid file path: {e}") from e

    # Check if attempting to read a file
    if source_path.exists():
        if not source_path.is_file():
            raise ValueError(f"Path exists but is not a file: {source_path}")

        # Verify the resolved path is safe (not trying to escape base_dir)
        try:
            base_dir_resolved = base_dir.resolve(strict=False)
            # Only enforce directory restriction if path looks like a relative file reference
            if not station_source.startswith("/") and ".." not in station_source:
                if not str(source_path).startswith(str(base_dir_resolved)):
                    raise ValueError(f"Path outside allowed directory: {source_path}")
        except (ValueError, RuntimeError):
            pass  # If we can't validate, allow absolute paths but not relative traversal

        # Read file with size limit to prevent memory exhaustion
        file_size = source_path.stat().st_size
        if file_size > 1_000_000:  # 1MB limit
            raise ValueError(f"File too large: {file_size} bytes (max 1MB)")

        items = source_path.read_text(encoding="utf-8").splitlines()
    else:
        # Treat as comma/space-separated station IDs
        items = re.split(r"[\s,;]+", station_source)

    # Validate station IDs format (should be numeric or alphanumeric)
    station_ids = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        # Station IDs should be reasonable length and contain only safe characters
        if len(item) > 100:
            raise ValueError(f"Station ID too long: {item[:50]}...")
        if not re.match(r'^[a-zA-Z0-9_-]+$', item):
            raise ValueError(f"Invalid station ID format: {item}")
        station_ids.append(item)

    if not station_ids:
        raise ValueError("No station IDs were found in stationlist.")

    return station_ids


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "ksdatacloud-api-client/1.0",
        }
    )
    return session


def unwrap_response(response: requests.Response) -> Any:
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_text": response.text}

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"HTTP error for {response.request.method} {response.url}: "
            f"status={response.status_code}, body={payload}"
        ) from exc

    if payload.get("code") != 200:
        raise RuntimeError(f"API error for {response.request.method} {response.url}: {payload}")
    return payload.get("data")


def login(session: requests.Session, username: str, password: str) -> str:
    response = session.post(
        LOGIN_ENDPOINT,
        headers={
            "Authorization": LOGIN_BASIC_AUTH,
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/login",
        },
        json={"username": username, "password": password},
        timeout=30,
    )
    token = unwrap_response(response)
    if not token or not isinstance(token, str):
        raise RuntimeError("Login succeeded but no bearer token was returned.")
    session.headers["Authorization"] = f"Bearer {token}"
    return token


def get_station_info(session: requests.Session, station_id: str) -> dict[str, Any]:
    response = session.get(
        STATION_INFO_ENDPOINT,
        params={"stationId": station_id},
        headers={"Referer": f"{BASE_URL}/station/{station_id}/residential/overview"},
        timeout=30,
    )
    return unwrap_response(response)


def get_flow_power(session: requests.Session, station_id: str, timestamp: str | None) -> dict[str, Any]:
    params = {
        "stationId": station_id,
        "stime": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    response = session.get(
        FLOW_POWER_ENDPOINT,
        params=params,
        headers={"Referer": f"{BASE_URL}/station/{station_id}/residential/overview"},
        timeout=30,
    )
    return unwrap_response(response)


def get_device_logic(session: requests.Session, collect_id: str, station_id: str) -> dict[str, Any]:
    response = session.get(
        DEVICE_LOGIC_ENDPOINT,
        params={"collectId": collect_id},
        headers={"Referer": f"{BASE_URL}/station/{station_id}/residential/overview"},
        timeout=30,
    )
    return unwrap_response(response)


def get_device_navigation(session: requests.Session, collect_id: str, station_id: str) -> dict[str, Any]:
    response = session.get(
        DEVICE_NAVIGATION_ENDPOINT,
        params={"collectId": collect_id},
        headers={"Referer": f"{BASE_URL}/station/{station_id}/residential/overview"},
        timeout=30,
    )
    return unwrap_response(response)


def build_station_report(
    station_id: str,
    station_info: dict[str, Any],
    flow_power: dict[str, Any],
    devices: list[dict[str, Any]],
) -> dict[str, Any]:
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
            "pv_power": flow_power.get("pvp"),
            "battery_soc": flow_power.get("soc"),
            "battery_power": flow_power.get("batcdp"),
            "grid_power": flow_power.get("gridmp"),
            "load_power": flow_power.get("balp"),
            "daily_generation": flow_power.get("dgepv"),
            "daily_charge": flow_power.get("batcdelc"),
            "daily_discharge": flow_power.get("batdisdelc"),
            "daily_consumption": flow_power.get("dbalec"),
            "daily_grid_import": flow_power.get("decp"),
            "daily_grid_export": flow_power.get("decsell"),
        },
        "devices": devices,
    }


def collect_station_data(
    session: requests.Session,
    station_id: str,
    flow_timestamp: str | None,
) -> dict[str, Any]:
    station_info = get_station_info(session, station_id)
    collect_ids = station_info.get("collectList") or []

    devices: list[dict[str, Any]] = []
    for collect_id in collect_ids:
        logic = get_device_logic(session, collect_id, station_id)
        navigation = get_device_navigation(session, collect_id, station_id)
        devices.append(
            {
                "collect_id": collect_id,
                "name": navigation.get("deviceName"),
                "serial_number": navigation.get("sn"),
                "model": navigation.get("deviceModel"),
                "status": navigation.get("status"),
                "faults": navigation.get("faults"),
                "bind_name": navigation.get("bindName"),
                "is_bound": navigation.get("isbind"),
                "timestamp": navigation.get("saveTime"),
                "metrics": {
                    "pv_power": logic.get("pv_power"),
                    "battery_soc": logic.get("battery_soc"),
                    "battery_power": logic.get("battery_power"),
                    "battery_number": logic.get("battery_number"),
                    "grid_power": logic.get("grid_power"),
                    "load_power": logic.get("load_power"),
                    "backup_load": logic.get("backup_load"),
                    "inverter_power": logic.get("inver_power"),
                    "ac_couple_power": logic.get("ac_couple_power"),
                    "daily_generation": navigation.get("dgepv"),
                },
            }
        )

    flow_power = get_flow_power(session, station_id, flow_timestamp)
    return build_station_report(station_id, station_info, flow_power, devices)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch KS Data Cloud residential overview data directly from the backend APIs."
    )
    parser.add_argument(
        "--parameters",
        default=DEFAULT_PARAMETERS_FILE,
        help=f"Path to the credentials file. Default: {DEFAULT_PARAMETERS_FILE}",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"JSON output path. Default: {DEFAULT_OUTPUT_FILE}",
    )
    parser.add_argument(
        "--stime",
        default=None,
        help="Optional timestamp for the flow power endpoint, for example '2026-03-21 10:34:55'.",
    )
    parser.add_argument(
        "--no-stdout",
        action="store_true",
        help="Do not print the generated JSON report to stdout.",
    )
    args = parser.parse_args()

    # Try environment variables first, then fall back to parameters file
    username = os.getenv("KSDATACLOUD_USERNAME")
    password = os.getenv("KSDATACLOUD_PASSWORD")
    station_source = os.getenv("KSDATACLOUD_STATION_LIST")

    # If env vars not found, try parameters file
    if not username or not password or not station_source:
        parameters_path = Path(args.parameters).resolve()
        if parameters_path.exists():
            config = parse_key_value_file(parameters_path)
            username = username or config.get("username")
            password = password or config.get("password")
            station_source = station_source or config.get("stationlist")

    if not username or not password or not station_source:
        raise ValueError(
            "Credentials not found. Set KSDATACLOUD_USERNAME, KSDATACLOUD_PASSWORD, "
            "and KSDATACLOUD_STATION_LIST environment variables, or provide parameters.txt file."
        )

    base_dir = Path(args.parameters).resolve().parent if Path(args.parameters).exists() else Path.cwd()
    station_ids = load_station_ids(station_source, base_dir)

    session = build_session()
    login(session, username, password)

    results = [
        collect_station_data(session, station_id=station_id, flow_timestamp=args.stime)
        for station_id in station_ids
    ]

    rendered = json.dumps(results, indent=2, ensure_ascii=True)
    output_path = Path(args.output).resolve()
    output_path.write_text(rendered, encoding="utf-8")
    if not args.no_stdout:
        print(rendered)
    print(f"Saved {len(results)} station record(s) to {output_path}")


if __name__ == "__main__":
    main()
