DOMAIN = "stromkosten_rechner"

CONF_POWER_SENSORS = "power_sensors"
CONF_SOLAR_POWER = "solar_power"
CONF_SOLAR_YIELD_DAY = "solar_yield_day"
CONF_YEARLY_START_DAY = "yearly_start_day"
CONF_COST_PER_KWH = "cost_per_kwh"

DEFAULT_POWER_SENSORS = """sensor.shellyem3_485519d9e23e_channel_a_power
sensor.shellyem3_485519d9e23e_channel_b_power
sensor.shellyem3_485519d9e23e_channel_c_power"""

DEFAULT_SOLAR_POWER = "sensor.hoymiles_hm_400_ch1_power"
DEFAULT_SOLAR_YIELD_DAY = "sensor.hoymiles_hm_400_ch1_yieldday"
DEFAULT_YEARLY_START_DAY = 1
DEFAULT_COST_PER_KWH = 0.30
