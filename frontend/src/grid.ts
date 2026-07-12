// Client-side mirror of layout.py's GridSpec, used only to draw the empty
// grid-cell click targets in the editor. The pixel geometry of actual tiles
// always comes from the backend's dash480/preview/render (which calls the
// real GridSpec) — these constants must stay in sync with layout.py's
// GRID_MARGIN_X / GRID_COL_GAP / GRID_ROW_GAP / GRID_BASE_Y / GRID_FOOTER_Y.
const GRID_MARGIN_X = 24;
const GRID_COL_GAP = 24;
const GRID_ROW_GAP = 20;
const GRID_BASE_Y = 80;
const GRID_FOOTER_Y = 430;
const DEVICE_SIZE = 480;

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export function cellRect(columns: number, rows: number, row: number, col: number): Rect {
  const colW = (DEVICE_SIZE - 2 * GRID_MARGIN_X - (columns - 1) * GRID_COL_GAP) / columns;
  const rowH = (GRID_FOOTER_Y - GRID_BASE_Y - (rows - 1) * GRID_ROW_GAP) / rows;
  return {
    x: GRID_MARGIN_X + col * (colW + GRID_COL_GAP),
    y: GRID_BASE_Y + row * (rowH + GRID_ROW_GAP),
    w: colW,
    h: rowH,
  };
}

export const DEVICE_PX = DEVICE_SIZE;
