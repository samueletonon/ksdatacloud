# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Home Assistant custom component** with full native integration
  - 7 sensor entities (PV power, battery SoC/power, grid power, load power, daily generation/consumption)
  - UI-based configuration flow (no YAML editing required)
  - Energy dashboard compatibility with proper device classes and state classes
  - Device registry integration grouping all sensors under station device
  - Automatic 5-minute polling with error recovery
  - Async API client using aiohttp
  - Token management with automatic refresh on expiration
  - Comprehensive error handling and logging
- Installation and usage documentation for Home Assistant integration
- Test script for validating async API conversion (`test_async_simple.py`)

### Changed
- Moved CHANGELOG to separate file
- Moved LICENSE to separate file
- Moved CONTRIBUTING guidelines to separate file
- Added `aiohttp>=3.8.0` to project dependencies

## [0.1.0] - 2026-03-24

### Added
- Browser automation scraper (`fetch_stations.py`)
- Direct API client (`fetch_stations_api.py`)
- Network flow inspector (`inspect_api_flow.py`)
- Environment variable support via `.env` files
- uv dependency management with `pyproject.toml`
- Comprehensive README with installation and usage instructions
- Security improvements (`.gitignore`, credential management)
- Support for multiple stations
- Historical data retrieval via `--stime` parameter
- Playwright browser automation for data collection

### Security
- Added `.env` file support for secure credential storage
- Credentials file secured with chmod 600
- Added `.gitignore` to prevent committing secrets and output files

[unreleased]: https://github.com/yourusername/ksdatacloud/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/ksdatacloud/releases/tag/v0.1.0
