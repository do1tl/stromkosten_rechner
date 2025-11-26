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

    def __init__(self, hass: HomeAssistant, power_sensors: list[str], yearly_start_day: int = 1):
        self.hass = hass
        self.power_sensors = power_sensors
        self.yearly_start_day = int(yearly_start_day)
        self._state = 0.0
        self._last_reset = self._get_yearly_start_date()
        self._accumulated = 0.0
        self._last_update_time = None
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