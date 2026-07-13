import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, PreviewTile, Selection, VisualPage, VisualTile } from "./types";
import { listPages, publishPanel, renderPreview, updatePage } from "./api";
import { DEVICE_PX } from "./grid";
import "./preview-canvas";
import "./inspector";

type SaveState = "idle" | "saving" | "saved" | "error";

/**
 * Debounced, single-flight auto-saver. At most one updatePage request is in
 * flight; edits arriving mid-flight replace the pending draft and are saved
 * next, so saves are serialized and each sends the complete latest draft —
 * stale-response clobbering is impossible by construction. The server's
 * returned page is intentionally never written back into the editor draft.
 */
class SaveController {
  private _timer: number | undefined;
  private _pending: VisualPage | null = null;
  private _inFlight: Promise<void> | null = null;
  private _retried = false;

  constructor(
    private _save: (draft: VisualPage) => Promise<unknown>,
    private _onStatus: (s: SaveState) => void,
  ) {}

  schedule(draft: VisualPage): void {
    this._pending = draft;
    this._retried = false; // each new edit gets a fresh auto-retry budget
    clearTimeout(this._timer);
    this._timer = window.setTimeout(() => this._run(), 800);
  }

  // Save any pending draft now. Returns true when everything is persisted;
  // false when the save failed — callers must NOT act on the store (publish,
  // area-append) in that case, since it doesn't reflect the draft.
  async flush(): Promise<boolean> {
    clearTimeout(this._timer);
    while (this._inFlight) await this._inFlight;
    if (this._pending) await this._run();
    return this._pending === null;
  }

  // Drop any pending draft — for when the draft is about to be replaced
  // wholesale (area-append reload), so a scheduled retry can't resurrect
  // the superseded page and overwrite the reloaded one.
  discard(): void {
    clearTimeout(this._timer);
    this._pending = null;
  }

  private async _run(): Promise<void> {
    if (this._inFlight || !this._pending) return;
    const draft = this._pending;
    this._pending = null;
    this._onStatus("saving");
    const attempt = Promise.resolve().then(() => this._save(draft));
    this._inFlight = attempt.then(
      () => undefined,
      () => undefined,
    );
    let ok = false;
    try {
      await attempt;
      ok = true;
    } catch {
      // Keep the draft so nothing is lost — unless a newer edit arrived
      // while this one was in flight, which supersedes it anyway.
      if (this._pending === null) this._pending = draft;
    }
    this._inFlight = null;
    if (ok) {
      if (this._pending) return this._run(); // a newer draft arrived mid-flight
      this._onStatus("saved");
      return;
    }
    if (!this._retried) {
      this._retried = true;
      this._timer = window.setTimeout(() => this._run(), 2000);
    } else {
      this._onStatus("error");
    }
  }
}

/**
 * The page editor: owns the draft page, selection, auto-save and publish
 * state. The canvas and inspector are pure views over the draft — every
 * mutation funnels through _applyDraft, which refreshes the preview and
 * schedules a save.
 */
