import logging
from homeassistant.components.button import ButtonEntity
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
    """Set up button platform."""
    buttons = [
        ResetYearlyDataButton(hass, config_entry.entry_id),
    ]
    async_add_entities(buttons)


class ResetYearlyDataButton(ButtonEntity):
    """Button to reset yearly data."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the button."""
        self.hass = hass
        self._entry_id = entry_id
        self._attr_name = "Jahreszähler Zurücksetzen"
        self._attr_unique_id = f"{entry_id}_reset_yearly"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            yearly_data = self.hass.data[DOMAIN][self._entry_id]["yearly_data"]
            yearly_data["energy_consumed"] = 0.0
            yearly_data["solar_produced"] = 0.0
            yearly_data["costs"] = 0.0
            yearly_data["savings"] = 0.0
            yearly_data["manual_meter_adjustment"] = 0.0
            yearly_data["einspeisung_yearly"] = 0.0
            yearly_data["einspeisung_daily"] = 0.0
            yearly_data["ht_energy"] = 0.0
            yearly_data["nt_energy"] = 0.0

            store = self.hass.data[DOMAIN][self._entry_id]["store"]
            await store.async_save(yearly_data)
            _LOGGER.info("Yearly data has been reset manually and saved to storage")

            for entity_id in self.hass.states.async_entity_ids("sensor"):
                if self._entry_id in entity_id:
                    try:
                        await self.hass.helpers.entity_component.async_update_entity(entity_id)
                    except Exception as e:
                        _LOGGER.warning(f"Could not update {entity_id}: {e}")

            for entity_id in self.hass.states.async_entity_ids("number"):
                if self._entry_id in entity_id:
                    try:
                        await self.hass.helpers.entity_component.async_update_entity(entity_id)
                    except Exception as e:
                        _LOGGER.warning(f"Could not update {entity_id}: {e}")
        except Exception as e:
            _LOGGER.error(f"Error resetting yearly data: {e}", exc_info=True)
