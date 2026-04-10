#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "playwright>=1.52.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, Page, TimeoutError, async_playwright

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


LOGIN_URL = "https://sync.ksdatacloud.com/login"
STATION_URL_TEMPLATE = "https://sync.ksdatacloud.com/station/{station_id}/residential/overview"
DEFAULT_PARAMETERS_FILE = "parameters.txt"
DEFAULT_OUTPUT_FILE = "stations_output.json"


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
    source_path = Path(station_source)
    if not source_path.is_absolute():
        source_path = base_dir / source_path

    if source_path.exists() and source_path.is_file():
        items = source_path.read_text(encoding="utf-8").splitlines()
    else:
        items = re.split(r"[\s,;]+", station_source)

    station_ids = [item.strip() for item in items if item.strip()]
    if not station_ids:
        raise ValueError("No station IDs were found in stationlist.")

    return station_ids


async def find_first_locator(page: Page, selectors: list[str]):
    for selector in selectors:
        locator = page.locator(selector)
        if await locator.count():
            return locator.first

    raise ValueError(f"None of the selectors matched: {selectors}")


async def login(page: Page, username: str, password: str) -> None:
    await page.goto(LOGIN_URL, wait_until="networkidle")

    username_input = await find_first_locator(
        page,
        [
            r"#\ABr5\BB-form-item",
            'input[type="email"]',
            'input[name="email"]',
            'input[autocomplete="username"]',
            'input:not([type="password"])',
        ],
    )
    password_input = await find_first_locator(
        page,
        [
            r"#\ABr6\BB-form-item",
            'input[type="password"]',
            'input[name="password"]',
            'input[autocomplete="current-password"]',
        ],
    )
    login_button = await find_first_locator(
        page,
        [
            'button:has-text("Login")',
            '.text-kstar-foreground',
            'button[type="submit"]',
        ],
    )

    await username_input.click()
    await username_input.fill(username)

    # Matches the recorded flow where focus is moved away before entering the password.
    focus_reset = page.locator(".bg-card\\/95")
    if await focus_reset.count():
        await focus_reset.first.click()

    await password_input.click()
    await password_input.fill(password)

    await login_button.click()
    await page.wait_for_url(re.compile(r"https://sync\.ksdatacloud\.com/(?!login).*"), timeout=30000)


async def extract_page_data(page: Page, station_id: str) -> dict[str, Any]:
    await page.wait_for_load_state("networkidle")

    try:
        await page.locator("main").wait_for(timeout=15000)
    except TimeoutError:
        pass

    data = await page.evaluate(
        """() => {
            const textOf = (element) => (element?.innerText || "").trim();

            const headings = Array.from(document.querySelectorAll("h1, h2, h3, h4"))
                .map((element) => textOf(element))
                .filter(Boolean);

            const tables = Array.from(document.querySelectorAll("table")).map((table) => {
                const headers = Array.from(table.querySelectorAll("thead th"))
                    .map((cell) => textOf(cell))
                    .filter(Boolean);
                const rows = Array.from(table.querySelectorAll("tbody tr")).map((row) =>
                    Array.from(row.querySelectorAll("td"))
                        .map((cell) => textOf(cell))
                        .filter(Boolean)
                ).filter((row) => row.length > 0);
                return { headers, rows };
            }).filter((table) => table.headers.length > 0 || table.rows.length > 0);

            const cards = Array.from(document.querySelectorAll("[class*='card'], .ant-card"))
                .map((element) => textOf(element))
                .filter((text) => text && text.length <= 1000);

            return {
                url: window.location.href,
                title: document.title,
                headings,
                tables,
                cards,
                body_text: textOf(document.body),
            };
        }"""
    )

    return {"station_id": station_id, **data}


async def collect_station_data(
    browser: Browser,
    username: str,
    password: str,
    station_ids: list[str],
) -> list[dict[str, Any]]:
    context = await browser.new_context()
    page = await context.new_page()

    await login(page, username, password)

    results: list[dict[str, Any]] = []
    for station_id in station_ids:
        station_url = STATION_URL_TEMPLATE.format(station_id=station_id)
        await page.goto(station_url, wait_until="networkidle")
        results.append(await extract_page_data(page, station_id))

    await context.close()
    return results


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log in to KS Data Cloud and collect overview data for station IDs."
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
        "--headful",
        action="store_true",
        help="Run Firefox with a visible browser window.",
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

    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=not args.headful)
        try:
            results = await collect_station_data(browser, username, password, station_ids)
        finally:
            await browser.close()

    output_path = Path(args.output).resolve()
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Saved {len(results)} station record(s) to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
