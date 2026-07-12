import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, Panel, VisualPage, PreviewTile } from "./types";
import {
  listPanels,
  listPages,
  createPage,
  updatePage,
  deletePage,
  publishPanel,
  renderPreview,
} from "./api";
import { cellRect, DEVICE_PX } from "./grid";
import "./entity-picker";

type View = "list" | "editor";

@customElement("dash480-panel")
export class Dash480Panel extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ type: Boolean }) narrow = false;

  @state() private _view: View = "list";
  @state() private _panels: Panel[] = [];
  @state() private _panelId: string | null = null;
  @state() private _pages: VisualPage[] = [];
  @state() private _reservedOrders: number[] = [];
  @state() private _editingPage: VisualPage | null = null;
  @state() private _previewTiles: PreviewTile[] = [];
  @state() private _newPageTitle = "";
  @state() private _pickerOpenFor: { row: number; col: number } | null = null;
  @state() private _status = "";

  connectedCallback(): void {
    super.connectedCallback();
    this._loadPanels();
  }

  private async _loadPanels() {
    const { panels } = await listPanels(this.hass);
    this._panels = panels;
    if (panels.length && !this._panelId) {
      this._panelId = panels[0].entry_id;
      await this._loadPages();
    }
  }

  private async _loadPages() {
    if (!this._panelId) return;
    const { pages, reserved_legacy_orders } = await listPages(this.hass, this._panelId);
    this._pages = pages;
    this._reservedOrders = reserved_legacy_orders;
  }

  private async _onPanelChange(e: Event) {
    this._panelId = (e.target as HTMLSelectElement).value;
    await this._loadPages();
  }

  private async _createPage() {
    if (!this._panelId || !this._newPageTitle.trim()) return;
    const { page } = await createPage(this.hass, this._panelId, this._newPageTitle.trim(), 3, 2);
    this._newPageTitle = "";
    await this._loadPages();
    await this._openEditor(page);
  }

  private async _openEditor(page: VisualPage) {
    this._editingPage = page;
    this._view = "editor";
    await this._refreshPreview();
  }

  private async _refreshPreview() {
    if (!this._editingPage) return;
    const { tiles } = await renderPreview(this.hass, this._editingPage);
    this._previewTiles = tiles;
  }

  private _backToList() {
    this._view = "list";
    this._editingPage = null;
    this._loadPages();
  }

  private async _deletePage(id: string) {
    await deletePage(this.hass, id);
    await this._loadPages();
  }

  private async _save() {
    if (!this._editingPage) return;
    const { title, columns, rows, tiles } = this._editingPage;
    await updatePage(this.hass, this._editingPage.id, { title, columns, rows, tiles });
    this._status = "Saved";
    setTimeout(() => (this._status = ""), 2000);
  }

  private async _publish() {
    if (!this._panelId) return;
    this._status = "Publishing…";
    await publishPanel(this.hass, this._panelId);
    this._status = "Published";
    setTimeout(() => (this._status = ""), 2000);
  }

  private _addTileAt(row: number, col: number) {
    this._pickerOpenFor = { row, col };
  }

  private async _onEntityPicked(e: CustomEvent<{ entity_id: string }>) {
    if (!this._editingPage || !this._pickerOpenFor) return;
    const { row, col } = this._pickerOpenFor;
    const tile = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      type: "entity" as const,
      entity_id: e.detail.entity_id,
      row,
      col,
      rs: 1,
      cs: 1,
    };
    this._editingPage = {
      ...this._editingPage,
      tiles: [
        ...this._editingPage.tiles.filter((t) => !(t.row === row && t.col === col)),
        tile,
      ],
    };
    this._pickerOpenFor = null;
    await this._refreshPreview();
  }

  private async _removeTile(tileId: string) {
    if (!this._editingPage) return;
    this._editingPage = {
      ...this._editingPage,
      tiles: this._editingPage.tiles.filter((t) => t.id !== tileId),
    };
    await this._refreshPreview();
  }

  render() {
    if (!this.hass) return nothing;
    return this._view === "list" ? this._renderList() : this._renderEditor();
  }

  private _renderList() {
    return html`
      <div class="wrap">
        <h1>Dash480</h1>
        ${this._panels.length > 1
          ? html`
              <select @change=${this._onPanelChange}>
                ${this._panels.map(
                  (p) =>
                    html`<option value=${p.entry_id} ?selected=${p.entry_id === this._panelId}>
                      ${p.title}
                    </option>`,
                )}
              </select>
            `
          : nothing}
        ${this._panels.length === 0
          ? html`<p>No Dash480 panels configured yet. Add one from Settings &gt; Devices &amp; Services.</p>`
          : html`
              <div class="pages">
                ${this._reservedOrders.map(
                  (o) =>
                    html`<div class="page-card reserved">Page ${o} — legacy (edit via Configure)</div>`,
                )}
                ${this._pages.map(
                  (p) => html`
                    <div class="page-card">
                      <div class="title" @click=${() => this._openEditor(p)}>
                        Page ${p.page_order}: ${p.title} (${p.tiles.length} tiles)
                      </div>
                      <button @click=${() => this._deletePage(p.id)}>Delete</button>
                    </div>
                  `,
                )}
              </div>
              <div class="new-page">
                <input
                  placeholder="New page title"
                  .value=${this._newPageTitle}
                  @input=${(e: InputEvent) => (this._newPageTitle = (e.target as HTMLInputElement).value)}
                />
                <button @click=${this._createPage}>+ New Page</button>
              </div>
            `}
      </div>
    `;
  }

  private _renderEditor() {
    const page = this._editingPage!;
    const cells: { row: number; col: number; rect: ReturnType<typeof cellRect> }[] = [];
    for (let row = 0; row < page.rows; row++) {
      for (let col = 0; col < page.columns; col++) {
        cells.push({ row, col, rect: cellRect(page.columns, page.rows, row, col) });
      }
    }
    return html`
      <div class="wrap editor">
        <div class="toolbar">
          <button @click=${this._backToList}>&lt; Back</button>
          <span class="page-title">${page.title}</span>
          <button @click=${this._save}>Save</button>
          <button @click=${this._publish}>Publish</button>
          <span class="status">${this._status}</span>
        </div>
        <div class="device" style="width:${DEVICE_PX}px;height:${DEVICE_PX}px;">
          ${cells.map(
            (c) => html`
              <div
                class="cell"
                style="left:${c.rect.x}px;top:${c.rect.y}px;width:${c.rect.w}px;height:${c.rect.h}px;"
                @click=${() => this._addTileAt(c.row, c.col)}
              ></div>
            `,
          )}
          ${this._previewTiles.map((t) => {
            const tile = page.tiles.find((pt) => pt.id === t.id);
            return html`
              <div class="tile" style="left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;">
                <div class="tile-label">${t.friendly_name}</div>
                <div class="tile-state">${t.state ?? "--"}</div>
                <button class="tile-remove" @click=${() => tile && this._removeTile(tile.id)}>×</button>
              </div>
            `;
          })}
        </div>
        <p class="hint">
          Click an empty cell to add an entity tile. Positions are approximate — verify on the real device.
        </p>
        ${this._pickerOpenFor
          ? html`
              <dash480-entity-picker
                .hass=${this.hass}
                tileType="entity"
                @entity-picked=${this._onEntityPicked}
                @picker-closed=${() => (this._pickerOpenFor = null)}
              ></dash480-entity-picker>
            `
          : nothing}
      </div>
    `;
  }

  static styles = css`
    :host {
      display: block;
      padding: 16px;
      color: var(--primary-text-color, #fff);
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .pages {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin: 16px 0;
    }
    .page-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      border-radius: 8px;
      background: var(--card-background-color, #1e1e1e);
    }
    .page-card.reserved {
      opacity: 0.5;
    }
    .title {
      cursor: pointer;
    }
    .new-page {
      display: flex;
      gap: 8px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .page-title {
      font-weight: bold;
      flex: 1;
    }
    .status {
      opacity: 0.7;
      font-size: 12px;
    }
    .device {
      position: relative;
      background: #0b1220;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #333;
    }
    .cell {
      position: absolute;
      border: 1px dashed rgba(255, 255, 255, 0.15);
      cursor: pointer;
      border-radius: 8px;
      box-sizing: border-box;
    }
    .cell:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    .tile {
      position: absolute;
      background: #1e293b;
      border-radius: 10px;
      color: #e5e7eb;
      padding: 6px;
      box-sizing: border-box;
      pointer-events: none;
    }
    .tile-label {
      font-size: 11px;
      opacity: 0.7;
    }
    .tile-state {
      font-size: 14px;
      margin-top: 4px;
    }
    .tile-remove {
      position: absolute;
      top: 2px;
      right: 2px;
      pointer-events: auto;
      background: transparent;
      border: none;
      color: #e5e7eb;
      cursor: pointer;
    }
    .hint {
      opacity: 0.6;
      font-size: 12px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-panel": Dash480Panel;
  }
}
