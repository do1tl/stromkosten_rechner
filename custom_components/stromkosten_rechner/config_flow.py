"""Config flow für Stromkosten Rechner."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

DOMAIN = "stromkosten_rechner"

class StromkostenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stromkosten Rechner."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Erstelle einen einzigartigen Titel
            await self.async_set_unique_id(user_input.get("name", "stromkosten_rechner"))
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=user_input.get("name", "Stromkosten Rechner"),
                data=user_input
            )

        # Basis Schema
        data_schema = vol.Schema({
            vol.Optional("name", default="Stromkosten Rechner"): str,
            vol.Required("shelly_phase_1"): cv.entity_id,
            vol.Required("shelly_phase_2"): cv.entity_id,
            vol.Required("shelly_phase_3"): cv.entity_id,
            vol.Required("hoymiles_1"): cv.entity_id,
            vol.Optional("hoymiles_2", default=""): cv.entity_id,
            vol.Optional("hoymiles_3", default=""): cv.entity_id,
            vol.Optional("hoymiles_4", default=""): cv.entity_id,
            vol.Required("kwh_preis", default=0.35): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return StromkostenOptionsFlow(config_entry)


class StromkostenOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "kwh_preis",
                    default=self.config_entry.data.get("kwh_preis", 0.35)
                ): vol.Coerce(float),
            })
        )
