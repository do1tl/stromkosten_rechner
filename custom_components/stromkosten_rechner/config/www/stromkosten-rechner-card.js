class StromkostenRechnerCard extends HTMLElement {
  setConfig(config) {
    if (!config.consumption_daily) {
      throw new Error("consumption_daily ist erforderlich");
    }
    this.config = config;
  }

  set hass(hass) {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    
    this._hass = hass;
    this._render();
  }

  _getState(entityId) {
    if (!this._hass || !entityId) return "0";
    const state = this._hass.states[entityId];
    if (!state) return "N/A";
    return state.state === "unavailable" ? "N/A" : parseFloat(state.state).toFixed(2);
  }

  _render() {
    if (!this._hass) return;

    const config = this.config;
    const consumption_daily = this._getState(config.consumption_daily);
    const consumption_monthly = this._getState(config.consumption_monthly);
    const consumption_yearly = this._getState(config.consumption_yearly);
    const cost_daily = this._getState(config.cost_daily);
    const cost_monthly = this._getState(config.cost_monthly);
    const cost_yearly = this._getState(config.cost_yearly);

    const html = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
        }
        .title {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 16px;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
          margin-bottom: 16px;
        }
        .box {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 12px;
          text-align: center;
          background: #f5f5f5;
        }
        .box-label {
          font-size: 12px;
          font-weight: bold;
          color: #666;
          margin-bottom: 8px;
        }
        .box-value {
          font-size: 20px;
          font-weight: bold;
          color: #333;
        }
        .box-unit {
          font-size: 11px;
          color: #999;
        }
      </style>

      <ha-card>
        <div class="title">⚡ Stromkosten</div>
        
        <div class="grid">
          <div class="box">
            <div class="box-label">Heute (Verbrauch)</div>
            <div class="box-value">${consumption_daily}</div>
            <div class="box-unit">kWh</div>
          </div>
          
          <div class="box">
            <div class="box-label">Heute (Kosten)</div>
            <div class="box-value">${cost_daily}</div>
            <div class="box-unit">€</div>
          </div>
          
          <div class="box">
            <div class="box-label">Monatlich (Verbrauch)</div>
            <div class="box-value">${consumption_monthly}</div>
            <div class="box-unit">kWh</div>
          </div>
          
          <div class="box">
            <div class="box-label">Monatlich (Kosten)</div>
            <div class="box-value">${cost_monthly}</div>
            <div class="box-unit">€</div>
          </div>
          
          <div class="box">
            <div class="box-label">Jährlich (Verbrauch)</div>
            <div class="box-value">${consumption_yearly}</div>
            <div class="box-unit">kWh</div>
          </div>
          
          <div class="box">
            <div class="box-label">Jährlich (Kosten)</div>
            <div class="box-value">${cost_yearly}</div>
            <div class="box-unit">€</div>
          </div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.innerHTML = html;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("stromkosten-rechner-card", StromkostenRechnerCard);
