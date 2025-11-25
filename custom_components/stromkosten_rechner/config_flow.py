import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_POWER_SENSORS,
    CONF_SOLAR_POWER,
    CONF_SOLAR_YIELD_DAY,
    CONF_YEARLY_START_DAY,
    CONF_COST_PER_KWH,
    DEFAULT_POWER_SENSORS,
    DEFAULT_SOLAR_POWER,
    DEFAULT_SOLAR_YIELD_DAY,
    DEFAULT_YEARLY_START_DAY,
    DEFAULT_COST_PER_KWH,
)


class StromkostenRechnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id("stromkosten_rechner_main")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Stromkosten Rechner",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_SENSORS,
                    default=DEFAULT_POWER_SENSORS
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required(
                    CONF_SOLAR_POWER,
                    default=DEFAULT_SOLAR_POWER
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_SOLAR_YIELD_DAY,
                    default=DEFAULT_SOLAR_YIELD_DAY
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_YEARLY_START_DAY,
                    default=DEFAULT_YEARLY_START_DAY
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=31, step=1)
                ),
                vol.Required(
                    CONF_COST_PER_KWH,
                    default=DEFAULT_COST_PER_KWH
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=10, step=0.01)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return StromkostenRechnerOptionsFlow(config_entry)


class StromkostenRechnerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_SENSORS,
                    default=self.config_entry.data.get(
                        CONF_POWER_SENSORS, DEFAULT_POWER_SENSORS
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required(
                    CONF_SOLAR_POWER,
                    default=self.config_entry.data.get(
                        CONF_SOLAR_POWER, DEFAULT_SOLAR_POWER
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_SOLAR_YIELD_DAY,
                    default=self.config_entry.data.get(
                        CONF_SOLAR_YIELD_DAY, DEFAULT_SOLAR_YIELD_DAY
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_YEARLY_START_DAY,
                    default=self.config_entry.data.get(
                        CONF_YEARLY_START_DAY, DEFAULT_YEARLY_START_DAY
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=31, step=1)
                ),
                vol.Required(
                    CONF_COST_PER_KWH,
                    default=self.config_entry.data.get(
                        CONF_COST_PER_KWH, DEFAULT_COST_PER_KWH
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=10, step=0.01)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
