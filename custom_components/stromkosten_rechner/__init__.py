import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    STORAGE_KEY,
    CONF_ABRECHNUNGSTAG,
    CONF_ABRECHNUNGSMONAT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button", "number"]
STORAGE_VERSION = 1


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
    yearly_data = await store.async_load()
    
    if yearly_data is None:
        yearly_data = {
            "energy_consumed": 0.0,
            "solar_produced": 0.0,
            "costs": 0.0,
            "savings": 0.0,
            "year": datetime.now().year,
            "manual_meter_adjustment": 0.0,
            "einspeisung_yearly": 0.0,
            "einspeisung_daily": 0.0,
            "ht_energy": 0.0,
            "nt_energy": 0.0,
        }
    
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "yearly_data": yearly_data,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def check_yearly_reset(now):
        """Check if yearly reset is needed."""
        await _async_check_and_reset_yearly(hass, entry, now)
    
    async_track_time_interval(hass, check_yearly_reset, timedelta(days=1))
    
    await _async_check_and_reset_yearly(hass, entry, datetime.now())
    
    _LOGGER.info(f"Stromkosten Rechner v2.1.1 initialized for entry {entry.entry_id}")
    
    return True


async def _async_check_and_reset_yearly(hass: HomeAssistant, entry: ConfigEntry, now: datetime):
    """Check if yearly reset is needed and perform it."""
    config = entry.data
    yearly_data = hass.data[DOMAIN][entry.entry_id]["yearly_data"]
    
    day = config.get(CONF_ABRECHNUNGSTAG, 1)
    month = config.get(CONF_ABRECHNUNGSMONAT, 1)
    
    try:
        reading_date = datetime(now.year, month, day)
    except ValueError:
        if month == 2:
            reading_date = datetime(now.year, month, 28)
        else:
            reading_date = datetime(now.year, month, 1)
    
    current_billing_year = now.year if now >= reading_date else now.year - 1
    stored_year = yearly_data.get("year")
    
    if stored_year is None or stored_year != current_billing_year:
        _LOGGER.info(
            f"Yearly reset triggered: stored_year={stored_year}, "
            f"current_billing_year={current_billing_year}, date={now.date()}"
        )
        
        yearly_data["year"] = current_billing_year
        yearly_data["energy_consumed"] = 0.0
        yearly_data["solar_produced"] = 0.0
        yearly_data["costs"] = 0.0
        yearly_data["savings"] = 0.0
        yearly_data["einspeisung_yearly"] = 0.0
        yearly_data["einspeisung_daily"] = 0.0
        yearly_data["manual_meter_adjustment"] = 0.0
        yearly_data["ht_energy"] = 0.0
        yearly_data["nt_energy"] = 0.0
        
        store = hass.data[DOMAIN][entry.entry_id]["store"]
        await store.async_save(yearly_data)
        
        _LOGGER.info(f"Yearly data reset complete for billing year {current_billing_year}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
