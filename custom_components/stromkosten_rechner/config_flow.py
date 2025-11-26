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
    CONF_YEARLY_START_MONTH,
    CONF_COST_PER_KWH,
    DEFAULT_POWER_SENSORS,
    DEFAULT_SOLAR_POWER,
    DEFAULT_SOLAR_YIELD_DAY,
    DEFAULT_YEARLY_START_DAY,
    DEFAULT_YEARLY_START_MONTH,
    DEFAULT_COST_PER_KWH,
)


class StromkostenRechnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            # Validierung: Tag muss für den gewählten Monat gültig sein
            day = user_input.get(CONF_YEARLY_START_DAY, 1)
            month = user_input.get(CONF_YEARLY_START_MONTH, 1)
            
            # Maximale Tage pro Monat
            days_in_month = {
                1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
                7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
            }
            
            if day > days_in_month.get(month, 31):
                errors["yearly_start_day"] = "invalid_day_for_month"
            else:
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
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional(
                    CONF_SOLAR_POWER,
                    default=DEFAULT_SOLAR_POWER
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor"
                    )
                ),
                vol.Optional(
                    CONF_SOLAR_YIELD_DAY,
                    default=DEFAULT_SOLAR_YIELD_DAY
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor"
                    )
                ),
                vol.Required(
                    CONF_YEARLY_START_MONTH,
                    default=DEFAULT_YEARLY_START_MONTH
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "1", "label": "Januar"},
                            {"value": "2", "label": "Februar"},
                            {"value": "3", "label": "März"},
                            {"value": "4", "label": "April"},
                            {"value": "5", "label": "Mai"},
                            {"value": "6", "label": "Juni"},
                            {"value": "7", "label": "Juli"},
                            {"value": "8", "label": "August"},
                            {"value": "9", "label": "September"},
                            {"value": "10", "label": "Oktober"},
                            {"value": "11", "label": "November"},
                            {"value": "12", "label": "Dezember"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(
                    CONF_YEARLY_START_DAY,
                    default=DEFAULT_YEARLY_START_DAY
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=31,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_COST_PER_KWH,
                    default=DEFAULT_COST_PER_KWH
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=10,
                        step=0.01,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="€/kWh"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "power_sensors_info": "Gib die Entity-IDs deiner Power-Sensoren ein (eine pro Zeile)",
                "date_info": "Der Ablesetermin für den jährlichen Verbrauch (z.B. 1. Januar)"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return StromkostenRechnerOptionsFlow(config_entry)


class StromkostenRechnerOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            day = user_input.get(CONF_YEARLY_START_DAY, 1)
            month = user_input.get(CONF_YEARLY_START_MONTH, 1)
            
            days_in_month = {
                1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
                7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
            }
            
            if day > days_in_month.get(month, 31):
                errors["yearly_start_day"] = "invalid_day_for_month"
            else:
                return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_SENSORS,
                    default=self.config_entry.data.get(
                        CONF_POWER_SENSORS, DEFAULT_POWER_SENSORS
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional(
                    CONF_SOLAR_POWER,
                    default=self.config_entry.data.get(
                        CONF_SOLAR_POWER, DEFAULT_SOLAR_POWER
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor"
                    )
                ),
                vol.Optional(
                    CONF_SOLAR_YIELD_DAY,
                    default=self.config_entry.data.get(
                        CONF_SOLAR_YIELD_DAY, DEFAULT_SOLAR_YIELD_DAY
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor"
                    )
                ),
                vol.Required(
                    CONF_YEARLY_START_MONTH,
                    default=str(self.config_entry.data.get(
                        CONF_YEARLY_START_MONTH, DEFAULT_YEARLY_START_MONTH
                    )),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "1", "label": "Januar"},
                            {"value": "2", "label": "Februar"},
                            {"value": "3", "label": "März"},
                            {"value": "4", "label": "April"},
                            {"value": "5", "label": "Mai"},
                            {"value": "6", "label": "Juni"},
                            {"value": "7", "label": "Juli"},
                            {"value": "8", "label": "August"},
                            {"value": "9", "label": "September"},
                            {"value": "10", "label": "Oktober"},
                            {"value": "11", "label": "November"},
                            {"value": "12", "label": "Dezember"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(
                    CONF_YEARLY_START_DAY,
                    default=self.config_entry.data.get(
                        CONF_YEARLY_START_DAY, DEFAULT_YEARLY_START_DAY
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=31,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_COST_PER_KWH,
                    default=self.config_entry.data.get(
                        CONF_COST_PER_KWH, DEFAULT_COST_PER_KWH
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=10,
                        step=0.01,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="€/kWh"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors
        )