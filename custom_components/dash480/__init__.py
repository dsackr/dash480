"""The Dash480 integration."""
from __future__ import annotations

import json
import logging
import os
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 3x3 grid tile layout helpers
# Each layout maps to a list of tile specs with:
# - row, col: 0-based grid position
# - rs, cs: row-span and col-span (defaults 1)
# - special: optional (e.g., "clock")
LAYOUT_TEMPLATES: dict[str, list[dict]] = {
    # 6 tiles (3x2)
    "grid_3x2": [
        {"row": 0, "col": 0}, {"row": 0, "col": 1}, {"row": 0, "col": 2},
        {"row": 1, "col": 0}, {"row": 1, "col": 1}, {"row": 1, "col": 2},
    ],
    # 9 tiles of size 1x1 (legacy)
    "grid_3x3": [
        {"row": 0, "col": 0}, {"row": 0, "col": 1}, {"row": 0, "col": 2},
        {"row": 1, "col": 0}, {"row": 1, "col": 1}, {"row": 1, "col": 2},
        {"row": 2, "col": 0}, {"row": 2, "col": 1}, {"row": 2, "col": 2},
    ],
    # Top row is a full-width special clock tile; remaining 6 are 1x1
    "clock_top": [
        {"row": 0, "col": 0, "cs": 3, "rs": 1, "special": "clock"},
        {"row": 1, "col": 0}, {"row": 1, "col": 1}, {"row": 1, "col": 2},
        {"row": 2, "col": 0}, {"row": 2, "col": 1}, {"row": 2, "col": 2},
    ],
    "shades_row": [
        {"row": 0, "col": 0}, {"row": 0, "col": 1}, {"row": 0, "col": 2},
        {"row": 1, "col": 0}, {"row": 1, "col": 1}, {"row": 1, "col": 2},
        {"row": 2, "col": 0, "cs": 3, "rs": 1, "special": "shades"},
    ],
}

