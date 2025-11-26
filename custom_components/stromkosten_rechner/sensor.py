import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, STATE_UNKNOWN, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_POWER_SENSORS,
    CONF_SOLAR_POWER,
    CONF_SOLAR_YIELD_DAY,
    CONF_YEARLY_START_DAY,
    CONF_YEARLY_START_MONTH,
    CONF_COST_PER_KWH,
)

_LOGGER = logging.getLogger(__name__)

# Update-Intervall für kontinuierliche Berechnung
UPDATE_INTERVAL = timedelta(seconds=10)


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
        self._last_update_time = None  # NEU: Zeitstempel des letzten Updates
        self._store = Store(hass, 1, f"{DOMAIN}_daily_consumption")

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        # Initialisiere Zeitstempel
        self._last_update_time = datetime.now()
        
        # State-Change-Tracker für sofortige Updates
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        
        # Periodischer Update alle 10 Sekunden (auch wenn sich nichts ändert)
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._periodic_update,
                UPDATE_INTERVAL
            )
        )
        
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        """Wird aufgerufen, wenn sich ein Power-Sensor ändert"""
        self.async_schedule_update_ha_state(force_refresh=True)

    async def _periodic_update(self, now):
        """Periodisches Update alle 10 Sekunden"""
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        now = datetime.now()
        current_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reset bei neuem Tag
        if current_date > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = current_date
            self._last_update_time = now
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })
            self._state = 0.0
            return

        # Berechne Zeit seit letztem Update
        if self._last_update_time is None:
            self._last_update_time = now
            return
        
        time_delta = (now - self._last_update_time).total_seconds()
        
        # Verhindere negative oder zu große Zeitdifferenzen
        if time_delta <= 0 or time_delta > 3600:
            self._last_update_time = now
            return

        # Summiere aktuelle Leistung aller Sensoren
        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        # Berechne Energie: Power (W) * Zeit (s) / 3600 / 1000 = kWh
        # Formel: kWh = (Watt * Sekunden) / 3.600.000
        if total_power > 0:
            energy_kwh = (total_power * time_delta) / 3600000
            self._accumulated += energy_kwh
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })

        self._last_update_time = now
        self._state = round(self._accumulated, 3)

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
        self._last_update_time = None
        self._store = Store(hass, 1, f"{DOMAIN}_monthly_consumption")

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        self._last_update_time = datetime.now()
        
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._periodic_update,
                UPDATE_INTERVAL
            )
        )
        
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def _periodic_update(self, now):
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        now = datetime.now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if current_month > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = current_month
            self._last_update_time = now
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })
            self._state = 0.0
            return

        if self._last_update_time is None:
            self._last_update_time = now
            return
        
        time_delta = (now - self._last_update_time).total_seconds()
        
        if time_delta <= 0 or time_delta > 3600:
            self._last_update_time = now
            return

        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        if total_power > 0:
            energy_kwh = (total_power * time_delta) / 3600000
            self._accumulated += energy_kwh
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })

        self._last_update_time = now
        self._state = round(self._accumulated, 3)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenConsumptionYearly(SensorEntity):
    _attr_name = "Yearly Consumption"
    _attr_unique_id = "stromkosten_consumption_yearly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-year"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], yearly_start_day: int = 1, yearly_start_month: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.yearly_start_day = int(yearly_start_day)
        self.yearly_start_month = int(yearly_start_month)
        self._state = 0.0
        self._last_reset = self._get_yearly_start_date()
        self._accumulated = 0.0
        self._last_update_time = None
        self._store = Store(hass, 1, f"{DOMAIN}_yearly_consumption")

    def _get_yearly_start_date(self) -> datetime:
        """Berechnet das Startdatum des aktuellen Abrechnungsjahres"""
        now = datetime.now()
        try:
            # Versuche Datum im aktuellen Jahr
            start_date = now.replace(month=self.yearly_start_month, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
            
            # Wenn in der Zukunft, nutze letztes Jahr
            if start_date > now:
                start_date = start_date.replace(year=now.year - 1)
            
            return start_date
        except ValueError:
            # Fallback bei ungültigem Datum
            return now.replace(month=self.yearly_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)

    async def async_added_to_hass(self) -> None:
        stored_data = await self._store.async_load()
        if stored_data:
            try:
                self._accumulated = float(stored_data.get("accumulated", 0.0))
                self._last_reset = datetime.fromisoformat(stored_data.get("last_reset", self._last_reset.isoformat()))
            except (ValueError, TypeError):
                pass
        
        self._last_update_time = datetime.now()
        
        self.async_on_remove(
            async_track_state_change(
                self.hass,
                self.power_sensors,
                self._power_changed
            )
        )
        
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._periodic_update,
                UPDATE_INTERVAL
            )
        )
        
        await self.async_update()

    @callback
    def _power_changed(self, entity_id, old_state, new_state):
        self.async_schedule_update_ha_state(force_refresh=True)

    async def _periodic_update(self, now):
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        now = datetime.now()
        new_reset_date = self._get_yearly_start_date()
        
        if new_reset_date > self._last_reset:
            self._accumulated = 0.0
            self._last_reset = new_reset_date
            self._last_update_time = now
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })
            self._state = 0.0
            return

        if self._last_update_time is None:
            self._last_update_time = now
            return
        
        time_delta = (now - self._last_update_time).total_seconds()
        
        if time_delta <= 0 or time_delta > 3600:
            self._last_update_time = now
            return

        total_power = 0.0
        for sensor_id in self.power_sensors:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in (STATE_UNKNOWN, None, "unavailable"):
                try:
                    total_power += float(state.state)
                except ValueError:
                    pass

        if total_power > 0:
            energy_kwh = (total_power * time_delta) / 3600000
            self._accumulated += energy_kwh
            await self._store.async_save({
                "accumulated": self._accumulated, 
                "last_reset": self._last_reset.isoformat()
            })

        self._last_update_time = now
        self._state = round(self._accumulated, 3)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


