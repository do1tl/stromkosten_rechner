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
        # Jahres-Sensoren
        JahresVerbrauchSensor(hass, config, config_entry.entry_id),
        JahresSolarertragSensor(hass, config, config_entry.entry_id),
        JahresKostenSensor(hass, config, config_entry.entry_id),
        JahresEinsparungSensor(hass, config, config_entry.entry_id),
        AktuellesAbrechnungsjahrSensor(hass, config, config_entry.entry_id),
    ]

    async_add_entities(sensors, True)


def get_current_billing_year(config):
    """Calculate current billing year based on Ablesetermin."""
    now = datetime.now()
    day = config.get("ablesetermin_tag", 1)
    month = config.get("ablesetermin_monat", 1)
    
    # Aktuelles Ablesedatum in diesem Jahr
    try:
        reading_date = datetime(now.year, month, day)
    except ValueError:
        # Falls ungültiges Datum (z.B. 31. Feb), nutze letzten Tag des Monats
        reading_date = datetime(now.year, month, 1)
    
    # Wenn wir vor dem Ablesetermin sind, befinden wir uns noch im vorherigen Abrechnungsjahr
    if now < reading_date:
        return now.year - 1
    else:
        return now.year


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

    def get_yearly_data(self):
        """Get yearly data storage."""
        return self.hass.data[DOMAIN][self._entry_id]["yearly_data"]


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
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                self._daily_energy += kwh_increment

                kwh_preis = float(self._config.get("kwh_preis", 0.35))
                self._state = round(self._daily_energy * kwh_preis, 2)
                
                # Update yearly costs
                yearly_data = self.get_yearly_data()
                yearly_data["costs"] = yearly_data.get("costs", 0.0) + (kwh_increment * kwh_preis)
                
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


# ==================== JAHRES-SENSOREN ====================

class JahresVerbrauchSensor(BaseSensor):
    """Jahresverbrauch sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Jahresverbrauch"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_jahresverbrauch"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:counter"
        self._last_year = None

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        # Check if new billing year started
        if yearly_data.get("year") != current_year:
            _LOGGER.info(f"New billing year started: {current_year}")
            yearly_data["year"] = current_year
            yearly_data["energy_consumed"] = 0.0
            yearly_data["solar_produced"] = 0.0
            yearly_data["costs"] = 0.0
            yearly_data["savings"] = 0.0
        
        # Get current consumption and add to yearly
        netzbezug_entity = f"sensor.stromkosten_netzbezug"
        state = self.hass.states.get(netzbezug_entity)
        
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(state.state)
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                yearly_data["energy_consumed"] = yearly_data.get("energy_consumed", 0.0) + kwh_increment
            except (ValueError, TypeError):
                pass
        
        self._state = round(yearly_data.get("energy_consumed", 0.0), 2)


class JahresSolarertragSensor(BaseSensor):
    """Jahres-Solarertrag sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Jahres-Solarertrag"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_jahres_solarertrag"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:solar-power-variant"
        self._last_solar_value = 0.0

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        
        # Get current solar production (daily)
        solar_entity = f"sensor.stromkosten_solarertrag"
        state = self.hass.states.get(solar_entity)
        
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                current_solar = float(state.state)
                # Only add if value increased (new day)
                if current_solar > self._last_solar_value:
                    diff = current_solar - self._last_solar_value
                    yearly_data["solar_produced"] = yearly_data.get("solar_produced", 0.0) + diff
                self._last_solar_value = current_solar
            except (ValueError, TypeError):
                pass
        
        self._state = round(yearly_data.get("solar_produced", 0.0), 2)


class JahresKostenSensor(BaseSensor):
    """Jahreskosten sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Jahreskosten"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_jahreskosten"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-multiple"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        self._state = round(yearly_data.get("costs", 0.0), 2)


class JahresEinsparungSensor(BaseSensor):
    """Jahres-Einsparung sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Jahres-Einsparungen"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_jahres_einsparungen"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-plus"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        
        # Calculate savings from yearly solar production
        solar_kwh = yearly_data.get("solar_produced", 0.0)
        kwh_preis = float(self._config.get("kwh_preis", 0.35))
        savings = solar_kwh * kwh_preis
        
        yearly_data["savings"] = savings
        self._state = round(savings, 2)


class AktuellesAbrechnungsjahrSensor(BaseSensor):
    """Current billing year sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Stromkosten Abrechnungsjahr"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_abrechnungsjahr"
        self._attr_icon = "mdi:calendar"

    async def async_update(self):
        """Update sensor."""
        current_year = get_current_billing_year(self._config)
        day = self._config.get("ablesetermin_tag", 1)
        month = self._config.get("ablesetermin_monat", 1)
        self._state = f"{current_year}/{current_year + 1}"
        
        # Add attributes
        self._attr_extra_state_attributes = {
            "ablesetermin": f"{day:02d}.{month:02d}.{current_year + 1}",
            "start_jahr": current_year,
            "ende_jahr": current_year + 1,
        }
