# Stromkosten Rechner

Home Assistant Integration zur Berechnung von Stromkosten und Solar-Einsparungen mit **Jahresstatistiken**.

## Features

✅ **Tägliche Statistiken**
- Gesamtverbrauch aller 3 Phasen vom Shelly 3EM
- Täglicher Solar-Ertrag von bis zu 4 Hoymiles
- Tägliche Kosten und Einsparungen

✅ **Jahresstatistiken** (NEU!)
- Jahresverbrauch in kWh
- Jahres-Solarertrag in kWh
- Jahreskosten in EUR
- Jahres-Einsparungen in EUR

✅ **Flexibler Ablesetermin**
- Konfigurierbar (z.B. 1. Januar oder Stadtwerke-Termin)
- Automatischer Jahreswechsel am Ablesetermin
- Sensor zeigt aktuelles Abrechnungsjahr

✅ **Manueller Reset**
- Button zum Zurücksetzen der Jahreszähler
- Nützlich bei Umzug oder Zählerwechsel

## Installation via HACS

1. Füge dieses Repository zu HACS hinzu als Custom Repository
2. URL: `https://github.com/do1tl/stromkosten_rechner`
3. Kategorie: Integration
4. Installiere "Stromkosten Rechner"
5. Starte Home Assistant neu
6. Füge Integration hinzu: Einstellungen → Geräte & Dienste

## Konfiguration

Benötigte Angaben:
- **Shelly 3EM**: 3 Entity-IDs für die 3 Phasen (z.B. `sensor.shelly3em_channel_a_power`)
- **Hoymiles**: 1-4 Entity-IDs für täglichen Ertrag (z.B. `sensor.hoymiles_daily_energy`)
- **Strompreis**: Dein kWh-Preis in EUR (z.B. 0.35)
- **Ablesetermin**: Tag (1-31) und Monat (1-12) deines Ablesetages

## Sensoren

### Tägliche Sensoren
- `sensor.stromkosten_gesamtverbrauch` - Summe aller Phasen (W)
- `sensor.stromkosten_solarertrag` - Täglicher Solar-Ertrag (kWh)
- `sensor.stromkosten_netzbezug` - Strom vom Netz (W)
- `sensor.stromkosten_kosten_heute` - Kosten heute (EUR)
- `sensor.stromkosten_einsparungen_heute` - Einsparungen heute (EUR)

### Jahres-Sensoren (NEU!)
- `sensor.stromkosten_jahresverbrauch` - Verbrauch seit Ablesetermin (kWh)
- `sensor.stromkosten_jahres_solarertrag` - Solar-Ertrag seit Ablesetermin (kWh)
- `sensor.stromkosten_jahreskosten` - Kosten seit Ablesetermin (EUR)
- `sensor.stromkosten_jahres_einsparungen` - Einsparungen seit Ablesetermin (EUR)
- `sensor.stromkosten_abrechnungsjahr` - Zeigt aktuelles Abrechnungsjahr

### Button
- `button.stromkosten_jahreszahler_zurucksetzen` - Setzt alle Jahreszähler auf 0

## Beispiel Dashboard

```yaml
type: entities
title: Stromkosten Übersicht
entities:
  - entity: sensor.stromkosten_gesamtverbrauch
    name: Aktueller Verbrauch
  - entity: sensor.stromkosten_kosten_heute
    name: Kosten Heute
  - entity: sensor.stromkosten_einsparungen_heute
    name: Ersparnis Heute
  - type: divider
  - entity: sensor.stromkosten_abrechnungsjahr
    name: Abrechnungsjahr
  - entity: sensor.stromkosten_jahresverbrauch
    name: Jahresverbrauch
  - entity: sensor.stromkosten_jahres_solarertrag
    name: Jahres Solar-Ertrag
  - entity: sensor.stromkosten_jahreskosten
    name: Jahreskosten
  - entity: sensor.stromkosten_jahres_einsparungen
    name: Jahres-Einsparungen
  - type: divider
  - entity: button.stromkosten_jahreszahler_zurucksetzen
    name: Zähler Zurücksetzen
```

## Wie funktioniert der Ablesetermin?

Wenn du z.B. **1. März** als Ablesetermin einstellst:
- Vom 1. März 2024 bis 28. Februar 2025 = Abrechnungsjahr 2024/2025
- Am 1. März 2025 werden automatisch alle Jahreszähler zurückgesetzt
- Es beginnt das Abrechnungsjahr 2025/2026

## Support

[GitHub Issues](https://github.com/do1tl/stromkosten_rechner/issues)

## Changelog

### v1.1.0 (2024-11-23)
- ✨ Jahresstatistiken hinzugefügt
- ✨ Konfigurierbarer Ablesetermin
- ✨ Automatischer Jahreswechsel
- ✨ Reset-Button für Jahreszähler
- ✨ Sensor für aktuelles Abrechnungsjahr

### v1.0.2 (2024-11-23)
- 🐛 Config Flow Fixes
- 📝 Dokumentation verbessert

### v1.0.0 (2024-11-23)
- 🎉 Erste Version