def get_days_in_current_year_period(yearly_start_day: int, yearly_start_month: int) -> int:
    """Berechnet die Anzahl der Tage seit Start des Abrechnungsjahres bis heute"""
    now = datetime.now()
    try:
        start_date = now.replace(month=yearly_start_month, day=yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
        if start_date > now:
            start_date = start_date.replace(year=now.year - 1)
        return (now - start_date).days + 1
    except ValueError:
        return 1


class StromkostenConsumptionYearlyPrognosis(SensorEntity):
    _attr_name = "Yearly Consumption Prognosis"
    _attr_unique_id = "stromkosten_consumption_yearly_prognosis"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:crystal-ball"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], yearly_start_day: int = 1, yearly_start_month: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.yearly_start_day = int(yearly_start_day)
        self.yearly_start_month = int(yearly_start_month)
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
        yearly_consumption = self.hass.states.get("sensor.stromkosten_consumption_yearly")
        
        if not yearly_consumption or yearly_consumption.state in (STATE_UNKNOWN, None, "unavailable"):
            self._state = 0.0
            return
        
        try:
            current_consumption = float(yearly_consumption.state)
            days_in_period = get_days_in_current_year_period(self.yearly_start_day, self.yearly_start_month)
            
            days_in_year = 365
            avg_daily = current_consumption / days_in_period
            
            self._state = round(avg_daily * days_in_year, 2)
        except (ValueError, TypeError, ZeroDivisionError):
            self._state = 0.0

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN


class StromkostenCostYearly(SensorEntity):
    _attr_name = "Yearly Consumption Cost"
    _attr_unique_id = "stromkosten_cost_yearly"
    _attr_unit_of_measurement = "€"
    _attr_icon = "mdi:cash"

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float, yearly_start_day: int = 1, yearly_start_month: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self.yearly_start_day = int(yearly_start_day)
        self.yearly_start_month = int(yearly_start_month)
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

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], cost_per_kwh: float, yearly_start_day: int = 1, yearly_start_month: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.cost_per_kwh = float(cost_per_kwh)
        self.yearly_start_day = int(yearly_start_day)
        self.yearly_start_month = int(yearly_start_month)
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


class SolarYieldYearly(SensorEntity):
    _attr_name = "Solar Yield Yearly"
    _attr_unique_id = "solar_yield_yearly"
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-year"

    def __init__(self, hass: HomeAssistant, solar_yield_day: Optional[str], yearly_start_day: int = 1, yearly_start_month: int = 1):
        self.hass = hass
        self.solar_yield_day = solar_yield_day
        self.yearly_start_day = int(yearly_start_day)
        self.yearly_start_month = int(yearly_start_month)
        self._state = 0.0
        self._last_reset = self._get_yearly_start_date()
        self._accumulated = 0.0
        self._last_yield_value = 0.0
        self._store = Store(hass, 1, f"{DOMAIN}_solar_yield_yearly")

    def _get_yearly_start_date(self) -> datetime:
        now = datetime.now()
        try:
            start_date = now.replace(month=self.yearly_start_month, day=self.yearly_start_day, hour=0, minute=0, second=0, microsecond=0)
            if start_date > now:
                start_date = start_date.replace(year=now.year - 1)
            return start_date
        except ValueError:
            return now.replace(month=self.yearly_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)

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

        self._state = round(self._accumulated + self._last_yield_value, 2)

    @property
    def state(self) -> str | None:
        return self._state if self._state is not None else STATE_UNKNOWN