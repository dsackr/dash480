export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

export interface HomeAssistant {
  connection: {
    sendMessagePromise<T = unknown>(msg: Record<string, unknown>): Promise<T>;
  };
  states: Record<string, HassEntity>;
  language: string;
}

export interface Panel {
  entry_id: string;
  node_name: string;
  title: string;
}

export interface VisualTile {
  id: string;
  type: TileType;
  entity_id?: string;
  row: number;
  col: number;
  rs?: number;
  cs?: number;
  icon?: string;
  min?: number;
  max?: number;
}

export interface VisualPage {
  id: string;
  panel_entry_id: string;
  page_order: number;
  title: string;
  columns: number;
  rows: number;
  tiles: VisualTile[];
}

export interface PreviewTile {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  state: string | null;
  attributes: Record<string, unknown>;
  friendly_name: string;
}

export interface CompatibleEntity {
  entity_id: string;
  friendly_name: string;
  domain: string;
  // Present on gauge-compatible entities only — used for min/max defaults.
  unit_of_measurement?: string | null;
  device_class?: string | null;
}

export interface IconChoice {
  label: string;
  code: string;
}

export type TileType = "entity" | "gauge" | "weather";

// What the editor's inspector is focused on: nothing (page settings),
// an empty cell (add-tile form), or an existing tile (its properties).
export type Selection =
  | { kind: "none" }
  | { kind: "cell"; row: number; col: number }
  | { kind: "tile"; tileId: string };

export interface Area {
  area_id: string;
  name: string;
  entity_count: number;
  device_count: number;
}

export interface GenerateFromAreaResult {
  created_pages: string[];
  placed_count: number;
  skipped_entity_ids: string[];
  skipped_incompatible_count: number;
}
