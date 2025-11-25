import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, STATE_UNKNOWN, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_POWER_SENSORS,
    CONF_SOLAR_POWER,
    CONF_SOLAR_YIELD_DAY,
    CONF_YEARLY_START_DAY,
    CONF_COST_PER_KWH,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    config_data = hass.data[DOMAIN][config_entry.entry_id]
    
    power_sensors = config_data.get(CONF_POWER_SENSORS, [])
    solar_power = config_data.get(CONF_SOLAR_POWER)
    solar_yield_day = config_data.get(CONF_SOLAR_YIELD_DAY)
    yearly_start_day = int(config_data.get(CONF_YEARLY_START_DAY, 1))
    cost_per_kwh = float(config_data.get(CONF_COST_PER_KWH, 0.30))

    entities = [
        StromkostenConsumptionDaily(hass, power_sensors),
        StromkostenConsumptionMonthly(hass, power_sensors),
        StromkostenConsumptionYearly(hass, power_sensors, yearly_start_day),
        StromkostenConsumptionYearlyPrognosis(hass, power_sensors, yearly_start_day),
        StromkostenCostDaily(hass, power_sensors, cost_per_kwh),
        StromkostenCostMonthly(hass, power_sensors, cost_per_kwh),
        StromkostenCostYearly(hass, power_sensors, cost_per_kwh, yearly_start_day),
        StromkostenCostYearlyPrognosis(hass, power_sensors, cost_per_kwh, yearly_start_day),
        SolarYieldDaily(hass, solar_yield_day),
        SolarYieldMonthly(hass, solar_yield_day),
        SolarYieldYearly(hass, solar_yield_day, yearly_start_day),
    ]

    async_add_entities(entities, True)
    return True


def get_day_of_year(date):
    return (date - date.replace(month=1, day=1)).days + 1


