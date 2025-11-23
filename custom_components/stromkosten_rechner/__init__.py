"""Stromkosten Rechner Integration."""
import logging
import json
import os
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"
PLATFORMS = ["sensor", "button", "number"]
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_yearly_data"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Load yearly data from Storage API
    store = hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
    yearly_data = await store.async_load()
    
    if yearly_data is None:
        yearly_data = {
            "energy_consumed": 0.0,
            "solar_produced": 0.0,
            "costs": 0.0,
            "savings": 0.0,
            "year": None,
            "manual_meter_adjustment": 0.0,
        }
    
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "yearly_data": yearly_data,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
