import logging
import voluptuous as vol
from datetime import datetime

from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"


@config_entries.HANDLERS.register(DOMAIN)
class StromkostenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the flow."""
        self.config_data = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step - Sensoren."""
        errors = {}

        if user_input is not None:
            try:
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
                    self.config_data.update(user_input)
                    for i in range(2, 5):
                        key = f"hoymiles_{i}"
                        if key in self.config_data and not self.config_data[key]:
                            self.config_data.pop(key, None)
                    
                    return await self.async_step_pricing()

            except Exception as e:
                _LOGGER.exception(f"Error in config flow: {e}")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required("shelly_phase_1"): str,
            vol.Required("shelly_phase_2"): str,
            vol.Required("shelly_phase_3"): str,
            vol.Required("hoymiles_1"): str,
            vol.Optional("hoymiles_2", default=""): str,
            vol.Optional("hoymiles_3", default=""): str,
            vol.Optional("hoymiles_4", default=""): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step": "1/4 - Sensoren"}
        )

    async def async_step_pricing(self, user_input=None):
        """Handle step 2 - Preiseinstellungen."""
        errors = {}

        if user_input is not None:
            try:
                if user_input.get("kwh_preis", 0) <= 0:
                    errors["kwh_preis"] = "must_be_positive"
                if user_input.get("grundgebuehr", 0) < 0:
                    errors["grundgebuehr"] = "must_be_positive"
                if user_input.get("einspeiseverguetung", 0) < 0:
                    errors["einspeiseverguetung"] = "must_be_positive"
                
                if not errors:
                    self.config_data.update(user_input)
                    return await self.async_step_billing()
            except Exception as e:
                _LOGGER.exception(f"Error in pricing step: {e}")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required("kwh_preis", default=0.35): vol.All(
                vol.Coerce(float), vol.Range(min=0.01, max=10.0)
            ),
            vol.Required("grundgebuehr", default=0.0): vol.All(
                vol.Coerce(float), vol.Range(min=0.0, max=1000.0)
            ),
            vol.Required("einspeiseverguetung", default=0.08): vol.All(
                vol.Coerce(float), vol.Range(min=0.0, max=1.0)
            ),
        })

        return self.async_show_form(
            step_id="pricing",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step": "2/4 - Preiseinstellungen"}
        )

    async def async_step_billing(self, user_input=None):
        """Handle step 3 - Abrechnungstermin."""
        errors = {}

        if user_input is not None:
            try:
                day = user_input.get("ablesetermin_tag", 1)
                month = user_input.get("ablesetermin_monat", 1)
                
                try:
                    datetime(2024, month, day)
                except ValueError:
                    errors["ablesetermin_tag"] = "invalid_date"
                    _LOGGER.error(f"Invalid date: {day}.{month}")
                
                if not errors:
                    self.config_data.update(user_input)
                    return await self.async_step_tariff()
            except Exception as e:
                _LOGGER.exception(f"Error in billing step: {e}")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required("ablesetermin_tag", default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=31)
            ),
            vol.Required("ablesetermin_monat", default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=12)
            ),
        })

        return self.async_show_form(
            step_id="billing",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step": "3/4 - Abrechnungstermin"}
        )

    async def async_step_tariff(self, user_input=None):
        """Handle step 4 - HT/NT Tarif."""
        errors = {}

        if user_input is not None:
            try:
                if user_input.get("ht_nt_enabled", False):
                    try:
                        datetime.strptime(user_input.get("ht_start", "06:00"), "%H:%M")
                        datetime.strptime(user_input.get("ht_end", "22:00"), "%H:%M")
                    except ValueError:
                        errors["ht_start"] = "invalid_time_format"
                        _LOGGER.error("Invalid time format for HT/NT")
                    
                    if user_input.get("ht_preis", 0) <= 0:
                        errors["ht_preis"] = "must_be_positive"
                    if user_input.get("nt_preis", 0) <= 0:
                        errors["nt_preis"] = "must_be_positive"
                
                if not errors:
                    self.config_data.update(user_input)
                    return self.async_create_entry(
                        title="Stromkosten Rechner",
                        data=self.config_data
                    )
            except Exception as e:
                _LOGGER.exception(f"Error in tariff step: {e}")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required("ht_nt_enabled", default=False): bool,
            vol.Required("ht_preis", default=0.45): vol.All(
                vol.Coerce(float), vol.Range(min=0.01, max=10.0)
            ),
            vol.Required("nt_preis", default=0.25): vol.All(
                vol.Coerce(float), vol.Range(min=0.01, max=10.0)
            ),
            vol.Required("ht_start", default="06:00"): str,
            vol.Required("ht_end", default="22:00"): str,
        })

        return self.async_show_form(
            step_id="tariff",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step": "4/4 - HT/NT Tarif (optional)"}
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
        errors = {}
        
        if user_input is not None:
            try:
                if user_input.get("ht_nt_enabled", False):
                    try:
                        datetime.strptime(user_input.get("ht_start", "06:00"), "%H:%M")
                        datetime.strptime(user_input.get("ht_end", "22:00"), "%H:%M")
                    except ValueError:
                        errors["ht_start"] = "invalid_time_format"
                
                if not errors:
                    return self.async_create_entry(title="", data=user_input)
            except Exception as e:
                _LOGGER.exception(f"Error in options flow: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "kwh_preis",
                    default=self.config_entry.data.get("kwh_preis", 0.35)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=10.0)),
                vol.Required(
                    "grundgebuehr",
                    default=self.config_entry.data.get("grundgebuehr", 0.0)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1000.0)),
                vol.Required(
                    "einspeiseverguetung",
                    default=self.config_entry.data.get("einspeiseverguetung", 0.08)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                vol.Required(
                    "ht_nt_enabled",
                    default=self.config_entry.data.get("ht_nt_enabled", False)
                ): bool,
                vol.Required(
                    "ht_preis",
                    default=self.config_entry.data.get("ht_preis", 0.45)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=10.0)),
                vol.Required(
                    "nt_preis",
                    default=self.config_entry.data.get("nt_preis", 0.25)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=10.0)),
                vol.Required(
                    "ht_start",
                    default=self.config_entry.data.get("ht_start", "06:00")
                ): str,
                vol.Required(
                    "ht_end",
                    default=self.config_entry.data.get("ht_end", "22:00")
                ): str,
            }),
            errors=errors
        )
