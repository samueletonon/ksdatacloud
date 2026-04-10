# KS Data Cloud - Home Assistant Integration

Complete guide for installing, configuring, and extending the KS Data Cloud integration.

---

## Current Status: Production Ready

The integration is **fully functional and ready to use**. All core files are in place:

| Component | Status |
|-----------|--------|
| `__init__.py` — Entry point, setup/teardown | ✅ |
| `manifest.json` — Integration metadata | ✅ |
| `config_flow.py` — UI-based configuration | ✅ |
| `const.py` — Constants and configuration | ✅ |
| `api.py` — API client with async/await | ✅ |
| `coordinator.py` — Data update coordinator | ✅ |
| `sensor.py` — 11 sensor entities | ✅ |
| `exceptions.py` — Custom exceptions | ✅ |
| `translations/en.json` — English translations | ✅ |
| Config Flow — UI-based setup (no YAML needed) | ✅ |
| Energy Dashboard compatibility | ✅ |
| Auto updates every 5 minutes | ✅ |
| Token refresh / auto re-authentication | ✅ |
| Extra attributes (location, timezone, timestamps) | ✅ |

---

## Quick Installation

### Prerequisites
- Home Assistant installed and running
- Access to your Home Assistant configuration directory
- KS Data Cloud account with station ID

### Installation Steps

**1. Copy the integration files**

```bash
cp -r custom_components/ksdatacloud /path/to/homeassistant/config/custom_components/

# Common paths:
# HA OS / Supervised:  /config/custom_components/ksdatacloud
# Docker:              /path/to/docker/volumes/homeassistant/config/custom_components/ksdatacloud
# Core (Python venv):  ~/.homeassistant/custom_components/ksdatacloud
```

**2. Restart Home Assistant**

- Go to: **Settings** → **System** → **Restart**
- Or use the command line: `ha core restart`

**3. Add the integration**

- Go to: **Settings** → **Devices & Services**
- Click: **+ Add Integration** (bottom right)
- Search: **"KS Data Cloud"**

**4. Configure credentials**

- **Email**: Your KS Data Cloud login email
- **Password**: Your KS Data Cloud password
- **Station ID**: Your station ID (see below how to find it)

**5. Complete setup**

Click **Submit**. The integration will validate credentials and create 11 sensors grouped under one device.

---

## Finding Your Station ID

1. Log in to [KS Data Cloud](https://sync.ksdatacloud.com)
2. Navigate to your station dashboard
3. Look at the URL:
   ```
   https://sync.ksdatacloud.com/station/2099123100000000/residential/overview
                                        ^^^^^^^^^^^^^^^^
                                        This is your Station ID
   ```
4. Copy the long number after `/station/`

---

## Sensors

Once configured, each station creates 11 sensor entities grouped under one device:

| Sensor | Unit | Description | Energy Dashboard |
|--------|------|-------------|------------------|
| **PV Power** | W | Current solar generation | Solar Production |
| **Battery State of Charge** | % | Battery charge level | Status |
| **Battery Power** | W | Charge/discharge power | Battery Storage |
| **Grid Power** | W | Import/export power | Grid Import/Export |
| **Load Power** | W | Home consumption | Real-time usage |
| **Daily Generation** | kWh | Solar production today | Solar Total |
| **Daily Consumption** | kWh | Home usage today | Consumption Total |

**Device info:** Name is your station name, Manufacturer is KS Data Cloud, Model is Solar Station, with a direct link to your station dashboard.

---

## Energy Dashboard Setup

1. Go to: **Settings** → **Dashboards** → **Energy**
2. **Add Solar Production** → select `sensor.{your_station}_daily_generation`
3. **Add Grid Consumption** → select `sensor.{your_station}_grid_power`
4. **Add Battery System** (optional):
   - Energy going in: `sensor.{your_station}_battery_power` (when negative)
   - Energy coming out: `sensor.{your_station}_battery_power` (when positive)
5. **Add Home Energy Usage** → select `sensor.{your_station}_daily_consumption`

---

## Troubleshooting

### Integration Not Appearing

```bash
# Verify files are in correct location
ls -la /path/to/homeassistant/config/custom_components/ksdatacloud/

# Check Home Assistant logs
tail -f /path/to/homeassistant/config/home-assistant.log | grep ksdatacloud
```

### Authentication Failed

1. Verify you can log in at https://sync.ksdatacloud.com
2. Check email and password are correct (no extra spaces)
3. Ensure station ID is correct (no dashes or spaces)

### Sensors Not Updating

```bash
tail -f /path/to/homeassistant/config/home-assistant.log | grep ksdatacloud

# Common errors:
# "Token expired"     → Will auto-refresh, wait 5 minutes
# "Cannot connect"    → Check internet connection
# "Station not found" → Verify station ID is correct
```

### Missing Dependencies

Home Assistant should auto-install `aiohttp>=3.8.0`. If needed: `pip3 install aiohttp>=3.8.0`, then restart.

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.ksdatacloud: debug
```

---

## Updating the Integration

```bash
# 1. Remove old version
rm -rf /path/to/homeassistant/config/custom_components/ksdatacloud

# 2. Copy new version
cp -r custom_components/ksdatacloud /path/to/homeassistant/config/custom_components/

# 3. Restart Home Assistant
ha core restart
```

---

## Optional Enhancements

The integration works without these, but they improve distribution and usability.

### HACS Support (recommended for sharing)

**a) `hacs.json` already exists in the repo root.**

**b) Add GitHub topics to your repository:**
- `home-assistant`, `hacs`, `homeassistant-integration`, `custom-component`

**c) Create a GitHub release:**
```bash
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

**d) Submit to HACS:**
- Fork https://github.com/hacs/default
- Add your repo to `custom_components.json` and create a PR

### Icon/Logo

Place a 256×256 `icon.png` in `custom_components/ksdatacloud/` and add `"icon": "mdi:solar-power"` to `manifest.json`.

### Options Flow (let users change settings without re-adding)

Add to `config_flow.py`:
```python
@staticmethod
@callback
def async_get_options_flow(config_entry):
    return KSDataCloudOptionsFlow(config_entry)

class KSDataCloudOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Optional("update_interval", default=5): int})
        )
```

### Custom Services

Add `services.yaml` and register in `__init__.py`:
```python
async def refresh_data(call):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_request_refresh()

hass.services.async_register(DOMAIN, "refresh_data", refresh_data)
```

### Diagnostics

Create `custom_components/ksdatacloud/diagnostics.py`:
```python
async def async_get_config_entry_diagnostics(hass, entry) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "station_id": coordinator.station_id,
        "last_update": coordinator.last_update_success,
        "data": coordinator.data,
    }
```

---

## Distribution Decision Matrix

| Goal | Steps |
|------|-------|
| Use it yourself | Manual copy (5 min) |
| Share with friends | Add HACS support (~30 min) |
| Public distribution | Add tests + docs (4–8 hours) |
| Official HA integration | All enhancements + quality standards (20+ hours) |

---

## Additional Documentation

- **[docs/HA_INSTALLATION.md](docs/HA_INSTALLATION.md)** — Detailed installation guide
- **[docs/HOME_ASSISTANT.md](docs/HOME_ASSISTANT.md)** — Technical architecture and API details
- **[custom_components/ksdatacloud/README.md](custom_components/ksdatacloud/README.md)** — Integration quick reference

---

**Version:** 0.3.0 | **Last Updated:** March 26, 2026
