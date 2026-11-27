import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { GaugeSeverity, PreviewTile, Selection, VisualPage, VisualTile } from "./types";
import { DEVICE_PX, Rect, cellFromPoint, cellRect, fitsAt, occupiedCells, spanRect } from "./grid";

// Same colors and sweep as layout.py's severity gauge (HA success / warning / error).
const SEVERITY_COLORS = { green: "#43A047", yellow: "#FFA600", red: "#DB4437" } as const;
const GAUGE_SWEEP = 270;
// conic-gradient 0° is 12 o'clock. The gauge starts at openHASP 135° (lower left),
// which is 225° clockwise from 12 o'clock.
const GAUGE_CSS_FROM = 225;

interface SeverityBand {
  color: string;
  start: number;
  end: number;
}

function severityBands(severity: GaugeSeverity | undefined, min: number, max: number): SeverityBand[] {
  if (!severity || !(max > min)) return [];
  const points: { key: keyof typeof SEVERITY_COLORS; level: number }[] = [];
  for (const key of ["green", "yellow", "red"] as const) {
    const level = severity[key];
    if (typeof level === "number" && Number.isFinite(level)) points.push({ key, level });
  }
  points.sort((a, b) => a.level - b.level);
  const bands: SeverityBand[] = [];
  for (let i = 0; i < points.length; i++) {
    const start = Math.min(max, Math.max(min, points[i].level));
    const end = i + 1 < points.length ? Math.min(max, Math.max(min, points[i + 1].level)) : max;
    if (end > start) bands.push({ color: SEVERITY_COLORS[points[i].key], start, end });
  }
  return bands;
}

function severityGradient(bands: SeverityBand[], min: number, max: number): string {
  const span = max - min;
  const stops: string[] = [];
  let cursor = 0;
  for (const band of bands) {
    const a = ((band.start - min) / span) * GAUGE_SWEEP;
    const b = ((band.end - min) / span) * GAUGE_SWEEP;
    if (a > cursor + 0.05) stops.push(`transparent ${cursor}deg ${a}deg`);
    stops.push(`${band.color} ${a}deg ${b}deg`);
    cursor = b;
  }
  if (cursor < 360) stops.push(`transparent ${cursor}deg 360deg`);
  return `conic-gradient(from ${GAUGE_CSS_FROM}deg, ${stops.join(", ")})`;
}

