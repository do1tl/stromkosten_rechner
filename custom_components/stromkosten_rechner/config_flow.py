"""Config flow für Stromkosten Rechner."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("shelly_phase_1"): cv.entity_id,
        vol.Required("shelly_phase_2"): cv.entity_id,
        vol.Required("shelly_phase_3"): cv.entity_id,
        vol.Required("hoymiles_1"): cv.entity_id,
        vol.Optional("hoymiles_2"): cv.entity_id,
        vol.Optional("hoymiles_3"): cv.entity_id,
        vol.Optional("hoymiles_4"): cv.entity_id,
        vol.Required("kwh_preis", default=0.35): cv.positive_float,
    }
)


class StromkostenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stromkosten Rechner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validierung der Entity IDs
                for key in ["shelly_phase_1", "shelly_phase_2", "shelly_phase_3", "hoymiles_1"]:
                    entity_id = user_input.get(key)
                    if not entity_id:
                        errors[key] = "required"
                        continue
                    
                    state = self.hass.states.get(entity_id)
                    if state is None:
                        errors[key] = "entity_not_found"

                if not errors:
                    # Erstelle einzigartige ID
                    await self.async_set_unique_id(f"stromkosten_{user_input['shelly_phase_1']}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Stromkosten Rechner",
                        data=user_input,
                    )

            except Exception as err:
                _LOGGER.exception("Unexpected error during setup: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> StromkostenOptionsFlowHandler:
        """Get the options flow for this handler."""
        return StromkostenOptionsFlowHandler(config_entry)


class StromkostenOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Stromkosten Rechner."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "kwh_preis",
                        default=self.config_entry.data.get("kwh_preis", 0.35),
                    ): cv.positive_float,
                }
            ),
        )
