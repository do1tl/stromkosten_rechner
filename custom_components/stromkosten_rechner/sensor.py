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
        GrundgebuehrSensor(hass, config, config_entry.entry_id),
        # Phase 2: Einspeisevergütung & Autarkie
        EigenverbrauchSensor(hass, config, config_entry.entry_id),
        Autoarkie_Sensor(hass, config, config_entry.entry_id),
        EinspeisungSensor(hass, config, config_entry.entry_id),
        EinspeiseErloeSensor(hass, config, config_entry.entry_id),
        # Phase 3: Spitzenlast & Prognosen
        SpitzenlastTodaySensor(hass, config, config_entry.entry_id),
        SpitzenlastWeekSensor(hass, config, config_entry.entry_id),
        PrognoseJahreskosten(hass, config, config_entry.entry_id),
        # Phase 4: Shelly-Verfügbarkeit & HT/NT
        ShellyPhase1VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        ShellyPhase2VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        ShellyPhase3VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        HTNTModusSensor(hass, config, config_entry.entry_id),
        # Jahres-Sensoren
        JahresVerbrauchSensor(hass, config, config_entry.entry_id),
        JahresSolarertragSensor(hass, config, config_entry.entry_id),
        JahresKostenSensor(hass, config, config_entry.entry_id),
        JahresEinsparungSensor(hass, config, config_entry.entry_id),
        JahresKostenMitGrundgebuehrSensor(hass, config, config_entry.entry_id),
        JahresEinspeisungSensor(hass, config, config_entry.entry_id),
        JahresEinspeiseErloeSensor(hass, config, config_entry.entry_id),
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
        self._attr_name = "Gesamtverbrauch"
        self._attr_unique_id = f"{entry_id}_gesamtverbrauch"
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
        self._attr_name = "Solarertrag"
        self._attr_unique_id = f"{entry_id}_solarertrag"
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
        self._attr_name = "Netzbezug"
        self._attr_unique_id = f"{entry_id}_netzbezug"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:transmission-tower"

    async def async_update(self):
        """Update sensor."""
        verbrauch_entity = f"sensor.gesamtverbrauch"
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
        self._attr_name = "Kosten Heute"
        self._attr_unique_id = f"{entry_id}_kosten"
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
        netzbezug_entity = f"sensor.netzbezug"
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
        self._attr_name = "Einsparungen Heute"
        self._attr_unique_id = f"{entry_id}_einsparungen"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:piggy-bank"

    async def async_update(self):
        """Update sensor."""
        solar_entity = f"sensor.solarertrag"
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


