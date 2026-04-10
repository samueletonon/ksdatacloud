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

from playwright.async_api import BrowserType, Page, Request, Response, async_playwright

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


LOGIN_URL = "https://sync.ksdatacloud.com/login"
STATION_URL_TEMPLATE = "https://sync.ksdatacloud.com/station/{station_id}/residential/overview"
DEFAULT_PARAMETERS_FILE = "parameters.txt"
DEFAULT_OUTPUT_FILE = "api_flow_output.json"
MAX_BODY_PREVIEW = 4000


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
    await page.set_viewport_size({"width": 1920, "height": 937})

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

    await username_input.fill(username)

    focus_reset = page.locator(".bg-card\\/95")
    if await focus_reset.count():
        await focus_reset.first.click()

    await password_input.fill(password)
    await login_button.click()
    await page.wait_for_url(re.compile(r"https://sync\.ksdatacloud\.com/(?!login).*"), timeout=30000)


def is_interesting_request(request: Request) -> bool:
    if "sync.ksdatacloud.com" not in request.url:
        return False
    return request.resource_type in {"document", "fetch", "xhr"}


def trim_text(value: str | None, limit: int = MAX_BODY_PREVIEW) -> str | None:
    if value is None:
        return None
    return value if len(value) <= limit else value[:limit] + "\n...[truncated]"


async def build_response_entry(response: Response) -> dict[str, Any]:
    request = response.request
    headers = await response.all_headers()
    content_type = headers.get("content-type", "")
    body_preview: str | None = None

    if "application/json" in content_type:
        try:
            json_body = await response.json()
            body_preview = trim_text(json.dumps(json_body, indent=2, ensure_ascii=True))
        except Exception as exc:
            body_preview = f"<failed to parse json: {exc}>"
    elif "text/" in content_type or "html" in content_type:
        try:
            body_preview = trim_text(await response.text())
        except Exception as exc:
            body_preview = f"<failed to read text body: {exc}>"

    post_data = request.post_data
    return {
        "method": request.method,
        "url": request.url,
        "resource_type": request.resource_type,
        "status": response.status,
        "ok": response.ok,
        "request_headers": request.headers,
        "request_post_data": trim_text(post_data),
        "response_headers": headers,
        "response_body_preview": body_preview,
    }


async def inspect_flow(
    browser_type: BrowserType,
    username: str,
    password: str,
    station_id: str,
    headful: bool,
) -> dict[str, Any]:
    browser = await browser_type.launch(headless=not headful)
    context = await browser.new_context()
    page = await context.new_page()

    events: list[dict[str, Any]] = []

    async def on_response(response: Response) -> None:
        if is_interesting_request(response.request):
            events.append(await build_response_entry(response))

    page.on("response", on_response)

    console_messages: list[str] = []
    page.on("console", lambda message: console_messages.append(f"{message.type}: {message.text}"))

    await login(page, username, password)
    station_url = STATION_URL_TEMPLATE.format(station_id=station_id)
    await page.goto(station_url, wait_until="networkidle")

    cookies = await context.cookies()
    title = await page.title()
    final_url = page.url

    await context.close()
    await browser.close()

    return {
        "login_url": LOGIN_URL,
        "station_url": station_url,
        "final_url": final_url,
        "page_title": title,
        "cookies": cookies,
        "console_messages": console_messages,
        "events": events,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect the network/API flow used by the KS Data Cloud station overview page."
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
        "--browser",
        choices=["firefox", "chromium"],
        default="firefox",
        help="Browser engine to use for inspection. Default: firefox",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run with a visible browser window.",
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
    station_id = station_ids[0]

    async with async_playwright() as playwright:
        browser_type = getattr(playwright, args.browser)
        result = await inspect_flow(browser_type, username, password, station_id, args.headful)

    output_path = Path(args.output).resolve()
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Saved API flow capture for station {station_id} to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
