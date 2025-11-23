# Stromkosten Rechner

Eine Home Assistant Custom Integration zur Berechnung von Stromkosten und Einsparungen durch Solar.

## Features

✅ Addiert alle 3 Phasen des Shelly 3EM  
✅ Unterstützt bis zu 4 Hoymiles Wechselrichter  
✅ Berechnet tägliche Kosten vom Netz  
✅ Berechnet Einsparungen durch Solar  
✅ Automatische Reset um Mitternacht  
✅ Konfigurierbar über UI

## Installation

### HACS (empfohlen)

1. Öffne HACS
2. Gehe zu "Integrationen"
3. Klicke auf die drei Punkte oben rechts
4. "Benutzerdefinierte Repositories"
5. Füge die URL dieses Repos hinzu
6. Kategorie: Integration
7. Klicke "Hinzufügen"
8. Suche nach "Stromkosten Rechner" und installiere es
9. Starte Home Assistant neu

### Manuell

1. Lade das `custom_components/stromkosten_rechner` Verzeichnis herunter
2. Kopiere es in dein Home Assistant `custom_components` Verzeichnis
3. Starte Home Assistant neu

## Konfiguration

1. Gehe zu Einstellungen → Geräte & Dienste
2. Klicke auf "Integration hinzufügen"
3. Suche nach "Stromkosten Rechner"
4. Gib folgende Daten ein:
   - **Shelly 3EM Phase 1, 2, 3**: Die Entity-IDs deiner Shelly Phasen (z.B. `sensor.shelly_power_1`)
   - **Hoymiles 1-4**: Die Entity-IDs deiner Hoymiles (täglicher Ertrag in kWh)
   - **kWh Preis**: Dein Strompreis in EUR (z.B. 0.35)

## Sensoren

Die Integration erstellt folgende Sensoren:

- `sensor.gesamtverbrauch` - Summe aller Shelly-Phasen (W)
- `sensor.solarertrag_heute` - Summe aller Hoymiles (kWh)
- `sensor.netzbezug_aktuell` - Strom vom Netz (W)
- `sensor.stromkosten_heute` - Kosten heute (EUR)
- `sensor.einsparungen_heute` - Einsparungen heute (EUR)

## Beispiel Dashboard

```yaml
type: entities
title: Stromkosten
entities:
  - entity: sensor.gesamtverbrauch
    name: Gesamtverbrauch
  - entity: sensor.solarertrag_heute
    name: Solar Ertrag heute
  - entity: sensor.stromkosten_heute
    name: Kosten heute
  - entity: sensor.einsparungen_heute
    name: Ersparnis heute
```

## Support

Bei Problemen oder Fragen bitte ein Issue auf GitHub erstellen.

## Lizenz

MIT License
