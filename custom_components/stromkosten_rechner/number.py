import logging
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
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
        self._attr_name = "Manueller Zählerstand Anpassung"
        self._attr_unique_id = f"{entry_id}_manual_meter"
        self._attr_icon = "mdi:counter"
        self._attr_native_min_value = -999999.9
        self._attr_native_max_value = 999999.9
        self._attr_native_step = 0.1
        self._attr_unit_of_measurement = "kWh"

        try:
            yearly_data = hass.data[DOMAIN][entry_id]["yearly_data"]
            self._attr_native_value = yearly_data.get("manual_meter_adjustment", 0.0)
        except (KeyError, TypeError):
            self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Update the meter adjustment."""
        try:
            yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
            yearly_data["manual_meter_adjustment"] = float(value)

            store = self.hass.data[DOMAIN][self._entry_id]["store"]
            await store.async_save(yearly_data)
            _LOGGER.info(f"Manual meter adjustment set to {value} kWh and saved")

            self._attr_native_value = float(value)

            for entity_id in self.hass.states.async_entity_ids("sensor"):
                if self._entry_id in entity_id and "jahres" in entity_id.lower():
                    try:
                        await self.hass.helpers.entity_component.async_update_entity(entity_id)
                    except Exception as e:
                        _LOGGER.warning(f"Could not update {entity_id}: {e}")
        except Exception as e:
            _LOGGER.error(f"Error setting manual meter value: {e}", exc_info=True)

    @property
    def native_value(self) -> float:
        """Return the current value."""
        try:
            yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
            return float(yearly_data.get("manual_meter_adjustment", 0.0))
        except (KeyError, TypeError, ValueError):
            return 0.0

    async def async_update(self):
        """Update the entity."""
        try:
            yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
            self._attr_native_value = float(yearly_data.get("manual_meter_adjustment", 0.0))
        except (KeyError, TypeError, ValueError):
            self._attr_native_value = 0.0
