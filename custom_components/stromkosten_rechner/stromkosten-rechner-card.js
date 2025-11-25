class StromkostenRechnerCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    this._validateConfig();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _validateConfig() {
    const requiredFields = [
      'consumption_daily',
      'consumption_monthly',
      'consumption_yearly',
      'consumption_yearly_prognosis',
      'cost_daily',
      'cost_monthly',
      'cost_yearly',
      'cost_yearly_prognosis'
    ];

    const missing = requiredFields.filter(field => !this.config[field]);
    if (missing.length > 0) {
      console.warn(`Stromkosten Rechner Card: Fehlende Konfigurationen: ${missing.join(', ')}`);
    }
  }

  _getState(entityId) {
    if (!this._hass || !entityId) return 0;
    const state = this._hass.states[entityId];
    if (!state || state.state === 'unavailable' || state.state === 'unknown') return 0;
    const value = parseFloat(state.state);
    return isNaN(value) ? 0 : value;
  }

  _render() {
    if (!this._hass) return;
    
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
    }

    const config = this.config;
    const consumption_daily = this._getState(config.consumption_daily);
    const consumption_monthly = this._getState(config.consumption_monthly);
    const consumption_yearly = this._getState(config.consumption_yearly);
    const consumption_yearly_prognosis = this._getState(config.consumption_yearly_prognosis);
    
    const cost_daily = this._getState(config.cost_daily);
    const cost_monthly = this._getState(config.cost_monthly);
    const cost_yearly = this._getState(config.cost_yearly);
    const cost_yearly_prognosis = this._getState(config.cost_yearly_prognosis);
    
    const solar_yield_daily = this._getState(config.solar_yield_daily);
    const solar_yield_monthly = this._getState(config.solar_yield_monthly);
    const solar_yield_yearly = this._getState(config.solar_yield_yearly);

    const title = config.title || '⚡ Stromzähler & Kosten';
    const consumptionColor = config.consumption_color || '#667eea';
    const costColor = config.cost_color || '#4caf50';
    const solarColor = config.solar_color || '#ffa500';

    const html = `
      <style>
        :host {
          display: block;
          --consumption-color: ${consumptionColor};
          --cost-color: ${costColor};
          --solar-color: ${solarColor};
        }

        ha-card {
          background: #ffffff;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.12);
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        .card-title {
          font-size: 24px;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 24px;
          text-align: center;
          letter-spacing: -0.3px;
        }

        .row-label {
          font-size: 13px;
          font-weight: 700;
          color: #555;
          margin-top: 20px;
          margin-bottom: 12px;
          text-transform: uppercase;
          letter-spacing: 1px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .row-label:first-of-type {
          margin-top: 0;
        }

        .counter-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }

        .counter-box {
          border-radius: 10px;
          padding: 16px;
          color: white;
          text-align: center;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          transition: transform 0.2s ease, box-shadow 0.2s ease;
          cursor: default;
          user-select: none;
        }

        .counter-box:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        }

        .counter-box.consumption {
          background: linear-gradient(135deg, var(--consumption-color) 0%, ${consumptionColor}dd 100%);
        }

        .counter-box.cost {
          background: linear-gradient(135deg, var(--cost-color) 0%, ${costColor}dd 100%);
        }

        .counter-box.solar {
          background: linear-gradient(135deg, var(--solar-color) 0%, ${solarColor}dd 100%);
        }

        .counter-label {
          font-size: 12px;
          opacity: 0.95;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 600;
          line-height: 1.4;
        }

        .counter-value {
          font-size: 28px;
          font-weight: 700;
          margin-bottom: 4px;
          line-height: 1;
        }

        .counter-unit {
          font-size: 11px;
          opacity: 0.9;
          font-weight: 500;
        }

        .prognosis-info {
          background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
          border-left: 5px solid #9c27b0;
          padding: 14px;
          margin: 16px 0;
          border-radius: 8px;
          font-size: 13px;
          color: #333;
          box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }

        .info-text {
          margin: 6px 0;
          line-height: 1.5;
        }

        .info-text strong {
          font-weight: 700;
          color: #1a1a1a;
        }

        @media (max-width: 600px) {
          ha-card {
            padding: 16px;
          }

          .card-title {
            font-size: 20px;
            margin-bottom: 16px;
          }

          .counter-grid {
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
          }

          .counter-box {
            padding: 12px;
          }

          .counter-value {
            font-size: 24px;
          }
        }
      </style>

      <ha-card>
        <div class="card-title">${title}</div>
        
        <div class="row-label">📊 Stromverbrauch & Kosten</div>
        <div class="counter-grid">
          <div class="counter-box consumption">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${consumption_daily.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${cost_daily.toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
          <div class="counter-box consumption">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${consumption_monthly.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${cost_monthly.toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
          <div class="counter-box consumption">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${consumption_yearly.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box cost">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${cost_yearly.toFixed(2)}</div>
            <div class="counter-unit">€</div>
          </div>
        </div>

        <div class="prognosis-info">
          <div class="info-text"><strong>📈 Jahresprognose</strong></div>
          <div class="info-text">Verbrauch: <strong>${consumption_yearly_prognosis.toFixed(0)} kWh/Jahr</strong></div>
          <div class="info-text">Kosten: <strong>${cost_yearly_prognosis.toFixed(2)} €/Jahr</strong></div>
        </div>

        ${this.config.solar_yield_daily ? `
        <div class="row-label">☀️ Solarertrag</div>
        <div class="counter-grid">
          <div class="counter-box solar">
            <div class="counter-label">Heute</div>
            <div class="counter-value">${solar_yield_daily.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box solar">
            <div class="counter-label">Monatlich</div>
            <div class="counter-value">${solar_yield_monthly.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
          <div class="counter-box solar">
            <div class="counter-label">Jährlich</div>
            <div class="counter-value">${solar_yield_yearly.toFixed(2)}</div>
            <div class="counter-unit">kWh</div>
          </div>
        </div>
        ` : ''}
      </ha-card>
    `;

    this.shadowRoot.innerHTML = html;
  }

  getCardSize() {
    return this.config.solar_yield_daily ? 6 : 4;
  }
}

customElements.define('stromkosten-rechner-card', StromkostenRechnerCard);
