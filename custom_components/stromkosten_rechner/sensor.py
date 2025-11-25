"""Sensor platform - IMPROVED VERSION with HT/NT support."""
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
        EigenverbrauchSensor(hass, config, config_entry.entry_id),
        AutarkieSensor(hass, config, config_entry.entry_id),
        EinspeisungSensor(hass, config, config_entry.entry_id),
        EinspeiseErloeSensor(hass, config, config_entry.entry_id),
        SpitzenlastTodaySensor(hass, config, config_entry.entry_id),
        SpitzenlastWeekSensor(hass, config, config_entry.entry_id),
        PrognoseJahreskosten(hass, config, config_entry.entry_id),
        ShellyPhase1VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        ShellyPhase2VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        ShellyPhase3VerfuegbarkeitSensor(hass, config, config_entry.entry_id),
        HTNTModusSensor(hass, config, config_entry.entry_id),
        HTEnergieSensor(hass, config, config_entry.entry_id),
        NTEnergieSensor(hass, config, config_entry.entry_id),
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
    
    try:
        reading_date = datetime(now.year, month, day)
    except ValueError:
        reading_date = datetime(now.year, month, 28)
    
    if now < reading_date:
        return now.year - 1
    else:
        return now.year


class BaseSensor(SensorEntity):
    """Base sensor with utilities."""

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

    async def save_yearly_data(self):
        """Save yearly data to storage."""
        try:
            store = self.hass.data[DOMAIN][self._entry_id]["store"]
            yearly_data = self.get_yearly_data()
            await store.async_save(yearly_data)
        except Exception as e:
            _LOGGER.error(f"Error saving yearly data: {e}")

    def get_kwh_preis(self):
        """Get current kWh price considering HT/NT tariff."""
        if not self._config.get("ht_nt_enabled", False):
            return float(self._config.get("kwh_preis", 0.35))
        
        now = datetime.now().time()
        
        try:
            ht_start_str = self._config.get("ht_start", "06:00")
            ht_end_str = self._config.get("ht_end", "22:00")
            ht_start = datetime.strptime(ht_start_str, "%H:%M").time()
            ht_end = datetime.strptime(ht_end_str, "%H:%M").time()
            
            if ht_start <= ht_end:
                is_ht = ht_start <= now < ht_end
            else:
                is_ht = now >= ht_start or now < ht_end
            
            if is_ht:
                return float(self._config.get("ht_preis", 0.45))
            else:
                return float(self._config.get("nt_preis", 0.25))
                
        except (ValueError, TypeError) as e:
            _LOGGER.error(f"Error parsing HT/NT times: {e}")
            return float(self._config.get("kwh_preis", 0.35))

    def is_ht_time(self):
        """Check if current time is HT."""
        if not self._config.get("ht_nt_enabled", False):
            return True
        
        now = datetime.now().time()
        
        try:
            ht_start = datetime.strptime(self._config.get("ht_start", "06:00"), "%H:%M").time()
            ht_end = datetime.strptime(self._config.get("ht_end", "22:00"), "%H:%M").time()
            
            if ht_start <= ht_end:
                return ht_start <= now < ht_end
            else:
                return now >= ht_start or now < ht_end
        except (ValueError, TypeError):
            return True


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

    async def async_added_to_hass(self):
        """Subscribe to gesamtverbrauch changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass, 
            ["sensor.gesamtverbrauch"], 
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        verbrauch_entity = "sensor.gesamtverbrauch"
        state = self.hass.states.get(verbrauch_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                self._state = round(float(state.state), 2)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class KostenSensor(BaseSensor):
    """Kosten sensor with HT/NT support."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Kosten Heute"
        self._attr_unique_id = f"{entry_id}_kosten"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"
        self._daily_energy_ht = 0.0
        self._daily_energy_nt = 0.0
        self._last_reset = datetime.now().date()

    async def async_added_to_hass(self):
        """Subscribe to netzbezug changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass, 
            ["sensor.netzbezug"], 
            state_changed
        )

    async def async_update(self):
        """Update sensor with HT/NT aware pricing."""
        now = datetime.now().date()
        if now != self._last_reset:
            self._daily_energy_ht = 0.0
            self._daily_energy_nt = 0.0
            self._state = 0.0
            self._last_reset = now

        netzbezug_entity = "sensor.netzbezug"
        state = self.hass.states.get(netzbezug_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(state.state)
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                
                if self._config.get("ht_nt_enabled", False):
                    if self.is_ht_time():
                        self._daily_energy_ht += kwh_increment
                    else:
                        self._daily_energy_nt += kwh_increment
                    
                    ht_preis = float(self._config.get("ht_preis", 0.45))
                    nt_preis = float(self._config.get("nt_preis", 0.25))
                    total_costs = (
                        self._daily_energy_ht * ht_preis +
                        self._daily_energy_nt * nt_preis
                    )
                else:
                    self._daily_energy_ht += kwh_increment
                    kwh_preis = float(self._config.get("kwh_preis", 0.35))
                    total_costs = self._daily_energy_ht * kwh_preis
                
                self._state = round(total_costs, 2)
                
                yearly_data = self.get_yearly_data()
                kwh_preis = self.get_kwh_preis()
                yearly_data["costs"] = yearly_data.get("costs", 0.0) + (kwh_increment * kwh_preis)
                
                if self._config.get("ht_nt_enabled", False):
                    if self.is_ht_time():
                        yearly_data["ht_energy"] = yearly_data.get("ht_energy", 0.0) + kwh_increment
                    else:
                        yearly_data["nt_energy"] = yearly_data.get("nt_energy", 0.0) + kwh_increment
                
                await self.save_yearly_data()
                
            except (ValueError, TypeError) as e:
                _LOGGER.warning(f"Error calculating costs: {e}")
        else:
            if self._config.get("ht_nt_enabled", False):
                ht_preis = float(self._config.get("ht_preis", 0.45))
                nt_preis = float(self._config.get("nt_preis", 0.25))
                self._state = round(
                    self._daily_energy_ht * ht_preis + self._daily_energy_nt * nt_preis, 2
                )
            else:
                kwh_preis = float(self._config.get("kwh_preis", 0.35))
                self._state = round(self._daily_energy_ht * kwh_preis, 2)


class EinsparungSensor(BaseSensor):
    """Einsparung sensor - daily savings from solar self-consumption."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einsparungen Heute"
        self._attr_unique_id = f"{entry_id}_einsparungen_heute"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:piggy-bank"

    async def async_added_to_hass(self):
        """Subscribe to eigenverbrauch changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.eigenverbrauch"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        eigenverbrauch_entity = "sensor.eigenverbrauch"
        state = self.hass.states.get(eigenverbrauch_entity)

        if state and state.state not in ["unknown", "unavailable"]:
            try:
                eigenverbrauch = float(state.state)
                kwh_preis = self.get_kwh_preis()
                einsparungen = eigenverbrauch * kwh_preis
                self._state = round(einsparungen, 2)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class GrundgebuehrSensor(BaseSensor):
    """Grundgebühr sensor - monthly base fee."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Grundgebühr Monatlich"
        self._attr_unique_id = f"{entry_id}_grundgebuehr_monatlich"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:receipt"

    async def async_update(self):
        """Update sensor."""
        grundgebuehr = float(self._config.get("grundgebuehr", 0.0))
        self._state = round(grundgebuehr, 2)


