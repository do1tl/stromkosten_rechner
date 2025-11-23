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
   - **Shelly 3EM Phase 1, 2, 3**: Die Entity-IDs deiner Shelly Phasen
   - **Hoymiles 1-4**: Die Entity-IDs deiner Hoymiles (täglicher Ertrag in kWh)
   - **kWh Preis**: Dein Strompreis in EUR (z.B. 0.35)

## Sensoren

Die Integration erstellt folgende Sensoren:

- `sensor.stromkosten_gesamtverbrauch` - Summe aller Shelly-Phasen (W)
- `sensor.stromkosten_solarertrag` - Summe aller Hoymiles (kWh)
- `sensor.stromkosten_netzbezug` - Strom vom Netz (W)
- `sensor.stromkosten_tagliche_kosten` - Kosten heute (EUR)
- `sensor.stromkosten_einsparungen` - Einsparungen heute (EUR)

## Beispiel Dashboard

```yaml
type: entities
title: Stromkosten
entities:
  - entity: sensor.stromkosten_gesamtverbrauch
    name: Gesamtverbrauch
  - entity: sensor.stromkosten_solarertrag
    name: Solar Ertrag heute
  - entity: sensor.stromkosten_tagliche_kosten
    name: Kosten heute
  - entity: sensor.stromkosten_einsparungen
    name: Ersparnis heute
```

## Support

Bei Problemen oder Fragen bitte ein Issue auf GitHub erstellen.

## Lizenz

MIT License