class GrundgebuehrSensor(BaseSensor):
    """Grundgebühr sensor - monatliche Grundgebühr."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Grundgebühr Monatlich"
        self._attr_unique_id = f"{entry_id}_grundgebuehr"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:file-invoice"

    async def async_update(self):
        """Update sensor."""
        grundgebuehr = float(self._config.get("grundgebuehr", 0.0))
        self._state = round(grundgebuehr, 2)


# ==================== PHASE 2: EINSPEISEVERGÜTUNG & AUTARKIE ====================

class EigenverbrauchSensor(BaseSensor):
    """Eigenverbrauch - direkt genutzte Solarenergie."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Eigenverbrauch"
        self._attr_unique_id = f"{entry_id}_eigenverbrauch"
        self._attr_unit_of_measurement = "kWh"
        self._attr_icon = "mdi:home-lightning-bolt"

    async def async_update(self):
        """Update sensor - Solar - Einspeisung."""
        solar_entity = f"sensor.solarertrag"
        solar_state = self.hass.states.get(solar_entity)
        
        yearly_data = self.get_yearly_data()
        einspeisung = yearly_data.get("einspeisung_daily", 0.0)
        
        if solar_state and solar_state.state not in ["unknown", "unavailable"]:
            try:
                solar_kwh = float(solar_state.state)
                eigenverbrauch = max(0.0, solar_kwh - einspeisung)
                self._state = round(eigenverbrauch, 3)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class Autoarkie_Sensor(BaseSensor):
    """Autarkiegrad - % Eigenverbrauch vs Gesamtverbrauch."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Autarkiegrad"
        self._attr_unique_id = f"{entry_id}_autarkie"
        self._attr_unit_of_measurement = "%"
        self._attr_icon = "mdi:percent"

    async def async_update(self):
        """Update sensor."""
        solar_entity = f"sensor.solarertrag"
        solar_state = self.hass.states.get(solar_entity)
        
        netzbezug_entity = f"sensor.netzbezug"
        netzbezug_state = self.hass.states.get(netzbezug_entity)
        
        if solar_state and solar_state.state not in ["unknown", "unavailable"] and \
           netzbezug_state and netzbezug_state.state not in ["unknown", "unavailable"]:
            try:
                solar_kwh = float(solar_state.state)
                netzbezug_w = float(netzbezug_state.state)
                netzbezug_kwh = (netzbezug_w / 1000.0) * (30.0 / 3600.0)
                
                total_verbrauch = netzbezug_kwh + solar_kwh
                if total_verbrauch > 0:
                    autarkie = (solar_kwh / total_verbrauch) * 100
                    self._state = round(min(100.0, autarkie), 1)
                else:
                    self._state = 0.0
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class EinspeisungSensor(BaseSensor):
    """Tägliche Einspeisung ins Netz."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einspeisung Heute"
        self._attr_unique_id = f"{entry_id}_einspeisung"
        self._attr_unit_of_measurement = "kWh"
        self._attr_icon = "mdi:transmission-tower-export"
        self._daily_einspeisung = 0.0
        self._last_reset = datetime.now().date()

    async def async_update(self):
        """Update sensor - wird berechnet als Solar - Eigennutzung."""
        now = datetime.now().date()
        if now != self._last_reset:
            self._daily_einspeisung = 0.0
            self._last_reset = now
            
        yearly_data = self.get_yearly_data()
        
        solar_entity = f"sensor.solarertrag"
        solar_state = self.hass.states.get(solar_entity)
        
        if solar_state and solar_state.state not in ["unknown", "unavailable"]:
            try:
                solar_kwh = float(solar_state.state)
                netzbezug_entity = f"sensor.netzbezug"
                netzbezug_state = self.hass.states.get(netzbezug_entity)
                
                if netzbezug_state and netzbezug_state.state not in ["unknown", "unavailable"]:
                    netzbezug_w = float(netzbezug_state.state)
                    netzbezug_kwh = (netzbezug_w / 1000.0) * (30.0 / 3600.0)
                    einspeisung = max(0.0, solar_kwh - netzbezug_kwh)
                    self._daily_einspeisung = einspeisung
                    yearly_data["einspeisung_daily"] = einspeisung
                    self._state = round(einspeisung, 3)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class EinspeiseErloeSensor(BaseSensor):
    """Erlös aus Stromeinspeisung heute."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einspeise-Erlös Heute"
        self._attr_unique_id = f"{entry_id}_einspeise_erloes"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-plus"

    async def async_update(self):
        """Update sensor."""
        einspeisung_entity = f"sensor.einspeisung_heute"
        einspeisung_state = self.hass.states.get(einspeisung_entity)
        
        einspeiseverguetung = float(self._config.get("einspeiseverguetung", 0.0))
        
        if einspeisung_state and einspeisung_state.state not in ["unknown", "unavailable"]:
            try:
                einspeisung_kwh = float(einspeisung_state.state)
                erloes = einspeisung_kwh * einspeiseverguetung
                self._state = round(erloes, 2)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


# ==================== PHASE 3: SPITZENLAST & PROGNOSEN ====================

class SpitzenlastTodaySensor(BaseSensor):
    """Höchster Verbrauch heute."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Spitzenlast Heute"
        self._attr_unique_id = f"{entry_id}_spitzenlast_today"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash"
        self._max_today = 0.0
        self._last_reset = datetime.now().date()

    async def async_update(self):
        """Update sensor."""
        now = datetime.now().date()
        if now != self._last_reset:
            self._max_today = 0.0
            self._last_reset = now
            
        verbrauch_entity = f"sensor.gesamtverbrauch"
        verbrauch_state = self.hass.states.get(verbrauch_entity)
        
        if verbrauch_state and verbrauch_state.state not in ["unknown", "unavailable"]:
            try:
                current_verbrauch = float(verbrauch_state.state)
                if current_verbrauch > self._max_today:
                    self._max_today = current_verbrauch
                self._state = round(self._max_today, 0)
            except (ValueError, TypeError):
                pass


