# Stromkosten Rechner

Home Assistant Integration zur Berechnung von Stromkosten und Solar-Einsparungen.

## Installation via HACS

1. Füge dieses Repository zu HACS hinzu als Custom Repository
2. URL: `https://github.com/do1tl/stromkosten_rechner`
3. Kategorie: Integration
4. Installiere "Stromkosten Rechner"
5. Starte Home Assistant neu
6. Füge Integration hinzu: Einstellungen → Geräte & Dienste

## Konfiguration

Benötigte Entity IDs:
- **Shelly 3EM**: 3 Sensoren für die 3 Phasen (z.B. `sensor.shelly3em_channel_a_power`)
- **Hoymiles**: 1-4 Sensoren für täglichen Ertrag (z.B. `sensor.hoymiles_daily_energy`)
- **Strompreis**: Dein kWh-Preis in EUR (z.B. 0.35)

## Sensoren

- `sensor.stromkosten_gesamtverbrauch` - Summe aller Phasen (W)
- `sensor.stromkosten_solarertrag` - Täglicher Solar-Ertrag (kWh)
- `sensor.stromkosten_netzbezug` - Strom vom Netz (W)
- `sensor.stromkosten_kosten_heute` - Kosten heute (EUR)
- `sensor.stromkosten_einsparungen_heute` - Einsparungen (EUR)

## Support

[GitHub Issues](https://github.com/do1tl/stromkosten_rechner/issues)
