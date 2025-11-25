# Strom Zähler Integration für Home Assistant

Diese Custom Integration für Home Assistant bietet eine Stromzähler-ähnliche Anzeige mit:
- **Täglichem, monatlichem und jährlichem Stromverbrauch** (Shelly 3EM)
- **Solarertrag** (Hoymilies)
- **Custom Lovelace Karte** mit modernem Design

## Installation

### 1. Integration in Home Assistant installieren

**Option A: Manuell**

1. Navigiere zu deinem Home Assistant `config` Verzeichnis
2. Erstelle das Verzeichnis: `custom_components/stromkosten_rechner/`
3. Kopiere alle Python-Dateien (`__init__.py`, `config_flow.py`, `const.py`, `sensor.py`) dort hin
4. Kopiere `manifest.json` und `strings.json` auch dort hin
5. Starte Home Assistant neu

**Option B: HACS (nach Veröffentlichung)**

Noch nicht in HACS verfügbar - wird später hinzugefügt

### 2. Integration konfigurieren

1. Gehe zu **Settings** → **Devices & Services** → **Integrations**
2. Klicke auf **Create Integration** und suche nach **Strom Zähler**
3. Fülle folgende Felder aus:

   | Feld | Beispiel |
   |------|----------|
   | **Power Sensors** | `sensor.shellyem3_485519d9e23e_channel_a_power`<br>`sensor.shellyem3_485519d9e23e_channel_b_power`<br>`sensor.shellyem3_485519d9e23e_channel_c_power` |
   | **Solar Power** | `sensor.hoymiles_hm_400_ch1_power` |
   | **Solar Yield Day** | `sensor.hoymiles_hm_400_ch1_yieldday` |

4. Klicke **Create**

### 3. Custom Lovelace Card installieren

1. Gehe zu **Settings** → **Dashboards** → **Resources**
2. Klicke auf **Create new resource**
3. URL: `/local/stromkosten-rechner-card.js`
4. Resource type: `JavaScript Module`
5. Klicke **Create**

Alternativ kannst du die Datei `stromkosten-rechner-card.js` in dein `www` Verzeichnis kopieren:
```
config/www/stromkosten-rechner-card.js
```

### 4. Dashboard Card hinzufügen

1. Bearbeite dein Dashboard
2. Klicke **+ Add card** → **By entity**
3. Wähle eine beliebige Entity aus (die wird nicht verwendet, nur zum Laden nötig)
4. Wechsle zu **Code Editor** und ersetze den Code mit:

```yaml
type: custom:stromkosten-rechner-card
consumption_daily: sensor.stromkosten_consumption_daily
consumption_monthly: sensor.stromkosten_consumption_monthly
consumption_yearly: sensor.stromkosten_consumption_yearly
solar_yield_daily: sensor.solar_yield_daily
solar_yield_monthly: sensor.solar_yield_monthly
solar_yield_yearly: sensor.solar_yield_yearly
```

## Verfügbare Sensoren

Die Integration erstellt automatisch folgende Sensoren:

### Stromverbrauch
- `sensor.stromkosten_consumption_daily` - Tagesverbrauch (kWh)
- `sensor.stromkosten_consumption_monthly` - Monatsverbrauch (kWh)
- `sensor.stromkosten_consumption_yearly` - Jahresverbrauch (kWh)

### Solarertrag
- `sensor.solar_yield_daily` - Tagesertrag (kWh)
- `sensor.solar_yield_monthly` - Monatsertrag (kWh)
- `sensor.solar_yield_yearly` - Jahresertrag (kWh)

## Datenquellen

### Shelly 3EM Integration
Der Shelly 3EM wird in Home Assistant über die Native Integration verwaltet:
1. **Settings** → **Devices & Services** → **Integrations**
2. Klicke auf **Add Integration**
3. Suche nach **Shelly** und installiere
4. Gib die IP-Adresse deines Shelly 3EM ein
5. Die Sensoren werden automatisch erstellt

### Hoymilies MQTT
Der Hoymilies benötigt MQTT:
1. **Settings** → **Devices & Services** → **Integrations**
2. Installiere **MQTT** Integration
3. Konfiguriere MQTT Broker
4. Der Hoymilies sollte automatisch erkannt werden

## Anpassungen

### Power Sensors anpassen
Du kannst die Power Sensors in der Integrationskonfiguration jederzeit anpassen:
1. **Settings** → **Devices & Services** → **Strom Zähler**
2. Klicke auf die Integration
3. Klicke das Zahnrad (Options)
4. Passe die Sensor-Namen an

## Problembehebung

### Sensoren zeigen keine Werte
1. Prüfe, ob der Shelly 3EM in HA erkannt wird: **Settings** → **Devices**
2. Prüfe die Sensornamen: **Developer Tools** → **States**
3. Stelle sicher, dass Hoymilies mit MQTT verbunden ist

### Integration wird nicht geladen
1. Prüfe die Home Assistant Logs: **Settings** → **System** → **Logs**
2. Stelle sicher, dass alle Dateien im `custom_components/stromkosten_rechner/` Verzeichnis sind
3. Starte Home Assistant neu

### Dashboard zeigt keine Werte
1. Prüfe die Browser-Konsole (F12) auf JavaScript Fehler
2. Stelle sicher, dass die Custom Card Resource korrekt konfiguriert ist
3. Prüfe, dass die Sensor-Namen in der Card Config korrekt sind

## Lizenz

Diese Integration ist für persönlichen Gebrauch gedacht.
