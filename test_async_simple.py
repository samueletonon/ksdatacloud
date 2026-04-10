#!/usr/bin/env python3
"""Simple test for async API conversion."""
import asyncio
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://sync.ksdatacloud.com"
LOGIN_ENDPOINT = f"{BASE_URL}/api/oauth/auth/login"
FLOW_POWER_ENDPOINT = f"{BASE_URL}/api/web/residential/station/detail/flow/power"
LOGIN_BASIC_AUTH = "Basic a3N0YXI6a3N0YXJTZWNyZXQ="


async def test_async_api():
    """Test async API calls."""
    username = os.getenv("KSDATACLOUD_USERNAME")
    password = os.getenv("KSDATACLOUD_PASSWORD")
    station_id = os.getenv("KSDATACLOUD_STATION_LIST")

    if not all([username, password, station_id]):
        print("❌ Missing environment variables")
        return False

    print(f"Testing async API with station: {station_id}\n")

    async with aiohttp.ClientSession() as session:
        try:
            # Test login
            print("1. Testing login...")
            async with session.post(
                LOGIN_ENDPOINT,
                headers={
                    "Authorization": LOGIN_BASIC_AUTH,
                    "Content-Type": "application/json",
                    "Origin": BASE_URL,
                    "Referer": f"{BASE_URL}/login",
                },
                json={"username": username, "password": password},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                data = await response.json()
                if data.get("code") != 200:
                    print(f"❌ Login failed: {data}")
                    return False
                token = data.get("data")
                print(f"✅ Login successful")

            # Test get flow power
            print("\n2. Testing get flow power...")
            async with session.get(
                FLOW_POWER_ENDPOINT,
                params={"stationId": station_id, "stime": "2026-03-25 10:00:00"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                data = await response.json()
                if data.get("code") != 200:
                    print(f"❌ Get flow power failed: {data}")
                    return False
                flow_data = data.get("data")
                print(f"✅ Flow power retrieved")
                print(f"   PV Power: {flow_data.get('pvp', 0)} W")
                print(f"   Battery SoC: {flow_data.get('soc', 0)} %")
                print(f"   Battery Power: {flow_data.get('batcdp', 0)} W")
                print(f"   Grid Power: {flow_data.get('gridmp', 0)} W")
                print(f"   Load Power: {flow_data.get('balp', 0)} W")

            print("\n✅ All async API tests passed!")
            return True

        except Exception as err:
            print(f"\n❌ Error: {err}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_async_api())
    exit(0 if success else 1)
