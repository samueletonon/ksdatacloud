#!/usr/bin/env python3
"""Test script for KS Data Cloud API client."""
import asyncio
import logging
import os
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# Add the custom_components directory to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components/ksdatacloud"))

from api import KSDataCloudAPI
from exceptions import KSDataCloudAuthError, KSDataCloudConnectionError

# Setup logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()


async def test_api():
    """Test the API client."""
    username = os.getenv("KSDATACLOUD_USERNAME")
    password = os.getenv("KSDATACLOUD_PASSWORD")
    station_id = os.getenv("KSDATACLOUD_STATION_LIST")

    if not all([username, password, station_id]):
        print("Error: Missing environment variables")
        print("Please set KSDATACLOUD_USERNAME, KSDATACLOUD_PASSWORD, KSDATACLOUD_STATION_LIST")
        return False

    print(f"Testing API with station: {station_id}")

    async with aiohttp.ClientSession() as session:
        api = KSDataCloudAPI(session, username, password)

        try:
            # Test login
            print("\n1. Testing login...")
            token = await api.async_login()
            print(f"✓ Login successful")

            # Test get station data
            print("\n2. Testing get station data...")
            data = await api.async_get_station_data(station_id)
            print(f"✓ Station data retrieved")
            print(f"  Station name: {data['station_name']}")
            print(f"  Location: {data['location']['address']}")
            print(f"  PV Power: {data['overview']['pv_power']} W")
            print(f"  Battery SoC: {data['overview']['battery_soc']} %")
            print(f"  Battery Power: {data['overview']['battery_power']} W")
            print(f"  Grid Power: {data['overview']['grid_power']} W")
            print(f"  Load Power: {data['overview']['load_power']} W")
            print(f"  Daily Generation: {data['overview']['daily_generation']} kWh")
            print(f"  Daily Consumption: {data['overview']['daily_consumption']} kWh")
            print(f"  Devices: {len(data['devices'])}")

            print("\n✅ All tests passed!")
            return True

        except KSDataCloudAuthError as err:
            print(f"\n❌ Authentication error: {err}")
            return False
        except KSDataCloudConnectionError as err:
            print(f"\n❌ Connection error: {err}")
            return False
        except Exception as err:
            print(f"\n❌ Unexpected error: {err}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
