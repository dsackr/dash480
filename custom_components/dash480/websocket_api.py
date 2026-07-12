"""Websocket API for the Dash480 visual page-builder sidebar panel.

All commands are namespaced `dash480/...` and require an admin user (this
controls a physical device's UI, same trust level as Settings > Devices).
Page CRUD here only ever touches the new visual-page store (pages_store.py)
— legacy Page config entries are untouched and keep working exactly as
before; `dash480/pages/list` surfaces their claimed page_order numbers
read-only so the frontend can show them as reserved and never collide.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .layout import GridSpec
from .pages_store import DEFAULT_COLUMNS, DEFAULT_ROWS, async_get_store, legacy_page_orders

# Domains selectable for an "entity" tile in the visual builder — matches
# select.py's ALLOWED_DOMAINS for the legacy per-slot picker (weather/gauge
# get their own tile types and compatibility lists in a later phase).
ENTITY_TILE_DOMAINS = {"switch", "light", "fan", "sensor", "cover", "calendar"}


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
        )
    except ValueError as err:
        connection.send_error(msg["id"], "no_free_page_order", str(err))
        return
    connection.send_result(msg["id"], {"page": page})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/update",
    vol.Required("id"): str,
    vol.Optional("title"): str,
    vol.Optional("columns"): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("rows"): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
    vol.Optional("tiles"): [dict],
})
@websocket_api.async_response
async def ws_update_page(hass: HomeAssistant, connection, msg: dict) -> None:
    store = async_get_store(hass)
    await store.async_load()
    patch = {k: v for k, v in msg.items() if k not in ("type", "id")}
    page = await store.async_update_page(msg["id"], patch)
    if page is None:
        connection.send_error(msg["id"], "not_found", "Unknown page id")
        return
    connection.send_result(msg["id"], {"page": page})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "dash480/pages/delete",
    vol.Required("id"): str,
})
@websocket_api.async_response
async def ws_delete_page(hass: HomeAssistant, connection, msg: dict) -> None:
    store = async_get_store(hass)
    await store.async_load()
    if not await store.async_delete_page(msg["id"]):
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
    if msg["tile_type"] != "entity":
        # gauge/weather compatibility lists arrive alongside those tile types.
        connection.send_result(msg["id"], {"entities": []})
        return
    entities = [
        {
            "entity_id": state.entity_id,
            "friendly_name": state.attributes.get("friendly_name", state.entity_id),
            "domain": state.domain,
        }
        for state in hass.states.async_all()
        if state.domain in ENTITY_TILE_DOMAINS
    ]
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
