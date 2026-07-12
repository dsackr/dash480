import type {
  CompatibleEntity,
  HomeAssistant,
  Panel,
  PreviewTile,
  VisualPage,
} from "./types";

function call<T>(hass: HomeAssistant, msg: Record<string, unknown>): Promise<T> {
  return hass.connection.sendMessagePromise<T>(msg);
}

export const listPanels = (hass: HomeAssistant) =>
  call<{ panels: Panel[] }>(hass, { type: "dash480/panels/list" });

export const listPages = (hass: HomeAssistant, panelEntryId: string) =>
  call<{ pages: VisualPage[]; reserved_legacy_orders: number[] }>(hass, {
    type: "dash480/pages/list",
    panel_entry_id: panelEntryId,
  });

export const createPage = (
  hass: HomeAssistant,
  panelEntryId: string,
  title: string,
  columns: number,
  rows: number,
) =>
  call<{ page: VisualPage }>(hass, {
    type: "dash480/pages/create",
    panel_entry_id: panelEntryId,
    title,
    columns,
    rows,
  });

export const updatePage = (
  hass: HomeAssistant,
  id: string,
  patch: Partial<Pick<VisualPage, "title" | "columns" | "rows" | "tiles">>,
) => call<{ page: VisualPage }>(hass, { type: "dash480/pages/update", page_id: id, ...patch });

export const deletePage = (hass: HomeAssistant, id: string) =>
  call<Record<string, never>>(hass, { type: "dash480/pages/delete", page_id: id });

export const publishPanel = (hass: HomeAssistant, panelEntryId: string) =>
  call<Record<string, never>>(hass, {
    type: "dash480/pages/publish",
    panel_entry_id: panelEntryId,
  });

export const renderPreview = (
  hass: HomeAssistant,
  draft: Pick<VisualPage, "columns" | "rows" | "tiles">,
) =>
  call<{ tiles: PreviewTile[] }>(hass, {
    type: "dash480/preview/render",
    page_draft: draft,
  });

export const compatibleEntities = (hass: HomeAssistant, tileType: string) =>
  call<{ entities: CompatibleEntity[] }>(hass, {
    type: "dash480/registry/compatible_entities",
    tile_type: tileType,
  });
