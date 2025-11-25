# ⚡ Stromkosten Rechner für Home Assistant

Umfassende Integration zur Überwachung von Stromverbrauch und -kosten mit moderner Lovelace Card.

## ✨ Features

- 📊 Stromverbrauch-Tracking (täglich, monatlich, jährlich)
- 💰 Automatische Kostenberechnung
- 🔮 Intelligente Jahresprognose
- ☀️ Solar-Integration (optional)
- 🎨 Moderne, animierte Lovelace Card

## 📦 Installation via HACS

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/do1tl/stromkosten_rechner`
3. Kategorie: Integration
4. Installieren & Home Assistant neu starten

## ⚙️ Konfiguration

1. Einstellungen → Geräte & Dienste → Integration hinzufügen
2. "Stromkosten Rechner" suchen
3. Sensoren konfigurieren (Shelly 3EM, Solar, etc.)

## 🎨 Dashboard Card

```yaml
type: custom:stromkosten-rechner-card
consumption_daily: sensor.stromkosten_consumption_daily
consumption_monthly: sensor.stromkosten_consumption_monthly
consumption_yearly: sensor.stromkosten_consumption_yearly
consumption_yearly_prognosis: sensor.stromkosten_consumption_yearly_prognosis
cost_daily: sensor.stromkosten_cost_daily
cost_monthly: sensor.stromkosten_cost_monthly
cost_yearly: sensor.stromkosten_cost_yearly
cost_yearly_prognosis: sensor.stromkosten_cost_yearly_prognosis
```

## 📊 Sensoren

- Verbrauch: täglich, monatlich, jährlich + Prognose
- Kosten: täglich, monatlich, jährlich + Prognose
- Solar: täglich, monatlich, jährlich (optional)

## 🔧 Kompatibilität

- Home Assistant 2024.1+
- Shelly 3EM
- Hoymiles Solar

## 📝 Lizenz

MIT License

## 🐛 Issues

https://github.com/do1tl/stromkosten_rechner/issues
