# Stromkosten Rechner

Home Assistant Integration zur Berechnung von Stromkosten und Solar-Einsparungen mit **Jahresstatistiken**, **Grundgebühren**, **Einspeisevergütung**, **Autarkie-Berechnungen**, **HT/NT Tarifen** und **Prognosen**.

## Features (v2.1.1)

✅ **Tägliche Statistiken**
- Gesamtverbrauch aller 3 Phasen vom Shelly 3EM
- Täglicher Solar-Ertrag von bis zu 4 Hoymiles
- Tägliche Kosten und Einsparungen (HT/NT-fähig)

✅ **HT/NT Tarife (NEU in v2.1.1!)**
- 🔥 **Hochtarif und Niedrigtarif Support**
- ⏰ Konfigurierbare Zeitfenster (z.B. HT: 06:00-22:00)
- 💰 Automatische Preisberechnung je nach Tageszeit
- 📊 Separate Tracking von HT und NT Energie
- 🎯 Aktueller Tarifmodus-Sensor

✅ **Jahresstatistiken**
- Jahresverbrauch in kWh
- Jahres-Solarertrag in kWh
- Jahreskosten in EUR (inkl. HT/NT)
- Jahres-Einsparungen in EUR
- Jahreskosten inkl. Grundgebühr
- **Automatischer Jahres-Reset am Ablesetermin**

✅ **Grundgebühr**
- Monatliche Grundgebühr konfigurierbar
- Wird automatisch in Jahreskosten eingerechnet

✅ **Multi-Step Config Flow**
- Schritt 1: Sensoren konfigurieren
- Schritt 2: Strompreis & Grundgebühr
- Schritt 3: Abrechnungstermin
- Schritt 4: HT/NT Tarif (optional)
- Validierung aller Eingaben

✅ **Manueller Zählerstand**
- Input-Number für manuelle Korrektion
- Speicherung via Storage API
- Nützlich für Messfehler-Korrektur

✅ **Persistenz via Storage API**
- Automatisches Speichern aller Jahreswerte
- Daten bleiben auch nach HA-Neustart erhalten
- Keine manuellen Dateiänderungen nötig

✅ **Flexibler Ablesetermin**
- Konfigurierbar (z.B. 1. Januar oder Stadtwerke-Termin)
- **Automatischer Jahreswechsel am Ablesetermin**
- Sensor zeigt aktuelles Abrechnungsjahr

✅ **Manueller Reset**
- Button zum Zurücksetzen der Jahreszähler
- Nützlich bei Umzug oder Zählerwechsel
- Speichert sofort in Storage

✅ **Einspeisevergütung & Autarkie**
- 💸 Einspeisevergütung konfigurierbar
- 📊 Eigenverbrauch vs Solarertrag
- 📈 Autarkiegrad in % (wie unabhängig vom Netz?)
- 💰 Tägliche & Jahres-Einspeisung tracken
- ✨ Erlös aus Stromeinspeisung berechnen
- **Verbesserte Einspeise-Logik** (v2.1.1)

✅ **Spitzenlast & Prognosen**
- ⚡ Höchster Verbrauch heute & diese Woche
- 📉 Jahreskosten-Hochrechnung basierend auf aktuellem Durchschnitt
- 🔮 "Wenn du so weiter machst, kostet das Jahr X EUR"
- 📊 Prognose wird täglich aktualisiert

✅ **Monitoring & Verfügbarkeit**
- 🔍 Shelly-Verfügbarkeits-Sensoren (prüft Erreichbarkeit)
- 🎨 Pre-built Lovelace Dashboard Template

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
- **Grundgebühr**: Monatliche Grundgebühr in EUR (z.B. 12.50)
- **Einspeisevergütung**: Vergütung pro kWh in EUR (z.B. 0.08)
- **Ablesetermin**: Tag (1-31) und Monat (1-12) deines Ablesetages

Optional (Schritt 4):
- **HT/NT aktivieren**: Hochtarif und Niedrigtarif
- **HT Preis**: Hochtarif-Preis in EUR/kWh (z.B. 0.45)
- **NT Preis**: Niedrigtarif-Preis in EUR/kWh (z.B. 0.25)
- **HT Start**: Beginn Hochtarif (z.B. 06:00)
- **HT Ende**: Ende Hochtarif (z.B. 22:00)

## Sensoren

### Tägliche Sensoren
- `sensor.gesamtverbrauch` - Summe aller Phasen (W)
- `sensor.solarertrag` - Täglicher Solar-Ertrag (kWh)
- `sensor.netzbezug` - Strom vom Netz (W)
- `sensor.kosten_heute` - Kosten heute (EUR) **HT/NT-fähig**
- `sensor.einsparungen_heute` - Einsparungen heute (EUR)
- `sensor.grundgebuehr_monatlich` - Monatliche Grundgebühr (EUR)

### HT/NT Sensoren (NEU in v2.1.1!)
- `sensor.ht_nt_modus` - Aktueller Tarifmodus (HT/NT)
- `sensor.ht_energie` - HT Energie heute (kWh)
- `sensor.nt_energie` - NT Energie heute (kWh)

### Einspeisevergütung & Autarkie
- `sensor.eigenverbrauch` - Direkt genutzte Solarenergie (kWh)
- `sensor.autarkiegrad` - Unabhängigkeit vom Netz (%)
- `sensor.einspeisung_heute` - Überschuss ins Netz (kWh)
- `sensor.einspeise_erloes_heute` - Einnahmen aus Einspeisung (EUR)

### Spitzenlast & Prognosen
- `sensor.spitzenlast_heute` - Höchster Verbrauch heute (W)
- `sensor.spitzenlast_woche` - Höchster Verbrauch Woche (W)
- `sensor.prognose_jahreskosten` - Hochrechnung Jahreskosten (EUR)