class SpitzenlastWeekSensor(BaseSensor):
    """Höchster Verbrauch diese Woche."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Spitzenlast Woche"
        self._attr_unique_id = f"{entry_id}_spitzenlast_week"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash-alert"
        self._max_week = 0.0
        self._week_number = 0

    async def async_update(self):
        """Update sensor."""
        now = datetime.now()
        current_week = now.isocalendar()[1]
        
        if current_week != self._week_number:
            self._max_week = 0.0
            self._week_number = current_week
            
        verbrauch_entity = f"sensor.gesamtverbrauch"
        verbrauch_state = self.hass.states.get(verbrauch_entity)
        
        if verbrauch_state and verbrauch_state.state not in ["unknown", "unavailable"]:
            try:
                current_verbrauch = float(verbrauch_state.state)
                if current_verbrauch > self._max_week:
                    self._max_week = current_verbrauch
                self._state = round(self._max_week, 0)
            except (ValueError, TypeError):
                pass


class PrognoseJahreskosten(BaseSensor):
    """Hochrechnung Jahreskosten basierend auf aktuellem Verbrauch."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Prognose Jahreskosten"
        self._attr_unique_id = f"{entry_id}_prognose_jahreskosten"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:chart-line"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        
        # Tage seit Ablesetermin
        config = self._config
        day = config.get("ablesetermin_tag", 1)
        month = config.get("ablesetermin_monat", 1)
        
        now = datetime.now()
        try:
            billing_start = datetime(now.year, month, day)
        except ValueError:
            billing_start = datetime(now.year, month, 28)
        
        if now < billing_start:
            try:
                billing_start = datetime(now.year - 1, month, day)
            except ValueError:
                billing_start = datetime(now.year - 1, month, 28)
        
        days_passed = (now - billing_start).days + 1
        current_costs = yearly_data.get("costs", 0.0)
        grundgebuehr = float(config.get("grundgebuehr", 0.0))
        months_passed = max(1, days_passed // 30)
        
        total_current = current_costs + (grundgebuehr * months_passed)
        
        if days_passed > 0:
            daily_average = total_current / days_passed
            prognose = daily_average * 365
            self._state = round(prognose, 2)
        else:
            self._state = 0.0


# ==================== JAHRES-SENSOREN ====================

class JahresVerbrauchSensor(BaseSensor):
    """Jahresverbrauch sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahresverbrauch"
        self._attr_unique_id = f"{entry_id}_jahresverbrauch"
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
        netzbezug_entity = f"sensor.netzbezug"
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
        self._attr_name = "Jahres-Solarertrag"
        self._attr_unique_id = f"{entry_id}_jahres_solarertrag"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:solar-power-variant"
        self._last_solar_value = 0.0

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        
        # Get current solar production (daily)
        solar_entity = f"sensor.solarertrag"
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
        self._attr_name = "Jahreskosten"
        self._attr_unique_id = f"{entry_id}_jahreskosten"
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
        self._attr_name = "Jahres-Einsparungen"
        self._attr_unique_id = f"{entry_id}_jahres_einsparungen"
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


class JahresKostenMitGrundgebuehrSensor(BaseSensor):
    """Jahreskosten inklusive Grundgebühr."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahreskosten mit Grundgebühr"
        self._attr_unique_id = f"{entry_id}_jahreskosten_mit_grundgebuehr"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        grundgebuehr = float(self._config.get("grundgebuehr", 0.0))
        
        # Get months since billing start
        from datetime import datetime
        config = self._config
        day = config.get("ablesetermin_tag", 1)
        month = config.get("ablesetermin_monat", 1)
        
        now = datetime.now()
        billing_start = datetime(now.year, month, day) if month != 2 or day <= 28 else datetime(now.year, month, 28)
        
        if now < billing_start:
            billing_start = datetime(now.year - 1, month, day) if month != 2 or day <= 28 else datetime(now.year - 1, month, 28)
        
        # Calculate months (approximation)
        months = max(1, (now - billing_start).days // 30 + 1)
        
        total_kosten = yearly_data.get("costs", 0.0) + (grundgebuehr * months)
        self._state = round(total_kosten, 2)


class JahresEinspeisungSensor(BaseSensor):
    """Jahres-Einspeisung sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahres-Einspeisung"
        self._attr_unique_id = f"{entry_id}_jahres_einspeisung"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:transmission-tower-export"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        
        # Track daily einspeisung
        einspeisung_today = yearly_data.get("einspeisung_daily", 0.0)
        yearly_einspeisung = yearly_data.get("einspeisung_yearly", 0.0)
        
        if einspeisung_today > 0:
            yearly_data["einspeisung_yearly"] = yearly_einspeisung + einspeisung_today
        
        self._state = round(yearly_data.get("einspeisung_yearly", 0.0), 2)


class JahresEinspeiseErloeSensor(BaseSensor):
    """Jahres-Einspeise-Erlös sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahres-Einspeise-Erlös"
        self._attr_unique_id = f"{entry_id}_jahres_einspeise_erloes"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-multiple"

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        einspeiseverguetung = float(self._config.get("einspeiseverguetung", 0.0))
        
        jahres_einspeisung = yearly_data.get("einspeisung_yearly", 0.0)
        erloes = jahres_einspeisung * einspeiseverguetung
        
        self._state = round(erloes, 2)


class AktuellesAbrechnungsjahrSensor(BaseSensor):
    """Current billing year sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Abrechnungsjahr"
        self._attr_unique_id = f"{entry_id}_abrechnungsjahr"
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


class ShellyPhase1VerfuegbarkeitSensor(BaseSensor):
    """Shelly Phase 1 Verfügbarkeit sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Shelly Phase 1 Verfügbarkeit"
        self._attr_unique_id = f"{entry_id}_shelly_p1_verfuegbarkeit"
        self._attr_icon = "mdi:check-circle"

    async def async_update(self):
        """Update sensor."""
        entity_id = self._config.get("shelly_phase_1")
        if not entity_id:
            self._state = "nicht konfiguriert"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
        else:
            self._state = "erreichbar"


class ShellyPhase2VerfuegbarkeitSensor(BaseSensor):
    """Shelly Phase 2 Verfügbarkeit sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Shelly Phase 2 Verfügbarkeit"
        self._attr_unique_id = f"{entry_id}_shelly_p2_verfuegbarkeit"
        self._attr_icon = "mdi:check-circle"

    async def async_update(self):
        """Update sensor."""
        entity_id = self._config.get("shelly_phase_2")
        if not entity_id:
            self._state = "nicht konfiguriert"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
        else:
            self._state = "erreichbar"


class ShellyPhase3VerfuegbarkeitSensor(BaseSensor):
    """Shelly Phase 3 Verfügbarkeit sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Shelly Phase 3 Verfügbarkeit"
        self._attr_unique_id = f"{entry_id}_shelly_p3_verfuegbarkeit"
        self._attr_icon = "mdi:check-circle"

    async def async_update(self):
        """Update sensor."""
        entity_id = self._config.get("shelly_phase_3")
        if not entity_id:
            self._state = "nicht konfiguriert"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
        else:
            self._state = "erreichbar"


class HTNTModusSensor(BaseSensor):
    """HT/NT Modus sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "HT/NT Modus"
        self._attr_unique_id = f"{entry_id}_ht_nt_modus"
        self._attr_icon = "mdi:clock"

    async def async_update(self):
        """Update sensor."""
        ht_nt_enabled = self._config.get("ht_nt_enabled", False)
        if not ht_nt_enabled:
            self._state = "deaktiviert"
            return
        
        from datetime import datetime
        now = datetime.now()
        ht_start_str = self._config.get("ht_start", "06:00")
        ht_end_str = self._config.get("ht_end", "22:00")
        
        try:
            ht_start = datetime.strptime(ht_start_str, "%H:%M").time()
            ht_end = datetime.strptime(ht_end_str, "%H:%M").time()
            
            if ht_start <= now.time() < ht_end:
                self._state = "Hochtarif (HT)"
            else:
                self._state = "Niedrigtarif (NT)"
        except ValueError:
            self._state = "ungültiges Zeitformat"
