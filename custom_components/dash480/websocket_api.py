"""Websocket API for the Dash480 visual page-builder sidebar panel.

All commands are namespaced `dash480/...` and require an admin user (this
controls a physical device's UI, same trust level as Settings > Devices).
Page CRUD here only ever touches the new visual-page store (pages_store.py)
— legacy Page config entries are untouched and keep working exactly as
before; `dash480/pages/list` surfaces their claimed page_order numbers
read-only so the frontend can show them as reserved and never collide.
"""
from __future__ import annotations

import uuid

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er

from .const import DOMAIN
from .layout import GridSpec
from .pages_store import (
    DEFAULT_COLUMNS,
    DEFAULT_ROWS,
    MAX_PAGE_ORDER,
    MIN_PAGE_ORDER,
    async_get_store,
    legacy_page_orders,
)

# Domains selectable for an "entity" tile in the visual builder — matches
# select.py's ALLOWED_DOMAINS for the legacy per-slot picker (weather/gauge
# get their own tile types and compatibility lists in a later phase).
ENTITY_TILE_DOMAINS = {"switch", "light", "fan", "sensor", "cover", "calendar"}

# A gauge is for any numeric entity with a meaningful range — sensor domain
# is filtered to states that actually parse as a number (excludes text/enum
# sensors); number/input_number entities are inherently numeric.
GAUGE_TILE_DOMAINS = {"sensor", "number", "input_number"}

# Grid used for auto-generated Area pages — a middle ground that keeps tiles
# comfortably sized (unlike e.g. a cramped 4-row grid) while still holding a
# useful number of entities per page before spilling into another one.
AREA_PAGE_COLUMNS = 3
AREA_PAGE_ROWS = 3


def _is_numeric_state(state) -> bool:
    try:
        float(state.state)
        return True
    except (TypeError, ValueError):
        return False


def _tile_type_for_domain(domain: str) -> str | None:
    """Which auto-generated tile type (if any) a domain maps to for Area
    generation. Deliberately conservative: numeric sensors become plain
    "entity" tiles here, not "gauge" — a gauge needs a meaningful min/max
    that can't be safely guessed in bulk; the user can upgrade one manually
    afterward in the builder.
    """
    if domain == "weather":
        return "weather"
    if domain in ENTITY_TILE_DOMAINS:
        return "entity"
    return None


