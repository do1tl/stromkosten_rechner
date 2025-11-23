# Stromkosten Rechner

Home Assistant Integration zur Berechnung von Stromkosten und Solar-Einsparungen mit **Jahresstatistiken**, **Grundgebühren**, **Einspeisevergütung**, **Autarkie-Berechnungen** und **Prognosen**.

## Features (v2.1.0)

✅ **Tägliche Statistiken**
- Gesamtverbrauch aller 3 Phasen vom Shelly 3EM
- Täglicher Solar-Ertrag von bis zu 4 Hoymiles
- Tägliche Kosten und Einsparungen

✅ **Jahresstatistiken**
- Jahresverbrauch in kWh
- Jahres-Solarertrag in kWh
- Jahreskosten in EUR
- Jahres-Einsparungen in EUR
- Jahreskosten inkl. Grundgebühr

✅ **Grundgebühr (Phase 1)**
- Monatliche Grundgebühr konfigurierbar
- Wird automatisch in Jahreskosten eingerechnet
- Im Setup als Schritt 2 konfigurierbar

✅ **Multi-Step Config Flow (Phase 1)**
- Schritt 1: Sensoren konfigurieren
- Schritt 2: Strompreis & Grundgebühr
- Schritt 3: Abrechnungstermin
- Schritt 4: HT/NT Tarif (neu!)
- Benutzerfreundliche Wizard-Integration

✅ **Manueller Zählerstand (Phase 1)**
- Input-Number für manuelle Korrektion
- Speicherung via Storage API
- Nützlich für Messfehler-Korrektur

✅ **Persistenz via Storage API (Phase 1)**
- Automatisches Speichern aller Jahreswerte
- Daten bleiben auch nach HA-Neustart erhalten
- Keine manuellen Dateiveränderungen nötig

✅ **Flexibler Ablesetermin (Phase 1)**
- Konfigurierbar (z.B. 1. Januar oder Stadtwerke-Termin)
- Automatischer Jahreswechsel am Ablesetermin
- Sensor zeigt aktuelles Abrechnungsjahr

✅ **Manueller Reset (Phase 1)**
- Button zum Zurücksetzen der Jahreszähler
- Nützlich bei Umzug oder Zählerwechsel

✅ **PHASE 2: Einspeisevergütung & Autarkie**
- 💸 Einspeisevergütung konfigurierbar
- 📊 Eigenverbrauch vs Solarertrag
- 📈 Autarkiegrad in % (wie unabhängig vom Netz?)
- 💰 Tägliche & Jahres-Einspeisung tracken
- ✨ Erlös aus Stromeinspeisung berechnen

✅ **PHASE 3: Spitzenlast & Prognosen**
- ⚡ Höchster Verbrauch heute & diese Woche
- 📉 Jahreskosten-Hochrechnung basierend auf aktuellem Durchschnitt
- 🔮 "Wenn du so weiter machst, kostet das Jahr X EUR"
- 📊 Prognose wird täglich aktualisiert

✅ **PHASE 4: Monitoring & Tarife (NEU!)**
- 🔍 Shelly-Verfügbarkeits-Sensoren (prüft Erreichbarkeit)
- ⏰ HT/NT Tarif Support (Hochtarif / Niedrigtarif)
- ⏱️ Konfigurierbare Zeitfenster für HT und NT
- 📊 Sensor zeigt aktuellen Tarifmodus
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
- **Ablesetermin**: Tag (1-31) und Monat (1-12) deines Ablesetages

## Sensoren

### Tägliche Sensoren
- `sensor.stromkosten_gesamtverbrauch` - Summe aller Phasen (W)
- `sensor.stromkosten_solarertrag` - Täglicher Solar-Ertrag (kWh)
- `sensor.stromkosten_netzbezug` - Strom vom Netz (W)
- `sensor.stromkosten_kosten_heute` - Kosten heute (EUR)
- `sensor.stromkosten_einsparungen_heute` - Einsparungen heute (EUR)
- `sensor.stromkosten_grundgebuehr_monatlich` - Monatliche Grundgebühr (EUR)

### Phase 2: Einspeisevergütung & Autarkie
- `sensor.stromkosten_eigenverbrauch` - Direkt genutzte Solarenergie (kWh)
- `sensor.stromkosten_autarkiegrad` - Unabhängigkeit vom Netz (%)
- `sensor.stromkosten_einspeisung_heute` - Überschuss ins Netz (kWh)
- `sensor.stromkosten_einspeise_erloes_heute` - Einnahmen aus Einspeisung (EUR)

