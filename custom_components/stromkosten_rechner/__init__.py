"""Stromkosten Rechner Integration für Home Assistant."""
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, CONF_POWER_SENSORS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Stromkosten Rechner component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stromkosten Rechner from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    await _setup_card(hass)
    
    config_data = dict(entry.data)
    power_sensors_str = config_data.get(CONF_POWER_SENSORS, "")
    
    if isinstance(power_sensors_str, str):
        power_sensors = [s.strip() for s in power_sensors_str.split("\n") if s.strip()]
        config_data[CONF_POWER_SENSORS] = power_sensors
    
    hass.data[DOMAIN][entry.entry_id] = config_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _setup_card(hass: HomeAssistant) -> None:
    """Setup the Lovelace card."""
    card_dir = Path(__file__).parent / "www"
    card_path = card_dir / "stromkosten-rechner-card.js"
    
    if not card_path.exists():
        _LOGGER.warning("Card-Datei nicht gefunden: %s", card_path)
        return
    
    version = "1.0.0"
    url = f"/hacsfiles/{DOMAIN}/stromkosten-rechner-card.js?v={version}"
    
    await hass.http.async_register_static_paths(
        [(f"/hacsfiles/{DOMAIN}", str(card_dir), False)]
    )
    
    _LOGGER.info("Stromkosten Rechner Card registriert: %s", url)

