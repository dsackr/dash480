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
  type: "entity" | "gauge" | "weather";
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
}