def _entities_for_area(hass: HomeAssistant, area_id: str) -> list:
    """Registry entries whose *effective* area is area_id — an entity's own
    area_id if set, else its device's area_id. Iterating device entities
    directly would over-count entities that override their device's area,
    and iterating entity.area_id alone would miss device-inherited ones.
    """
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)
    result = []
    for entry in entity_reg.entities.values():
        effective_area = entry.area_id
        if effective_area is None and entry.device_id:
            device = device_reg.async_get(entry.device_id)
            effective_area = device.area_id if device else None
        if effective_area == area_id:
            result.append(entry)
    return result


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "dash480/panels/list"})
@websocket_api.async_response
async def ws_list_panels(hass: HomeAssistant, connection, msg: dict) -> None:
    panels = [
        {"entry_id": entry.entry_id, "node_name": entry.data.get("node_name"), "title": entry.title}
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.data.get("role") == "panel"
    ]
    connection.send_result(msg["id"], {"panels": panels})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/list",
    vol.Required("panel_entry_id"): str,
})
@websocket_api.async_response
async def ws_list_pages(hass: HomeAssistant, connection, msg: dict) -> None:
    panel_entry_id = msg["panel_entry_id"]
    store = async_get_store(hass)
    await store.async_load()
    connection.send_result(msg["id"], {
        "pages": store.list_pages(panel_entry_id),
        "reserved_legacy_orders": sorted(legacy_page_orders(hass, panel_entry_id)),
    })


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/create",
    vol.Required("panel_entry_id"): str,
    vol.Required("title"): str,
    vol.Optional("columns", default=DEFAULT_COLUMNS): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("rows", default=DEFAULT_ROWS): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("page_order"): vol.All(vol.Coerce(int), vol.Range(min=MIN_PAGE_ORDER, max=MAX_PAGE_ORDER)),
})
@websocket_api.async_response
async def ws_create_page(hass: HomeAssistant, connection, msg: dict) -> None:
    if hass.config_entries.async_get_entry(msg["panel_entry_id"]) is None:
        connection.send_error(msg["id"], "not_found", "Unknown panel_entry_id")
        return
    store = async_get_store(hass)
    await store.async_load()
    try:
        page = await store.async_create_page(
            panel_entry_id=msg["panel_entry_id"],
            title=msg["title"],
            columns=msg["columns"],
            rows=msg["rows"],
            page_order=msg.get("page_order"),
        )
    except ValueError as err:
        connection.send_error(msg["id"], "no_free_page_order", str(err))
        return
    connection.send_result(msg["id"], {"page": page})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/update",
    vol.Required("page_id"): str,
    vol.Optional("title"): str,
    vol.Optional("columns"): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("rows"): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("tiles"): [dict],
})
@websocket_api.async_response
async def ws_update_page(hass: HomeAssistant, connection, msg: dict) -> None:
    store = async_get_store(hass)
    await store.async_load()
    patch = {k: v for k, v in msg.items() if k not in ("type", "id", "page_id")}
    page = await store.async_update_page(msg["page_id"], patch)
    if page is None:
        connection.send_error(msg["id"], "not_found", "Unknown page id")
        return
    connection.send_result(msg["id"], {"page": page})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/delete",
    vol.Required("page_id"): str,
})
@websocket_api.async_response
async def ws_delete_page(hass: HomeAssistant, connection, msg: dict) -> None:
    store = async_get_store(hass)
    await store.async_load()
    if not await store.async_delete_page(msg["page_id"]):
        connection.send_error(msg["id"], "not_found", "Unknown page id")
        return
    connection.send_result(msg["id"], {})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/reorder",
    vol.Required("panel_entry_id"): str,
    vol.Required("ordered_ids"): [str],
})
@websocket_api.async_response
async def ws_reorder_pages(hass: HomeAssistant, connection, msg: dict) -> None:
    store = async_get_store(hass)
    await store.async_load()
    await store.async_reorder(msg["panel_entry_id"], msg["ordered_ids"])
    connection.send_result(msg["id"], {"pages": store.list_pages(msg["panel_entry_id"])})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/publish",
    vol.Required("panel_entry_id"): str,
})
@websocket_api.async_response
async def ws_publish(hass: HomeAssistant, connection, msg: dict) -> None:
    panel_entry_id = msg["panel_entry_id"]
    publisher = hass.data.get(DOMAIN, {}).get("publishers", {}).get(panel_entry_id)
    if not publisher or not publisher.get("publish_all"):
        connection.send_error(msg["id"], "not_found", "Panel not loaded (or unknown panel_entry_id)")
        return
    await publisher["publish_all"]()
    connection.send_result(msg["id"], {})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/registry/compatible_entities",
    vol.Required("tile_type"): str,
})
@websocket_api.async_response
async def ws_compatible_entities(hass: HomeAssistant, connection, msg: dict) -> None:
    tile_type = msg["tile_type"]
    if tile_type == "entity":
        entities = [
            {
                "entity_id": state.entity_id,
                "friendly_name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.domain,
            }
            for state in hass.states.async_all()
            if state.domain in ENTITY_TILE_DOMAINS
        ]
    elif tile_type == "gauge":
        entities = [
            {
                "entity_id": state.entity_id,
                "friendly_name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.domain,
                "unit_of_measurement": state.attributes.get("unit_of_measurement"),
                "device_class": state.attributes.get("device_class"),
            }
            for state in hass.states.async_all()
            if state.domain in GAUGE_TILE_DOMAINS and _is_numeric_state(state)
        ]
    elif tile_type == "weather":
        entities = [
            {
                "entity_id": state.entity_id,
                "friendly_name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.domain,
            }
            for state in hass.states.async_all()
            if state.domain == "weather"
        ]
    else:
        entities = []
    entities.sort(key=lambda e: e["friendly_name"].lower())
    connection.send_result(msg["id"], {"entities": entities})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/preview/render",
    vol.Required("page_draft"): dict,
})
@websocket_api.async_response
async def ws_render_preview(hass: HomeAssistant, connection, msg: dict) -> None:
    """Read-only: pixel geometry + current state for a draft page's tiles,
    for the frontend's live mockup. Never touches the device."""
    draft = msg["page_draft"]
    columns = int(draft.get("columns") or DEFAULT_COLUMNS)
    rows = int(draft.get("rows") or DEFAULT_ROWS)
    grid = GridSpec(columns=columns, rows=rows)

    tiles_out = []
    for tile in draft.get("tiles") or []:
        x, y = grid.xy(int(tile.get("row", 0)), int(tile.get("col", 0)))
        w, h = grid.wh(int(tile.get("rs", 1)), int(tile.get("cs", 1)))
        entity_id = tile.get("entity_id")
        state = hass.states.get(entity_id) if entity_id else None
        tiles_out.append({
            "id": tile.get("id"),
            "x": x, "y": y, "w": w, "h": h,
            "state": state.state if state else None,
            "attributes": dict(state.attributes) if state else {},
            "friendly_name": (state.attributes.get("friendly_name") if state else None) or entity_id,
        })
    connection.send_result(msg["id"], {"tiles": tiles_out})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "dash480/registry/areas"})
