"""Config flow for Stromkosten Rechner."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"


@config_entries.HANDLERS.register(DOMAIN)
class StromkostenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validierung
            try:
                # Prüfe ob Entity IDs existieren
                required_fields = [
                    "shelly_phase_1",
                    "shelly_phase_2", 
                    "shelly_phase_3",
                    "hoymiles_1"
                ]
                
                for field in required_fields:
                    entity_id = user_input.get(field)
                    if entity_id:
                        state = self.hass.states.get(entity_id)
                        if state is None:
                            errors[field] = "entity_not_found"
                            _LOGGER.error(f"Entity not found: {entity_id}")

                if not errors:
                    # Bereinige leere optionale Felder
                    clean_input = user_input.copy()
                    for i in range(2, 5):
                        key = f"hoymiles_{i}"
                        if key in clean_input and not clean_input[key]:
                            del clean_input[key]

                    return self.async_create_entry(
                        title="Stromkosten Rechner",
                        data=clean_input
                    )

            except Exception as e:
                _LOGGER.exception(f"Error in config flow: {e}")
                errors["base"] = "unknown"

        # Schema
        data_schema = vol.Schema({
            vol.Required("shelly_phase_1"): str,
            vol.Required("shelly_phase_2"): str,
            vol.Required("shelly_phase_3"): str,
            vol.Required("hoymiles_1"): str,
            vol.Optional("hoymiles_2", default=""): str,
            vol.Optional("hoymiles_3", default=""): str,
            vol.Optional("hoymiles_4", default=""): str,
            vol.Required("kwh_preis", default=0.35): vol.All(
                vol.Coerce(float), vol.Range(min=0.01, max=10.0)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return StromkostenOptionsFlow(config_entry)


class StromkostenOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "kwh_preis",
                    default=self.config_entry.data.get("kwh_preis", 0.35)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=10.0)),
            })
        )