class EigenverbrauchSensor(BaseSensor):
    """Eigenverbrauch sensor - solar self-consumption today."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Eigenverbrauch"
        self._attr_unique_id = f"{entry_id}_eigenverbrauch"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:home-lightning-bolt"

    async def async_added_to_hass(self):
        """Subscribe to solar and feed-in changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.solarertrag", "sensor.einspeisung_heute"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        solar_state = self.hass.states.get("sensor.solarertrag")
        feed_state = self.hass.states.get("sensor.einspeisung_heute")

        if solar_state and feed_state:
            if (solar_state.state not in ["unknown", "unavailable"] and 
                feed_state.state not in ["unknown", "unavailable"]):
                try:
                    solarertrag = float(solar_state.state)
                    einspeisung = float(feed_state.state)
                    eigenverbrauch = max(0, solarertrag - einspeisung)
                    self._state = round(eigenverbrauch, 2)
                except (ValueError, TypeError):
                    self._state = 0.0
            else:
                self._state = 0.0
        else:
            self._state = 0.0


class AutarkieSensor(BaseSensor):
    """Autarkie sensor - self-sufficiency percentage."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Autarkiegrad"
        self._attr_unique_id = f"{entry_id}_autarkiegrad"
        self._attr_unit_of_measurement = "%"
        self._attr_icon = "mdi:percent"

    async def async_added_to_hass(self):
        """Subscribe to eigenverbrauch and netzbezug changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.eigenverbrauch", "sensor.netzbezug"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        eigenverbrauch_state = self.hass.states.get("sensor.eigenverbrauch")
        netzbezug_state = self.hass.states.get("sensor.netzbezug")

        if eigenverbrauch_state and netzbezug_state:
            if (eigenverbrauch_state.state not in ["unknown", "unavailable"] and
                netzbezug_state.state not in ["unknown", "unavailable"]):
                try:
                    eigenverbrauch = float(eigenverbrauch_state.state)
                    netzbezug = float(netzbezug_state.state)
                    total_power = eigenverbrauch + netzbezug
                    
                    if total_power == 0:
                        autarkie = 100.0
                    else:
                        autarkie = (eigenverbrauch / total_power) * 100
                    
                    self._state = round(min(100, autarkie), 2)
                except (ValueError, TypeError):
                    self._state = 0.0
            else:
                self._state = 0.0
        else:
            self._state = 0.0


