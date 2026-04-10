# KS Data Cloud Collector

A data collection and analysis tool for solar/battery residential monitoring stations on the [KS Data Cloud platform](https://sync.ksdatacloud.com).

## Overview

This project provides automated data collection from KS Data Cloud residential solar/battery monitoring systems. It supports multiple collection methods:

- **Browser Automation** - Scrapes data using Playwright to simulate user interactions
- **Direct API Access** - Connects directly to the REST API for structured data retrieval
- **Network Flow Analysis** - Captures and documents API traffic for debugging

## Features

- 🔐 Secure credential management via environment variables
- 🔄 Multiple data collection strategies (browser scraping + direct API)
- 📊 Structured JSON output with comprehensive metrics
- 🏠 Multi-station support
- 🔍 Network traffic inspection for API discovery
- ⚡ Async/await for efficient data collection
- 🏡 **Home Assistant custom component** for native integration

## Quick Start

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to project directory
cd ksdatacloud

# 3. Install dependencies
uv sync

# 4. Install Playwright browsers
uv run playwright install firefox

# 5. Configure credentials
cp .env.example .env
# Edit .env with your credentials

# 6. Run data collection
uv run fetch_stations_api.py
```

## Home Assistant Integration 🏡

**NEW:** Native Home Assistant custom component for real-time monitoring!

The project now includes a full Home Assistant integration with:
- ✅ 7 sensor entities (PV power, battery, grid, load, daily totals)
- ✅ UI-based configuration (no YAML editing)
- ✅ Energy dashboard compatibility
- ✅ Device registry integration
- ✅ Automatic 5-minute updates
- ✅ Error recovery & token refresh

**Quick Setup:**
```bash
# Copy integration to Home Assistant
cp -r custom_components/ksdatacloud /path/to/homeassistant/config/custom_components/

# Restart Home Assistant, then:
# Settings → Devices & Services → Add Integration → "KS Data Cloud"
```

📖 **[Full Installation Guide](docs/HA_INSTALLATION.md)**

📋 **[Integration Details](docs/HOME_ASSISTANT.md)**

## Installation

### Prerequisites

- **Python 3.9 or higher** - Check with `python --version` or `python3 --version`
- **[uv](https://github.com/astral-sh/uv)** - Modern Python package manager (recommended)
- **Node.js 18+** - For Playwright (check with `node --version`)

### Installing uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (using pip):**
```bash
pip install uv
```

### Step-by-Step Setup

1. **Navigate to project directory**

   ```bash
   cd /path/to/ksdatacloud
   ```

2. **Install Python dependencies**

   Using uv (recommended):
   ```bash
   uv sync
   ```

   This creates a virtual environment at `.venv/` and installs:
   - `playwright` - Browser automation
   - `requests` - HTTP client
   - `python-dotenv` - Environment variable management

   **Alternative using pip:**
   ```bash
   pip install playwright requests python-dotenv
   ```

3. **Install Playwright browsers**

   ```bash
   uv run playwright install firefox
   ```

   This downloads the Firefox browser (~85MB). Required for browser-based scraping.

   **Alternative using pip:**
   ```bash
   python -m playwright install firefox
   ```

   **Optional:** Install Chromium for the network inspector:
   ```bash
   uv run playwright install chromium
   ```

4. **Configure credentials**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your favorite text editor:
   ```bash
   nano .env
   # or
   vim .env
   # or
   code .env
   ```

   Add your KS Data Cloud credentials:
   ```bash
   KSDATACLOUD_USERNAME=your.email@example.com
   KSDATACLOUD_PASSWORD=your_password_here
   KSDATACLOUD_STATION_LIST=2099123100000000
   ```

   **Multiple stations:** Use comma-separated IDs:
   ```bash
   KSDATACLOUD_STATION_LIST=station1,station2,station3
   ```

   **Station list file:** Or specify a file path:
   ```bash
   KSDATACLOUD_STATION_LIST=stations.txt
   ```
   Where `stations.txt` contains one station ID per line.

5. **Verify installation**

   Test that everything works:
   ```bash
   uv run fetch_stations_api.py --no-stdout
   ```

   You should see:
   ```
   Saved 1 station record(s) to /path/to/stations_api_output.json
   ```

## How to Execute

### Method 1: Using uv (Recommended)

The scripts are designed to run with `uv run`, which automatically manages dependencies:

```bash
uv run fetch_stations_api.py
```

**Why use `uv run`?**
- ✓ Automatically activates virtual environment
- ✓ Manages inline script dependencies
- ✓ No need to manually activate `.venv`
- ✓ Works the same on all platforms

### Method 2: Direct Execution

The scripts have a shebang and can be executed directly (after making them executable):

```bash
chmod +x fetch_stations_api.py
./fetch_stations_api.py
```

This works because the shebang `#!/usr/bin/env -S uv run --script` tells the system to use uv.

### Method 3: Using the Virtual Environment

If you prefer the traditional approach:

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Run script
python fetch_stations_api.py

# Deactivate when done
deactivate
```

## Usage Examples

### 1. Direct API Collection (Recommended)

Fetches structured data directly from the REST API - fastest and most reliable:

```bash
# Basic usage - prints JSON to console and saves to file
uv run fetch_stations_api.py

# Save only (no console output)
uv run fetch_stations_api.py --no-stdout

# Custom output file
uv run fetch_stations_api.py --output my_data.json

# Get historical data (if available)
uv run fetch_stations_api.py --stime "2026-03-21 10:34:55"

# Multiple options combined
uv run fetch_stations_api.py --output data.json --no-stdout
```

**Output file:** `stations_api_output.json` (or custom name)

**What you get:**
- Station metadata (name, location, owner)
- Real-time power metrics (PV, battery, grid, load)
- Daily totals (generation, consumption, import/export)
- Device-level data for all connected inverters

### 2. Browser-Based Scraping

Collects data by automating a Firefox browser session - useful when API is unavailable:

```bash
# Basic usage (headless mode)
uv run fetch_stations.py

# Show browser window (useful for debugging)
uv run fetch_stations.py --headful

# Custom output file
uv run fetch_stations.py --output browser_data.json

# Use custom credentials file (legacy)
uv run fetch_stations.py --parameters my_creds.txt

# Watch the browser work
uv run fetch_stations.py --headful --output test.json
```

**Output file:** `stations_output.json` (or custom name)

**What you get:**
- Raw HTML content from the station overview page
- Tables, headings, and card data
- Less structured than API output

**When to use:**
- API is down or changed
- Need to see exactly what the web UI shows
- Debugging UI changes

### 3. Network Flow Inspector

Captures all API requests/responses during a browser session - for debugging and API discovery:

```bash
# Basic usage with Firefox
uv run inspect_api_flow.py

# Use Chromium instead
uv run inspect_api_flow.py --browser chromium

# Show browser window
uv run inspect_api_flow.py --headful

# Custom output file
uv run inspect_api_flow.py --output network_log.json

# Full featured debugging session
uv run inspect_api_flow.py --browser chromium --headful --output debug.json
```

**Output file:** `api_flow_output.json` (or custom name)

**What you get:**
- Complete network traffic log
- All API requests and responses
- Request/response headers
- Request payloads and response bodies
- Console messages from the page

**When to use:**
- Debugging authentication issues
- Discovering new API endpoints
- Understanding the login flow
- Investigating errors

## Command Reference

### fetch_stations_api.py

| Option | Description | Default |
|--------|-------------|---------|
| `--parameters <file>` | Path to credentials file | `parameters.txt` |
| `--output <file>` | JSON output file path | `stations_api_output.json` |
| `--stime <timestamp>` | Historical data timestamp | Current time |
| `--no-stdout` | Don't print JSON to console | Print enabled |

**Examples:**
```bash
# Get current data
uv run fetch_stations_api.py

# Get yesterday's data at 2pm
uv run fetch_stations_api.py --stime "2026-03-24 14:00:00"

# Save to custom location
uv run fetch_stations_api.py --output ~/Desktop/solar_data.json
```

### fetch_stations.py

| Option | Description | Default |
|--------|-------------|---------|
| `--parameters <file>` | Path to credentials file | `parameters.txt` |
| `--output <file>` | JSON output file path | `stations_output.json` |
| `--headful` | Show browser window | Headless mode |

**Examples:**
```bash
# Headless data collection
uv run fetch_stations.py

# Watch the browser (debugging)
uv run fetch_stations.py --headful

# Multiple stations with custom output
uv run fetch_stations.py --output all_stations.json
```

### inspect_api_flow.py

| Option | Description | Default |
|--------|-------------|---------|
| `--parameters <file>` | Path to credentials file | `parameters.txt` |
| `--output <file>` | JSON output file path | `api_flow_output.json` |
| `--browser <engine>` | Browser engine (firefox/chromium) | `firefox` |
| `--headful` | Show browser window | Headless mode |

**Examples:**
```bash
# Capture network traffic with Firefox
uv run inspect_api_flow.py

# Use Chromium and watch
uv run inspect_api_flow.py --browser chromium --headful

# Save to specific location
uv run inspect_api_flow.py --output ~/logs/api_capture.json
```

## Output Data Format

### API Output Structure

```json
{
  "station_id": "XXXXXXXXXXXXXXXX",
  "station_name": "AAAA BBBB",
  "location": {
    "address": "street city",
    "country": "country",
    "timezone": "Europe/Amsterdam",
    "latitude": xxxx,
    "longitude": xxxx
  },
  "owner": {
    "name": "Owner Name",
    "email": "owner@example.com",
    "phone": "+31..."
  },
  "station": {
    "installed_capacity": 5.0,
    "electricity_unit": "kWh",
    "grid_time": "2024-01-15 10:30:00",
    "collect_ids": ["device_1", "device_2"]
  },
  "overview": {
    "timestamp": "2026-03-24 14:30:00",
    "pv_power": 3200,
    "battery_soc": 85,
    "battery_power": -500,
    "grid_power": 200,
    "load_power": 2900,
    "daily_generation": 18.5,
    "daily_charge": 12.3,
    "daily_discharge": 8.7,
    "daily_consumption": 25.2,
    "daily_grid_import": 5.4,
    "daily_grid_export": 2.1
  },
  "devices": [
    {
      "collect_id": "device_1",
      "name": "Inverter 1",
      "serial_number": "SN12345678",
      "model": "HY5000",
      "status": "online",
      "metrics": {
        "pv_power": 3200,
        "battery_soc": 85,
        "battery_power": -500,
        "grid_power": 200,
        "load_power": 2900
      }
    }
  ]
}
```

## API Endpoints

The tool interacts with these KS Data Cloud endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/api/oauth/auth/login` | Authentication (returns Bearer token) |
| `/api/web/station/manager/getinfo` | Station metadata (location, owner, devices) |
| `/api/web/residential/station/detail/flow/power` | Real-time power flow and daily totals |
| `/api/residential/device/detail/logic` | Device-level metrics |
| `/api/residential/device/detail/navigation/data` | Device status and navigation info |

**Authentication:**
- Uses Basic Auth with hardcoded client credentials
- Returns JWT Bearer token for subsequent requests
- Token passed in `Authorization: Bearer <token>` header

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `KSDATACLOUD_USERNAME` | Login email | `your.email@example.com` |
| `KSDATACLOUD_PASSWORD` | Login password | `your_password` |
| `KSDATACLOUD_STATION_LIST` | Station IDs (comma-separated) or file path | `station1,station2` |

### Legacy Configuration (parameters.txt)

If environment variables are not set, the scripts fall back to reading `parameters.txt`:

```
username="your.email@example.com"
password="your_password"
stationlist="2099123100000000"
```

**⚠️ Security Note:** The `parameters.txt` method is deprecated. Always use `.env` for credential storage.

## Project Structure

```
ksdatacloud/
├── fetch_stations.py           # Browser automation scraper
├── fetch_stations_api.py        # Direct API client
├── inspect_api_flow.py          # Network traffic analyzer
├── pyproject.toml               # Python project configuration (uv)
├── package.json                 # Node.js dependencies (Playwright)
├── playwright.config.ts         # Playwright test configuration
├── .env                         # Credentials (DO NOT COMMIT)
├── .env.example                 # Credential template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # ISC License
├── docs/                        # Documentation
│   ├── HOME_ASSISTANT.md        # HA integration architecture
│   └── HA_INSTALLATION.md       # HA installation guide
├── custom_components/           # Home Assistant integration
│   └── ksdatacloud/            # Custom component files
└── tests/                       # Test directory
    └── example.spec.ts          # Example Playwright tests
```

## Development

### Running with uv

The scripts use uv's inline dependency syntax:

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "playwright>=1.52.0",
#   "requests>=2.32.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
```

This allows running scripts directly without virtual environment setup:

```bash
uv run fetch_stations_api.py
```

### Installing Development Dependencies

```bash
uv sync --dev
```

This installs:
- `black` - Code formatter
- `mypy` - Type checker
- `pytest` - Test framework

### Code Formatting

```bash
uv run black *.py
```

### Type Checking

```bash
uv run mypy fetch_stations.py fetch_stations_api.py inspect_api_flow.py
```

## Troubleshooting

### Authentication Errors

**Problem:** `Login succeeded but no bearer token was returned`

**Solution:** Check that credentials are correct and the API hasn't changed. Use `inspect_api_flow.py` to debug the login flow.

### Selector Errors

**Problem:** `None of the selectors matched`

**Solution:** The web UI may have changed. Run with `--headful` to see the page, then update selectors in the script.

### Browser Not Found

**Problem:** `Executable doesn't exist`

**Solution:** Install Playwright browsers:
```bash
uv run playwright install firefox
```

### Missing Environment Variables

**Problem:** `Credentials not found. Set KSDATACLOUD_USERNAME...`

**Solution:**
1. Verify `.env` file exists and has correct values
2. Or create `parameters.txt` with credentials (legacy method)

## Security Considerations

- ✅ **Never commit credentials** - `.env` and `parameters.txt` are in `.gitignore`
- ✅ **Use environment variables** - Prefer `.env` over `parameters.txt`
- ✅ **Secure file permissions** - Set `chmod 600 .env` on Unix systems
- ⚠️ **API credentials in code** - `LOGIN_BASIC_AUTH` is hardcoded (KS Data Cloud public client ID)
- ⚠️ **Output files** - May contain sensitive data; `.gitignore` excludes all `*.json` files

## Support

For issues related to:
- **This tool**: Open an issue in this repository
- **KS Data Cloud platform**: Contact KS Data Cloud support
- **Playwright**: Visit [Playwright documentation](https://playwright.dev)

## License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting enhancements
- Submitting pull requests
- Code style guidelines
- Development workflow

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.
