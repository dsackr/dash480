import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";
import type { HomeAssistant, Panel, VisualPage } from "./types";
import { createPage, deletePage, generateFromArea, listPages, listPanels } from "./api";
import type { Dash480PageEditor } from "./page-editor";
import "./page-editor";
import "./area-picker";

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
  @state() private _newPageTitle = "";
  @state() private _areaPickerMode: "append" | "new_page" | null = null;
  @state() private _status = "";

  private _editorRef: Ref<Dash480PageEditor> = createRef();

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
    this._openEditor(page);
  }

  private _openEditor(page: VisualPage) {
    this._editingPage = page;
    this._view = "editor";
  }

  private _onEditorClosed() {
    this._view = "list";
    this._editingPage = null;
    this._loadPages();
  }

  private async _deletePage(page: VisualPage) {
    if (!window.confirm(`Delete page "${page.title}"? This can't be undone.`)) return;
    await deletePage(this.hass, page.id);
    await this._loadPages();
  }

  private _openAreaPicker(mode: "append" | "new_page") {
    this._areaPickerMode = mode;
  }

  private async _onAreaPicked(e: CustomEvent<{ area_id: string }>) {
    const mode = this._areaPickerMode;
    this._areaPickerMode = null;
    if (!mode || !this._panelId) return;
    const editor = this._editorRef.value;
    const targetPageId = mode === "append" ? this._editingPage?.id : undefined;
    if (mode === "append") {
      if (!targetPageId || !editor) return;
      // The backend appends to the *saved* page — flush pending auto-saves
      // first so they aren't clobbered when the editor reloads the page.
      const saved = await editor.prepareForAreaAppend();
      if (!saved) {
        this._status = "Couldn't save your pending edits — area append cancelled.";
        setTimeout(() => (this._status = ""), 4000);
        return;
      }
    }
    const result = await generateFromArea(this.hass, this._panelId, e.detail.area_id, mode, targetPageId);
    const skipped = result.skipped_entity_ids.length + result.skipped_incompatible_count;
    this._status = `Placed ${result.placed_count} entities${skipped ? `, ${skipped} skipped` : ""}`;
    setTimeout(() => (this._status = ""), 4000);
    if (mode === "append" && editor) {
      await editor.reloadAfterAreaAppend();
    } else {
      await this._loadPages();
    }
  }

  render() {
    if (!this.hass) return nothing;
    return html`
      <div class="wrap">
        ${this._view === "list" ? this._renderList() : this._renderEditor()}
      </div>
      ${this._areaPickerMode
        ? html`
            <dash480-area-picker
              .hass=${this.hass}
              @area-picked=${this._onAreaPicked}
              @picker-closed=${() => (this._areaPickerMode = null)}
            ></dash480-area-picker>
          `
        : nothing}
    `;
  }

  private _renderList() {
    return html`
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
                    <button @click=${() => this._deletePage(p)}>Delete</button>
                  </div>
                `,
              )}
            </div>
            <div class="new-page">
              <input
                placeholder="New page title"
                .value=${this._newPageTitle}
                @input=${(e: InputEvent) => (this._newPageTitle = (e.target as HTMLInputElement).value)}
                @keydown=${(e: KeyboardEvent) => e.key === "Enter" && this._createPage()}
              />
              <button @click=${this._createPage}>+ New Page</button>
              <button @click=${() => this._openAreaPicker("new_page")}>+ Generate Page from Area</button>
            </div>
            <span class="status">${this._status}</span>
          `}
    `;
  }

  private _renderEditor() {
    return html`
      <dash480-page-editor
        ${ref(this._editorRef)}
        .hass=${this.hass}
        .panelId=${this._panelId!}
        .initialPage=${this._editingPage!}
        @editor-closed=${this._onEditorClosed}
        @area-append-requested=${() => this._openAreaPicker("append")}
      ></dash480-page-editor>
      <span class="status">${this._status}</span>
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
      flex: 1;
    }
    .new-page {
      display: flex;
      gap: 8px;
    }
    .new-page input {
      padding: 8px 10px;
      font-size: 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
    }
    button {
      padding: 8px 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    button:hover {
      border-color: #888;
    }
    .status {
      opacity: 0.7;
      font-size: 12px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-panel": Dash480Panel;
  }
}