@customElement("dash480-page-editor")
export class Dash480PageEditor extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property({ attribute: false }) panelId!: string;
  @property({ attribute: false }) initialPage!: VisualPage;

  @state() private _draft!: VisualPage;
  @state() private _selection: Selection = { kind: "none" };
  @state() private _previewTiles: PreviewTile[] = [];
  @state() private _saveState: SaveState = "idle";
  @state() private _publishDirty = false;
  @state() private _publishing = false;
  @state() private _status = "";

  private _saver = new SaveController(
    (draft) => updatePage(this.hass, draft.id, {
      title: draft.title,
      columns: draft.columns,
      rows: draft.rows,
      tiles: draft.tiles,
    }),
    (s) => {
      this._saveState = s;
      if (s === "saved") {
        setTimeout(() => {
          if (this._saveState === "saved") this._saveState = "idle";
        }, 2000);
      }
    },
  );
  private _previewSeq = 0;

  connectedCallback(): void {
    super.connectedCallback();
    this._draft = { ...this.initialPage, tiles: [...this.initialPage.tiles] };
    this._refreshPreview();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    // Best-effort: don't lose a pending edit if the element is torn down.
    void this._saver.flush();
  }

  private async _refreshPreview() {
    const seq = ++this._previewSeq;
    const { tiles } = await renderPreview(this.hass, this._draft);
    if (seq === this._previewSeq) this._previewTiles = tiles;
  }

  private _applyDraft(next: VisualPage, refreshPreview = true) {
    this._draft = next;
    this._publishDirty = true;
    if (refreshPreview) this._refreshPreview();
    this._saver.schedule(next);
  }

  // ---------- events from canvas ----------

  private _onCellSelected(e: CustomEvent<{ row: number; col: number }>) {
    this._selection = { kind: "cell", ...e.detail };
  }

  private _onTileSelected(e: CustomEvent<{ tileId: string }>) {
    this._selection = { kind: "tile", tileId: e.detail.tileId };
  }

  private _onSelectionCleared() {
    this._selection = { kind: "none" };
  }

  private _onTileMoved(e: CustomEvent<{ tileId: string; row: number; col: number }>) {
    const { tileId, row, col } = e.detail;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((t) => (t.id === tileId ? { ...t, row, col } : t)),
    });
  }

  private _onTileResized(e: CustomEvent<{ tileId: string; rs: number; cs: number }>) {
    const { tileId, rs, cs } = e.detail;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((t) => (t.id === tileId ? { ...t, rs, cs } : t)),
    });
  }

  // ---------- events from inspector ----------

  private _onTileAdded(e: CustomEvent<{ tile: VisualTile }>) {
    const tile = e.detail.tile;
    this._applyDraft({ ...this._draft, tiles: [...this._draft.tiles, tile] });
    // Seamlessly switch the inspector to edit mode for the new tile.
    this._selection = { kind: "tile", tileId: tile.id };
  }

  private _onTileChanged(e: CustomEvent<{ tile: VisualTile }>) {
    const tile = e.detail.tile;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((t) => (t.id === tile.id ? tile : t)),
    });
  }

  private _onTileRemoved(e: CustomEvent<{ tileId: string }>) {
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.filter((t) => t.id !== e.detail.tileId),
    });
    this._selection = { kind: "none" };
  }

  private _onPageChanged(e: CustomEvent<Partial<Pick<VisualPage, "title" | "rows" | "columns">>>) {
    // A title-only change can't move any tile — skip the preview round-trip.
    const geometryChanged = e.detail.rows !== undefined || e.detail.columns !== undefined;
    this._applyDraft({ ...this._draft, ...e.detail }, geometryChanged);
  }

  // ---------- toolbar ----------

  private async _back() {
    const saved = await this._saver.flush();
    if (!saved && !window.confirm("Your latest changes couldn't be saved. Leave anyway and lose them?")) {
      return;
    }
    this.dispatchEvent(new CustomEvent("editor-closed"));
  }

  private _flash(message: string, ms = 3000) {
    this._status = message;
    setTimeout(() => {
      if (this._status === message) this._status = "";
    }, ms);
  }

  private async _publish() {
    this._publishing = true;
    try {
      const saved = await this._saver.flush();
      if (!saved) {
        this._flash("Not published — saving failed. Retry the save first.");
        return;
      }
      const seqBefore = this._previewSeq;
      await publishPanel(this.hass, this.panelId);
      // Only clear the dirty dot if no edits arrived while publishing.
      if (seqBefore === this._previewSeq) this._publishDirty = false;
      this._flash("Published", 2000);
    } catch {
      this._flash("Publish failed — check that the panel is loaded.");
    } finally {
      this._publishing = false;
    }
  }

  // Called by dash480-panel before an area-append: the backend appends to
  // the *saved* page, so pending edits must land first. Returns false when
  // they couldn't be saved — the append must be aborted.
  async prepareForAreaAppend(): Promise<boolean> {
    return this._saver.flush();
  }

  async reloadAfterAreaAppend(): Promise<void> {
    // The store copy is about to become the draft; drop any pending save so
    // a late retry can't overwrite the appended page with the old draft.
    this._saver.discard();
    const { pages } = await listPages(this.hass, this.panelId);
    const updated = pages.find((p) => p.id === this._draft.id);
    if (updated) {
      this._draft = updated;
      this._publishDirty = true;
      this._selection = { kind: "none" };
      await this._refreshPreview();
    }
  }

  private _saveLabel(): string {
    switch (this._saveState) {
      case "saving":
        return "Saving…";
      case "saved":
        return "Saved";
      case "error":
        return "Save failed";
      default:
        return "";
    }
  }

  render() {
    if (!this._draft) return nothing;
    return html`
      <div class="toolbar">
        <button class="back" @click=${this._back}>‹ Back</button>
        <span class="page-title">${this._draft.title}</span>
        <span class="save-state ${this._saveState}">${this._saveLabel()}</span>
        ${this._saveState === "error"
          ? html`<button @click=${() => this._saver.flush()}>Retry</button>`
          : nothing}
        <button @click=${() => this.dispatchEvent(new CustomEvent("area-append-requested"))}>
          + Add Area Entities
        </button>
        <button class="publish ${this._publishDirty ? "dirty" : ""}" ?disabled=${this._publishing} @click=${this._publish}>
          ${this._publishing ? "Publishing…" : this._publishDirty ? "● Publish to device" : "Publish to device"}
        </button>
        <span class="status">${this._status}</span>
      </div>
      <div class="body">
        <dash480-preview-canvas
          style="flex: 0 0 ${DEVICE_PX}px;"
          .page=${this._draft}
          .previewTiles=${this._previewTiles}
          .selection=${this._selection}
          @cell-selected=${this._onCellSelected}
          @tile-selected=${this._onTileSelected}
          @selection-cleared=${this._onSelectionCleared}
          @tile-moved=${this._onTileMoved}
          @tile-resized=${this._onTileResized}
        ></dash480-preview-canvas>
        <dash480-inspector
          class="inspector"
          .hass=${this.hass}
          .page=${this._draft}
          .selection=${this._selection}
          @tile-added=${this._onTileAdded}
          @tile-changed=${this._onTileChanged}
          @tile-removed=${this._onTileRemoved}
          @page-changed=${this._onPageChanged}
        ></dash480-inspector>
      </div>
    `;
  }

  static styles = css`
    :host {
      display: block;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .toolbar button {
      padding: 8px 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    .toolbar button:hover {
      border-color: #888;
    }
    .page-title {
      font-weight: bold;
      font-size: 16px;
    }
    .save-state {
      font-size: 12px;
      opacity: 0.6;
      min-width: 60px;
    }
    .save-state.error {
      color: #f87171;
      opacity: 1;
    }
    .publish.dirty {
      border-color: var(--primary-color, #38bdf8);
      color: var(--primary-color, #38bdf8);
      font-weight: 600;
    }
    .publish:disabled {
      opacity: 0.6;
      cursor: default;
    }
    .status {
      font-size: 12px;
      opacity: 0.7;
    }
    .body {
      display: flex;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
    }
    .inspector {
      flex: 1;
      min-width: 280px;
      max-width: 400px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-page-editor": Dash480PageEditor;
  }
}