function needleRotation(value: number, min: number, max: number): number {
  const span = max - min;
  const frac = span > 0 ? Math.min(1, Math.max(0, (value - min) / span)) : 0;
  return ((135 + frac * GAUGE_SWEEP) % 360) - 270;
}

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
    const isCamera = tile.entity_id?.startsWith("camera.");
    const isBattery = tile.entity_id?.toLowerCase().includes("battery") || t.friendly_name?.toLowerCase().includes("battery");
    const isClock = tile.type === "clock";
    let pct = 0;
    let gaugeBands: SeverityBand[] = [];
    let gaugeMin = 0;
    let gaugeMax = 100;
    let needleDeg = -135;
    if (isGauge) {
      gaugeMin = tile.min ?? 0;
      gaugeMax = tile.max ?? 100;
      if (gaugeMax <= gaugeMin) gaugeMax = gaugeMin + 1;
      const raw = Number(t.state);
      const numeric = !Number.isNaN(raw);
      if (numeric && gaugeMax > gaugeMin) {
        pct = Math.max(0, Math.min(100, ((raw - gaugeMin) / (gaugeMax - gaugeMin)) * 100));
      }
      gaugeBands = severityBands(tile.severity, gaugeMin, gaugeMax);
      needleDeg = needleRotation(numeric ? raw : gaugeMin, gaugeMin, gaugeMax);
    }
    const gaugeUnit = typeof t.attributes?.["unit_of_measurement"] === "string" ? t.attributes["unit_of_measurement"] : "";
    const gaugeText =
      t.state == null || t.state === "" || t.state === "unknown" || t.state === "unavailable"
        ? "--"
        : `${t.state}${gaugeUnit}`;
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
                ? gaugeBands.length
                  ? html`
                      <div class="gauge-wrap">
                        <div class="gauge-face" style="background: ${severityGradient(gaugeBands, gaugeMin, gaugeMax)}"></div>
                        <div class="gauge-needle" style="transform: rotate(${needleDeg}deg)"></div>
                        <div class="gauge-value">${gaugeText}</div>
                      </div>
                    `
                  : html`
                      <div class="gauge-ring" style="background: conic-gradient(#38bdf8 ${pct * 3.6}deg, #334155 0deg);">
                        <div class="gauge-ring-inner">${t.state ?? "--"}</div>
                      </div>
                    `
                : isWeather
                  ? html`
                      <div class="weather-condition">${t.state ?? "--"}</div>
                      <div class="tile-state">${temp !== undefined ? `${temp}${tempUnit}` : "--"}</div>
                    `
                  : isCamera && t.attributes?.["entity_picture"]
                    ? html`
                        <img
                          src="${t.attributes["entity_picture"]}"
                          style="width: 100%; height: calc(100% - 30px); object-fit: contain; margin-top: 4px;"
                          draggable="false"
                        />
                      `
                    : isBattery
                      ? (() => {
                          const val = parseInt(t.state ?? "", 10) || 50;
                          const pctVal = Math.max(0, Math.min(100, val));
                          const barW = Math.round((pctVal / 100) * 42);
                          const color = pctVal < 15 ? "#EF4444" : (pctVal < 50 ? "#F59E0B" : "#10B981");
                          return html`
                            <div class="battery-preview-container" style="display: flex; align-items: center; justify-content: center; gap: 12px; height: calc(100% - 30px); margin-top: 4px;">
                              <div class="battery-outline" style="position: relative; width: 48px; height: 24px; border: 2px solid #e2e8f0; border-radius: 4px; box-sizing: border-box; display: flex; align-items: center; padding: 1px;">
                                <div class="battery-bar" style="width: ${barW}px; height: 100%; background-color: ${color}; border-radius: 2px; transition: width 0.2s ease;"></div>
                                <div class="battery-cap" style="position: absolute; right: -6px; top: 5px; width: 4px; height: 10px; background-color: #e2e8f0; border-radius: 1px;"></div>
                              </div>
                              <div class="battery-text" style="font-size: 20px; font-weight: bold; color: #e2e8f0;">${pctVal}%</div>
                            </div>
                          `;
                        })()
                      : isClock
                        ? html`
                            <div class="clock-time" style="font-size: 24px; font-weight: bold; text-align: center; margin-top: 8px;">
                              ${this._now.getHours().toString().padStart(2, '0')}:${this._now.getMinutes().toString().padStart(2, '0')}
                            </div>
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

  @state() private _now: Date = new Date();
  private _clockTimer: ReturnType<typeof setInterval> | null = null;

  connectedCallback(): void {
    super.connectedCallback();
    this._clockTimer = setInterval(() => {
      this._now = new Date();
      this.requestUpdate();
    }, 1000);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._clockTimer) clearInterval(this._clockTimer);
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
    .gauge-wrap {
      position: relative;
      width: 74%;
      max-width: 96px;
      aspect-ratio: 1;
      margin: 4px auto 0;
    }
    .gauge-face {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      -webkit-mask: radial-gradient(circle, transparent 52%, #000 53%);
      mask: radial-gradient(circle, transparent 52%, #000 53%);
    }
    .gauge-needle {
      position: absolute;
      left: 50%;
      bottom: 50%;
      width: 2px;
      height: 44%;
      margin-left: -1px;
      background: #111827;
      border-radius: 1px;
      transform-origin: center bottom;
    }
    .gauge-value {
      position: absolute;
      left: 0;
      right: 0;
      top: 60%;
      text-align: center;
      font-size: 11px;
      line-height: 1.2;
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
