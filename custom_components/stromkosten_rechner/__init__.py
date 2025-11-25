"""Stromkosten Rechner Integration für Home Assistant."""
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.components.http import StaticPathConfig
from aiohttp import web

from .const import DOMAIN, CONF_POWER_SENSORS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Stromkosten Rechner component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stromkosten Rechner from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    config_data = dict(entry.data)
    power_sensors_str = config_data.get(CONF_POWER_SENSORS, "")
    
    if isinstance(power_sensors_str, str):
        power_sensors = [s.strip() for s in power_sensors_str.split("\n") if s.strip()]
        config_data[CONF_POWER_SENSORS] = power_sensors
    
    hass.data[DOMAIN][entry.entry_id] = config_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    card_dir = Path(__file__).parent / "www"
    
    hass.http.register_static_paths(
        [
            StaticPathConfig(
                url_path="/stromkosten_rechner_card",
                path=str(card_dir),
                cache_headers=False
            )
        ]
    )
    
    await _copy_card_to_www_async(hass)

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


async def _copy_card_to_www_async(hass: HomeAssistant) -> None:
    """Copy card file to www directory."""
    try:
        card_src = Path(__file__).parent / "www" / "stromkosten-rechner-card.js"
        www_dir = Path(hass.config.path("www"))
        www_dir.mkdir(parents=True, exist_ok=True)
        
        card_dest = www_dir / "stromkosten-rechner-card.js"
        
        if card_src.exists():
            with open(card_src, 'r') as f:
                content = f.read()
            with open(card_dest, 'w') as f:
                f.write(content)
            _LOGGER.info("Card-Datei kopiert nach: %s", card_dest)
        else:
            _LOGGER.warning("Card-Quelldatei nicht gefunden: %s", card_src)
    except Exception as e:
        _LOGGER.error("Fehler beim Kopieren der Card-Datei: %s", e)
