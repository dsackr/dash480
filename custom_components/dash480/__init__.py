"""The Dash480 integration."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
from homeassistant.components import mqtt, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.helpers.event import async_track_state_change_event
import voluptuous as vol

from .const import DOMAIN
from .layout import (
    build_option_page,
    build_page_ring,
    display_state,
    format_calendar_summary,
    gauge_arc_value,
    gauge_display_value,
    header_footer_objects,
    home_fallback_objects,
    option_page_allocator,
    page_background,
    resolve_layout,
    resolve_palette,
    render_page,
    render_tile_page,
    ring_neighbors,
)
from .pages_store import async_get_store

_LOGGER = logging.getLogger(__name__)


async def _gather_panel_pages(hass: HomeAssistant, panel_entry_id: str) -> list[tuple[int, str, Any]]:
    """(page_order, source, page_obj) for every legacy Page entry + visual
    page on this panel, sorted by page_order. `source` is "legacy" (a Page
    ConfigEntry, rendered via layout.render_page) or "visual" (a plain dict
    from pages_store.py, rendered via layout.render_tile_page). Single
    source of truth for the page ring/nav so the two page models can coexist
    without colliding (pages_store's allocator already keeps their
    page_order numbers disjoint per panel).
    """
    legacy = [
        (int(e.data.get("page_order", 99)), "legacy", e)
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.data.get("role") == "page" and e.data.get("panel_entry_id") == panel_entry_id
    ]
    visual_store = async_get_store(hass)
    await visual_store.async_load()
    visual = [
        (int(p["page_order"]), "visual", p)
        for p in visual_store.list_pages(panel_entry_id)
    ]
    return sorted(legacy + visual, key=lambda item: item[0])


def _page1_exists(pages: list[tuple[int, str, Any]]) -> bool:
    return any(order == 1 for order, _, _ in pages)


PANEL_URL_PATH = "dash480"
PANEL_MODULE_FILENAME = "dash480-panel.js"
PANEL_STATIC_URL = f"/dash480_static/{PANEL_MODULE_FILENAME}"


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the visual-builder sidebar panel and its static JS bundle.

    The bundle is built (Vite + TypeScript + Lit) from frontend/ and its
    output is committed to panel_dist/ — HACS installs never need Node.
    """
    dist_path = Path(__file__).parent / "panel_dist" / PANEL_MODULE_FILENAME
    if not dist_path.is_file():
        # StaticPathConfig doesn't validate the target exists — registration
        # below will "succeed" either way, but every request for it will
        # 404 until this file is actually on disk (e.g. an installer that
        # didn't sync the panel_dist/ directory).
        _LOGGER.error(
            "Dash480: panel bundle missing at %s (size on disk: n/a) — the "
            "sidebar panel will 404 until custom_components/dash480/panel_dist/%s "
            "exists here. Directory listing of %s: %s",
            dist_path,
            PANEL_MODULE_FILENAME,
            dist_path.parent,
            sorted(p.name for p in dist_path.parent.iterdir()) if dist_path.parent.is_dir() else "<missing>",
        )
    else:
        _LOGGER.info("Dash480: panel bundle found at %s (%d bytes)", dist_path, dist_path.stat().st_size)
    await hass.http.async_register_static_paths([
        StaticPathConfig(PANEL_STATIC_URL, str(dist_path), False)
    ])
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name="dash480-panel",
        module_url=PANEL_STATIC_URL,
        sidebar_title="Dash480",
        sidebar_icon="mdi:tablet-dashboard",
        require_admin=True,
        config={},
    )