def _tile_specs_for_layout(layout: str) -> list[dict]:
    return LAYOUT_TEMPLATES.get(layout or "", LAYOUT_TEMPLATES["grid_3x3"]).copy()

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
        """Build the full JSONL layout and dump to a file (no publish)."""
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
        # Header/footer
        lines: list[str] = []
        def _home_lines(title: str, temp_text: str) -> list[str]:
            return _home_layout_lines(node_name, title, temp_text)
        st = hass.states.get(temp_entity) if temp_entity else None
        tval = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            tval = str(st.state)
        lines.extend(_home_lines(home_title, tval))
        # Pages
        all_entries = hass.config_entries.async_entries(DOMAIN)
        page_entries = [e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == eid]
        page_entries.sort(key=lambda e: int(e.data.get("page_order", 99)))
        page_numbers = [int(e.data.get("page_order", 99)) for e in page_entries]
        pages_ring = [1] + page_numbers
        if page_numbers:
            prev_home = page_numbers[-1]
            next_home = page_numbers[0]
            lines.append(f'{{"page":1,"id":0,"obj":"page","prev":{prev_home},"next":{next_home}}}')

        def pprev(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx - 1) % len(pages_ring)]

        def pnext(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx + 1) % len(pages_ring)]

        option_specs: list[dict] = []
        next_option_page = 50

        def alloc_option_page() -> int:
            nonlocal next_option_page
            pid = next_option_page
            next_option_page += 1
            return pid

        for pe in page_entries:
            p = int(pe.data.get("page_order", 99))
            lines.append(f'{{"page":{p},"id":0,"obj":"page","prev":{pprev(p)},"next":{pnext(p)}}}')
            lines.append(f'{{"page":{p},"obj":"obj","id":80,"x":0,"y":0,"w":480,"h":480,"bg_color":"#0B1220","bg_opa":255,"click":false}}')

            layout = pe.options.get("layout")
            slot_defs = [(f"s{i}", pe.options.get(f"s{i}", "")) for i in range(1, 13)]
            if layout != "shades_row" and any(ent and ent.split(".")[0] == "cover" for _, ent in slot_defs):
                layout = "shades_row"
            if not layout:
                layout = "grid_3x2"
            tiles = _tile_specs_for_layout(layout)

            filled_slots = [(key, ent) for key, ent in slot_defs if ent]
            assignments: list[tuple[dict, tuple[str, str] | None]] = []
            if layout == "shades_row":
                cover_queue = [(k, e) for (k, e) in filled_slots if e.split(".")[0] == "cover"]
                other_queue = [(k, e) for (k, e) in filled_slots if e.split(".")[0] != "cover"]
                for spec in tiles:
                    if spec.get("special") == "shades":
                        slot = cover_queue.pop(0) if cover_queue else (other_queue.pop(0) if other_queue else None)
                    else:
                        slot = other_queue.pop(0) if other_queue else (cover_queue.pop(0) if cover_queue else None)
                    assignments.append((spec, slot))
            else:
                queue = filled_slots.copy()
                for spec in tiles:
                    slot = queue.pop(0) if queue else None
                    assignments.append((spec, slot))

            render_index = 1
            base_x = 24
            base_y = 120
            col_step = 128 + 24
            row_step = 120 + 20

            def cell_xy(row: int, col: int) -> tuple[int, int]:
                return (base_x + col * col_step, base_y + row * row_step)

            def cell_wh(rs: int, cs: int) -> tuple[int, int]:
                width = 128 * cs + 24 * (cs - 1)
                height = (120 * rs) + 20 * (rs - 1)
                return width, height
            for spec, slot in assignments:
                if not slot:
                    continue
                rs = int(spec.get("rs", 1))
                cs = int(spec.get("cs", 1))
                row = int(spec.get("row", 0))
                col = int(spec.get("col", 0))
                x, y = cell_xy(row, col)
                w, h = cell_wh(rs, cs)
                if spec.get("special") == "clock":
                    lines.append(f'{{"page":{p},"obj":"label","id":70,"x":{x},"y":{y+4},"w":{w},"h":{h-8},"text":"00:00","template":"%H:%M","text_font":96,"align":"center","text_color":"#E5E7EB","bg_opa":0}}')
                    continue
                key, ent = slot
                slot_digit = min(render_index, 9)
                base = slot_digit * 10
                render_index += 1
                st_ent = hass.states.get(ent)
                label = st_ent.attributes.get("friendly_name", ent) if st_ent else ent
                special = spec.get("special")
                if special == "shades":
                    full_x = cell_xy(row, 0)[0]
                    full_w = cell_wh(1, 3)[0]
                    full_y = y + (h - 88) // 2
                    lines.append(f'{{"page":{p},"obj":"obj","id":{base+5},"x":{full_x},"y":{full_y},"w":{full_w},"h":88,"radius":18,"bg_color":"#0B1220"}}')
                    lines.append(f'{{"page":{p},"obj":"label","id":{base+6},"x":{full_x+18},"y":{full_y+12},"w":{full_w-36},"h":24,"text":"{label}","text_font":20,"text_color":"#9CA3AF","bg_opa":0}}')
                    lines.append(f'{{"page":{p},"obj":"btnmatrix","id":{base+7},"x":{full_x+30},"y":{full_y+42},"w":{full_w-60},"h":56,"text_font":28,"options":["Up","Pause","Down"],"one_check":0,"radius":12}}')
                    continue

                lines.append(f'{{"page":{p},"obj":"obj","id":{base+1},"x":{x},"y":{y},"w":{w},"h":{h},"radius":14,"bg_color":"#1E293B","bg_opa":255,"click":false}}')
                lines.append(f'{{"page":{p},"obj":"label","id":{base},"x":{x+8},"y":{y+6},"w":{w-16},"h":24,"text":"{label}","text_font":18,"text_color":"#9CA3AF","bg_opa":0}}')
                domain = ent.split(".")[0]
                if domain in ("switch", "light", "fan"):
                    icon = "\\uE4DC" if domain == "fan" else "\\uE425"
                    lines.append(f'{{"page":{p},"obj":"btn","id":{base+2},"x":{x + max(20,(w-96)//2)},"y":{y+36},"w":96,"h":72,"text":"{icon}","text_font":72,"toggle":true,"radius":14,"bg_color":"#1E293B","bg_opa":255,"text_color":"#FFFFFF","border_width":0}}')
                    if domain == "fan":
                        lines.append(f'{{"page":{p},"obj":"label","id":{base+3},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"Tap for speed","text_font":20,"align":"center","text_color":"#9CA3AF","bg_opa":0,"click":false}}')
                        option_specs.append({
                            "entity": ent,
                            "type": "fan",
                            "origin_page": p,
                            "page_id": alloc_option_page(),
                            "friendly_name": label,
                            "trigger_topic": f"p{p}b{base+2}",
                        })
                    elif domain == "light" and st_ent and st_ent.attributes.get("supported_color_modes"):
                        modes = st_ent.attributes.get("supported_color_modes", [])
                        mode_str = ",".join(modes).lower()
                        has_color = any(m in mode_str for m in ("hs", "rgb", "rgbw", "rgbww"))
                        if has_color:
                            lines.append(f'{{"page":{p},"obj":"label","id":{base+3},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"Tap for color","text_font":20,"align":"center","text_color":"#9CA3AF","bg_opa":0,"click":false}}')
                            option_specs.append({
                                "entity": ent,
                                "type": "light_color",
                                "origin_page": p,
                                "page_id": alloc_option_page(),
                                "friendly_name": label,
                                "trigger_topic": f"p{p}b{base+2}",
                            })
                elif domain == "sensor":
                    val = st_ent.state if st_ent and st_ent.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                    lines.append(f'{{"page":{p},"obj":"btn","id":{base+2},"x":{x + max(20,(w-88)//2)},"y":{y+40},"w":88,"h":64,"text":"{val}","text_font":20,"toggle":false,"bg_opa":0,"border_width":0,"radius":0}}')
                else:
                    val = st_ent.state if st_ent and st_ent.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                    lines.append(f'{{"page":{p},"obj":"btn","id":{base+2},"x":{x + max(20,(w-88)//2)},"y":{y+40},"w":88,"h":64,"text":"{val}","text_font":20,"toggle":false,"bg_opa":0,"border_width":0,"radius":0}}')

        # Emit option pages after main pages
        def _emit_option_pages():
            for spec in option_specs:
                page_id = spec["page_id"]
                origin = spec["origin_page"]
                entity = spec["entity"]
                friendly = spec["friendly_name"]
                opt_type = spec["type"]
                lines.append(f'{{"page":{page_id},"id":0,"obj":"page","prev":{origin},"next":{origin}}}')
                lines.append(f'{{"page":{page_id},"obj":"obj","id":10,"x":0,"y":0,"w":480,"h":480,"bg_color":"#0B1220","bg_opa":255,"click":false}}')
                lines.append(f'{{"page":{page_id},"obj":"label","id":11,"x":24,"y":24,"w":432,"h":48,"text":"{friendly}","text_font":36,"align":"center","text_color":"#E5E7EB","bg_opa":0}}')
                lines.append(f'{{"page":{page_id},"obj":"btn","id":190,"x":360,"y":24,"w":96,"h":48,"text":"Close","text_font":24,"radius":12,"bg_color":"#1F2937","text_color":"#FFFFFF","border_width":0}}')

                if opt_type == "fan":
                    lines.append(f'{{"page":{page_id},"obj":"label","id":40,"x":24,"y":96,"w":432,"h":36,"text":"--","text_font":28,"align":"center","text_color":"#9CA3AF","bg_opa":0}}')
                    lines.append(f'{{"page":{page_id},"obj":"btnmatrix","id":60,"x":72,"y":168,"w":336,"h":144,"text_font":32,"options":["Off","Low","Med","High"],"toggle":1,"one_check":1,"val":0,"radius":16}}')
                elif opt_type == "light_color":
                    lines.append(f'{{"page":{page_id},"obj":"btn","id":40,"x":168,"y":108,"w":144,"h":72,"text":"Power","text_font":30,"toggle":1,"radius":14,"bg_color":"#1E293B","bg_opa":255,"text_color":"#FFFFFF","border_width":0}}')
                    colors = [
                        ("#FFFFFF", "White"),
                        ("#FF0000", "Red"),
                        ("#00FF00", "Green"),
                        ("#0000FF", "Blue"),
                        ("#FDE68A", "Warm"),
                        ("#D0E1FF", "Cool"),
                    ]
                    btn_id = 80
                    start_x = 72
                    start_y = 216
                    btn_w = 96
                    btn_h = 96
                    gap = 24
                    for idx, (hexcol, label_text) in enumerate(colors):
                        cx = start_x + (idx % 3) * (btn_w + gap)
                        cy = start_y + (idx // 3) * (btn_h + 40)
                        lines.append(f'{{"page":{page_id},"obj":"btn","id":{btn_id},"x":{cx},"y":{cy},"w":{btn_w},"h":{btn_h},"radius":16,"bg_color":"{hexcol}","text":"{label_text}","text_font":22,"bg_grad_dir":"none","border_width":0}}')
                        btn_id += 1

        _emit_option_pages()

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

    store["services_registered"] = True
    return True

# List of platforms to support.
PLATFORMS = ["switch", "text", "number", "button", "select"]
PLATFORMS_PAGE = ["text", "button", "select"]

def _home_layout_lines(node_name: str, title: str, temp_text: str) -> list[str]:
    """Build JSONL lines for header/footer and home page with 3 relays."""
    lines: list[str] = []
    # Ensure page 0 and 1 exist
    lines.append('{"page":0,"id":0,"obj":"page"}')
    # Define page 1 without prev/next; navigation is set later by publisher when pages are known
    lines.append('{"page":1,"id":0,"obj":"page"}')
    # Header (page 0)
    lines.append('{"page":0,"id":10,"obj":"obj","x":0,"y":0,"w":480,"h":56,"bg_color":"#1F2937","bg_opa":255,"radius":0,"border_width":0,"bg_grad_dir":"none","outline_width":0,"shadow_width":0}')
    # Header left: date (replaces small clock)
    lines.append('{"page":0,"id":1,"obj":"label","x":12,"y":8,"w":120,"h":40,"text":"--","template":"%b %d","text_font":35,"align":"left","text_color":"#E5E7EB","bg_opa":0}')
    # Center title (p0b2)
    t = title.replace('"', '\\"')
    lines.append(f'{{"page":0,"id":2,"obj":"btn","x":140,"y":8,"w":200,"h":40,"text":"{t}","text_font":35,"text_color":"#FFFFFF","bg_opa":0,"border_width":0,"radius":0,"outline_width":0,"shadow_width":0,"toggle":false}}')
    # Right temp (p0b3)
    tt = temp_text.replace('"', '\\"') if temp_text else "--"
    lines.append(f'{{"page":0,"id":3,"obj":"btn","x":320,"y":8,"w":148,"h":40,"text":"{tt}","text_font":24,"align":"right","text_color":"#E5E7EB","bg_opa":0,"border_width":0,"radius":0,"outline_width":0,"shadow_width":0,"toggle":false}}')
    # Footer navigation (page 0) — span full 480px (3x160)
    lines.append('{"page":0,"id":90,"obj":"btn","action":{"down": "page prev"},"x":0,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE141","text_color":"#FFFFFF","radius":0,"border_side":0,"border_width":0,"bg_grad_dir":"none","outline_width":0,"shadow_width":0,"text_font":48}')
    lines.append('{"page":0,"id":91,"obj":"btn","action":{"down": "page 1"},"x":160,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE2DC","text_color":"#FFFFFF","radius":0,"border_side":0,"border_width":0,"bg_grad_dir":"none","outline_width":0,"shadow_width":0,"text_font":48}')
    lines.append('{"page":0,"id":92,"obj":"btn","action":{"down": "page next"},"x":320,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE142","text_color":"#FFFFFF","radius":0,"border_side":0,"border_width":0,"bg_grad_dir":"none","outline_width":0,"shadow_width":0,"text_font":48}')
    # Home page background area (use ID within 100..199 range)
    lines.append('{"page":1,"obj":"obj","id":180,"x":0,"y":0,"w":480,"h":480,"bg_color":"#0B1220","bg_opa":255,"click":false}')
    # Large digital clock just below the header
    lines.append('{"page":1,"obj":"label","id":100,"x":0,"y":72,"w":480,"h":96,"text":"00:00","template":"%H:%M","text_font":96,"align":"center","text_color":"#E5E7EB","bg_opa":0}')
    # Three relay buttons within 100..199 range (112/122/132)
    lines.append('{"page":1,"obj":"btn","id":112,"x":25,"y":300,"w":120,"h":60,"text":"Relay 1","text_font":26,"toggle":true,"groupid":1,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":122,"x":175,"y":300,"w":120,"h":60,"text":"Relay 2","text_font":26,"toggle":true,"groupid":2,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":132,"x":325,"y":300,"w":120,"h":60,"text":"Relay 3","text_font":26,"toggle":true,"groupid":3,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    return lines


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
    # control map (id -> entity_id) and sensor text map (entity -> list of (page,id))
    hass.data[DOMAIN][entry.entry_id]["ctrl_map"] = {}
    hass.data[DOMAIN][entry.entry_id]["sensor_map"] = {}

    # helper to publish current temp to header right label (p0b3)
    async def _publish_temp(value: str) -> None:
        await mqtt.async_publish(
            hass,
            f"hasp/{node_name}/command/p0b3.text",
            value if value else "--",
        )

    async def _push_home_layout() -> None:
        """Clear and push header/footer + home relays."""
        # Clear existing pages first
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        temp_text = ""
        if temp_entity:
            st = hass.states.get(temp_entity)
            if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
                temp_text = str(st.state)
        lines = _home_layout_lines(node_name, home_title, temp_text)
        for line in lines:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", line)

    async def _publish_page_num(
        p: int,
        pe,
        ctrl_map: dict,
        sensor_map: dict,
        ent_toggle_map: dict,
        ent_matrix_map: dict,
        matrix_map: dict,
        color_btn_map: dict,
        option_specs: list,
        option_open_map: dict,
        fan_status_map: dict,
        alloc_option_page,
    ) -> None:
        # Compute prev/next based on current configured pages
        all_entries = hass.config_entries.async_entries(DOMAIN)
        page_entries = [e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == entry.entry_id]
        page_entries.sort(key=lambda e: int(e.data.get("page_order", 99)))
        nums = [int(e.data.get("page_order", 99)) for e in page_entries]
        ring = [1] + nums
        def pprev(pp):
            i = ring.index(pp); return ring[(i-1) % len(ring)]
        def pnext(pp):
            i = ring.index(pp); return ring[(i+1) % len(ring)]
        # Clear page and draw base
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", str(p))
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"id":0,"obj":"page","prev":{pprev(p)},"next":{pnext(p)}}}')
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"obj","id":80,"x":0,"y":0,"w":480,"h":480,"bg_color":"#0B1220","bg_opa":255,"click":false}}')
        # Prebuild hidden modal
        for line in [
            f'{{"page":{p},"obj":"btn","id":193,"x":0,"y":0,"w":480,"h":480,"text":"","toggle":false,"bg_color":"#000000","bg_opa":160,"radius":0,"border_width":0,"hidden":1}}',
            f'{{"page":{p},"obj":"obj","id":194,"x":60,"y":120,"w":360,"h":240,"bg_color":"#1E293B","bg_opa":255,"radius":16,"border_width":0,"hidden":1}}',
            f'{{"page":{p},"obj":"label","id":195,"x":60,"y":132,"w":360,"h":32,"text":"","text_font":26,"align":"center","text_color":"#E5E7EB","bg_opa":0,"hidden":1}}',
            f'{{"page":{p},"obj":"btnmatrix","id":196,"x":92,"y":176,"w":296,"h":96,"text_font":20,"options":["Off"],"toggle":1,"one_check":1,"val":0,"radius":10,"hidden":1}}',
            f'{{"page":{p},"obj":"btn","id":197,"x":316,"y":312,"w":92,"h":36,"text":"Close","text_font":18,"radius":10,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0,"hidden":1}}',
        ]:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", line)
        hass.data[DOMAIN][entry.entry_id].setdefault("popup_overlay_targets", {})[p] = [("b",193),("o",194),("l",195),("m",196),("b",197)]
        popup_map = hass.data[DOMAIN][entry.entry_id].setdefault("popup_map", {})
        popup_map[f"p{p}b193"] = {"type": "close_popup", "page": p}
        popup_map[f"p{p}b197"] = {"type": "close_popup", "page": p}
        # Draw tiles (reuse logic in _publish_all path)
        # Auto-select layout when unspecified so covers get full-width row controls
        layout = pe.options.get("layout")
        slots_all = [(f"s{i}", pe.options.get(f"s{i}", "")) for i in range(1, 13)]
        if layout != "shades_row":
            if any(ent and ent.split(".")[0] == "cover" for _, ent in slots_all):
                layout = "shades_row"
        if not layout:
            layout = "grid_3x2"
        tiles = _tile_specs_for_layout(layout)
        # Pair layout slots with configured entities, preferring the shades row for covers
        filled_slots = [(key, ent) for key, ent in slots_all if ent]
        assignments: list[tuple[dict, tuple[str, str] | None]] = []
        if layout == "shades_row":
            cover_queue = [(k, e) for (k, e) in filled_slots if e.split(".")[0] == "cover"]
            other_queue = [(k, e) for (k, e) in filled_slots if e.split(".")[0] != "cover"]
            for spec in tiles:
                if spec.get("special") == "shades":
                    slot = cover_queue.pop(0) if cover_queue else (other_queue.pop(0) if other_queue else None)
                else:
                    slot = other_queue.pop(0) if other_queue else (cover_queue.pop(0) if cover_queue else None)
                assignments.append((spec, slot))
        else:
            queue = filled_slots.copy()
            for spec in tiles:
                slot = queue.pop(0) if queue else None
                assignments.append((spec, slot))
        # Geometry for 3 columns x 2 rows (maximized height)
        def cell_xy(rc: int, cc: int) -> tuple[int, int]:
            base_x = 24; col_step = 128 + 24
            base_y = 80
            # content bottom before footer is y=430
            avail = 430 - base_y
            row_gap = 20
            tile_h = (avail - row_gap) // 2
            row_step = tile_h + row_gap
            return (base_x + cc * col_step, base_y + rc * row_step)
        def cell_wh(rs: int, cs: int) -> tuple[int, int]:
            w = 128 * cs + 24 * (cs - 1)
            h = (120 * rs) + 20 * (rs - 1)
            return (w, h)
        render_index = 1
        for spec, slot in assignments:
            if not slot:
                continue
            rs=int(spec.get("rs",1)); cs=int(spec.get("cs",1)); row=int(spec.get("row",0)); col=int(spec.get("col",0))
            x,y = cell_xy(row,col); w,h = cell_wh(rs,cs)
            if spec.get("special") == "clock":
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"label","id":70,"x":{x},"y":{y+4},"w":{w},"h":{h-8},"text":"00:00","template":"%H:%M","text_font":96,"align":"center","text_color":"#E5E7EB","bg_opa":0}}')
                continue
            key, ent = slot
            slot_digit = min(render_index,9); base3 = slot_digit*10
            render_index += 1
            st_ent = hass.states.get(ent); label = st_ent.attributes.get("friendly_name", ent) if st_ent else ent
            special = spec.get("special")
            if special == "shades":
                full_x = cell_xy(row, 0)[0]
                full_w = cell_wh(1, 3)[0]
                full_y = y + (h - 88) // 2
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"obj","id":{base3+5},"x":{full_x},"y":{full_y},"w":{full_w},"h":88,"radius":18,"bg_color":"#0B1220"}}')
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"label","id":{base3+6},"x":{full_x+18},"y":{full_y+12},"w":{full_w-36},"h":24,"text":"{label}","text_font":20,"text_color":"#9CA3AF","bg_opa":0}}')
                mid = base3 + 7
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{"page":{p},"obj":"btnmatrix","id":{mid},"x":{full_x+30},"y":{full_y+42},"w":{full_w-60},"h":56,"text_font":28,"options":["Up","Pause","Down"],"one_check":0,"radius":12}}',
                )
                mi = {"type": "cover_cmd", "entity": ent}
                matrix_map[f"p{p}m{mid}"] = mi
                ent_matrix_map.setdefault(ent, []).append((p, mid, mi))
                continue

            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"obj","id":{base3+1},"x":{x},"y":{y},"w":{w},"h":{h},"radius":14,"bg_color":"#1E293B","bg_opa":255,"click":false}}')
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"label","id":{base3},"x":{x+8},"y":{y+6},"w":{max(112,w-16)},"h":24,"text":"{label}","text_font":18,"text_color":"#9CA3AF","bg_opa":0}}')
            # Place icon lower so it is easier to press and leave breathing room for the label
            bx = x + max(20,(w-96)//2); by = y + 36
            domain = ent.split(".")[0]
            option_spec: dict | None = None
            if domain in ("switch", "light", "fan"):
                # Icon selection by slot option, default per domain
                icon_code = pe.options.get(f"{key}_icon") or ("E210" if domain == "fan" else "E425")
                try:
                    int(icon_code, 16)
                except Exception:
                    icon_code = "E425"
                icon = f"\\u{icon_code}"
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{"page":{p},"obj":"btn","id":{base3+2},"x":{bx},"y":{by},"w":96,"h":72,"text":"{icon}","text_font":72,"toggle":1,"radius":14,"bg_color":"#1E293B","bg_opa":255,"text_color":"#FFFFFF","border_width":0}}',
                )
                ent_toggle_map.setdefault(ent, []).append((p, base3 + 2))
                is_light = domain == "light"
                is_fan = domain == "fan"
                modes = st_ent.attributes.get("supported_color_modes", []) if st_ent else []
                has_color = False
                try:
                    m = ",".join(modes).lower()
                    has_color = ("hs" in m) or ("rgb" in m) or ("rgbw" in m) or ("rgbww" in m)
                except Exception:
                    pass
                if is_fan:
                    # Reserve option page for fan speed/percentage controls
                    opt_page = alloc_option_page()
                    trigger_btn_id = base3 + 4
                    option_spec = {
                        "entity": ent,
                        "type": "fan",
                        "origin_page": p,
                        "page_id": opt_page,
                        "friendly_name": label,
                        "trigger_topic": f"p{p}b{trigger_btn_id}",
                    }
                    option_specs.append(option_spec)
                    option_open_map[option_spec["trigger_topic"]] = option_spec
                    status_id = base3 + 3
                    await mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        f'{{"page":{p},"obj":"label","id":{status_id},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"Tap for speed","text_font":20,"align":"center","text_color":"#9CA3AF","bg_opa":0,"click":false}}',
                    )
                    fan_status_map.setdefault(ent, []).append((p, ('l', status_id)))
                    await mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        f'{{"page":{p},"obj":"btn","id":{trigger_btn_id},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"","toggle":0,"radius":6,"bg_opa":0,"border_width":0}}',
                    )
                elif is_light and has_color:
                    opt_page = alloc_option_page()
                    option_spec = {
                        "entity": ent,
                        "type": "light_color",
                        "origin_page": p,
                        "page_id": opt_page,
                        "friendly_name": label,
                        "trigger_topic": f"p{p}b{base3+4}",
                    }
                    option_specs.append(option_spec)
                    option_open_map[option_spec["trigger_topic"]] = option_spec
                    hint_id = base3 + 3
                    await mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        f'{{"page":{p},"obj":"label","id":{hint_id},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"Tap for color","text_font":20,"align":"center","text_color":"#9CA3AF","bg_opa":0,"click":false}}',
                    )
                    await mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        f'{{"page":{p},"obj":"btn","id":{base3+4},"x":{x+8},"y":{y+h-36},"w":{w-16},"h":28,"text":"","toggle":0,"radius":6,"bg_opa":0,"border_width":0}}',
                    )
            elif domain == "cover" and layout == "shades_row":
                # Shades spanning full row (3 columns)
                full_x = cell_xy(row, 0)[0]
                full_w = cell_wh(1, 3)[0]
                full_y = y + (h - 88) // 2
                # Background bar
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{\"page\":{p},\"obj\":\"obj\",\"id\":{base3+5},\"x\":{full_x},\"y\":{full_y},\"w\":{full_w},\"h\":88,\"radius\":18,\"bg_color\":\"#0B1220\"}}')
                # Label on left
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{\"page\":{p},\"obj\":\"label\",\"id\":{base3+6},\"x\":{full_x+18},\"y\":{full_y+12},\"w\":{full_w-36},\"h\":24,\"text\":\"{label}\",\"text_font\":20,\"text_color\":\"#9CA3AF\",\"bg_opa\":0}}')
                # Matrix centered under label
                mid = base3 + 7
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{\"page\":{p},\"obj\":\"btnmatrix\",\"id\":{mid},\"x\":{full_x+30},\"y\":{full_y+42},\"w\":{full_w-60},\"h\":56,\"text_font\":28,\"options\":[\"Up\",\"Pause\",\"Down\"],\"one_check\":0,\"radius\":12}}'
                )
                mi = {"type": "cover_cmd", "entity": ent}
                matrix_map[f"p{p}m{mid}"] = mi
                ent_matrix_map.setdefault(ent, []).append((p, mid, mi))
                # Always map main button on/off unless the entity uses a dedicated options page
                if option_spec is None:
                    ctrl_map[f"p{p}b{base3+2}"] = ent
            else:
                val = st_ent.state if st_ent and st_ent.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"btn","id":{base3+2},"x":{bx},"y":{by},"w":88,"h":64,"text":"{val}","text_font":20,"toggle":false,"bg_opa":0,"border_width":0,"radius":0}}')
                sensor_map.setdefault(ent, []).append((p, base3+2))

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
    ) -> None:
        for spec in option_specs:
            page_id = spec["page_id"]
            origin = spec["origin_page"]
            entity = spec["entity"]
            friendly = spec["friendly_name"]
            option_type = spec["type"]
            option_page_titles[page_id] = f"{friendly} Options"

            await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", str(page_id))
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{\"page\":{page_id},\"id\":0,\"obj\":\"page\",\"prev\":{origin},\"next\":{origin}}}'
            )
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{\"page\":{page_id},\"obj\":\"obj\",\"id\":10,\"x\":0,\"y\":0,\"w\":480,\"h\":480,\"bg_color\":\"#0B1220\",\"bg_opa\":255,\"click\":false}}'
            )
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{\"page\":{page_id},\"obj\":\"label\",\"id\":11,\"x\":24,\"y\":24,\"w\":432,\"h\":48,\"text\":\"{friendly}\",\"text_font\":36,\"align\":\"center\",\"text_color\":\"#E5E7EB\",\"bg_opa\":0}}'
            )

            close_id = 190
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{\"page\":{page_id},\"obj\":\"btn\",\"id\":{close_id},\"x\":360,\"y\":24,\"w\":96,\"h\":48,\"text\":\"Close\",\"text_font\":24,\"radius\":12,\"bg_color\":\"#1F2937\",\"text_color\":\"#FFFFFF\",\"border_width\":0}}'
            )
            option_close_map[f"p{page_id}b{close_id}"] = {"return_page": origin, "entity": entity}

            if option_type == "fan":
                status_label_id = 40
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{\"page\":{page_id},\"obj\":\"label\",\"id\":{status_label_id},\"x\":24,\"y\":96,\"w\":432,\"h\":36,\"text\":\"--\",\"text_font\":28,\"align\":\"center\",\"text_color\":\"#9CA3AF\",\"bg_opa\":0}}'
                )
                fan_status_map.setdefault(entity, []).append((page_id, ('l', status_label_id)))

                matrix_id = 60
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{\"page\":{page_id},\"obj\":\"btnmatrix\",\"id\":{matrix_id},\"x\":72,\"y\":168,\"w\":336,\"h\":144,\"text_font\":32,\"options\":[\"Off\",\"Low\",\"Med\",\"High\"],\"toggle\":1,\"one_check\":1,\"val\":0,\"radius\":16}}'
                )
                meta = {"type": "fan_select", "entity": entity}
                matrix_map[f"p{page_id}m{matrix_id}"] = meta
                ent_matrix_map.setdefault(entity, []).append((page_id, matrix_id, meta))

            elif option_type == "light_color":
                power_btn_id = 40
                await mqtt.async_publish(
                    hass,
                    f"hasp/{node_name}/command/jsonl",
                    f'{{\"page\":{page_id},\"obj\":\"btn\",\"id\":{power_btn_id},\"x\":168,\"y\":108,\"w\":144,\"h\":72,\"text\":\"Power\",\"text_font\":30,\"toggle\":1,\"radius\":14,\"bg_color\":\"#1E293B\",\"bg_opa\":255,\"text_color\":\"#FFFFFF\",\"border_width\":0}}'
                )
                ctrl_map[f"p{page_id}b{power_btn_id}"] = entity
                ent_toggle_map.setdefault(entity, []).append((page_id, power_btn_id))

                colors = [
                    ("#FFFFFF", {"rgb_color": [255, 255, 255]}, "White"),
                    ("#FF0000", {"rgb_color": [255, 0, 0]}, "Red"),
                    ("#00FF00", {"rgb_color": [0, 255, 0]}, "Green"),
                    ("#0000FF", {"rgb_color": [0, 0, 255]}, "Blue"),
                    ("#FDE68A", {"color_temp_kelvin": 2700}, "Warm"),
                    ("#D0E1FF", {"color_temp_kelvin": 6500}, "Cool"),
                ]
                btn_id = 80
                start_x = 72
                start_y = 216
                btn_w = 96
                btn_h = 96
                gap = 24
                for idx, (hexcol, payload, label_text) in enumerate(colors):
                    cx = start_x + (idx % 3) * (btn_w + gap)
                    cy = start_y + (idx // 3) * (btn_h + 40)
                    await mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        f'{{\"page\":{page_id},\"obj\":\"btn\",\"id\":{btn_id},\"x\":{cx},\"y\":{cy},\"w\":{btn_w},\"h\":{btn_h},\"radius\":16,\"bg_color\":\"{hexcol}\",\"text\":\"{label_text}\",\"text_font\":22,\"bg_grad_dir\":\"none\",\"border_width\":0}}'
                    )
                    color_btn_map[f"p{page_id}b{btn_id}"] = {"entity": entity, "payload": payload, "main_btn": power_btn_id}
                    btn_id += 1

    async def _publish_all() -> None:
        """Publish full layout based on config entities (pages, titles, slots)."""
        _LOGGER.info("Dash480: publishing all for node=%s", node_name)
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        # Header/footer
        st = hass.states.get(temp_entity) if temp_entity else None
        tval = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            tval = str(st.state)
        lines = _home_layout_lines(node_name, home_title, tval)
        for line in lines:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", line)
        # Build page list from Page entries linked to this panel
        all_entries = hass.config_entries.async_entries(DOMAIN)
        page_entries = [e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == entry.entry_id]
        page_entries.sort(key=lambda e: int(e.data.get("page_order", 99)))
        page_numbers = [int(e.data.get("page_order", 99)) for e in page_entries]
        # include home page 1 at start for wrap math
        pages_ring = [1] + page_numbers
        # Update page 1 prev/next to wrap to first/last page if pages exist
        if page_numbers:
            prev_home = page_numbers[-1]
            next_home = page_numbers[0]
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{"page":1,"id":0,"obj":"page","prev":{prev_home},"next":{next_home}}}',
            )
        def pprev(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx - 1) % len(pages_ring)]
        def pnext(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx + 1) % len(pages_ring)]
        # Draw each page
        ctrl_map: dict[str, str] = {}
        sensor_map: dict[str, list[tuple[int, int]]] = {}
        matrix_map: dict[str, dict] = {}
        ent_toggle_map: dict[str, list[tuple[int, int]]] = {}
        ent_matrix_map: dict[str, list[tuple[int, int, dict]]] = {}
        color_btn_map: dict[str, dict] = {}
        fan_status_map: dict[str, list[tuple[int, tuple[str, int]]]] = {}
        option_specs: list[dict] = []
        option_open_map: dict[str, dict] = {}
        next_option_page = 50

        def alloc_option_page():
            nonlocal next_option_page
            page_id = next_option_page
            next_option_page += 1
            return page_id
        for pe in page_entries:
            p = int(pe.data.get("page_order", 99))
            await _publish_page_num(
                p,
                pe,
                ctrl_map,
                sensor_map,
                ent_toggle_map,
                ent_matrix_map,
                matrix_map,
                color_btn_map,
                option_specs,
                option_open_map,
                fan_status_map,
                alloc_option_page,
            )
        option_close_map: dict[str, dict] = {}
        option_page_titles: dict[int, str] = {}
        await _publish_option_pages(option_specs, ctrl_map, ent_toggle_map, ent_matrix_map, matrix_map, color_btn_map, option_close_map, option_page_titles, fan_status_map)
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
            # Update all matrices for this entity
            for p, mid, meta in ent_matrix_map.get(entity_id, []):
                if meta["type"] == "light_dim":
                    bri = st.attributes.get("brightness")
                    if isinstance(bri, int):
                        pct = max(1, min(100, int(round(bri * 100 / 255))))
                        idx = 0 if pct <= 25 else 1 if pct <= 50 else 2 if pct <= 75 else 3
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}m{mid}.val", str(idx))
                elif meta["type"] == "fan_preset":
                    mode = (st.attributes.get("preset_mode") or "").strip()
                    presets = meta.get("presets", [])
                    if mode and presets:
                        try:
                            idx = presets.index(mode)
                            await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}m{mid}.val", str(idx))
                        except ValueError:
                            pass
                elif meta["type"] == "fan_pct":
                    pct = st.attributes.get("percentage") or 0
                    idx = 0 if pct == 0 else 1 if pct <= 33 else 2 if pct <= 66 else 3
                    await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}m{mid}.val", str(idx))
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
                    st = hass.states.get(eid)
                    val = st.state if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                    for (pnum, bid) in sensor_map.get(eid, []):
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}b{bid}.text", val)
                return _cb
            cb = await _make_cb(ent)
            unsub = async_track_state_change_event(hass, [ent], cb)
            hass.data[DOMAIN][entry.entry_id][f"unsub_sensor_{ent}"] = unsub

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
                if m["type"] == "light_dim":
                    # Deprecated: removed from layout
                    pass
                elif m["type"] == "fan_preset":
                    # Deprecated: removed from layout
                    pass
                elif m["type"] == "fan_pct":
                    # Deprecated: removed from layout
                    pass
                elif m["type"] == "fan_select":
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
                            # Off => reset to default white
                            hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p{p}b{bid}.text_color", "#FFFFFF"))
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
                    title = home_title if p == 1 else (page_entry.options.get("title", f"Page {p}") if page_entry else f"Page {p}")
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
        st = hass.states.get(temp_entity)
        val = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            val = str(st.state)
        await _publish_temp(val)

    if temp_entity:
        unsub_temp = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
        hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp

    # React to options changes (from Configure dialog or services)
    async def _options_updated(hass_: HomeAssistant, updated: ConfigEntry):
        nonlocal home_title, temp_entity
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
            st = hass.states.get(temp_entity) if temp_entity else None
            val = "--"
            if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
                val = str(st.state)
            await _publish_temp(val)
        # Update title immediately
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title)

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
        val = "--"
        st = hass.states.get(temp_entity) if temp_entity else None
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            val = str(st.state)
        await _publish_temp(val)
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