class EinspeisungSensor(BaseSensor):
    """Einspeisung sensor - solar feed-in today."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einspeisung Heute"
        self._attr_unique_id = f"{entry_id}_einspeisung_heute"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:transmission-tower-export"

    async def async_added_to_hass(self):
        """Subscribe to solar and self-consumption changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.solarertrag", "sensor.eigenverbrauch"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        solar_state = self.hass.states.get("sensor.solarertrag")
        eigenverbrauch_state = self.hass.states.get("sensor.eigenverbrauch")

        if solar_state and eigenverbrauch_state:
            if (solar_state.state not in ["unknown", "unavailable"] and
                eigenverbrauch_state.state not in ["unknown", "unavailable"]):
                try:
                    solarertrag = float(solar_state.state)
                    eigenverbrauch = float(eigenverbrauch_state.state)
                    einspeisung = max(0, solarertrag - eigenverbrauch)
                    self._state = round(einspeisung, 2)
                except (ValueError, TypeError):
                    self._state = 0.0
            else:
                self._state = 0.0
        else:
            self._state = 0.0


class EinspeiseErloeSensor(BaseSensor):
    """Einspeise-Erlös sensor - feed-in compensation today."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Einspeise Erlöes Heute"
        self._attr_unique_id = f"{entry_id}_einspeise_erloes_heute"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:cash-multiple"

    async def async_added_to_hass(self):
        """Subscribe to einspeisung changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.einspeisung_heute"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        einspeisung_state = self.hass.states.get("sensor.einspeisung_heute")

        if einspeisung_state and einspeisung_state.state not in ["unknown", "unavailable"]:
            try:
                einspeisung = float(einspeisung_state.state)
                einspeiseverguetung = float(self._config.get("einspeiseverguetung", 0.0))
                erloes = einspeisung * einspeiseverguetung
                self._state = round(erloes, 2)
            except (ValueError, TypeError):
                self._state = 0.0
        else:
            self._state = 0.0


class SpitzenlastTodaySensor(BaseSensor):
    """Spitzenlast today sensor - peak load today."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Spitzenlast Heute"
        self._attr_unique_id = f"{entry_id}_spitzenlast_heute"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash-triangle"
        self._spitzenlast = 0.0
        self._last_reset = datetime.now().date()

    async def async_added_to_hass(self):
        """Subscribe to gesamtverbrauch changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.gesamtverbrauch"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        now = datetime.now().date()
        if now != self._last_reset:
            self._spitzenlast = 0.0
            self._last_reset = now

        verbrauch_state = self.hass.states.get("sensor.gesamtverbrauch")
        if verbrauch_state and verbrauch_state.state not in ["unknown", "unavailable"]:
            try:
                verbrauch = float(verbrauch_state.state)
                if verbrauch > self._spitzenlast:
                    self._spitzenlast = verbrauch
            except (ValueError, TypeError):
                pass

        self._state = round(self._spitzenlast, 2)