### Phase 3: Spitzenlast & Prognosen
- `sensor.stromkosten_spitzenlast_heute` - Höchster Verbrauch heute (W)
- `sensor.stromkosten_spitzenlast_woche` - Höchster Verbrauch Woche (W)
- `sensor.stromkosten_prognose_jahreskosten` - Hochrechnung Jahreskosten (EUR)

### Phase 4: Monitoring & Tarife
- `sensor.stromkosten_shelly_p1_verfuegbarkeit` - Shelly Phase 1 Verfügbarkeit
- `sensor.stromkosten_shelly_p2_verfuegbarkeit` - Shelly Phase 2 Verfügbarkeit
- `sensor.stromkosten_shelly_p3_verfuegbarkeit` - Shelly Phase 3 Verfügbarkeit
- `sensor.stromkosten_ht_nt_modus` - Aktueller Tarifmodus (HT/NT)

### Jahres-Sensoren
- `sensor.stromkosten_jahresverbrauch` - Verbrauch seit Ablesetermin (kWh)
- `sensor.stromkosten_jahres_solarertrag` - Solar-Ertrag seit Ablesetermin (kWh)
- `sensor.stromkosten_jahreskosten` - Kosten seit Ablesetermin (EUR)
- `sensor.stromkosten_jahres_einsparungen` - Einsparungen seit Ablesetermin (EUR)
- `sensor.stromkosten_jahreskosten_mit_grundgebuehr` - Jahreskosten inkl. Grundgebühr (EUR)
- `sensor.stromkosten_jahres_einspeisung` - Gesamteinspeisung im Jahr (kWh)
- `sensor.stromkosten_jahres_einspeise_erloes` - Einnahmen aus Einspeisung (EUR)
- `sensor.stromkosten_abrechnungsjahr` - Zeigt aktuelles Abrechnungsjahr

### Input-Number
- `number.stromkosten_manueller_zaehlerstand_anpassung` - Manuelle Korrektion des Zählerstandes (kWh)

### Button
- `button.stromkosten_jahreszahler_zurucksetzen` - Setzt alle Jahreszähler auf 0 und speichert

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

### v2.1.0 (2024-11-23) - PHASE 4 UPDATE: Monitoring & Tarife
- ✨ **Shelly-Verfügbarkeits-Sensoren** - Prüft Erreichbarkeit jeder Phase
- ✨ **HT/NT Tarif Support** - Hochtarif und Niedrigtarif Konfiguration
- ✨ **HT/NT Modus Sensor** - Zeigt aktuellen Tarifmodus an
- ✨ **Konfigurierbare HT-Zeitfenster** - HT Start und Ende Uhrzeit
- ✨ **Lovelace Dashboard Template** - Pre-built Dashboard mit allen Sensoren
- ✨ **4-Schritt Config Flow** - Neuer Schritt für HT/NT Einstellungen
- 📝 README und Dokumentation aktualisiert

### v2.0.0 (2024-11-23) - PHASE 2 & 3 UPDATE
- ✨ **PHASE 2: Einspeisevergütung** - Stromerlös tracken
- ✨ **PHASE 2: Autarkiegrad** - % Unabhängigkeit vom Netz
- ✨ **PHASE 2: Eigenverbrauch** - Eigennutzung vs Einspeisung
- ✨ **PHASE 2: Jahres-Einspeisung** - Gesamteinspeisung im Jahr
- ✨ **PHASE 3: Spitzenlast-Tracking** - Höchstverbrauch heute/Woche
- ✨ **PHASE 3: Prognosen** - Jahreskosten-Hochrechnung
- ✨ **PHASE 3: Einspeise-Erlös** - Einnahmen berechnen
- 📝 README mit allen Features aktualisiert

### v1.2.0 (2024-11-23) - PHASE 1 UPDATE
- ✨ **Persistenz via Storage API** - Alle Daten persistent speichern
- ✨ **Grundgebühr Feature** - Monatliche Grundgebühr konfigurierbar
- ✨ **Multi-Step Config Flow** - 3-Schritt Konfigurationswizard
- ✨ **Manueller Zählerstand** - Input-Number für Korrektion
- ✨ **Jahreskosten mit Grundgebühr** - Neuer Sensor
- 🐛 Button speichert nun auch in Storage API
- 📝 Dokumentation aktualisiert

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