### Monitoring
- `sensor.shelly_p1_verfuegbarkeit` - Shelly Phase 1 Verfügbarkeit
- `sensor.shelly_p2_verfuegbarkeit` - Shelly Phase 2 Verfügbarkeit
- `sensor.shelly_p3_verfuegbarkeit` - Shelly Phase 3 Verfügbarkeit

### Jahres-Sensoren
- `sensor.jahresverbrauch` - Verbrauch seit Ablesetermin (kWh)
- `sensor.jahres_solarertrag` - Solar-Ertrag seit Ablesetermin (kWh)
- `sensor.jahreskosten` - Kosten seit Ablesetermin (EUR)
- `sensor.jahres_einsparungen` - Einsparungen seit Ablesetermin (EUR)
- `sensor.jahreskosten_mit_grundgebuehr` - Jahreskosten inkl. Grundgebühr (EUR)
- `sensor.jahres_einspeisung` - Gesamteinspeisung im Jahr (kWh)
- `sensor.jahres_einspeise_erloes` - Einnahmen aus Einspeisung (EUR)
- `sensor.abrechnungsjahr` - Zeigt aktuelles Abrechnungsjahr

### Entitäten
- `number.manueller_zaehlerstand_anpassung` - Manuelle Korrektion (kWh)
- `button.jahreszahler_zurucksetzen` - Reset-Button

## Automatischer Jahres-Reset

**NEU in v2.1.1**: Der automatische Reset funktioniert jetzt korrekt!

Wenn du z.B. **1. März** als Ablesetermin einstellst:
- Vom 1. März 2024 bis 28. Februar 2025 = Abrechnungsjahr 2024/2025
- Am 1. März 2025 werden **automatisch** alle Jahreszähler zurückgesetzt
- Es beginnt das Abrechnungsjahr 2025/2026
- Die Prüfung erfolgt täglich beim Start und um 00:05 Uhr

## HT/NT Tarif Beispiel

Typische Konfiguration für Nachtstrom:
- **HT Start**: 06:00 (Hochtarif beginnt um 6 Uhr morgens)
- **HT Ende**: 22:00 (Hochtarif endet um 22 Uhr abends)
- **HT Preis**: 0.45 EUR/kWh
- **NT Preis**: 0.25 EUR/kWh

Die Integration wechselt automatisch zwischen den Tarifen und berechnet die Kosten entsprechend.

## Beispiel Dashboard

```yaml
type: entities
title: Stromkosten Übersicht
entities:
  - entity: sensor.stromkosten_gesamtverbrauch
    name: Aktueller Verbrauch
  - entity: sensor.stromkosten_ht_nt_modus
    name: Tarif-Modus
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
  - entity: sensor.stromkosten_jahreskosten_mit_grundgebuehr
    name: Jahreskosten (inkl. Grundgebühr)
  - entity: sensor.stromkosten_prognose_jahreskosten
    name: Prognose Jahreskosten
  - type: divider
  - entity: button.stromkosten_jahreszahler_zurucksetzen
    name: Zähler Zurücksetzen
```

## Support

[GitHub Issues](https://github.com/do1tl/stromkosten_rechner/issues)

## Changelog

### v2.1.1 (2024-11-24) - BUGFIX UPDATE
- 🐛 **FIX: HT/NT Tarife werden jetzt tatsächlich verwendet** in Kostenberechnung
- 🐛 **FIX: Automatischer Jahres-Reset funktioniert jetzt korrekt**
- 🐛 **FIX: Einspeisung-Berechnung verbessert** (Solar vs. Verbrauch)
- ✨ **NEU: Tägliche Prüfung auf Jahreswechsel** (00:05 Uhr + beim Start)
- ✨ **NEU: HT/NT Energie-Sensoren** (separate Tracking)
- 🔧 **IMPROVED: Storage wird nach jedem Update gespeichert**
- 🔧 **IMPROVED: Sensor-Dependencies** für Echtzeit-Updates
- 🔧 **IMPROVED: Error Handling** überall verbessert
- 🔧 **IMPROVED: Config Flow Validierung** (Datum & Zeit-Format)
- 🔧 **IMPROVED: Button & Number** speichern sofort in Storage
- 📚 **DOC: README komplett überarbeitet**

### v2.1.0 (2024-11-23) - PHASE 4 UPDATE
- ✨ Shelly-Verfügbarkeits-Sensoren
- ✨ HT/NT Tarif Konfiguration
- ✨ HT/NT Modus Sensor
- ✨ 4-Schritt Config Flow
- ✨ Lovelace Dashboard Template

### v2.0.0 (2024-11-23) - PHASE 2 & 3 UPDATE
- ✨ Einspeisevergütung & Autarkie
- ✨ Spitzenlast-Tracking
- ✨ Prognosen

### v1.2.0 (2024-11-23) - PHASE 1 UPDATE
- ✨ Persistenz via Storage API
- ✨ Grundgebühr Feature
- ✨ Multi-Step Config Flow
- ✨ Manueller Zählerstand

### v1.1.0 (2024-11-23)
- ✨ Jahresstatistiken
- ✨ Konfigurierbarer Ablesetermin
- ✨ Reset-Button

### v1.0.0 (2024-11-23)
- 🎉 Erste Version

## Migration von v2.1.0 auf v2.1.1

Keine Migration nötig! Einfach die neuen Dateien überschreiben und Home Assistant neu starten. Deine gespeicherten Daten bleiben erhalten.

**Wichtig**: Wenn du HT/NT aktiviert hast, werden die Preise ab jetzt automatisch verwendet. Prüfe deine Kosten-Sensoren nach dem Update!
