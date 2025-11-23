"""Number platform for Stromkosten Rechner."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform."""
    numbers = [
        ManuellerZaehlerstandNumber(hass, config_entry.entry_id),
    ]
    async_add_entities(numbers)


class ManuellerZaehlerstandNumber(NumberEntity):
    """Number for manual meter adjustment."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the number."""
        self.hass = hass
        self._entry_id = entry_id
        self._attr_name = "Stromkosten Manueller Zählerstand Anpassung"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_manual_meter"
        self._attr_icon = "mdi:counter"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 999999.9
        self._attr_native_step = 0.1
        self._attr_unit_of_measurement = "kWh"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Update the meter adjustment."""
        yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
        yearly_data["manual_meter_adjustment"] = float(value)
        
        store = self.hass.data[DOMAIN][self._entry_id]["store"]
        await store.async_save(yearly_data)
        
        _LOGGER.info(f"Manual meter adjustment set to {value} kWh")
        self._attr_native_value = value

    @property
    def native_value(self) -> float:
        """Return the current value."""
        yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
        return yearly_data.get("manual_meter_adjustment", 0.0)