def get_days_in_current_year_period(yearly_start_day: int):
    now = datetime.now()
    
    if now.day >= yearly_start_day:
        start_date = now.replace(day=yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = (now.replace(month=now.month-1 if now.month > 1 else 12, year=now.year-1 if now.month == 1 else now.year, day=yearly_start_day, hour=0, minute=0, second=0, microsecond=0))
    
    days_elapsed = (now - start_date).days + 1
    return max(1, days_elapsed)


class StromkostenConsumptionDaily(SensorEntity):
    _attr_name = "Daily Consumption"
    _attr_unique_id = "stromkosten_consumption_daily"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str]):
        self.hass = hass
        self.power_sensors = power_sensors
        self._state = 0.0
        self._last_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self._accumulated = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_daily_consumption")

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        now = datetime.now()
        current_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if current_date > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = current_date
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        if total_power > 0:
            self._accumulated += (total_power / 1000 / 3600)
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        self._state = round(self._accumulated, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenConsumptionMonthly(SensorEntity):
    _attr_name = "Monthly Consumption"
    _attr_unique_id = "stromkosten_consumption_monthly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-month"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str]):
        self.hass = hass
        self.power_sensors = power_sensors
        self._state = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._accumulated = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_monthly_consumption")

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        now = datetime.now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if current_month > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = current_month
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        if total_power > 0:
            self._accumulated += (total_power / 1000 / 3600)
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        self._state = round(self._accumulated, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenConsumptionYearly(SensorEntity):
    _attr_name = "Yearly Consumption"
    _attr_unique_id = "stromkosten_consumption_yearly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-year"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], yearly_start_day: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0
        self._last_reset = self._get_yearly_start_date()
        self._accumulated = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_yearly_consumption")

    def _get_yearly_start_date(self) -> datetime:
        now = datetime.now()
        if now.day >= self.yearly_start_day:
            return now.replace(month=1, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
        else:
            prev_year = now.year - 1
            return now.replace(year=prev_year, month=1, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        new_reset_date = self._get_yearly_start_date()
        
        if new_reset_date > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = new_reset_date
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        if total_power > 0:
            self._accumulated += (total_power / 1000 / 3600)
            await self._store.async_save({"accumulated": self._accumulated, "last_reset": self._last_reset.isoformat()})

        self._state = round(self._accumulated, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenConsumptionYearlyPrognosis(SensorEntity):
    _attr_name = "Yearly Consumption Prognosis"
    _attr_unique_id = "stromkosten_consumption_yearly_prognosis"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:crystal-ball"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], yearly_start_day: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        daily_consumption = self.hass.states.get("sensor.stromkosten_consumption_daily")
        
        if not daily_consumption or daily_consumption.state in (STATE_UNKNOWN, None, "unavailable"):
            self._state = 0.0
            return
        
        try:
            today_consumption = float(daily_consumption.state)
            days_in_period = get_days_in_current_year_period(self.yearly_start_day)
            
            days_in_year = 365
            
            self._state = round((today_consumption / days_in_period) * days_in_year, 2)
        except (ValueError, TypeError):
            self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenCostDaily(SensorEntity):
    _attr_name = "Daily Consumption Cost"
    _attr_unique_id = "stromkosten_cost_daily"
    _attr_unit_of_measurement = "€"
    _attr_icon = "mdi:cash"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        daily_consumption = self.hass.states.get("sensor.stromkosten_consumption_daily")
        
        if daily_consumption and daily_consumption.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                consumption = float(daily_consumption.state)
                self._state = round(consumption * self.cost_per_kwh, 2)
            except ValueError:
                self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenCostMonthly(SensorEntity):
    _attr_name = "Monthly Consumption Cost"
    _attr_unique_id = "stromkosten_cost_monthly"
    _attr_unit_of_measurement = "€"
    _attr_icon = "mdi:cash"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        monthly_consumption = self.hass.states.get("sensor.stromkosten_consumption_monthly")
        
        if monthly_consumption and monthly_consumption.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                consumption = float(monthly_consumption.state)
                self._state = round(consumption * self.cost_per_kwh, 2)
            except ValueError:
                self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenCostYearly(SensorEntity):
    _attr_name = "Yearly Consumption Cost"
    _attr_unique_id = "stromkosten_cost_yearly"
    _attr_unit_of_measurement = "€"
    _attr_icon = "mdi:cash"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float, yearly_start_day: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        yearly_consumption = self.hass.states.get("sensor.stromkosten_consumption_yearly")
        
        if yearly_consumption and yearly_consumption.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                consumption = float(yearly_consumption.state)
                self._state = round(consumption * self.cost_per_kwh, 2)
            except ValueError:
                self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenCostYearlyPrognosis(SensorEntity):
    _attr_name = "Yearly Consumption Cost Prognosis"
    _attr_unique_id = "stromkosten_cost_yearly_prognosis"
    _attr_unit_of_measurement = "€"
    _attr_icon = "mdi:cash-multiple"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float, yearly_start_day: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        yearly_prognosis = self.hass.states.get("sensor.stromkosten_consumption_yearly_prognosis")
        
        if yearly_prognosis and yearly_prognosis.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                consumption = float(yearly_prognosis.state)
                self._state = round(consumption * self.cost_per_kwh, 2)
            except ValueError:
                self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class SolarYieldDaily(SensorEntity):
    _attr_name = "Solar Yield Daily"
    _attr_unique_id = "solar_yield_daily"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:solar-power"

    def __init__(self, hass: HomeAssistant, solar_yield_day: Optional[str]):
        self.hass = hass
        self.solar_yield_day = solar_yield_day
        self._state = 0.0

    async def async_added_to_hass(self) -> None:
        if self.solar_yield_day:
            self.async_on_remove(
                async_track_state_change(
                    self.hass,
                    self.solar_yield_day,
                    self._yield_changed
                )
            )

    @callback
    def _yield_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        if self.solar_yield_day:
            state = self.hass.states.get(self.solar_yield_day)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    self._state = round(float(state.state), 2)
                except ValueError:
                    pass

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class SolarYieldMonthly(SensorEntity):
    _attr_name = "Solar Yield Monthly"
    _attr_unique_id = "solar_yield_monthly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-month"

    def __init__(self, hass: HomeAssistant, solar_yield_day: Optional[str]):
        self.hass = hass
        self.solar_yield_day = solar_yield_day
        self._state = 0.0
        self._last_reset = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._accumulated = 0.0
        self._last_yield_value = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_solar_yield_monthly")

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
                self._last_yield_value = float(stored_data.get("last_yield_value", 0.0))
            except (ValueError, TypeError):
                pass
        
        if self.solar_yield_day:
            self.async_on_remove(
                async_track_state_change(
                    self.hass,
                    self.solar_yield_day,
                    self._yield_changed
                )
            )
        await self.async_update()

    @callback
    def _yield_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        if not self.solar_yield_day:
            self._state = 0.0
            return

        now = datetime.now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if current_month > self._last_reset:
            self._accumulated = 0.0
            self._last_yield_value = 0.0
            self._last_reset = current_month
            await self._store.async_save({
                "accumulated": self._accumulated,
                "last_reset": self._last_reset.isoformat(),
                "last_yield_value": self._last_yield_value
            })

        state = self.hass.states.get(self.solar_yield_day)
        if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                yield_value = float(state.state)
                if yield_value < self._last_yield_value:
                    self._accumulated += self._last_yield_value
                    await self._store.async_save({
                        "accumulated": self._accumulated,
                        "last_reset": self._last_reset.isoformat(),
                        "last_yield_value": 0.0
                    })
                self._last_yield_value = yield_value
            except ValueError:
                pass

        self._state = round(self._accumulated, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class SolarYieldYearly(SensorEntity):
    _attr_name = "Solar Yield Yearly"
    _attr_unique_id = "solar_yield_yearly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-year"

    def __init__(self, hass: HomeAssistant, solar_yield_day: Optional[str], yearly_start_day: int = 1):
        self.hass = hass
        self.solar_yield_day = solar_yield_day
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0
        self._last_reset = self._get_yearly_start_date()
        self._accumulated = 0.0
        self._last_yield_value = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_solar_yield_yearly")

    def _get_yearly_start_date(self) -> datetime:
        now = datetime.now()
        if now.day >= self.yearly_start_day:
            return now.replace(month=1, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
        else:
            prev_year = now.year - 1
            return now.replace(year=prev_year, month=1, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
                self._last_yield_value = float(stored_data.get("last_yield_value", 0.0))
            except (ValueError, TypeError):
                pass
        
        if self.solar_yield_day:
            self.async_on_remove(
                async_track_state_change(
                    self.hass,
                    self.solar_yield_day,
                    self._yield_changed
                )
            )
        await self.async_update()

    @callback
    def _yield_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        if not self.solar_yield_day:
            self._state = 0.0
            return

        new_reset_date = self._get_yearly_start_date()
        
        if new_reset_date > self._last_reset:
            self._accumulated = 0.0
            self._last_yield_value = 0.0
            self._last_reset = new_reset_date
            await self._store.async_save({
                "accumulated": self._accumulated,
                "last_reset": self._last_reset.isoformat(),
                "last_yield_value": self._last_yield_value
            })

        state = self.hass.states.get(self.solar_yield_day)
        if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
            try:
                yield_value = float(state.state)
                if yield_value < self._last_yield_value:
                    self._accumulated += self._last_yield_value
                    await self._store.async_save({
                        "accumulated": self._accumulated,
                        "last_reset": self._last_reset.isoformat(),
                        "last_yield_value": 0.0
                    })
                self._last_yield_value = yield_value
            except ValueError:
                pass

        self._state = round(self._accumulated, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN
