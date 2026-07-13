import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type {
  CompatibleEntity,
  HomeAssistant,
  IconChoice,
  Selection,
  TileType,
  VisualPage,
  VisualTile,
} from "./types";
import { compatibleEntities, listIcons } from "./api";
import { MAX_TILES_PER_PAGE, fitsAt, occupiedCells } from "./grid";
import "./entity-select";

// Sensible gauge min/max so a fresh gauge reads correctly without manual
// tuning — unit is the strongest hint, then device_class, then 0..100.
function gaugeDefaults(e: CompatibleEntity): { min: number; max: number } {
  switch (e.unit_of_measurement) {
    case "%":
      return { min: 0, max: 100 };
    case "°C":
      return { min: 0, max: 40 };
    case "°F":
      return { min: 32, max: 100 };
    case "W":
      return { min: 0, max: 1000 };
    case "kW":
      return { min: 0, max: 10 };
  }
  switch (e.device_class) {
    case "battery":
    case "humidity":
      return { min: 0, max: 100 };
    case "temperature":
      return { min: 0, max: 40 };
  }
  return { min: 0, max: 100 };
}

// "Power (E425)" → "Power" — the codepoint suffix helps nobody in a picker.
const iconLabel = (label: string) => label.replace(/\s*\([0-9A-F]+\)\s*$/i, "");

/**
 * Right-hand properties panel of the page editor. Three modes driven by
 * `selection`: page settings (nothing selected), add-tile form (empty cell
 * selected), tile properties (tile selected). All edits are emitted as
 * events — the page editor owns the draft and auto-saves.
 */
@customElement("dash480-inspector")
export class Dash480Inspector extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ attribute: false }) page!: VisualPage;
  @property({ attribute: false }) selection: Selection = { kind: "none" };

  @state() private _addType: TileType = "entity";
  @state() private _icons: IconChoice[] = [];
  // Entities compatible with the selected tile's type, to detect a current
  // entity that's no longer compatible (shown with a warning, not blanked).
  @state() private _compatible: CompatibleEntity[] | null = null;
  @state() private _shrinkError = "";
  @state() private _rangeError = "";
  @state() private _addError = "";
  // Discards out-of-order compatibleEntities responses (rapid selection or
  // type changes) so _compatible always matches the displayed tile's type.
  private _compatSeq = 0;

  connectedCallback(): void {
    super.connectedCallback();
    listIcons(this.hass).then((res) => (this._icons = res.icons));
  }

  protected willUpdate(changed: Map<string, unknown>): void {
    if (changed.has("selection")) {
      this._shrinkError = "";
      this._rangeError = "";
      this._addError = "";
      const tile = this._selectedTile();
      if (tile) {
        this._compatible = null;
        this._loadCompatible(tile.type);
      }
    }
  }

  private _loadCompatible(type: TileType) {
    const seq = ++this._compatSeq;
    compatibleEntities(this.hass, type).then((res) => {
      if (seq === this._compatSeq) this._compatible = res.entities;
    });
  }

  private _selectedTile(): VisualTile | undefined {
    if (this.selection.kind !== "tile") return undefined;
    const id = this.selection.tileId;
    return this.page.tiles.find((t) => t.id === id);
  }

  private _emit<T>(name: string, detail: T) {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
  }

  // ---------- Mode A: page settings ----------

  private _changeGrid(dim: "rows" | "columns", e: Event) {
    const select = e.target as HTMLSelectElement;
    const value = Number(select.value);
    const rows = dim === "rows" ? value : this.page.rows;
    const columns = dim === "columns" ? value : this.page.columns;
    const orphans = this.page.tiles.filter(
      (t) => t.row + (t.rs ?? 1) > rows || t.col + (t.cs ?? 1) > columns,
    );
    if (orphans.length) {
      const names = orphans.map((t) => t.entity_id ?? t.id).join(", ");
      this._shrinkError = `${orphans.length} tile${orphans.length > 1 ? "s" : ""} won't fit in a ${rows}×${columns} grid — move or remove first: ${names}`;
      select.value = String(this.page[dim]);
      return;
    }
    this._shrinkError = "";
    this._emit("page-changed", { [dim]: value });
  }

  private _renderPageSettings() {
    const p = this.page;
    return html`
      <h3>Page settings</h3>
      <label class="field">
        <span>Title</span>
        <input
          .value=${p.title}
          @change=${(e: Event) => this._emit("page-changed", { title: (e.target as HTMLInputElement).value })}
        />
      </label>
      <div class="row2">
        <label class="field">
          <span>Rows</span>
          <select @change=${(e: Event) => this._changeGrid("rows", e)}>
            ${[1, 2, 3, 4, 5, 6].map((n) => html`<option value=${n} ?selected=${n === p.rows}>${n}</option>`)}
          </select>
        </label>
        <label class="field">
          <span>Columns</span>
          <select @change=${(e: Event) => this._changeGrid("columns", e)}>
            ${[1, 2, 3, 4, 5, 6].map((n) => html`<option value=${n} ?selected=${n === p.columns}>${n}</option>`)}
          </select>
        </label>
      </div>
      ${this._shrinkError ? html`<div class="error">${this._shrinkError}</div>` : nothing}
      <div class="meta">${p.tiles.length} / ${MAX_TILES_PER_PAGE} tiles</div>
      <div class="hint">Click a tile to edit it, or an empty cell to add one. Drag tiles to move them.</div>
    `;
  }

  // ---------- Mode B: add tile ----------

  private _onAddEntityPicked(e: CustomEvent<{ entity: CompatibleEntity }>) {
    if (this.selection.kind !== "cell") return;
    const { row, col } = this.selection;
    // The cell may have been filled since it was selected (e.g. a tile was
    // dragged onto it while the add form sat open) — never create overlaps.
    if (!fitsAt(row, col, 1, 1, this.page.rows, this.page.columns, occupiedCells(this.page.tiles))) {
      this._addError = "That cell is now occupied — pick another cell.";
      return;
    }
    this._addError = "";
    const entity = e.detail.entity;
    const tile: VisualTile = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      type: this._addType,
      entity_id: entity.entity_id,
      row,
      col,
      rs: 1,
      cs: 1,
      ...(this._addType === "gauge" ? gaugeDefaults(entity) : {}),
    };
    this._emit("tile-added", { tile });
  }

  private _renderAddForm() {
    if (this.page.tiles.length >= MAX_TILES_PER_PAGE) {
      return html`
        <h3>Add tile</h3>
        <div class="error">Page is full (${MAX_TILES_PER_PAGE} tiles max). Remove a tile first.</div>
      `;
    }
    const sel = this.selection as { kind: "cell"; row: number; col: number };
    return html`
      <h3>Add tile</h3>
      <div class="meta">Row ${sel.row + 1}, column ${sel.col + 1}</div>
      ${this._renderTypeButtons(this._addType, (t) => (this._addType = t))}
      <label class="field">
        <span>Entity</span>
        <dash480-entity-select
          .hass=${this.hass}
          .tileType=${this._addType}
          @entity-selected=${this._onAddEntityPicked}
        ></dash480-entity-select>
      </label>
      ${this._addError ? html`<div class="error">${this._addError}</div>` : nothing}
      <div class="hint">The tile is added as soon as you pick an entity — you can adjust everything afterwards.</div>
    `;
  }

  private _renderTypeButtons(current: TileType, onPick: (t: TileType) => void) {
    const types: { value: TileType; label: string }[] = [
      { value: "entity", label: "Entity" },
      { value: "gauge", label: "Gauge" },
      { value: "weather", label: "Weather" },
    ];
    return html`
      <div class="segmented">
        ${types.map(
          (t) => html`
            <button class=${t.value === current ? "active" : ""} @click=${() => onPick(t.value)}>
              ${t.label}
            </button>
          `,
        )}
      </div>
    `;
  }

  // ---------- Mode C: edit tile ----------

  private _changeTileType(tile: VisualTile, newType: TileType) {
    if (newType === tile.type) return;
    // Apply the type change synchronously so rapid clicks commit in click
    // order and a concurrent move/resize can't be clobbered by a stale
    // snapshot when the fetch resolves.
    const updated: VisualTile = { ...tile, type: newType };
    delete updated.min;
    delete updated.max;
    delete updated.icon;
    this._emit("tile-changed", { tile: updated });
    // Then check the kept entity against the new type's compatible list; the
    // follow-up edit re-reads the tile's *current* state so it preserves any
    // edits made while the fetch was in flight.
    const seq = ++this._compatSeq;
    compatibleEntities(this.hass, newType).then((res) => {
      if (seq !== this._compatSeq) return;
      this._compatible = res.entities;
      const current = this.page.tiles.find((t) => t.id === tile.id);
      if (!current || current.type !== newType) return;
      const entity = current.entity_id
        ? res.entities.find((e) => e.entity_id === current.entity_id)
        : undefined;
      if (current.entity_id && !entity) {
        const cleared = { ...current };
        delete cleared.entity_id;
        this._emit("tile-changed", { tile: cleared });
      } else if (entity && newType === "gauge" && current.min === undefined && current.max === undefined) {
        this._emit("tile-changed", { tile: { ...current, ...gaugeDefaults(entity) } });
      }
    });
  }

  private _onEditEntityPicked(tile: VisualTile, e: CustomEvent<{ entity: CompatibleEntity }>) {
    const entity = e.detail.entity;
    const updated: VisualTile = { ...tile, entity_id: entity.entity_id };
    if (tile.type === "gauge" && tile.min === undefined && tile.max === undefined) {
      Object.assign(updated, gaugeDefaults(entity));
    }
    this._emit("tile-changed", { tile: updated });
  }

  private _changeRange(tile: VisualTile, field: "min" | "max", e: Event) {
    const input = e.target as HTMLInputElement;
    const value = Number(input.value);
    const revert = () => (input.value = String(tile[field] ?? (field === "min" ? 0 : 100)));
    if (!Number.isFinite(value)) {
      revert();
      return;
    }
    const min = field === "min" ? value : tile.min ?? 0;
    const max = field === "max" ? value : tile.max ?? 100;
    if (max <= min) {
      this._rangeError = "Max must be greater than min";
      revert();
      return;
    }
    this._rangeError = "";
    this._emit("tile-changed", { tile: { ...tile, min, max } });
  }

  private _changeSpan(tile: VisualTile, field: "rs" | "cs", delta: number) {
    const rs = (tile.rs ?? 1) + (field === "rs" ? delta : 0);
    const cs = (tile.cs ?? 1) + (field === "cs" ? delta : 0);
    if (rs < 1 || cs < 1) return;
    const occupied = occupiedCells(this.page.tiles, tile.id);
    if (!fitsAt(tile.row, tile.col, rs, cs, this.page.rows, this.page.columns, occupied)) return;
    this._emit("tile-changed", { tile: { ...tile, rs, cs } });
  }

  private _spanStepper(tile: VisualTile, field: "rs" | "cs", label: string, occupied: Set<string>) {
    const value = tile[field] ?? 1;
    const canGrow = fitsAt(
      tile.row,
      tile.col,
      field === "rs" ? value + 1 : tile.rs ?? 1,
      field === "cs" ? value + 1 : tile.cs ?? 1,
      this.page.rows,
      this.page.columns,
      occupied,
    );
    return html`
      <label class="field">
        <span>${label}</span>
        <div class="stepper">
          <button ?disabled=${value <= 1} @click=${() => this._changeSpan(tile, field, -1)}>−</button>
          <span class="stepper-value">${value}</span>
          <button
            ?disabled=${!canGrow}
            title=${canGrow ? "" : "No room to grow — blocked by the grid edge or another tile"}
            @click=${() => this._changeSpan(tile, field, 1)}
          >
            +
          </button>
        </div>
      </label>
    `;
  }

  private _renderTileEditor(tile: VisualTile) {
    const occupied = occupiedCells(this.page.tiles, tile.id);
    const entityCompatible =
      !tile.entity_id || this._compatible === null
        ? true
        : this._compatible.some((e) => e.entity_id === tile.entity_id);
    return html`
      <h3>Tile</h3>
      <label class="field">
        <span>Type</span>
        ${this._renderTypeButtons(tile.type, (t) => this._changeTileType(tile, t))}
      </label>
      <label class="field">
        <span>Entity</span>
        <dash480-entity-select
          .hass=${this.hass}
          .tileType=${tile.type}
          .value=${tile.entity_id}
          .warning=${entityCompatible
            ? undefined
            : tile.type === "gauge"
              ? "This entity isn't currently numeric — the gauge may not render."
              : "This entity isn't compatible with this tile type."}
          @entity-selected=${(e: CustomEvent<{ entity: CompatibleEntity }>) => this._onEditEntityPicked(tile, e)}
        ></dash480-entity-select>
      </label>
      ${!tile.entity_id
        ? html`<div class="error">No entity selected — this tile won't show on the device.</div>`
        : nothing}
      ${tile.type === "gauge"
        ? html`
            <div class="row2">
              <label class="field">
                <span>Min</span>
                <input
                  type="number"
                  .value=${String(tile.min ?? 0)}
                  @change=${(e: Event) => this._changeRange(tile, "min", e)}
                />
              </label>
              <label class="field">
                <span>Max</span>
                <input
                  type="number"
                  .value=${String(tile.max ?? 100)}
                  @change=${(e: Event) => this._changeRange(tile, "max", e)}
                />
              </label>
            </div>
            ${this._rangeError ? html`<div class="error">${this._rangeError}</div>` : nothing}
          `
        : nothing}
      ${tile.type === "entity"
        ? html`
            <label class="field">
              <span>Icon</span>
              <select
                @change=${(e: Event) => {
                  const code = (e.target as HTMLSelectElement).value;
                  const updated = { ...tile };
                  if (code) updated.icon = code;
                  else delete updated.icon;
                  this._emit("tile-changed", { tile: updated });
                }}
              >
                <option value="" ?selected=${!tile.icon}>Automatic</option>
                ${this._icons.map(
                  (i) => html`
                    <option value=${i.code} ?selected=${tile.icon === i.code}>${iconLabel(i.label)}</option>
                  `,
                )}
              </select>
            </label>
          `
        : nothing}
      <div class="row2">
        ${this._spanStepper(tile, "rs", "Height (rows)", occupied)}
        ${this._spanStepper(tile, "cs", "Width (columns)", occupied)}
      </div>
      <div class="meta">Row ${tile.row + 1}, column ${tile.col + 1} — drag the tile to move it.</div>
      <button class="remove" @click=${() => this._emit("tile-removed", { tileId: tile.id })}>Remove tile</button>
    `;
  }

  render() {
    if (!this.page) return nothing;
    let body;
    if (this.selection.kind === "tile") {
      const tile = this._selectedTile();
      body = tile ? this._renderTileEditor(tile) : this._renderPageSettings();
    } else if (this.selection.kind === "cell") {
      body = this._renderAddForm();
    } else {
      body = this._renderPageSettings();
    }
    return html`<div class="panel">${body}</div>`;
  }

  static styles = css`
    :host {
      display: block;
    }
    .panel {
      background: var(--card-background-color, #1e1e1e);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 200px;
    }
    h3 {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .field > span {
      font-size: 12px;
      opacity: 0.7;
    }
    input,
    select {
      padding: 8px 10px;
      font-size: 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
    }
    select option {
      background: var(--card-background-color, #1e1e1e);
    }
    .row2 {
      display: flex;
      gap: 12px;
    }
    .segmented {
      display: flex;
      border: 1px solid #555;
      border-radius: 6px;
      overflow: hidden;
    }
    .segmented button {
      flex: 1;
      padding: 8px 0;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    .segmented button + button {
      border-left: 1px solid #555;
    }
    .segmented button.active {
      background: var(--primary-color, #38bdf8);
      color: #0b1220;
      font-weight: 600;
    }
    .stepper {
      display: flex;
      align-items: center;
      gap: 4px;
      border: 1px solid #555;
      border-radius: 6px;
      overflow: hidden;
    }
    .stepper button {
      width: 34px;
      padding: 8px 0;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 16px;
    }
    .stepper button:disabled {
      opacity: 0.3;
      cursor: default;
    }
    .stepper-value {
      flex: 1;
      text-align: center;
      font-size: 14px;
    }
    .meta {
      font-size: 12px;
      opacity: 0.6;
    }
    .hint {
      font-size: 12px;
      opacity: 0.6;
      line-height: 1.4;
    }
    .error {
      font-size: 12px;
      color: #f87171;
      line-height: 1.4;
    }
    .remove {
      margin-top: 4px;
      padding: 10px;
      border-radius: 6px;
      border: 1px solid #7f1d1d;
      background: transparent;
      color: #f87171;
      cursor: pointer;
      font-size: 13px;
    }
    .remove:hover {
      background: rgba(248, 113, 113, 0.1);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-inspector": Dash480Inspector;
  }
}
