import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { CompatibleEntity, HomeAssistant } from "./types";
import { compatibleEntities } from "./api";

/**
 * Inline searchable entity combobox for the inspector. Collapsed it shows
 * the current selection (or a placeholder); expanded it shows a search
 * input over a scrollable result list. Emits `entity-selected` with the
 * full CompatibleEntity so the inspector gets unit/device_class without a
 * second lookup.
 */
@customElement("dash480-entity-select")
export class Dash480EntitySelect extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property() tileType = "entity";
  @property() value: string | undefined;
  // Shown when the current value isn't in the compatible list (e.g. a gauge
  // entity that stopped being numeric).
  @property() warning: string | undefined;

  @state() private _entities: CompatibleEntity[] = [];
  @state() private _open = false;
  @state() private _search = "";
  // Which tileType the current fetch was issued for — reload only when it
  // actually changes (hass is replaced on every HA state change, and an
  // empty result is a valid answer, not a reason to refetch).
  private _loadedType: string | null = null;

  protected willUpdate(changed: PropertyValues): void {
    void changed;
    if (this.hass && this.tileType !== this._loadedType) {
      const type = this.tileType;
      this._loadedType = type;
      compatibleEntities(this.hass, type).then((res) => {
        if (this._loadedType === type) this._entities = res.entities;
      });
    }
  }

  private _filtered(): CompatibleEntity[] {
    const q = this._search.trim().toLowerCase();
    if (!q) return this._entities;
    return this._entities.filter(
      (e) => e.friendly_name.toLowerCase().includes(q) || e.entity_id.toLowerCase().includes(q),
    );
  }

  private _pick(entity: CompatibleEntity) {
    this._open = false;
    this._search = "";
    this.dispatchEvent(new CustomEvent("entity-selected", { detail: { entity }, bubbles: true, composed: true }));
  }

  private _toggle() {
    this._open = !this._open;
    if (this._open) {
      this.updateComplete.then(() => {
        this.shadowRoot?.querySelector<HTMLInputElement>(".search")?.focus();
      });
    }
  }

  render() {
    const current = this.value ? this._entities.find((e) => e.entity_id === this.value) : undefined;
    const label = current?.friendly_name ?? this.value ?? "Choose an entity…";
    return html`
      <button class="current ${this.value ? "" : "placeholder"}" @click=${this._toggle}>
        <span class="name">${label}</span>
        ${this.value ? html`<span class="id">${this.value}</span>` : nothing}
        <span class="chevron">${this._open ? "▴" : "▾"}</span>
      </button>
      ${this.warning ? html`<div class="warning">⚠ ${this.warning}</div>` : nothing}
      ${this._open
        ? html`
            <div class="dropdown">
              <input
                class="search"
                placeholder="Search entities…"
                .value=${this._search}
                @input=${(e: InputEvent) => (this._search = (e.target as HTMLInputElement).value)}
              />
              <div class="list">
                ${this._filtered().length === 0
                  ? html`<div class="empty">No matching entities</div>`
                  : this._filtered().map(
                      (e) => html`
                        <button
                          class="row ${e.entity_id === this.value ? "selected" : ""}"
                          @click=${() => this._pick(e)}
                        >
                          <span class="name">${e.friendly_name}</span>
                          <span class="id">${e.entity_id}</span>
                        </button>
                      `,
                    )}
              </div>
            </div>
          `
        : nothing}
    `;
  }

  static styles = css`
    :host {
      display: block;
      position: relative;
    }
    .current {
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 2px;
      padding: 8px 10px;
      border: 1px solid #555;
      border-radius: 6px;
      background: transparent;
      color: inherit;
      cursor: pointer;
      text-align: left;
      position: relative;
    }
    .current:hover {
      border-color: #888;
    }
    .current.placeholder .name {
      opacity: 0.6;
    }
    .chevron {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0.6;
      font-size: 11px;
    }
    .name {
      font-size: 14px;
    }
    .id {
      font-size: 11px;
      opacity: 0.6;
    }
    .warning {
      margin-top: 4px;
      font-size: 12px;
      color: #fbbf24;
    }
    .dropdown {
      position: absolute;
      top: calc(100% + 4px);
      left: 0;
      right: 0;
      z-index: 10;
      background: var(--card-background-color, #1e1e1e);
      border: 1px solid #555;
      border-radius: 6px;
      padding: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
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
      max-height: 240px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .row {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      padding: 6px 8px;
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
    .row.selected {
      background: rgba(56, 189, 248, 0.15);
    }
    .empty {
      padding: 12px;
      text-align: center;
      opacity: 0.6;
      font-size: 13px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-entity-select": Dash480EntitySelect;
  }
}
