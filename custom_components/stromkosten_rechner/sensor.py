"""Sensor platform für Stromkosten Rechner."""
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"
SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromkosten Rechner sensors."""
    config = config_entry.data
    
    sensors = [
        StromkostenGesamtverbrauchSensor(hass, config),
        StromkostenSolarertragSensor(hass, config),
        StromkostenNetzbezugSensor(hass, config),
        StromkostenKostenSensor(hass, config),
        StromkostenEinsparungSensor(hass, config),
        StromkostenTagesKostenSensor(hass, config),
        StromkostenTagesEinsparungSensor(hass, config),
    ]
    
    async_add_entities(sensors, True)


class StromkostenGesamtverbrauchSensor(SensorEntity):
    """Sensor für Gesamtverbrauch aller Shelly-Phasen."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Gesamtverbrauch"
        self._attr_unique_id = f"{DOMAIN}_gesamtverbrauch"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    async def async_added_to_hass(self):
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

    async def async_update(self):
        """Update the sensor."""
        total = 0
        
        for phase in ["shelly_phase_1", "shelly_phase_2", "shelly_phase_3"]:
            entity_id = self._config[phase]
            state = self.hass.states.get(entity_id)
            
            if state and state.state not in ["unknown", "unavailable"]:
                try:
                    total += float(state.state)
                except ValueError:
                    _LOGGER.warning(f"Konnte Wert von {entity_id} nicht konvertieren: {state.state}")
        
        self._state = round(total, 2)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenSolarertragSensor(SensorEntity):
    """Sensor für gesamten Solarertrag."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Solarertrag"
        self._attr_unique_id = f"{DOMAIN}_solarertrag"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    async def async_added_to_hass(self):
        """Register callbacks."""
        entities = []
        for i in range(1, 5):
            hoymiles = self._config.get(f"hoymiles_{i}", "")
            if hoymiles:
                entities.append(hoymiles)
        
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)
        
        if entities:
            async_track_state_change_event(self.hass, entities, sensor_state_listener)

    async def async_update(self):
        """Update the sensor."""
        total = 0
        
        for i in range(1, 5):
            hoymiles = self._config.get(f"hoymiles_{i}", "")
            if hoymiles:
                state = self.hass.states.get(hoymiles)
                
                if state and state.state not in ["unknown", "unavailable"]:
                    try:
                        total += float(state.state)
                    except ValueError:
                        _LOGGER.warning(f"Konnte Wert von {hoymiles} nicht konvertieren: {state.state}")
        
        self._state = round(total, 3)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenNetzbezugSensor(SensorEntity):
    """Sensor für Netzbezug (Verbrauch - Solar)."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Netzbezug"
        self._attr_unique_id = f"{DOMAIN}_netzbezug"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    async def async_added_to_hass(self):
        """Register callbacks."""
        entities = [
            self._config["shelly_phase_1"],
            self._config["shelly_phase_2"],
            self._config["shelly_phase_3"],
        ]
        
        for i in range(1, 5):
            hoymiles = self._config.get(f"hoymiles_{i}", "")
            if hoymiles:
                entities.append(hoymiles)
        
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)
        
        async_track_state_change_event(self.hass, entities, sensor_state_listener)

    async def async_update(self):
        """Update the sensor."""
        # Hole Gesamtverbrauch
        verbrauch_sensor = self.hass.states.get(f"sensor.stromkosten_gesamtverbrauch")
        solar_sensor = self.hass.states.get(f"sensor.stromkosten_solarertrag")
        
        verbrauch = 0
        solar = 0
        
        if verbrauch_sensor and verbrauch_sensor.state not in ["unknown", "unavailable"]:
            try:
                verbrauch = float(verbrauch_sensor.state)
            except ValueError:
                pass
        
        # Solar ist in kWh täglich, wir brauchen die aktuelle Leistung
        # Für echte Berechnung sollten wir die aktuellen Power-Sensoren der Hoymiles nutzen
        # Hier vereinfacht: Netzbezug = Verbrauch (Solar wird über Einsparung berechnet)
        
        self._state = round(max(0, verbrauch), 2)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenKostenSensor(SensorEntity):
    """Sensor für tägliche Stromkosten vom Netz."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._daily_energy = 0
        self._last_reset = dt_util.now().date()
        self._attr_name = "Stromkosten Tägliche Kosten"
        self._attr_unique_id = f"{DOMAIN}_kosten"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"

    async def async_update(self):
        """Update the sensor."""
        # Prüfe ob neuer Tag
        now = dt_util.now().date()
        if now != self._last_reset:
            self._daily_energy = 0
            self._last_reset = now
        
        # Berechne Kosten basierend auf Netzbezug
        netzbezug = self.hass.states.get(f"sensor.stromkosten_netzbezug")
        
        if netzbezug and netzbezug.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(netzbezug.state)
                # Umrechnung W zu kWh für diesen Update-Zyklus (30 Sekunden)
                kwh = (power_w / 1000) * (30 / 3600)
                self._daily_energy += kwh
                
                kwh_preis = self._config.get("kwh_preis", 0.35)
                self._state = round(self._daily_energy * kwh_preis, 2)
            except ValueError:
                pass

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenEinsparungSensor(SensorEntity):
    """Sensor für Einsparungen durch Solar."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Einsparungen"
        self._attr_unique_id = f"{DOMAIN}_einsparungen"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-plus"

    async def async_update(self):
        """Update the sensor."""
        solar_sensor = self.hass.states.get(f"sensor.stromkosten_solarertrag")
        
        if solar_sensor and solar_sensor.state not in ["unknown", "unavailable"]:
            try:
                solar_kwh = float(solar_sensor.state)
                kwh_preis = self._config.get("kwh_preis", 0.35)
                self._state = round(solar_kwh * kwh_preis, 2)
            except ValueError:
                pass

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenTagesKostenSensor(SensorEntity):
    """Sensor für Gesamtkosten heute."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Heute Gesamt"
        self._attr_unique_id = f"{DOMAIN}_heute_gesamt"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash"

    async def async_update(self):
        """Update the sensor."""
        kosten = self.hass.states.get(f"sensor.stromkosten_tagliche_kosten")
        
        if kosten and kosten.state not in ["unknown", "unavailable"]:
            try:
                self._state = float(kosten.state)
            except ValueError:
                pass

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class StromkostenTagesEinsparungSensor(SensorEntity):
    """Sensor für Einsparungen heute."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self._state = 0
        self._attr_name = "Stromkosten Einsparungen Heute"
        self._attr_unique_id = f"{DOMAIN}_einsparungen_heute"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:piggy-bank"

    async def async_update(self):
        """Update the sensor."""
        einsparungen = self.hass.states.get(f"sensor.stromkosten_einsparungen")
        
        if einsparungen and einsparungen.state not in ["unknown", "unavailable"]:
            try:
                self._state = float(einsparungen.state)
            except ValueError:
                pass

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state