@websocket_api.async_response
async def ws_list_areas(hass: HomeAssistant, connection, msg: dict) -> None:
    area_reg = ar.async_get(hass)
    device_reg = dr.async_get(hass)
    areas = [
        {
            "area_id": area.id,
            "name": area.name,
            "entity_count": len(_entities_for_area(hass, area.id)),
            "device_count": len(dr.async_entries_for_area(device_reg, area.id)),
        }
        for area in area_reg.async_list_areas()
    ]
    areas.sort(key=lambda a: a["name"].lower())
    connection.send_result(msg["id"], {"areas": areas})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/registry/entities_for_area",
    vol.Required("area_id"): str,
})
@websocket_api.async_response
async def ws_entities_for_area(hass: HomeAssistant, connection, msg: dict) -> None:
    entities = []
    for entry in _entities_for_area(hass, msg["area_id"]):
        if entry.disabled:
            continue
        state = hass.states.get(entry.entity_id)
        if not state:
            continue
        entities.append({
            "entity_id": entry.entity_id,
            "friendly_name": state.attributes.get("friendly_name", entry.entity_id),
            "domain": entry.entity_id.split(".")[0],
        })
    entities.sort(key=lambda e: e["friendly_name"].lower())
    connection.send_result(msg["id"], {"entities": entities})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/generate_from_area",
    vol.Required("panel_entry_id"): str,
    vol.Required("area_id"): str,
    vol.Required("mode"): vol.In(["append", "new_page"]),
    vol.Optional("target_page_id"): str,
    vol.Optional("first_page_order"): vol.All(vol.Coerce(int), vol.Range(min=MIN_PAGE_ORDER, max=MAX_PAGE_ORDER)),
})
@websocket_api.async_response
async def ws_generate_from_area(hass: HomeAssistant, connection, msg: dict) -> None:
    """Build tiles from an Area's entities — either appended to an existing
    page's free cells, or as one or more brand-new pages (spilling into
    additional pages if there are more entities than one page's grid holds,
    or until page_order 1..9 runs out). Every dropped entity is reported
    back, never silently discarded.
    """
    panel_entry_id = msg["panel_entry_id"]
    area_id = msg["area_id"]
    mode = msg["mode"]

    area_reg = ar.async_get(hass)
    area = area_reg.async_get_area(area_id)
    if area is None:
        connection.send_error(msg["id"], "not_found", "Unknown area_id")
        return

    entries = _entities_for_area(hass, area_id)
    candidates = []
    incompatible_count = 0
    for entry in entries:
        if entry.disabled:
            continue
        state = hass.states.get(entry.entity_id)
        if not state:
            continue
        domain = entry.entity_id.split(".")[0]
        tile_type = _tile_type_for_domain(domain)
        if tile_type is None:
            incompatible_count += 1
            continue
        candidates.append((entry.entity_id, tile_type))

    store = async_get_store(hass)
    await store.async_load()

    created_pages: list[str] = []
    skipped_entity_ids: list[str] = []

    if mode == "append":
        target_id = msg.get("target_page_id")
        page = store.get_page(target_id) if target_id else None
        if page is None:
            connection.send_error(msg["id"], "not_found", "Unknown target_page_id")
            return
        occupied = {(t.get("row", 0), t.get("col", 0)) for t in page["tiles"]}
        free_cells = [
            (r, c)
            for r in range(page["rows"])
            for c in range(page["columns"])
            if (r, c) not in occupied
        ]
        new_tiles = list(page["tiles"])
        for (entity_id, tile_type), (r, c) in zip(candidates, free_cells):
            new_tiles.append({
                "id": uuid.uuid4().hex, "type": tile_type, "entity_id": entity_id,
                "row": r, "col": c, "rs": 1, "cs": 1,
            })
        await store.async_update_page(target_id, {"tiles": new_tiles})
        created_pages = [target_id]
        skipped_entity_ids = [c[0] for c in candidates[len(free_cells):]]
    else:
        remaining = list(candidates)
        page_num = 0
        per_page = AREA_PAGE_COLUMNS * AREA_PAGE_ROWS
        requested_first_order = msg.get("first_page_order")
        while remaining:
            if page_num == 0 and requested_first_order is not None:
                # Caller picked an explicit slot for the first page (e.g. the
                # frontend could offer this) — auto-allocation alone would
                # take the *lowest* free order, which could be page 1 (the
                # device's home/fallback screen) with no warning.
                page_order = requested_first_order
            else:
                page_order = store.allocate_page_order(panel_entry_id)
            if page_order is None:
                break  # no free page_order (1..9) left for this panel
            chunk, remaining = remaining[:per_page], remaining[per_page:]
            tiles = [
                {
                    "id": uuid.uuid4().hex, "type": tile_type, "entity_id": entity_id,
                    "row": i // AREA_PAGE_COLUMNS, "col": i % AREA_PAGE_COLUMNS, "rs": 1, "cs": 1,
                }
                for i, (entity_id, tile_type) in enumerate(chunk)
            ]
            page_num += 1
            title = area.name if page_num == 1 else f"{area.name} ({page_num})"
            try:
                page = await store.async_create_page(
                    panel_entry_id=panel_entry_id, title=title,
                    columns=AREA_PAGE_COLUMNS, rows=AREA_PAGE_ROWS, tiles=tiles, page_order=page_order,
                )
            except ValueError as err:
                connection.send_error(msg["id"], "no_free_page_order", str(err))
                return
            created_pages.append(page["id"])
        skipped_entity_ids = [c[0] for c in remaining]

    connection.send_result(msg["id"], {
        "created_pages": created_pages,
        "placed_count": len(candidates) - len(skipped_entity_ids),
        "skipped_entity_ids": skipped_entity_ids,
        "skipped_incompatible_count": incompatible_count,
    })


def async_register(hass: HomeAssistant) -> None:
    """Register every dash480/* websocket command. Call once per integration setup."""
    websocket_api.async_register_command(hass, ws_list_panels)
    websocket_api.async_register_command(hass, ws_list_pages)
    websocket_api.async_register_command(hass, ws_create_page)
    websocket_api.async_register_command(hass, ws_update_page)
    websocket_api.async_register_command(hass, ws_delete_page)
    websocket_api.async_register_command(hass, ws_reorder_pages)
    websocket_api.async_register_command(hass, ws_publish)
    websocket_api.async_register_command(hass, ws_compatible_entities)
    websocket_api.async_register_command(hass, ws_render_preview)
    websocket_api.async_register_command(hass, ws_list_areas)
    websocket_api.async_register_command(hass, ws_entities_for_area)
    websocket_api.async_register_command(hass, ws_generate_from_area)