class SpitzenlastWeekSensor(BaseSensor):
    """Spitzenlast week sensor - peak load this week."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Spitzenlast Woche"
        self._attr_unique_id = f"{entry_id}_spitzenlast_woche"
        self._attr_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash-triangle"
        self._spitzenlast_woche = 0.0
        self._last_reset = datetime.now().isocalendar()[1]

    async def async_added_to_hass(self):
        """Subscribe to gesamtverbrauch changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.gesamtverbrauch"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        current_week = datetime.now().isocalendar()[1]
        if current_week != self._last_reset:
            self._spitzenlast_woche = 0.0
            self._last_reset = current_week

        verbrauch_state = self.hass.states.get("sensor.gesamtverbrauch")
        if verbrauch_state and verbrauch_state.state not in ["unknown", "unavailable"]:
            try:
                verbrauch = float(verbrauch_state.state)
                if verbrauch > self._spitzenlast_woche:
                    self._spitzenlast_woche = verbrauch
            except (ValueError, TypeError):
                pass

        self._state = round(self._spitzenlast_woche, 2)


class PrognoseJahreskosten(BaseSensor):
    """Prognose Jahreskosten sensor - yearly cost forecast."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Prognose Jahreskosten"
        self._attr_unique_id = f"{entry_id}_prognose_jahreskosten"
        self._attr_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:chart-line"

    async def async_added_to_hass(self):
        """Subscribe to jahreskosten and abrechnungsjahr changes."""
        @callback
        def state_changed(event):
            self.async_schedule_update_ha_state(True)

        async_track_state_change_event(
            self.hass,
            ["sensor.jahreskosten", "sensor.abrechnungsjahr"],
            state_changed
        )

    async def async_update(self):
        """Update sensor."""
        jahreskosten_state = self.hass.states.get("sensor.jahreskosten")
        abrechnungsjahr_state = self.hass.states.get("sensor.abrechnungsjahr")

        if jahreskosten_state and abrechnungsjahr_state:
            if (jahreskosten_state.state not in ["unknown", "unavailable"] and
                abrechnungsjahr_state.state not in ["unknown", "unavailable"]):
                try:
                    jahreskosten = float(jahreskosten_state.state)
                    abrechnungsjahr = str(abrechnungsjahr_state.state)
                    
                    if "/" in abrechnungsjahr:
                        start_year = int(abrechnungsjahr.split("/")[0])
                    else:
                        start_year = int(abrechnungsjahr[:4])
                    
                    abrechnungstag = self._config.get("ablesetermin_tag", 1)
                    abrechnungsmonat = self._config.get("ablesetermin_monat", 1)
                    
                    start_date = datetime(start_year, abrechnungsmonat, abrechnungstag)
                    today = datetime.now().date()
                    days_passed = (
                        datetime.combine(today, datetime.min.time()) - start_date
                    ).days + 1
                    
                    if days_passed > 0:
                        prognose = jahreskosten / days_passed * 365
                        self._state = round(prognose, 2)
                    else:
                        self._state = 0.0
                except (ValueError, TypeError, AttributeError):
                    self._state = 0.0
            else:
                self._state = 0.0
        else:
            self._state = 0.0


class HTNTModusSensor(BaseSensor):
    """HT/NT Modus sensor - current tariff mode."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "HT/NT Modus"
        self._attr_unique_id = f"{entry_id}_ht_nt_modus"
        self._attr_icon = "mdi:clock"

    async def async_update(self):
        """Update sensor."""
        if not self._config.get("ht_nt_enabled", False):
            self._state = "Deaktiviert"
        else:
            self._state = "HT" if self.is_ht_time() else "NT"


class HTEnergieSensor(BaseSensor):
    """HT Energie sensor - high tariff energy yearly."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahres HT Energie"
        self._attr_unique_id = f"{entry_id}_ht_energie"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:lightning-bolt"
        self._last_billing_year = None

    async def async_update(self):
        """Update sensor."""
        if not self._config.get("ht_nt_enabled", False):
            self._state = 0.0
            return

        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        if self._last_billing_year != current_year:
            yearly_data["ht_energy"] = 0.0
            self._last_billing_year = current_year
            await self.save_yearly_data()

        ht_energy = yearly_data.get("ht_energy", 0.0)
        self._state = round(ht_energy, 2)


class NTEnergieSensor(BaseSensor):
    """NT Energie sensor - low tariff energy yearly."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahres NT Energie"
        self._attr_unique_id = f"{entry_id}_nt_energie"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:lightning-bolt"
        self._last_billing_year = None

    async def async_update(self):
        """Update sensor."""
        if not self._config.get("ht_nt_enabled", False):
            self._state = 0.0
            return

        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        if self._last_billing_year != current_year:
            yearly_data["nt_energy"] = 0.0
            self._last_billing_year = current_year
            await self.save_yearly_data()

        nt_energy = yearly_data.get("nt_energy", 0.0)
        self._state = round(nt_energy, 2)