# Top-level (component) setup: register services once and route by entry_id
async def async_setup(hass: HomeAssistant, config):
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("services_registered"):
        return True

    async def _pick_entry_id(call) -> str | None:
        eid = call.data.get("entry_id")
        if eid:
            return eid
        publishers = hass.data.get(DOMAIN, {}).get("publishers", {})
        if len(publishers) == 1:
            return next(iter(publishers.keys()))
        _LOGGER.warning("Dash480: entry_id required when multiple panels exist")
        return None

    async def svc_publish_all(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        pub = hass.data.get(DOMAIN, {}).get("publishers", {}).get(eid)
        if not pub or not pub.get("publish_all"):
            _LOGGER.warning("Dash480: no publisher for entry_id=%s", eid)
            return
        _LOGGER.info("Dash480: publish_all(entry_id=%s)", eid)
        try:
            await pub["publish_all"]()
        except Exception as exc:
            _LOGGER.exception("Dash480: publish_all failed for %s: %s", eid, exc)

    async def svc_publish_home(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        pub = hass.data.get(DOMAIN, {}).get("publishers", {}).get(eid)
        if not pub or not pub.get("publish_home"):
            _LOGGER.warning("Dash480: no home publisher for entry_id=%s", eid)
            return
        _LOGGER.info("Dash480: publish_home(entry_id=%s)", eid)
        try:
            await pub["publish_home"]()
        except Exception as exc:
            _LOGGER.exception("Dash480: publish_home failed for %s: %s", eid, exc)

    async def svc_set_home_title(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        title = str(call.data.get("home_title", "")).strip()
        entry = hass.config_entries.async_get_entry(eid)
        if not entry:
            _LOGGER.warning("Dash480: entry not found for set_home_title: %s", eid)
            return
        new_opts = {**entry.options, "home_title": title or entry.data.get("node_name", "Dash")}
        hass.config_entries.async_update_entry(entry, options=new_opts)

    async def svc_set_temp_entity(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        ent = str(call.data.get("temp_entity", "")).strip()
        entry = hass.config_entries.async_get_entry(eid)
        if not entry:
            _LOGGER.warning("Dash480: entry not found for set_temp_entity: %s", eid)
            return
        new_opts = {**entry.options, "temp_entity": ent}
        hass.config_entries.async_update_entry(entry, options=new_opts)

    hass.services.async_register(DOMAIN, "publish_all", svc_publish_all)
    hass.services.async_register(DOMAIN, "publish_home", svc_publish_home)
    hass.services.async_register(DOMAIN, "set_home_title", svc_set_home_title)
    hass.services.async_register(DOMAIN, "set_temp_entity", svc_set_temp_entity)

    async def svc_dump_layout(call):
        """Build the full JSONL layout and dump to a file (no publish).

        Renders through the same layout.render_page/build_option_page used by
        the live publisher, so this file is an accurate preview of what gets
        pushed to the device.
        """
        eid = await _pick_entry_id(call)
        if not eid:
            return
        entry = hass.config_entries.async_get_entry(eid)
        if not entry or entry.data.get("role") != "panel":
            _LOGGER.warning("Dash480: dump_layout requires a Panel entry_id")
            return
        node_name = entry.data.get("node_name")
        home_title = entry.options.get("home_title", node_name)
        temp_entity = entry.options.get("temp_entity", "")
        theme = entry.options.get("theme", "dark")
        sun_state = hass.states.get("sun.sun")
        sun_above = sun_state.state == "above_horizon" if sun_state else None
        palette = resolve_palette(theme, sun_above)

        lines: list[str] = []
        tval = display_state(hass.states.get(temp_entity) if temp_entity else None)
        lines.extend(json.dumps(obj) for obj in header_footer_objects(node_name, home_title, tval, palette))

        merged_pages = await _gather_panel_pages(hass, eid)
        page_numbers = [order for order, _, _ in merged_pages]
        pages_ring = build_page_ring(page_numbers)
        if not _page1_exists(merged_pages):
            prev_home, next_home = ring_neighbors(pages_ring, 1)
            lines.extend(json.dumps(obj) for obj in home_fallback_objects(prev_home, next_home, palette))

        option_specs: list[dict] = []
        alloc_option_page = option_page_allocator(50)

        for p, source, page_obj in merged_pages:
            prev_p, next_p = ring_neighbors(pages_ring, p)
            lines.append(json.dumps({"page": p, "id": 0, "obj": "page", "prev": prev_p, "next": next_p}))
            lines.append(json.dumps(page_background(p, palette=palette)))

            if source == "legacy":
                pe = page_obj
                slot_defs = [(f"s{i}", pe.options.get(f"s{i}", "")) for i in range(1, 13)]
                icon_overrides = {f"s{i}": pe.options.get(f"s{i}_icon") for i in range(1, 13)}
                page_layout = resolve_layout(pe.options.get("layout"), slot_defs)
                render = render_page(p, page_layout, slot_defs, icon_overrides, hass.states.get, alloc_option_page, palette)
            else:
                render = render_tile_page(p, page_obj, hass.states.get, alloc_option_page, palette)

            lines.extend(json.dumps(obj) for obj in render.objects)
            option_specs.extend(render.option_specs)

        for spec in option_specs:
            option_render = build_option_page(spec, palette)
            lines.extend(json.dumps(obj) for obj in option_render.objects)

        # Write file to config/dash480_exports
        base = hass.config.path("dash480_exports")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"dash480_{node_name}_pages.jsonl")
        data = "\n".join(lines) + "\n"
        def _write():
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        await hass.async_add_executor_job(_write)
        _LOGGER.info("Dash480: dump_layout wrote %s (%d lines)", path, len(lines))

    hass.services.async_register(DOMAIN, "dump_layout", svc_dump_layout)

    from .websocket_api import async_register as async_register_websocket_api  # local import

    async_register_websocket_api(hass)
    await _async_register_panel(hass)

    store["services_registered"] = True
    return True

# List of platforms to support.
PLATFORMS = ["switch", "text", "number", "button", "select"]
PLATFORMS_PAGE = ["text", "button", "select"]


async def async_get_options_flow(entry: ConfigEntry):
    """Expose options flow to HA (wrapper around options_flow module)."""
    from .options_flow import Dash480OptionsFlowHandler  # local import

    return Dash480OptionsFlowHandler(entry)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dash480 from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    role = entry.data.get("role", "panel")
    # If this is a Page entry, set up page entities only and return early.
    if role == "page":
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_PAGE)
        return True
    # Panel entry setup
    node_name = entry.data["node_name"]
    home_title = entry.options.get("home_title", node_name)
    temp_entity = entry.options.get("temp_entity", "")
    theme = entry.options.get("theme", "dark")
    # control map (id -> entity_id) and sensor text map (entity -> list of (page,id))
    hass.data[DOMAIN][entry.entry_id]["ctrl_map"] = {}
    hass.data[DOMAIN][entry.entry_id]["sensor_map"] = {}

    def _sun_is_up() -> bool | None:
        sun_state = hass.states.get("sun.sun")
        return sun_state.state == "above_horizon" if sun_state else None

    def _current_palette() -> dict:
        return resolve_palette(theme, _sun_is_up())

    async def _on_sun_change(event) -> None:
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        old_val = old_state.state if old_state else None
        new_val = new_state.state if new_state else None
        if old_val == new_val:
            # sun.sun updates attributes (azimuth etc.) far more often than
            # its above/below-horizon state flips — only redraw on a real flip.
            return
        await _publish_all()

    async def _sync_theme_tracking() -> None:
        unsub_prev = hass.data[DOMAIN][entry.entry_id].get("unsub_sun")
        if unsub_prev:
            unsub_prev()
            hass.data[DOMAIN][entry.entry_id]["unsub_sun"] = None
        if theme == "follow_sun":
            unsub_sun = async_track_state_change_event(hass, ["sun.sun"], _on_sun_change)
            hass.data[DOMAIN][entry.entry_id]["unsub_sun"] = unsub_sun

    # helper to publish current temp to header right label (p0b3)
    async def _publish_temp(value: str) -> None:
        await mqtt.async_publish(
            hass,
            f"hasp/{node_name}/command/p0b3.text",
            value if value else "--",
        )

    async def _push_home_layout() -> None:
        """Clear and push header/footer + home page.

        If a Page entry has claimed page_order 1, delegate to _publish_all()
        instead — that's the only path that correctly wires up its live
        entity tracking (touch routing, state-change listeners), which this
        function alone can't do without duplicating _publish_all's tail.
        """
        merged_pages = await _gather_panel_pages(hass, entry.entry_id)
        if _page1_exists(merged_pages):
            await _publish_all()
            return
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        palette = _current_palette()
        temp_text = display_state(hass.states.get(temp_entity)) if temp_entity else ""
        for obj in header_footer_objects(node_name, home_title, temp_text, palette):
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))
        page_numbers = [order for order, _, _ in merged_pages]
        ring = build_page_ring(page_numbers)
        prev_home, next_home = ring_neighbors(ring, 1)
        for obj in home_fallback_objects(prev_home, next_home, palette):
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))

    async def _publish_page_num(
        p: int,
        source: str,
        page_obj,
        ring: list,
        ctrl_map: dict,
        sensor_map: dict,
        ent_toggle_map: dict,
        ent_matrix_map: dict,
        matrix_map: dict,
        color_btn_map: dict,
        option_specs: list,
        option_open_map: dict,
        fan_status_map: dict,
        gauge_map: dict,
        alloc_option_page,
        palette: dict,
    ) -> None:
        prev_p, next_p = ring_neighbors(ring, p)
        # Clear page and draw base
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", str(p))
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl",
                                  json.dumps({"page": p, "id": 0, "obj": "page", "prev": prev_p, "next": next_p}))
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl",
                                  json.dumps(page_background(p, palette=palette)))
        # Prebuild hidden modal (legacy popup overlay bookkeeping — see
        # popup_map / popup_overlay_targets handling in _state_event)
        for obj in [
            {"page": p, "obj": "btn", "id": 193, "x": 0, "y": 0, "w": 480, "h": 480, "text": "",
             "toggle": False, "bg_color": "#000000", "bg_opa": 160, "radius": 0, "border_width": 0, "hidden": 1},
            {"page": p, "obj": "obj", "id": 194, "x": 60, "y": 120, "w": 360, "h": 240,
             "bg_color": palette["tile_bg"], "bg_opa": 255, "radius": 16, "border_width": 0, "hidden": 1},
            {"page": p, "obj": "label", "id": 195, "x": 60, "y": 132, "w": 360, "h": 32, "text": "",
             "text_font": 26, "align": "center", "text_color": palette["text"], "bg_opa": 0, "hidden": 1},
            {"page": p, "obj": "btnmatrix", "id": 196, "x": 92, "y": 176, "w": 296, "h": 96, "text_font": 20,
             "options": ["Off"], "toggle": 1, "one_check": 1, "val": 0, "radius": 10, "hidden": 1},
            {"page": p, "obj": "btn", "id": 197, "x": 316, "y": 312, "w": 92, "h": 36, "text": "Close",
             "text_font": 18, "radius": 10, "bg_color": palette["secondary_btn_bg"],
             "text_color": palette["secondary_btn_text"], "border_width": 0, "hidden": 1},
        ]:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))
        # Reset (not pre-arm) overlay bookkeeping: no popup is open right after
        # a fresh publish, so this must start empty or the very next tile tap
        # gets misread by _state_event as "dismiss the open popup" and swallowed.
        hass.data[DOMAIN][entry.entry_id].setdefault("popup_overlay_targets", {})[p] = []
        popup_map = hass.data[DOMAIN][entry.entry_id].setdefault("popup_map", {})
        popup_map[f"p{p}b193"] = {"type": "close_popup", "page": p}
        popup_map[f"p{p}b197"] = {"type": "close_popup", "page": p}

        # Draw tiles — single shared implementation (layout.render_page for
        # legacy Page entries, layout.render_tile_page for visual pages),
        # also used by the dump_layout debug export, so these can no longer
        # drift out of sync.
        if source == "legacy":
            pe = page_obj
            slot_defs = [(f"s{i}", pe.options.get(f"s{i}", "")) for i in range(1, 13)]
            icon_overrides = {f"s{i}": pe.options.get(f"s{i}_icon") for i in range(1, 13)}
            page_layout = resolve_layout(pe.options.get("layout"), slot_defs)
            render = render_page(p, page_layout, slot_defs, icon_overrides, hass.states.get, alloc_option_page, palette)
        else:
            render = render_tile_page(p, page_obj, hass.states.get, alloc_option_page, palette)

        for obj in render.objects:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))

        ctrl_map.update(render.ctrl_map)
        matrix_map.update(render.matrix_map)
        for ent, targets in render.sensor_map.items():
            sensor_map.setdefault(ent, []).extend(targets)
        for ent, targets in render.ent_toggle_map.items():
            ent_toggle_map.setdefault(ent, []).extend(targets)
        for ent, targets in render.ent_matrix_map.items():
            ent_matrix_map.setdefault(ent, []).extend(targets)
        for ent, targets in render.fan_status_map.items():
            fan_status_map.setdefault(ent, []).extend(targets)
        for ent, targets in render.gauge_map.items():
            gauge_map.setdefault(ent, []).extend(targets)
        for option_spec in render.option_specs:
            option_specs.append(option_spec)
            option_open_map[option_spec["trigger_topic"]] = option_spec

    async def _publish_option_pages(
        option_specs: list,
        ctrl_map: dict,
        ent_toggle_map: dict,
        ent_matrix_map: dict,
        matrix_map: dict,
        color_btn_map: dict,
        option_close_map: dict,
        option_page_titles: dict,
        fan_status_map: dict,
        palette: dict,
    ) -> None:
        # Visual chrome comes from the same layout.build_option_page used by
        # dump_layout; only the interactive touch-routing maps are built here.
        for spec in option_specs:
            page_id = spec["page_id"]
            origin = spec["origin_page"]
            entity = spec["entity"]
            option_page_titles[page_id] = f"{spec['friendly_name']} Options"

            await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", str(page_id))
            option_render = build_option_page(spec, palette)
            for obj in option_render.objects:
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))

            option_close_map[f"p{page_id}b{option_render.close_button_id}"] = {"return_page": origin, "entity": entity}

            if spec["type"] == "fan":
                fan_status_map.setdefault(entity, []).append((page_id, ("l", option_render.fan_status_label_id)))
                meta = {"type": "fan_select", "entity": entity}
                matrix_map[f"p{page_id}m{option_render.fan_matrix_id}"] = meta
                ent_matrix_map.setdefault(entity, []).append((page_id, option_render.fan_matrix_id, meta))

            elif spec["type"] == "light_color":
                ctrl_map[f"p{page_id}b{option_render.power_button_id}"] = entity
                ent_toggle_map.setdefault(entity, []).append((page_id, option_render.power_button_id))
                for btn_id, _hexcol, payload in option_render.color_buttons:
                    color_btn_map[f"p{page_id}b{btn_id}"] = {"entity": entity, "payload": payload, "main_btn": option_render.power_button_id}

    async def _publish_all() -> None:
        """Publish full layout based on config entities (pages, titles, slots)."""
        _LOGGER.info("Dash480: publishing all for node=%s", node_name)
        palette = _current_palette()
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        # Header/footer
        tval = display_state(hass.states.get(temp_entity) if temp_entity else None)
        for obj in header_footer_objects(node_name, home_title, tval, palette):
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))
        # Build page list from legacy Page entries + visual pages linked to this panel
        merged_pages = await _gather_panel_pages(hass, entry.entry_id)
        page_numbers = [order for order, _, _ in merged_pages]
        pages_ring = build_page_ring(page_numbers)
        # Draw the home-page fallback only if nothing has claimed order 1
        if not _page1_exists(merged_pages):
            prev_home, next_home = ring_neighbors(pages_ring, 1)
            for obj in home_fallback_objects(prev_home, next_home, palette):
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", json.dumps(obj))
        # Draw each page
        ctrl_map: dict[str, str] = {}
        sensor_map: dict[str, list[tuple[int, int]]] = {}
        matrix_map: dict[str, dict] = {}
        ent_toggle_map: dict[str, list[tuple[int, int]]] = {}
        ent_matrix_map: dict[str, list[tuple[int, int, dict]]] = {}
        color_btn_map: dict[str, dict] = {}
        fan_status_map: dict[str, list[tuple[int, tuple[str, int]]]] = {}
        gauge_map: dict[str, list[tuple[int, int, int, float, float]]] = {}
        option_specs: list[dict] = []
        option_open_map: dict[str, dict] = {}
        alloc_option_page = option_page_allocator(50)
        for p, source, page_obj in merged_pages:
            await _publish_page_num(
                p,
                source,
                page_obj,
                pages_ring,
                ctrl_map,
                sensor_map,
                ent_toggle_map,
                ent_matrix_map,
                matrix_map,
                color_btn_map,
                option_specs,
                option_open_map,
                fan_status_map,
                gauge_map,
                alloc_option_page,
                palette,
            )
        option_close_map: dict[str, dict] = {}
        option_page_titles: dict[int, str] = {}
        await _publish_option_pages(option_specs, ctrl_map, ent_toggle_map, ent_matrix_map, matrix_map, color_btn_map, option_close_map, option_page_titles, fan_status_map, palette)
        hass.data[DOMAIN][entry.entry_id]["option_open_map"] = option_open_map
        hass.data[DOMAIN][entry.entry_id]["option_close_map"] = option_close_map
        hass.data[DOMAIN][entry.entry_id]["option_page_titles"] = option_page_titles
        hass.data[DOMAIN][entry.entry_id]["option_return_map"] = {spec["page_id"]: spec["origin_page"] for spec in option_specs}
        hass.data[DOMAIN][entry.entry_id]["option_specs"] = option_specs
        hass.data[DOMAIN][entry.entry_id]["ctrl_map"] = ctrl_map
        hass.data[DOMAIN][entry.entry_id]["sensor_map"] = sensor_map
        hass.data[DOMAIN][entry.entry_id]["matrix_map"] = matrix_map
        hass.data[DOMAIN][entry.entry_id]["ent_toggle_map"] = ent_toggle_map
        hass.data[DOMAIN][entry.entry_id]["ent_matrix_map"] = ent_matrix_map
        hass.data[DOMAIN][entry.entry_id]["color_btn_map"] = color_btn_map
        hass.data[DOMAIN][entry.entry_id]["fan_status_map"] = fan_status_map
        hass.data[DOMAIN][entry.entry_id]["gauge_map"] = gauge_map
        # rewire toggle/matrix listeners
        for key in list(hass.data[DOMAIN][entry.entry_id].keys()):
            if key.startswith("unsub_ent_"):
                u = hass.data[DOMAIN][entry.entry_id].pop(key)
                try:
                    u()
                except Exception:
                    pass
        async def _sync_entity_state(entity_id: str):
            st = hass.states.get(entity_id)
            if not st:
                return
            # Update all toggle instances for this entity
            for p, bid in ent_toggle_map.get(entity_id, []):
                is_on = str(st.state).lower() == "on"
                val = "1" if is_on else "0"
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.val", val)
            # Update color tint for color-capable lights (main button text_color)
            domain = entity_id.split(".")[0]
            if domain == "fan":
                label = "Off"
                state_on = str(st.state).lower() == "on"
                if state_on:
                    preset = (st.attributes.get("preset_mode") or "").strip()
                    pct = st.attributes.get("percentage")
                    if preset:
                        label = preset.title()
                    elif isinstance(pct, (int, float)):
                        if pct <= 0:
                            label = "Off"
                        elif pct <= 33:
                            label = "Low"
                        elif pct <= 66:
                            label = "Med"
                        else:
                            label = "High"
                    else:
                        label = "On"
                for p, (obj_type, target_id) in hass.data[DOMAIN][entry.entry_id].get("fan_status_map", {}).get(entity_id, []):
                    topic = f"hasp/{node_name}/command/p{p}{obj_type}{target_id}.text"
                    await mqtt.async_publish(hass, topic, label)
            elif domain == "light":
                rgb = st.attributes.get("rgb_color")
                color_temp = st.attributes.get("color_temp_kelvin") or st.attributes.get("color_temp")
                color_hex = None
                if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
                    try:
                        color_hex = f"#{int(rgb[0]):02X}{int(rgb[1]):02X}{int(rgb[2]):02X}"
                    except Exception:
                        color_hex = None
                elif isinstance(color_temp, int):
                    color_hex = "#FFD8A8" if color_temp <= 3500 else "#D0E1FF"
                if color_hex:
                    for p, bid in ent_toggle_map.get(entity_id, []):
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.text_color", color_hex)
        # subscribe for future changes and do an initial sync
        for ent in set(list(ent_toggle_map.keys()) + list(ent_matrix_map.keys())):
            def _make_cb(eid: str):
                async def _cb(event):
                    await _sync_entity_state(eid)
                return _cb
            cb = _make_cb(ent)
            unsub = async_track_state_change_event(hass, [ent], cb)
            hass.data[DOMAIN][entry.entry_id][f"unsub_ent_{ent}"] = unsub
            await _sync_entity_state(ent)
        # rewire sensor listeners
        # remove previous
        for key in list(hass.data[DOMAIN][entry.entry_id].keys()):
            if key.startswith("unsub_sensor_"):
                u = hass.data[DOMAIN][entry.entry_id].pop(key)
                try:
                    u()
                except Exception:
                    pass
        for ent, targets in sensor_map.items():
            async def _make_cb(eid: str):
                async def _cb(event):
                    state = hass.states.get(eid)
                    val = format_calendar_summary(state) if eid.split(".")[0] == "calendar" else display_state(state)
                    for (pnum, bid) in sensor_map.get(eid, []):
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}b{bid}.text", val)
                return _cb
            cb = await _make_cb(ent)
            unsub = async_track_state_change_event(hass, [ent], cb)
            hass.data[DOMAIN][entry.entry_id][f"unsub_sensor_{ent}"] = unsub

        # rewire gauge listeners — a gauge needs both the arc's .val and the
        # value label's .text kept in sync, unlike a plain sensor's single
        # .text update, so it gets its own map/subscription pair.
        for key in list(hass.data[DOMAIN][entry.entry_id].keys()):
            if key.startswith("unsub_gauge_"):
                u = hass.data[DOMAIN][entry.entry_id].pop(key)
                try:
                    u()
                except Exception:
                    pass
        for ent in gauge_map:
            def _make_gauge_cb(eid: str):
                async def _cb(event):
                    state = hass.states.get(eid)
                    for (pnum, arc_id, label_id, gmin, gmax) in gauge_map.get(eid, []):
                        val = gauge_arc_value(state, gmin, gmax)
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}b{arc_id}.val", str(val))
                        await mqtt.async_publish(
                            hass, f"hasp/{node_name}/command/p{pnum}b{label_id}.text", gauge_display_value(state)
                        )
                return _cb
            cb = _make_gauge_cb(ent)
            unsub = async_track_state_change_event(hass, [ent], cb)
            hass.data[DOMAIN][entry.entry_id][f"unsub_gauge_{ent}"] = unsub

    # Define the callback for when the device comes online
    @callback
    def push_layout(msg):
        """Handle device online message and push full layout.
        We publish all pages on LWT=online so navigation and pages are
        consistent immediately after boot (no blank extra pages).
        """
        if msg.payload == "online":
            hass.async_create_task(_publish_all())

    # Subscribe to device LWT (online/offline)
    unsubscribe_handle = await mqtt.async_subscribe(
        hass,
        f"hasp/{node_name}/LWT",
        push_layout,
    )

    # Store the handle for later cleanup
    hass.data[DOMAIN][entry.entry_id]["unsubscribe"] = unsubscribe_handle

    # Subscribe to touch events for home relay buttons and to page changes
    @callback
    def _state_event(msg):
        topic_tail = msg.topic.split("/")[-1]
        data = None
        try:
            data = json.loads(msg.payload)
        except Exception:
            data = None
        if isinstance(data, dict):
            event = str(data.get("event", ""))
            val = data.get("val", -1)
            try:
                _LOGGER.debug("Dash480: touch %s event=%s val=%s", topic_tail, event, val)
            except Exception:
                pass
        else:
            event = ""
            val = -1
        def _queue_page(page_id: int) -> None:
            hass.async_create_task(
                mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/page",
                    str(page_id),
                )
            )

        # Relay button routing on 'up'
        if event == "up":
            # Global cooldown guard to ignore any touch for a brief period after closing a popup
            try:
                import time as _t
                if _t.monotonic() < hass.data[DOMAIN][entry.entry_id].get("popup_cooldown_until", 0.0):
                    return
            except Exception:
                pass
            option_close = hass.data[DOMAIN][entry.entry_id].get("option_close_map", {}).get(topic_tail)
            if option_close:
                return_page = option_close.get("return_page", 1)
                _queue_page(return_page)
                entity_for_sync = option_close.get("entity")
                if entity_for_sync:
                    hass.async_create_task(_sync_entity_state(entity_for_sync))
                return
            option_open = hass.data[DOMAIN][entry.entry_id].get("option_open_map", {}).get(topic_tail)
            if option_open:
                target_page = option_open.get("page_id")
                _queue_page(target_page)
                entity_for_sync = option_open.get("entity")
                if entity_for_sync:
                    hass.async_create_task(_sync_entity_state(entity_for_sync))
                return
            # If an overlay is visible on this page, consume any non-overlay tap to close it
            pnum = None; tchar = None; oid = None
            if topic_tail.startswith("p"):
                s = topic_tail[1:]
                i = 0
                while i < len(s) and s[i].isdigit():
                    i += 1
                if i > 0 and i < len(s):
                    try:
                        pnum = int(s[:i])
                        tchar = s[i]
                        oid = int(s[i+1:]) if s[i+1:].isdigit() else None
                    except Exception:
                        pnum = None
            if isinstance(pnum, int):
                targets = hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(pnum, [])
                if targets and (tchar, oid) not in targets:
                    for (typ, ooid) in list(targets):
                        try:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}{typ}{ooid}.hidden", "1"))
                        except Exception:
                            pass
                    # Clear overlay bookkeeping
                    try:
                        hass.data[DOMAIN][entry.entry_id]["popup_overlay_targets"][pnum] = []
                        hass.data[DOMAIN][entry.entry_id].get("matrix_map", {}).pop(f"p{pnum}m196", None)
                    except Exception:
                        pass
                    try:
                        import time as _t
                        hass.data[DOMAIN][entry.entry_id]["popup_cooldown_until"] = _t.monotonic() + 0.35
                    except Exception:
                        pass
                    return
            # Popup routing
            pm = hass.data[DOMAIN][entry.entry_id].get("popup_map", {}).get(topic_tail)
            if pm:
                # Close actions first
                if pm.get("type") == "close_popup":
                    pg = pm.get("page")
                    for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(pg, []):
                        try:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pg}{typ}{oid}.hidden", "1"))
                        except Exception:
                            pass
                    # Clear overlay bookkeeping
                    try:
                        hass.data[DOMAIN][entry.entry_id]["popup_overlay_targets"][pg] = []
                        hass.data[DOMAIN][entry.entry_id].get("matrix_map", {}).pop(f"p{pg}m196", None)
                    except Exception:
                        pass
                    # Cooldown to prevent re-open
                    try:
                        import time as _t
                        hass.data[DOMAIN][entry.entry_id]["popup_cooldown_until"] = _t.monotonic() + 0.35
                    except Exception:
                        pass
                    return
                # Open actions (fan speed or light color)
                if pm.get("type") not in ("fan_select", "light_color"):
                    # Not a popup open, continue
                    pass
                else:
                    # Guard against immediate reopen after a close
                    try:
                        import time as _t
                        if _t.monotonic() < hass.data[DOMAIN][entry.entry_id].get("popup_cooldown_until", 0.0):
                            return
                    except Exception:
                        pass
                    try:
                        p = int(topic_tail.split("b")[0].replace("p", ""))
                    except Exception:
                        p = pm.get("page") or 1
                    ent = pm.get("entity")
                    kind = pm.get("type")
                    btn_id = pm.get("btn_id")
                # Hide any existing popup overlays for this page
                for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(p, []):
                    try:
                        hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}{typ}{oid}.hidden", "1"))
                    except Exception:
                        pass
                # Overlay ids: use fixed ids per page to avoid >255
                base_overlay = 193
                bg_id = base_overlay + 0
                box_id = base_overlay + 1
                title_id = base_overlay + 2
                matrix_id = base_overlay + 3
                close_id = base_overlay + 4
                hass.data[DOMAIN][entry.entry_id].setdefault("popup_overlay_targets", {}).setdefault(p, []).clear()
                hass.data[DOMAIN][entry.entry_id]["popup_overlay_targets"][p].extend([
                    ("b", bg_id),
                    ("o", box_id),
                    ("l", title_id),
                    ("m", matrix_id),
                    ("b", close_id),
                ])
                # Prebuilt overlay: update title/options, then unhide elements
                title = "Fan Speed" if kind == "fan_select" else "Light Color"
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}l{title_id}.text", title))
                if kind == "fan_select":
                    # Update matrix options
                    hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"btnmatrix","id":{matrix_id},"options":["Off","Low","Med","High"],"val":0}}'))
                    meta = {"type": "fan_select", "entity": ent}
                else:
                    hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"btnmatrix","id":{matrix_id},"options":["Off","Red","Green","Blue","Warm","Cool"],"val":0}}'))
                    meta = {"type": "light_color", "entity": ent, "btn_id": btn_id}
                hass.data[DOMAIN][entry.entry_id].setdefault("matrix_map", {})[f"p{p}m{matrix_id}"] = meta
                # Unhide all overlay parts
                for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(p, [("b",193),("o",194),("l",195),("m",196),("b",197)]):
                    hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}{typ}{oid}.hidden", "0"))
                return
            # Home relays (page 1 IDs moved into 100..199 range)
            if topic_tail == "p1b112":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output1", payload))
            elif topic_tail == "p1b122":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output2", payload))
            elif topic_tail == "p1b132":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output40", payload))
            else:
                # Color chip handling
                cmeta = hass.data[DOMAIN][entry.entry_id].get("color_btn_map", {}).get(topic_tail)
                if cmeta:
                    ent = cmeta["entity"]
                    payload = cmeta.get("payload", {})
                    # Always turn on when selecting a color
                    data = {"entity_id": ent}
                    data.update(payload)
                    hass.async_create_task(hass.services.async_call("light", "turn_on", data))
                    # Visually set the main power button to on
                    try:
                        pnum = int(topic_tail.split("b")[0].replace("p",""))
                        main_btn = cmeta.get("main_btn")
                        if main_btn:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}b{main_btn}.val", "1"))
                    except Exception:
                        pass
                    return
                # Generic tile routing based on ctrl_map
                ent = hass.data[DOMAIN][entry.entry_id].get("ctrl_map", {}).get(topic_tail)
                if ent:
                    domain = ent.split(".")[0]
                    if domain == "switch":
                        svc = "turn_on" if val == 1 else "turn_off"
                        hass.async_create_task(hass.services.async_call("switch", svc, {"entity_id": ent}))
                    elif domain == "light":
                        svc = "turn_on" if val == 1 else "turn_off"
                        hass.async_create_task(hass.services.async_call("light", svc, {"entity_id": ent}))
                    elif domain == "fan":
                        if val == 1:
                            hass.async_create_task(hass.services.async_call("fan", "turn_on", {"entity_id": ent}))
                        else:
                            hass.async_create_task(hass.services.async_call("fan", "turn_off", {"entity_id": ent}))
                # Popup close handling
                pm2 = hass.data[DOMAIN][entry.entry_id].get("popup_map", {}).get(topic_tail)
                if pm2 and pm2.get("type") == "close_popup":
                    pg = pm2.get("page")
                    # Hide any known overlay targets in this page's range
                    for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(pg, []):
                        try:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pg}{typ}{oid}.hidden", "1"))
                        except Exception:
                            pass
                    # Short cooldown to avoid accidental reopen
                    try:
                        import time as _t
                        hass.data[DOMAIN][entry.entry_id]["popup_cooldown_until"] = _t.monotonic() + 0.35
                    except Exception:
                        pass
                    return
                    # Start a short cooldown to avoid unintended popup re-open
                    try:
                        hass.data[DOMAIN][entry.entry_id]["popup_cooldown_until"] = time.monotonic() + 0.35
                    except Exception:
                        pass
        # Matrices (popup selections)
        if topic_tail.startswith("p") and ("m" in topic_tail) and (event in ("up", "changed")):
            m = hass.data[DOMAIN][entry.entry_id].get("matrix_map", {}).get(topic_tail)
            if m:
                ent = m["entity"]
                if m["type"] == "fan_select":
                    pct_map = {0: 0, 1: 33, 2: 66, 3: 100}
                    pct = pct_map.get(int(val), 0)
                    if pct == 0:
                        hass.async_create_task(hass.services.async_call("fan", "turn_off", {"entity_id": ent}))
                    else:
                        hass.async_create_task(hass.services.async_call("fan", "set_percentage", {"entity_id": ent, "percentage": pct}))
                    # Hide popup overlay after selection
                    try:
                        p = int(topic_tail.split("m")[0].replace("p", ""))
                    except Exception:
                        p = 1
                    for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(p, []):
                        try:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}{typ}{oid}.hidden", "1"))
                        except Exception:
                            pass
                elif m["type"] == "light_color":
                    # 0..5 => Off, Red, Green, Blue, Warm, Cool
                    idx = int(val)
                    if idx == 0:
                        hass.async_create_task(hass.services.async_call("light", "turn_off", {"entity_id": ent}))
                        color_hex = None
                    elif idx == 1:
                        hass.async_create_task(hass.services.async_call("light", "turn_on", {"entity_id": ent, "rgb_color": [255, 0, 0]}))
                        color_hex = "#FF0000"
                    elif idx == 2:
                        hass.async_create_task(hass.services.async_call("light", "turn_on", {"entity_id": ent, "rgb_color": [0, 255, 0]}))
                        color_hex = "#00FF00"
                    elif idx == 3:
                        hass.async_create_task(hass.services.async_call("light", "turn_on", {"entity_id": ent, "rgb_color": [0, 0, 255]}))
                        color_hex = "#0000FF"
                    elif idx == 4:
                        hass.async_create_task(hass.services.async_call("light", "turn_on", {"entity_id": ent, "color_temp_kelvin": 2700}))
                        color_hex = "#FFD8A8"
                    else:
                        hass.async_create_task(hass.services.async_call("light", "turn_on", {"entity_id": ent, "color_temp_kelvin": 6500}))
                        color_hex = "#D0E1FF"
                    # Update main button tint if known
                    bid = m.get("btn_id")
                    try:
                        p = int(topic_tail.split("m")[0].replace("p", ""))
                    except Exception:
                        p = 1
                    if bid:
                        if color_hex:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.text_color", color_hex))
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.val", "1"))
                        else:
                            # Off => reset to default tile toggle-button text color
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.text_color", _current_palette()["toggle_btn_text"]))
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.val", "0"))
                    # Hide overlay
                    for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(p, []):
                        try:
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}{typ}{oid}.hidden", "1"))
                        except Exception:
                            pass
                elif m["type"] == "cover_cmd":
                    idx = int(val)
                    svc = "open_cover" if idx == 0 else "stop_cover" if idx == 1 else "close_cover"
                    hass.async_create_task(hass.services.async_call("cover", svc, {"entity_id": ent}))
        # Title on page change and ensure any popups are hidden
        if topic_tail == "page":
            page = str(msg.payload)
            if page.isdigit():
                p = int(page)
                # Track current page
                hass.data[DOMAIN][entry.entry_id]["current_page"] = p
                # Resolve title from Page entries map or option pages
                option_title = hass.data[DOMAIN][entry.entry_id].get("option_page_titles", {}).get(p)
                if option_title:
                    title = option_title
                else:
                    all_entries = hass.config_entries.async_entries(DOMAIN)
                    page_entry = next((e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == entry.entry_id and int(e.data.get("page_order", 0)) == p), None)
                    if page_entry is not None:
                        title = page_entry.options.get("title", f"Page {p}")
                    else:
                        # Not a legacy Page entry — check visual pages (the
                        # store is already loaded by this point since a page
                        # can only be navigated to after being published).
                        visual_page = next(
                            (vp for vp in async_get_store(hass).list_pages(entry.entry_id)
                             if int(vp.get("page_order", -1)) == p),
                            None,
                        )
                        if visual_page is not None:
                            title = visual_page.get("title", f"Page {p}")
                        else:
                            title = home_title if p == 1 else f"Page {p}"
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", title))
                # Defensive: hide any overlay remnants on this page (within page block)
                for (typ, oid) in hass.data[DOMAIN][entry.entry_id].get("popup_overlay_targets", {}).get(p, []):
                    try:
                        hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}{typ}{oid}.hidden", "1"))
                    except Exception:
                        pass
        # Long-press on header title rebuilds current page
        if topic_tail == "p0b2" and event == "long":
            # Rebuild full layout to keep maps in sync
            hass.async_create_task(_publish_all())

    unsub_events = await mqtt.async_subscribe(hass, f"hasp/{node_name}/state/#", _state_event)
    hass.data[DOMAIN][entry.entry_id]["unsub_events"] = unsub_events

    # Track temp entity changes
    async def _on_temp_change(event):
        if not temp_entity:
            return
        await _publish_temp(display_state(hass.states.get(temp_entity)))

    if temp_entity:
        unsub_temp = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
        hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp

    # Arm sun tracking immediately if this panel starts in follow_sun mode.
    await _sync_theme_tracking()

    # React to options changes (from Configure dialog or services)
    async def _options_updated(hass_: HomeAssistant, updated: ConfigEntry):
        nonlocal home_title, temp_entity, theme
        home_title = updated.options.get("home_title", updated.data.get("node_name", "Dash"))
        new_temp = updated.options.get("temp_entity", "")
        if new_temp != temp_entity:
            # resubscribe to temp entity changes
            unsub_prev = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
            if unsub_prev:
                unsub_prev()
                hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = None
            temp_entity = new_temp
            if temp_entity:
                unsub_new = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
                hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_new
            # push current temp immediately
            await _publish_temp(display_state(hass.states.get(temp_entity) if temp_entity else None))
        # Update title immediately
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title)
        new_theme = updated.options.get("theme", "dark")
        if new_theme != theme:
            theme = new_theme
            await _sync_theme_tracking()
            await _publish_all()

    unsub_update = entry.add_update_listener(_options_updated)
    hass.data[DOMAIN][entry.entry_id]["unsub_update"] = unsub_update

    # Services: allow setting options and forcing a publish when UI Configure is unavailable
    async def _resolve_entry(call: ServiceCall) -> ConfigEntry | None:
        eid = call.data.get("entry_id")
        if eid:
            return hass.config_entries.async_get_entry(eid)
        # default to this entry if only one exists for our domain
        entries = [e for e in hass.config_entries.async_entries(DOMAIN)]
        if len(entries) == 1:
            return entries[0]
        return None

    async def _svc_set_home_title(call: ServiceCall):
        nonlocal home_title
        e = await _resolve_entry(call)
        if not e:
            return
        title = str(call.data.get("home_title", "")).strip()
        # Persist on entry options
        new_opts = {**e.options, "home_title": title or e.data.get("node_name", "Dash")}
        hass.config_entries.async_update_entry(e, options=new_opts)
        # Update local cache and live header immediately
        home_title = new_opts["home_title"]
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title)

    async def _svc_set_temp_entity(call: ServiceCall):
        nonlocal temp_entity
        e = await _resolve_entry(call)
        if not e:
            return
        temp = str(call.data.get("temp_entity", "")).strip()
        new_opts = {**e.options, "temp_entity": temp}
        hass.config_entries.async_update_entry(e, options=new_opts)
        # Update subscription to new entity and push current value to header
        temp_entity = temp
        # tear down old tracker if present
        unsub_temp_prev = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
        if unsub_temp_prev:
            unsub_temp_prev()
            hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = None
        # publish current value
        await _publish_temp(display_state(hass.states.get(temp_entity) if temp_entity else None))
        # re-subscribe for future updates
        if temp_entity:
            unsub_temp_new = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
            hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp_new

    async def _svc_publish_home(call: ServiceCall):
        await _push_home_layout()

    # Note: Services are registered at component level in async_setup().

    # Register publishers for component-level services
    hass.data[DOMAIN].setdefault("publishers", {})[entry.entry_id] = {
        "publish_all": _publish_all,
        "publish_home": _push_home_layout,
    }
    # Forward the setup to the platforms.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from the MQTT topic
    unsubscribe_handle = hass.data[DOMAIN][entry.entry_id].get("unsubscribe")
    if unsubscribe_handle:
        unsubscribe_handle()
    unsub_events = hass.data[DOMAIN][entry.entry_id].get("unsub_events")
    if unsub_events:
        unsub_events()
    unsub_temp = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
    if unsub_temp:
        unsub_temp()
    unsub_sun = hass.data[DOMAIN][entry.entry_id].get("unsub_sun")
    if unsub_sun:
        unsub_sun()
    unsub_update = hass.data[DOMAIN][entry.entry_id].get("unsub_update")
    if unsub_update:
        unsub_update()
    # Remove publishers
    pubs = hass.data.get(DOMAIN, {}).get("publishers", {})
    if entry.entry_id in pubs:
        pubs.pop(entry.entry_id, None)

    # Forward the unload to the platforms.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up the hass.data entry
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
