import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { PreviewTile, Selection, VisualPage, VisualTile } from "./types";
import { DEVICE_PX, Rect, cellFromPoint, cellRect, fitsAt, occupiedCells, spanRect } from "./grid";

const DRAG_THRESHOLD_PX = 5;

interface DragState {
  tileId: string;
  mode: "move" | "resize";
  // Pointer offset from the tile's top-left at pointerdown, in device px —
  // keeps the tile under the hand instead of jumping its corner to the cursor.
  grabDx: number;
  grabDy: number;
  startX: number;
  startY: number;
  active: boolean; // becomes true once DRAG_THRESHOLD_PX is exceeded
  ghost: { rect: Rect; row: number; col: number; rs: number; cs: number; valid: boolean } | null;
  // Cached at pointerdown — none of these can change mid-drag, and
  // recomputing them per pointermove (60–120 Hz) is pure waste.
  canvasLeft: number;
  canvasTop: number;
  tile: VisualTile;
  occupied: Set<string>;
}

/**
 * The 480×480 device mockup: grid cells, live tiles, selection highlight,
 * drag-to-move and corner drag-to-resize. Emits `cell-selected`,
 * `tile-selected`, `selection-cleared`, `tile-moved {tileId,row,col}` and
 * `tile-resized {tileId,rs,cs}` — it never mutates the page itself, and all
 * drag state stays local until pointerup commits.
 */
@customElement("dash480-preview-canvas")
export class Dash480PreviewCanvas extends LitElement {
  @property({ attribute: false }) page!: VisualPage;
  @property({ attribute: false }) previewTiles: PreviewTile[] = [];
  @property({ attribute: false }) selection: Selection = { kind: "none" };

  @state() private _drag: DragState | null = null;

  private _emit<T>(name: string, detail?: T) {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
  }

  private _onTilePointerDown(e: PointerEvent, previewTile: PreviewTile, mode: "move" | "resize") {
    if (e.button !== 0) return;
    e.stopPropagation();
    const tile = this.page.tiles.find((t) => t.id === previewTile.id);
    if (!tile) return;
    const canvas = (this.shadowRoot!.querySelector(".device") as HTMLElement).getBoundingClientRect();
    const x = e.clientX - canvas.left;
    const y = e.clientY - canvas.top;
    this._drag = {
      tileId: previewTile.id,
      mode,
      grabDx: x - previewTile.x,
      grabDy: y - previewTile.y,
      startX: x,
      startY: y,
      active: false,
      ghost: null,
      canvasLeft: canvas.left,
      canvasTop: canvas.top,
      tile,
      occupied: occupiedCells(this.page.tiles, tile.id),
    };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }

  private _onPointerMove(e: PointerEvent) {
    const drag = this._drag;
    if (!drag) return;
    const p = { x: e.clientX - drag.canvasLeft, y: e.clientY - drag.canvasTop };
    if (!drag.active) {
      if (Math.hypot(p.x - drag.startX, p.y - drag.startY) < DRAG_THRESHOLD_PX) return;
      drag.active = true;
    }
    const { tile, occupied } = drag;
    const { rows, columns } = this.page;
    let ghost: DragState["ghost"] = null;
    if (drag.mode === "move") {
      const anchor = cellFromPoint(columns, rows, p.x - drag.grabDx, p.y - drag.grabDy);
      if (anchor) {
        const rs = tile.rs ?? 1;
        const cs = tile.cs ?? 1;
        ghost = {
          ...anchor,
          rs,
          cs,
          rect: spanRect(columns, rows, anchor.row, anchor.col, rs, cs),
          valid: fitsAt(anchor.row, anchor.col, rs, cs, rows, columns, occupied),
        };
      }
    } else {
      const cell = cellFromPoint(columns, rows, p.x, p.y);
      if (cell) {
        const rs = Math.max(1, cell.row - tile.row + 1);
        const cs = Math.max(1, cell.col - tile.col + 1);
        ghost = {
          row: tile.row,
          col: tile.col,
          rs,
          cs,
          rect: spanRect(columns, rows, tile.row, tile.col, rs, cs),
          valid: fitsAt(tile.row, tile.col, rs, cs, rows, columns, occupied),
        };
      }
    }
    this._drag = { ...drag, ghost };
  }

