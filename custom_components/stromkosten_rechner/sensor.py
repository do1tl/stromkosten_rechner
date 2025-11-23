"""Sensor platform für Stromkosten Rechner."""
from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stromkosten Rechner sensors."""
    config = config_entry.data

    sensors = [
        StromkostenGesamtverbrauchSensor(hass, config, config_entry.entry_id),
        StromkostenSolarertragSensor(hass, config, config_entry.entry_id),
        StromkostenNetzbezugSensor(hass, config, config_entry.entry_id),
        StromkostenKostenSensor(hass, config, config_entry.entry_id),
        StromkostenEinsparungSensor(hass, config, config_entry.entry_id),
    ]

    async_add_entities(sensors, True)


class StromkostenBaseSensor(SensorEntity):
    """Base class for Stromkosten sensors."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._entry_id = entry_id
        self._attr_should_poll = True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Stromkosten Rechner",
            "manufacturer": "Custom",
            "model": "Energy Cost Calculator",
        }


class StromkostenGesamtverbrauchSensor(StromkostenBaseSensor):
    """Sensor für Gesamtverbrauch aller Shelly-Phasen."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Gesamtverbrauch"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_gesamtverbrauch"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        entities = [
            self._config["shelly_phase_1"],
            self._config["shelly_phase_2"],
            self._config["shelly_phase_3"],
        ]

        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(self.hass, entities, sensor_state_listener)

    async def async_update(self) -> None:
        """Update the sensor."""
        total = 0

        for phase in ["shelly_phase_1", "shelly_phase_2", "shelly_phase_3"]:
            entity_id = self._config[phase]
            state = self.hass.states.get(entity_id)

            if state and state.state not in ["unknown", "unavailable", "None"]:
                try:
                    total += float(state.state)
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not convert value from %s: %s", entity_id, state.state
                    )

        self._attr_native_value = round(total, 2)


class StromkostenSolarertragSensor(StromkostenBaseSensor):
    """Sensor für gesamten Solarertrag."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Solarertrag Heute"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_solarertrag"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        entities = []
        for i in range(1, 5):
            hoymiles = self._config.get(f"hoymiles_{i}")
            if hoymiles:
                entities.append(hoymiles)

        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)

        if entities:
            async_track_state_change_event(self.hass, entities, sensor_state_listener)

    async def async_update(self) -> None:
        """Update the sensor."""
        total = 0

        for i in range(1, 5):
            hoymiles = self._config.get(f"hoymiles_{i}")
            if hoymiles:
                state = self.hass.states.get(hoymiles)

                if state and state.state not in ["unknown", "unavailable", "None"]:
                    try:
                        total += float(state.state)
                    except (ValueError, TypeError):
                        _LOGGER.warning(
                            "Could not convert value from %s: %s", hoymiles, state.state
                        )

        self._attr_native_value = round(total, 3)


class StromkostenNetzbezugSensor(StromkostenBaseSensor):
    """Sensor für aktuellen Netzbezug."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Netzbezug Aktuell"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_netzbezug"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_value = 0

    async def async_update(self) -> None:
        """Update the sensor."""
        verbrauch_sensor = self.hass.states.get(
            f"sensor.gesamtverbrauch"
        )

        verbrauch = 0

        if verbrauch_sensor and verbrauch_sensor.state not in [
            "unknown",
            "unavailable",
            "None",
        ]:
            try:
                verbrauch = float(verbrauch_sensor.state)
            except (ValueError, TypeError):
                pass

        self._attr_native_value = round(max(0, verbrauch), 2)


class StromkostenKostenSensor(StromkostenBaseSensor):
    """Sensor für tägliche Stromkosten."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Heute"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_kosten"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"
        self._daily_energy = 0
        self._last_reset = dt_util.now().date()
        self._attr_native_value = 0

    async def async_update(self) -> None:
        """Update the sensor."""
        now = dt_util.now().date()
        if now != self._last_reset:
            self._daily_energy = 0
            self._last_reset = now

        netzbezug = self.hass.states.get(f"sensor.netzbezug_aktuell")

        if netzbezug and netzbezug.state not in ["unknown", "unavailable", "None"]:
            try:
                power_w = float(netzbezug.state)
                kwh = (power_w / 1000) * (30 / 3600)
                self._daily_energy += kwh

                kwh_preis = self._config.get("kwh_preis", 0.35)
                self._attr_native_value = round(self._daily_energy * kwh_preis, 2)
            except (ValueError, TypeError):
                pass


class StromkostenEinsparungSensor(StromkostenBaseSensor):
    """Sensor für Einsparungen durch Solar."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einsparungen Heute"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_einsparungen"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-plus"
        self._attr_native_value = 0

    async def async_update(self) -> None:
        """Update the sensor."""
        solar_sensor = self.hass.states.get(f"sensor.solarertrag_heute")

        if solar_sensor and solar_sensor.state not in ["unknown", "unavailable", "None"]:
            try:
                solar_kwh = float(solar_sensor.state)
                kwh_preis = self._config.get("kwh_preis", 0.35)
                self._attr_native_value = round(solar_kwh * kwh_preis, 2)
            except (ValueError, TypeError):
                pass
