// Client-side mirror of layout.py's GridSpec, used to draw the empty
// grid-cell click targets and drag ghosts in the editor. The pixel geometry
// of actual tiles always comes from the backend's dash480/preview/render
// (which calls the real GridSpec) — these constants must stay in sync with
// layout.py's GRID_MARGIN_X / GRID_COL_GAP / GRID_ROW_GAP / GRID_BASE_Y /
// GRID_FOOTER_Y.
import type { VisualTile } from "./types";

const GRID_MARGIN_X = 24;
const GRID_COL_GAP = 24;
const GRID_ROW_GAP = 20;
const GRID_BASE_Y = 80;
const GRID_FOOTER_Y = 430;
const DEVICE_SIZE = 480;

// Mirrors layout.py's MAX_TILES_PER_PAGE — the renderer silently drops
// tiles beyond this, so the editor refuses to add them in the first place.
export const MAX_TILES_PER_PAGE = 24;

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

function cellSize(columns: number, rows: number): { colW: number; rowH: number } {
  return {
    colW: (DEVICE_SIZE - 2 * GRID_MARGIN_X - (columns - 1) * GRID_COL_GAP) / columns,
    rowH: (GRID_FOOTER_Y - GRID_BASE_Y - (rows - 1) * GRID_ROW_GAP) / rows,
  };
}

export function cellRect(columns: number, rows: number, row: number, col: number): Rect {
  return spanRect(columns, rows, row, col, 1, 1);
}

// Rect covering a rs×cs span anchored at (row, col) — same math as the
// backend GridSpec.wh (spans absorb the gaps between the cells they cover).
export function spanRect(columns: number, rows: number, row: number, col: number, rs: number, cs: number): Rect {
  const { colW, rowH } = cellSize(columns, rows);
  return {
    x: GRID_MARGIN_X + col * (colW + GRID_COL_GAP),
    y: GRID_BASE_Y + row * (rowH + GRID_ROW_GAP),
    w: colW * cs + GRID_COL_GAP * (cs - 1),
    h: rowH * rs + GRID_ROW_GAP * (rs - 1),
  };
}

// Inverse hit-test: which cell contains a device-space point. Points in the
// gaps snap to the nearest cell; points above the header band or below the
// footer band are outside the grid entirely.
export function cellFromPoint(
  columns: number,
  rows: number,
  px: number,
  py: number,
): { row: number; col: number } | null {
  const TOLERANCE = 10;
  if (py < GRID_BASE_Y - TOLERANCE || py > GRID_FOOTER_Y + TOLERANCE) return null;
  if (px < GRID_MARGIN_X - TOLERANCE || px > DEVICE_SIZE - GRID_MARGIN_X + TOLERANCE) return null;
  const { colW, rowH } = cellSize(columns, rows);
  const col = Math.max(0, Math.min(columns - 1, Math.floor((px - GRID_MARGIN_X) / (colW + GRID_COL_GAP))));
  const row = Math.max(0, Math.min(rows - 1, Math.floor((py - GRID_BASE_Y) / (rowH + GRID_ROW_GAP))));
  return { row, col };
}

// Every cell covered by the given tiles (spans expanded), as "row,col" keys.
export function occupiedCells(tiles: VisualTile[], excludeId?: string): Set<string> {
  const occupied = new Set<string>();
  for (const t of tiles) {
    if (t.id === excludeId) continue;
    const rs = t.rs ?? 1;
    const cs = t.cs ?? 1;
    for (let r = t.row; r < t.row + rs; r++) {
      for (let c = t.col; c < t.col + cs; c++) {
        occupied.add(`${r},${c}`);
      }
    }
  }
  return occupied;
}

// Whether a rs×cs span anchored at (row, col) stays in bounds and doesn't
// overlap any occupied cell. The backend does no validation — this is the
// only guard against overlapping/out-of-bounds tiles.
export function fitsAt(
  row: number,
  col: number,
  rs: number,
  cs: number,
  rows: number,
  columns: number,
  occupied: Set<string>,
): boolean {
  if (row < 0 || col < 0 || row + rs > rows || col + cs > columns) return false;
  for (let r = row; r < row + rs; r++) {
    for (let c = col; c < col + cs; c++) {
      if (occupied.has(`${r},${c}`)) return false;
    }
  }
  return true;
}

export const DEVICE_PX = DEVICE_SIZE;
