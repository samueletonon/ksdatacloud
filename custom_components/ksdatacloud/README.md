# KS Data Cloud Home Assistant Integration

This directory contains the Home Assistant custom component for KS Data Cloud solar/battery monitoring.

## Installation

### Option 1: Manual Installation

1. Copy the `custom_components/ksdatacloud` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "KS Data Cloud"
5. Enter your credentials and station ID

### Option 2: HACS Installation (Future)

This integration will be available via HACS once published.

## Configuration

The integration is configured via the Home Assistant UI:

1. **Email**: Your KS Data Cloud login email
2. **Password**: Your KS Data Cloud password
3. **Station ID**: Your station ID (found in the KS Data Cloud dashboard URL)

Example station URL: `https://sync.ksdatacloud.com/station/2099123100000000/residential/overview`
Station ID: `2099123100000000`

## Features

### Sensors Created

Each configured station creates 11 sensors:

1. **PV Power** (W) - Current solar generation power
2. **Battery State of Charge** (%) - Battery charge level
3. **Battery Power** (W) - Battery charging/discharging power (negative = charging)
4. **Grid Power** (W) - Grid import/export power (negative = export)
5. **Load Power** (W) - Home consumption power
6. **Daily Generation** (kWh) - Total solar generation today
7. **Daily Consumption** (kWh) - Total home consumption today
8. **Daily Battery Charge** (kWh) - Total battery charged today
9. **Daily Battery Discharge** (kWh) - Total battery discharged today
10. **Daily Grid Import** (kWh) - Total grid imported today
11. **Daily Grid Export** (kWh) - Total grid exported today

### Device Integration

All sensors are grouped under a single device in the device registry with:
- Device name: Your station name
- Manufacturer: KS Data Cloud
- Model: Solar Station
- Configuration URL: Link to your station dashboard

### Energy Dashboard

The sensors are fully compatible with Home Assistant's Energy Dashboard:
- Daily Generation → Solar production
- Daily Consumption → Home usage
- Battery Power → Battery storage
- Grid Power → Grid import/export

### Additional Features

- **5-minute updates**: Data refreshes automatically every 5 minutes
- **Automatic re-authentication**: Handles token expiration automatically
- **Error recovery**: Graceful handling of network issues
- **Extra attributes**: Each sensor includes location, timezone, and last update timestamp

## Troubleshooting

### Integration not appearing

- Ensure you've copied the entire `ksdatacloud` directory to `config/custom_components/`
- Restart Home Assistant completely
- Check Home Assistant logs for errors

### Authentication errors

- Verify your email and password are correct
- Ensure you can log in at https://sync.ksdatacloud.com
- Check that your station ID is correct

### Sensors not updating

- Check Home Assistant logs for API errors
- Verify your internet connection
- Ensure the KS Data Cloud service is online

### Finding your Station ID

1. Log in to https://sync.ksdatacloud.com
2. Navigate to your station
3. Look at the URL: `https://sync.ksdatacloud.com/station/{STATION_ID}/residential/overview`
4. The long number after `/station/` is your station ID

## Support

For issues and feature requests, please open an issue on the GitHub repository.

## Version

Current version: 0.3.0

## License

ISC License - See main project LICENSE file
