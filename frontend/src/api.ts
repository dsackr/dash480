import type {
  Area,
  CompatibleEntity,
  GenerateFromAreaResult,
  HomeAssistant,
  IconChoice,
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

// The inspector and its embedded entity-select both need the compatible
// list for the same tile type at the same moment — a short-lived cache
// collapses those into one round-trip (entity states barely move on the
// timescale of a single editing gesture).
const COMPAT_CACHE_MS = 10_000;
const compatCache = new Map<string, { at: number; result: Promise<{ entities: CompatibleEntity[] }> }>();

export const compatibleEntities = (hass: HomeAssistant, tileType: string) => {
  const hit = compatCache.get(tileType);
  if (hit && Date.now() - hit.at < COMPAT_CACHE_MS) return hit.result;
  const result = call<{ entities: CompatibleEntity[] }>(hass, {
    type: "dash480/registry/compatible_entities",
    tile_type: tileType,
  });
  compatCache.set(tileType, { at: Date.now(), result });
  result.catch(() => compatCache.delete(tileType));
  return result;
};

// Static per-install list — fetch once per page load.
let iconsCache: Promise<{ icons: IconChoice[] }> | null = null;

export const listIcons = (hass: HomeAssistant) => {
  if (!iconsCache) {
    iconsCache = call<{ icons: IconChoice[] }>(hass, { type: "dash480/registry/icons" });
    iconsCache.catch(() => (iconsCache = null));
  }
  return iconsCache;
};

export const listAreas = (hass: HomeAssistant) =>
  call<{ areas: Area[] }>(hass, { type: "dash480/registry/areas" });

export const generateFromArea = (
  hass: HomeAssistant,
  panelEntryId: string,
  areaId: string,
  mode: "append" | "new_page",
  targetPageId?: string,
) =>
  call<GenerateFromAreaResult>(hass, {
    type: "dash480/pages/generate_from_area",
    panel_entry_id: panelEntryId,
    area_id: areaId,
    mode,
    ...(targetPageId ? { target_page_id: targetPageId } : {}),
  });
