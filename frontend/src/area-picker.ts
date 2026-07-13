import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { Area, HomeAssistant } from "./types";
import { listAreas } from "./api";

@customElement("dash480-area-picker")
export class Dash480AreaPicker extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @state() private _areas: Area[] = [];
  @state() private _search = "";

  connectedCallback(): void {
    super.connectedCallback();
    listAreas(this.hass).then((res) => {
      this._areas = res.areas;
    });
  }

  private _filtered(): Area[] {
    const q = this._search.trim().toLowerCase();
    if (!q) return this._areas;
    return this._areas.filter((a) => a.name.toLowerCase().includes(q));
  }

  private _pick(areaId: string) {
    this.dispatchEvent(new CustomEvent("area-picked", { detail: { area_id: areaId } }));
  }

  private _cancel() {
    this.dispatchEvent(new CustomEvent("picker-closed"));
  }

  render() {
    const filtered = this._filtered();
    return html`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(e: Event) => e.stopPropagation()}>
          <input
            class="search"
            placeholder="Search areas…"
            .value=${this._search}
            @input=${(e: InputEvent) => (this._search = (e.target as HTMLInputElement).value)}
          />
          <div class="list">
            ${filtered.length === 0
              ? html`<div class="empty">No matching areas</div>`
              : filtered.map(
                  (a) => html`
                    <button class="row" @click=${() => this._pick(a.area_id)}>
                      <span class="name">${a.name}</span>
                      <span class="counts">${a.entity_count} entities · ${a.device_count} devices</span>
                    </button>
                  `,
                )}
          </div>
          <button class="cancel" @click=${this._cancel}>Cancel</button>
        </div>
      </div>
    `;
  }

  static styles = css`
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .dialog {
      background: var(--card-background-color, #1e1e1e);
      color: var(--primary-text-color, #fff);
      border-radius: 8px;
      padding: 16px;
      width: min(420px, 90vw);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .search {
      padding: 8px;
      font-size: 14px;
      border-radius: 4px;
      border: 1px solid #666;
      background: transparent;
      color: inherit;
    }
    .list {
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .row {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      padding: 8px;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      border-radius: 4px;
      text-align: left;
    }
    .row:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    .name {
      font-size: 14px;
    }
    .counts {
      font-size: 11px;
      opacity: 0.6;
    }
    .empty {
      padding: 16px;
      text-align: center;
      opacity: 0.6;
    }
    .cancel {
      align-self: flex-end;
      padding: 6px 12px;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-area-picker": Dash480AreaPicker;
  }
}
