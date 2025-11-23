"""Sensor platform."""
from datetime import timedelta, datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

DOMAIN = "stromkosten_rechner"
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors."""
    config = config_entry.data

    sensors = [
        GesamtverbrauchSensor(hass, config, config_entry.entry_id),
        SolarertragSensor(hass, config, config_entry.entry_id),
        NetzbezugSensor(hass, config, config_entry.entry_id),
        KostenSensor(hass, config, config_entry.entry_id),
        EinsparungSensor(hass, config, config_entry.entry_id),
    ]

    async_add_entities(sensors, True)


class BaseSensor(SensorEntity):
    """Base sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        self.hass = hass
        self._config = config
        self._entry_id = entry_id
        self._state = None
        self._available = True

    @property
    def should_poll(self):
        """Poll for updates."""
        return True

    @property
    def available(self):
        """Return availability."""
        return self._available

    @property
    def state(self):
        """Return state."""
        return self._state


class GesamtverbrauchSensor(BaseSensor):
    """Gesamtverbrauch sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Gesamtverbrauch"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_gesamtverbrauch"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:lightning-bolt"

    async def async_added_to_hass(self):
        """When added to hass."""
        entities = [
            self._config.get("shelly_phase_1"),
            self._config.get("shelly_phase_2"),
            self._config.get("shelly_phase_3"),
        ]

        @callback
        def state_changed(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(self.hass, entities, state_changed)

    async def async_update(self):
        """Update sensor."""
        total = 0.0

        for i in range(1, 4):
            entity_id = self._config.get(f"shelly_phase_{i}")
            if not entity_id:
                continue

            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unknown", "unavailable"]:
                try:
                    total += float(state.state)
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(f"Cannot convert {entity_id}: {e}")

        self._state = round(total, 2)


class SolarertragSensor(BaseSensor):
    """Solarertrag sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Solarertrag"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_solarertrag"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:solar-power"

    async def async_added_to_hass(self):
        """When added to hass."""
        entities = []
        for i in range(1, 5):
            entity_id = self._config.get(f"hoymiles_{i}")
            if entity_id:
                entities.append(entity_id)

        @callback
        def state_changed(event):
            """Handle state changes."""
            self.async_schedule_update_ha_state(True)

        if entities:
            async_track_state_change_event(self.hass, entities, state_changed)

    async def async_update(self):
        """Update sensor."""
        total = 0.0

        for i in range(1, 5):
            entity_id = self._config.get(f"hoymiles_{i}")
            if not entity_id:
                continue

            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unknown", "unavailable"]:
                try:
                    total += float(state.state)
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(f"Cannot convert {entity_id}: {e}")

        self._state = round(total, 3)


class NetzbezugSensor(BaseSensor):
    """Netzbezug sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Netzbezug"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_netzbezug"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:transmission-tower"

    async def async_update(self):
        """Update sensor."""
        verbrauch_entity = f"sensor.stromkosten_gesamtverbrauch"
        state = self.hass.states.get(verbrauch_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                self._state = round(float(state.state), 2)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class KostenSensor(BaseSensor):
    """Kosten sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Kosten Heute"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_kosten"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"
        self._daily_energy = 0.0
        self._last_reset = datetime.now().date()

    async def async_update(self):
        """Update sensor."""
        # Reset bei neuem Tag
        now = datetime.now().date()
        if now != self._last_reset:
            self._daily_energy = 0.0
            self._last_reset = now

        # Hole Netzbezug
        netzbezug_entity = f"sensor.stromkosten_netzbezug"
        state = self.hass.states.get(netzbezug_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(state.state)
                # Umrechnung zu kWh für 30 Sekunden
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                self._daily_energy += kwh_increment

                kwh_preis = float(self._config.get("kwh_preis", 0.35))
                self._state = round(self._daily_energy * kwh_preis, 2)
            except (ValueError, TypeError) as e:
                _LOGGER.warning(f"Error calculating costs: {e}")
        else:
            self._state = round(self._daily_energy * float(self._config.get("kwh_preis", 0.35)), 2)


class EinsparungSensor(BaseSensor):
    """Einsparung sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Einsparungen Heute"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_einsparungen"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:piggy-bank"

    async def async_update(self):
        """Update sensor."""
        solar_entity = f"sensor.stromkosten_solarertrag"
        state = self.hass.states.get(solar_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                solar_kwh = float(state.state)
                kwh_preis = float(self._config.get("kwh_preis", 0.35))
                self._state = round(solar_kwh * kwh_preis, 2)
            except (ValueError, TypeError) as e:
                _LOGGER.warning(f"Error calculating savings: {e}")
                self._state = 0.0
        else:
            self._state = 0.0