  private _onPointerUp() {
    const drag = this._drag;
    if (!drag) return;
    this._drag = null;
    if (!drag.active) {
      // A plain click on the tile.
      this._emit("tile-selected", { tileId: drag.tileId });
      return;
    }
    const ghost = drag.ghost;
    if (!ghost || !ghost.valid) return; // snap back — the real tile never moved
    const tile = drag.tile;
    if (drag.mode === "move") {
      if (ghost.row !== tile.row || ghost.col !== tile.col) {
        this._emit("tile-moved", { tileId: tile.id, row: ghost.row, col: ghost.col });
      }
    } else if (ghost.rs !== (tile.rs ?? 1) || ghost.cs !== (tile.cs ?? 1)) {
      this._emit("tile-resized", { tileId: tile.id, rs: ghost.rs, cs: ghost.cs });
    }
  }

  private _onPointerCancel() {
    this._drag = null;
  }

  render() {
    if (!this.page) return nothing;
    const page = this.page;
    const occupied = occupiedCells(page.tiles);
    const cells: { row: number; col: number; rect: Rect }[] = [];
    for (let row = 0; row < page.rows; row++) {
      for (let col = 0; col < page.columns; col++) {
        if (occupied.has(`${row},${col}`)) continue;
        cells.push({ row, col, rect: cellRect(page.columns, page.rows, row, col) });
      }
    }
    const selectedId = this.selection.kind === "tile" ? this.selection.tileId : null;
    const dragTileId = this._drag?.active ? this._drag.tileId : null;
    const ghost = this._drag?.active ? this._drag.ghost : null;
    return html`
      <div
        class="device"
        style="width:${DEVICE_PX}px;height:${DEVICE_PX}px;"
        @click=${() => this._emit("selection-cleared")}
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerCancel}
      >
        ${cells.map(
          (c) => html`
            <div
              class="cell ${this.selection.kind === "cell" &&
              this.selection.row === c.row &&
              this.selection.col === c.col
                ? "selected"
                : ""}"
              style="left:${c.rect.x}px;top:${c.rect.y}px;width:${c.rect.w}px;height:${c.rect.h}px;"
              @click=${(e: Event) => {
                e.stopPropagation();
                this._emit("cell-selected", { row: c.row, col: c.col });
              }}
            >
              <span class="plus">+</span>
            </div>
          `,
        )}
        ${this.previewTiles.map((t) => this._renderTile(t, t.id === selectedId, t.id === dragTileId))}
        ${ghost
          ? html`
              <div
                class="ghost ${ghost.valid ? "valid" : "invalid"}"
                style="left:${ghost.rect.x}px;top:${ghost.rect.y}px;width:${ghost.rect.w}px;height:${ghost.rect.h}px;"
              ></div>
            `
          : nothing}
      </div>
    `;
  }

  private _renderTile(t: PreviewTile, selected: boolean, dragging: boolean) {
    const tile = this.page.tiles.find((pt) => pt.id === t.id);
    if (!tile) return nothing;
    const isGauge = tile.type === "gauge";
    const isWeather = tile.type === "weather";
    let pct = 0;
    if (isGauge) {
      const min = tile.min ?? 0;
      const max = tile.max ?? 100;
      const raw = Number(t.state);
      if (!Number.isNaN(raw) && max > min) {
        pct = Math.max(0, Math.min(100, ((raw - min) / (max - min)) * 100));
      }
    }
    const temp = t.attributes?.["temperature"];
    const tempUnit = t.attributes?.["temperature_unit"] ?? "";
    const missingEntity = !tile.entity_id;
    return html`
      <div
        class="tile ${selected ? "selected" : ""} ${dragging ? "dragging" : ""} ${missingEntity ? "missing" : ""}"
        style="left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;"
        @pointerdown=${(e: PointerEvent) => this._onTilePointerDown(e, t, "move")}
        @click=${(e: Event) => e.stopPropagation()}
      >
        ${missingEntity
          ? html`<div class="tile-missing-label">No entity —<br />select one</div>`
          : html`
              <div class="tile-label">${t.friendly_name}</div>
              ${isGauge
                ? html`
                    <div class="gauge-ring" style="background: conic-gradient(#38bdf8 ${pct * 3.6}deg, #334155 0deg);">
                      <div class="gauge-ring-inner">${t.state ?? "--"}</div>
                    </div>
                  `
                : isWeather
                  ? html`
                      <div class="weather-condition">${t.state ?? "--"}</div>
                      <div class="tile-state">${temp !== undefined ? `${temp}${tempUnit}` : "--"}</div>
                    `
                  : html`<div class="tile-state">${t.state ?? "--"}</div>`}
            `}
        ${selected
          ? html`
              <div
                class="resize-handle"
                title="Drag to resize"
                @pointerdown=${(e: PointerEvent) => this._onTilePointerDown(e, t, "resize")}
              ></div>
            `
          : nothing}
      </div>
    `;
  }

  static styles = css`
    :host {
      display: block;
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
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .cell .plus {
      opacity: 0;
      font-size: 20px;
      color: rgba(255, 255, 255, 0.5);
    }
    .cell:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    .cell:hover .plus {
      opacity: 1;
    }
    .cell.selected {
      border-color: var(--primary-color, #38bdf8);
      border-style: solid;
    }
    .tile {
      position: absolute;
      background: #1e293b;
      border-radius: 10px;
      color: #e5e7eb;
      padding: 6px;
      box-sizing: border-box;
      cursor: grab;
      touch-action: none;
      user-select: none;
      -webkit-user-select: none;
    }
    .tile.selected {
      outline: 2px solid var(--primary-color, #38bdf8);
    }
    .tile.dragging {
      opacity: 0.4;
    }
    .tile.missing {
      border: 1px dashed rgba(255, 255, 255, 0.3);
      background: rgba(30, 41, 59, 0.5);
    }
    .tile-missing-label {
      font-size: 11px;
      opacity: 0.6;
      text-align: center;
      margin-top: 12px;
      line-height: 1.4;
    }
    .tile-label {
      font-size: 11px;
      opacity: 0.7;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .tile-state {
      font-size: 14px;
      margin-top: 4px;
    }
    .weather-condition {
      font-size: 20px;
      margin-top: 12px;
      text-align: center;
    }
    .gauge-ring {
      width: 60%;
      max-width: 80px;
      aspect-ratio: 1;
      margin: 8px auto 0;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .gauge-ring-inner {
      width: 68%;
      aspect-ratio: 1;
      border-radius: 50%;
      background: #1e293b;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      text-align: center;
    }
    .resize-handle {
      position: absolute;
      right: 0;
      bottom: 0;
      width: 14px;
      height: 14px;
      cursor: nwse-resize;
      border-right: 3px solid var(--primary-color, #38bdf8);
      border-bottom: 3px solid var(--primary-color, #38bdf8);
      border-bottom-right-radius: 8px;
    }
    .ghost {
      position: absolute;
      border-radius: 10px;
      pointer-events: none;
      box-sizing: border-box;
    }
    .ghost.valid {
      border: 2px solid #4ade80;
      background: rgba(74, 222, 128, 0.12);
    }
    .ghost.invalid {
      border: 2px solid #f87171;
      background: rgba(248, 113, 113, 0.12);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "dash480-preview-canvas": Dash480PreviewCanvas;
  }
}