class JahresVerbrauchSensor(BaseSensor):
    """Jahresverbrauch sensor."""

    def __init__(self, hass, config, entry_id):
        """Initialize."""
        super().__init__(hass, config, entry_id)
        self._attr_name = "Jahresverbrauch"
        self._attr_unique_id = f"{entry_id}_jahresverbrauch"
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:counter"
        self._last_billing_year = None

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        if self._last_billing_year != current_year:
            yearly_data["energy_consumed"] = 0.0
            self._last_billing_year = current_year
            await self.save_yearly_data()
        
        netzbezug_entity = "sensor.netzbezug"
        state = self.hass.states.get(netzbezug_entity)
        
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(state.state)
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                yearly_data["energy_consumed"] = yearly_data.get("energy_consumed", 0.0) + kwh_increment
                await self.save_yearly_data()
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
        self._last_billing_year = None

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        if self._last_billing_year != current_year:
            yearly_data["solar_produced"] = 0.0
            self._last_billing_year = current_year
            await self.save_yearly_data()
        
        solar_entity = "sensor.solarertrag"
        state = self.hass.states.get(solar_entity)
        
        if state and state.state not in ["unknown", "unavailable"]:
            try:
                power_w = float(state.state)
                kwh_increment = (power_w / 1000.0) * (30.0 / 3600.0)
                yearly_data["solar_produced"] = yearly_data.get("solar_produced", 0.0) + kwh_increment
                await self.save_yearly_data()
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
        
        solar_kwh = yearly_data.get("solar_produced", 0.0)
        
        if self._config.get("ht_nt_enabled", False):
            ht_preis = float(self._config.get("ht_preis", 0.45))
            nt_preis = float(self._config.get("nt_preis", 0.25))
            avg_preis = (ht_preis + nt_preis) / 2
        else:
            avg_preis = float(self._config.get("kwh_preis", 0.35))
        
        savings = solar_kwh * avg_preis
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
        self._last_billing_year = None
        self._last_daily_value = 0.0
        self._last_update_day = None

    async def async_update(self):
        """Update sensor."""
        yearly_data = self.get_yearly_data()
        current_year = get_current_billing_year(self._config)
        
        if self._last_billing_year != current_year:
            yearly_data["einspeisung_yearly"] = 0.0
            self._last_billing_year = current_year
            self._last_daily_value = 0.0
            self._last_update_day = None
            await self.save_yearly_data()
        
        today = datetime.now().date()
        if self._last_update_day != today:
            einspeisung_state = self.hass.states.get("sensor.einspeisung_heute")
            if einspeisung_state and einspeisung_state.state not in ["unknown", "unavailable"]:
                try:
                    current_einspeisung = float(einspeisung_state.state)
                    if current_einspeisung >= self._last_daily_value:
                        increment = current_einspeisung - self._last_daily_value
                        yearly_data["einspeisung_yearly"] = yearly_data.get("einspeisung_yearly", 0.0) + increment
                        await self.save_yearly_data()
                    self._last_daily_value = 0.0
                except (ValueError, TypeError):
                    pass
            self._last_update_day = today
        
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
    """Aktuelles Abrechnungsjahr sensor."""

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
            self._attr_icon = "mdi:close-circle"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
            self._attr_icon = "mdi:alert-circle"
        else:
            self._state = "erreichbar"
            self._attr_icon = "mdi:check-circle"


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
            self._attr_icon = "mdi:close-circle"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
            self._attr_icon = "mdi:alert-circle"
        else:
            self._state = "erreichbar"
            self._attr_icon = "mdi:check-circle"


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
            self._attr_icon = "mdi:close-circle"
            return
        
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            self._state = "nicht erreichbar"
            self._attr_icon = "mdi:alert-circle"
        else:
            self._state = "erreichbar"
            self._attr_icon = "mdi:check-circle"
