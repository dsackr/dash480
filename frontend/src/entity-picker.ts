import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { CompatibleEntity, HomeAssistant } from "./types";
import { compatibleEntities } from "./api";

@customElement("dash480-entity-picker")
export class Dash480EntityPicker extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property() tileType = "entity";

  @state() private _entities: CompatibleEntity[] = [];
  @state() private _search = "";

  connectedCallback(): void {
    super.connectedCallback();
    compatibleEntities(this.hass, this.tileType).then((res) => {
      this._entities = res.entities;
    });
  }

  private _filtered(): CompatibleEntity[] {
    const q = this._search.trim().toLowerCase();
    if (!q) return this._entities;
    return this._entities.filter(
      (e) => e.friendly_name.toLowerCase().includes(q) || e.entity_id.toLowerCase().includes(q),
    );
  }

  private _pick(entityId: string) {
    this.dispatchEvent(new CustomEvent("entity-picked", { detail: { entity_id: entityId } }));
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
            placeholder="Search entities…"
            .value=${this._search}
            @input=${(e: InputEvent) => (this._search = (e.target as HTMLInputElement).value)}
          />
          <div class="list">
            ${filtered.length === 0
              ? html`<div class="empty">No matching entities</div>`
              : filtered.map(
                  (e) => html`
                    <button class="row" @click=${() => this._pick(e.entity_id)}>
                      <span class="name">${e.friendly_name}</span>
                      <span class="id">${e.entity_id}</span>
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
    .id {
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
    "dash480-entity-picker": Dash480EntityPicker;
  }
}
