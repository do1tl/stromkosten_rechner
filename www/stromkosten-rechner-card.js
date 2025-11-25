class StromkostenRechnerCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
    }

    const config = this.config;
    const hass = this._hass;

    const consumption_daily = hass.states[config.consumption_daily || "sensor.stromkosten_consumption_daily"];
    const consumption_monthly = hass.states[config.consumption_monthly || "sensor.stromkosten_consumption_monthly"];
    const consumption_yearly = hass.states[config.consumption_yearly || "sensor.stromkosten_consumption_yearly"];
    const consumption_yearly_prognosis = hass.states[config.consumption_yearly_prognosis || "sensor.stromkosten_consumption_yearly_prognosis"];
    
    const cost_daily = hass.states[config.cost_daily || "sensor.stromkosten_cost_daily"];
    const cost_monthly = hass.states[config.cost_monthly || "sensor.stromkosten_cost_monthly"];
    const cost_yearly = hass.states[config.cost_yearly || "sensor.stromkosten_cost_yearly"];
    const cost_yearly_prognosis = hass.states[config.cost_yearly_prognosis || "sensor.stromkosten_cost_yearly_prognosis"];
    
    const solar_yield_daily = hass.states[config.solar_yield_daily || "sensor.solar_yield_daily"];
    const solar_yield_monthly = hass.states[config.solar_yield_monthly || "sensor.solar_yield_monthly"];
    const solar_yield_yearly = hass.states[config.solar_yield_yearly || "sensor.solar_yield_yearly"];

    const getValue = (state) => state ? parseFloat(state.state) : 0;

    const html = `
      <style>
        :host {
          --primary-color: #2196f3;
          --secondary-color: #ff9800;
          --background-color: #f5f5f5;
          --card-background: #ffffff;
          --text-color: #333333;
          --border-color: #e0e0e0;
        }

        ha-card {
          background: var(--card-background);
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          padding: 16px;
        }

        .card-title {
          font-size: 24px;
          font-weight: bold;
          color: var(--text-color);
          margin-bottom: 20px;
          text-align: center;
        }

        .counter-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }

        .counter-box {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 8px;
          padding: 12px;
          color: white;
          text-align: center;
          border: 1px solid var(--border-color);
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .counter-box.consumption {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .counter-box.cost {
          background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        }

        .counter-box.solar {
          background: linear-gradient(135deg, #ffa500 0%, #ff6347 100%);
        }

        .counter-box.prognosis {
          background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
          opacity: 0.9;
        }

        .counter-label {
          font-size: 11px;
          opacity: 0.9;
          margin-bottom: 6px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 600;
        }

        .counter-value {
          font-size: 22px;
          font-weight: bold;
          margin-bottom: 2px;
        }

        .counter-unit {
          font-size: 10px;
          opacity: 0.8;
        }

        .row-label {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-color);
          margin-top: 14px;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .row-label:first-of-type {
          margin-top: 0;
        }

        .prognosis-info {
          background: #f5f5f5;
          border-left: 4px solid #9c27b0;
          padding: 10px;
          margin: 10px 0;
          border-radius: 4px;
          font-size: 12px;
          color: #333;
        }

        .info-text {
          margin: 4px 0;
        }
      </style>

      <ha-card>
        <div class="card-title">⚡ Stromzähler & Kosten</div>
        
        <div class="row-label">📊 Stromverbrauch & Kosten</div>
        <div class="counter-grid">
          <div class="counter-box consumption">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${getValue(consumption_daily).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${getValue(cost_daily).toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
          <div class="counter-box consumption">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${getValue(consumption_monthly).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${getValue(cost_monthly).toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
          <div class="counter-box consumption">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${getValue(consumption_yearly).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${getValue(cost_yearly).toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
        </div>

        <div class="prognosis-info">
          <div class="info-text"><strong>📈 Prognose:</strong></div>
          <div class="info-text">Verbrauch: <strong>${getValue(consumption_yearly_prognosis).toFixed(0)} kWh/Jahr</strong></div>
          <div class="info-text">Kosten: <strong>${getValue(cost_yearly_prognosis).toFixed(2)} €/Jahr</strong></div>
        </div>

        <div class="row-label">☀️ Solarertrag</div>
        <div class="counter-grid">
          <div class="counter-box solar">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${getValue(solar_yield_daily).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box solar">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${getValue(solar_yield_monthly).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box solar">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${getValue(solar_yield_yearly).toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.innerHTML = html;
  }

  getCardSize() {
    return 5;
  }
}

customElements.define('stromkosten-rechner-card', StromkostenRechnerCard);
