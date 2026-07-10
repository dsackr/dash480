"""Shared layout-building logic for Dash480.

This is the single source of truth for turning a page's configuration
(layout template + slot -> entity assignments) into openHASP JSONL objects.
It is used by the live MQTT publisher (`__init__.py`) and by the
`dump_layout` debug service, which previously each maintained their own
hand-written copy of this logic and had drifted out of sync (different
geometry constants, different default icons).

Pure Python, no Home Assistant imports, so it can be unit tested without a
running instance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# A "state" is anything with `.state: str` and `.attributes: Mapping` — this
# matches homeassistant.core.State without importing it.
StateLookup = Callable[[str], Any]

BG_COLOR = "#0B1220"
TILE_BG = "#1E293B"
LABEL_COLOR = "#9CA3AF"
TEXT_COLOR = "#E5E7EB"

# Mirrors homeassistant.const.STATE_UNKNOWN / STATE_UNAVAILABLE as plain
# strings so this module has no runtime dependency on Home Assistant.
UNAVAILABLE_STATES = (None, "", "unknown", "unavailable")


def display_state(state: Any) -> str:
    """Human-displayable text for an HA state object, or '--' if unset/unavailable."""
    return str(state.state) if state and state.state not in UNAVAILABLE_STATES else "--"


# ---------------------------------------------------------------------------
# Layout templates (which grid cells exist for a given page layout)
# ---------------------------------------------------------------------------

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


def tile_specs_for_layout(layout: str) -> list[dict]:
    return LAYOUT_TEMPLATES.get(layout or "", LAYOUT_TEMPLATES["grid_3x3"]).copy()


def resolve_layout(layout: str | None, slot_defs: list[tuple[str, str]]) -> str:
    """Auto-select shades_row when any assigned slot is a cover; else grid_3x2 default."""
    if layout != "shades_row" and any(ent and ent.split(".")[0] == "cover" for _, ent in slot_defs):
        return "shades_row"
    return layout or "grid_3x2"


def assign_slots(layout: str, slot_defs: list[tuple[str, str]]) -> list[tuple[dict, tuple[str, str] | None]]:
    """Pair layout tile specs with configured entities, preferring the shades row for covers."""
    tiles = tile_specs_for_layout(layout)
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
    return assignments


# ---------------------------------------------------------------------------
# Grid geometry (3 columns x 2 rows, sized to fill the space between the
# header and footer). This is the geometry actually pushed to the device.
# ---------------------------------------------------------------------------

GRID_BASE_X = 24
GRID_COL_W = 128
GRID_COL_GAP = 24
GRID_COL_STEP = GRID_COL_W + GRID_COL_GAP
GRID_BASE_Y = 80
GRID_FOOTER_Y = 430
GRID_ROW_GAP = 20


def cell_xy(row: int, col: int) -> tuple[int, int]:
    avail = GRID_FOOTER_Y - GRID_BASE_Y
    tile_h = (avail - GRID_ROW_GAP) // 2
    row_step = tile_h + GRID_ROW_GAP
    return (GRID_BASE_X + col * GRID_COL_STEP, GRID_BASE_Y + row * row_step)


def cell_wh(rs: int, cs: int) -> tuple[int, int]:
    width = GRID_COL_W * cs + GRID_COL_GAP * (cs - 1)
    height = (120 * rs) + GRID_ROW_GAP * (rs - 1)
    return (width, height)


def ring_neighbors(ring: list[int], page: int) -> tuple[int, int]:
    """Return (prev, next) page numbers for `page` within the wraparound ring."""
    idx = ring.index(page)
    return ring[(idx - 1) % len(ring)], ring[(idx + 1) % len(ring)]


def page_nav(page: int, prev_page: int, next_page: int) -> dict:
    return {"page": page, "id": 0, "obj": "page", "prev": prev_page, "next": next_page}


def page_background(page: int, obj_id: int = 80) -> dict:
    return {"page": page, "obj": "obj", "id": obj_id, "x": 0, "y": 0, "w": 480, "h": 480,
            "bg_color": BG_COLOR, "bg_opa": 255, "click": False}


def option_page_allocator(start: int = 50) -> Callable[[], int]:
    """Return a function that hands out sequential option-page ids starting at `start`."""
    state = {"next": start}

    def alloc() -> int:
        page_id = state["next"]
        state["next"] += 1
        return page_id

    return alloc


# ---------------------------------------------------------------------------
# Header/footer + home page chrome
# ---------------------------------------------------------------------------

def home_layout_objects(node_name: str, title: str, temp_text: str) -> list[dict]:
    """Header/footer chrome plus the home page's clock and 3 relay buttons."""
    return [
        {"page": 0, "id": 0, "obj": "page"},
        {"page": 1, "id": 0, "obj": "page"},
        {"page": 0, "id": 10, "obj": "obj", "x": 0, "y": 0, "w": 480, "h": 56,
         "bg_color": "#1F2937", "bg_opa": 255, "radius": 0, "border_width": 0,
         "bg_grad_dir": "none", "outline_width": 0, "shadow_width": 0},
        {"page": 0, "id": 1, "obj": "label", "x": 12, "y": 8, "w": 120, "h": 40,
         "text": "--", "template": "%b %d", "text_font": 35, "align": "left",
         "text_color": TEXT_COLOR, "bg_opa": 0},
        {"page": 0, "id": 2, "obj": "btn", "x": 140, "y": 8, "w": 200, "h": 40,
         "text": title, "text_font": 35, "text_color": "#FFFFFF", "bg_opa": 0,
         "border_width": 0, "radius": 0, "outline_width": 0, "shadow_width": 0,
         "toggle": False},
        {"page": 0, "id": 3, "obj": "btn", "x": 320, "y": 8, "w": 148, "h": 40,
         "text": temp_text or "--", "text_font": 24, "align": "right",
         "text_color": TEXT_COLOR, "bg_opa": 0, "border_width": 0, "radius": 0,
         "outline_width": 0, "shadow_width": 0, "toggle": False},
        {"page": 0, "id": 90, "obj": "btn", "action": {"down": "page prev"}, "x": 0, "y": 430,
         "w": 160, "h": 50, "bg_color": "#2C3E50", "text": "", "text_color": "#FFFFFF",
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
        {"page": 0, "id": 91, "obj": "btn", "action": {"down": "page 1"}, "x": 160, "y": 430,
         "w": 160, "h": 50, "bg_color": "#2C3E50", "text": "", "text_color": "#FFFFFF",
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
        {"page": 0, "id": 92, "obj": "btn", "action": {"down": "page next"}, "x": 320, "y": 430,
         "w": 160, "h": 50, "bg_color": "#2C3E50", "text": "", "text_color": "#FFFFFF",
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
        {"page": 1, "obj": "obj", "id": 180, "x": 0, "y": 0, "w": 480, "h": 480,
         "bg_color": BG_COLOR, "bg_opa": 255, "click": False},
        {"page": 1, "obj": "label", "id": 100, "x": 0, "y": 72, "w": 480, "h": 96,
         "text": "00:00", "template": "%H:%M", "text_font": 96, "align": "center",
         "text_color": TEXT_COLOR, "bg_opa": 0},
        {"page": 1, "obj": "btn", "id": 112, "x": 25, "y": 300, "w": 120, "h": 60,
         "text": "Relay 1", "text_font": 26, "toggle": True, "groupid": 1, "radius": 8,
         "bg_color": "#374151", "text_color": "#FFFFFF", "border_width": 0},
        {"page": 1, "obj": "btn", "id": 122, "x": 175, "y": 300, "w": 120, "h": 60,
         "text": "Relay 2", "text_font": 26, "toggle": True, "groupid": 2, "radius": 8,
         "bg_color": "#374151", "text_color": "#FFFFFF", "border_width": 0},
        {"page": 1, "obj": "btn", "id": 132, "x": 325, "y": 300, "w": 120, "h": 60,
         "text": "Relay 3", "text_font": 26, "toggle": True, "groupid": 3, "radius": 8,
         "bg_color": "#374151", "text_color": "#FFFFFF", "border_width": 0},
    ]


# ---------------------------------------------------------------------------
# Page tile rendering — the part that used to be duplicated 2x (live publish
# + debug dump), with the two copies drifting apart over time.
# ---------------------------------------------------------------------------

@dataclass
class PageRender:
    objects: list[dict] = field(default_factory=list)
    ctrl_map: dict[str, str] = field(default_factory=dict)
    sensor_map: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    ent_toggle_map: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    ent_matrix_map: dict[str, list[tuple[int, int, dict]]] = field(default_factory=dict)
    matrix_map: dict[str, dict] = field(default_factory=dict)
    fan_status_map: dict[str, list[tuple[int, tuple[str, int]]]] = field(default_factory=dict)
    option_specs: list[dict] = field(default_factory=list)


def render_page(
    page: int,
    layout: str,
    slot_defs: list[tuple[str, str]],
    icon_overrides: dict[str, str],
    state_lookup: StateLookup,
    alloc_option_page: Callable[[], int],
) -> PageRender:
    """Build every JSONL tile object and touch-routing map fragment for one page.

    Shared by the live MQTT publisher and the `dump_layout` debug export, so a
    layout change only needs to be made in one place.
    """
    out = PageRender()
    assignments = assign_slots(layout, slot_defs)
    render_index = 1

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
            out.objects.append({
                "page": page, "obj": "label", "id": 70, "x": x, "y": y + 4, "w": w, "h": h - 8,
                "text": "00:00", "template": "%H:%M", "text_font": 96, "align": "center",
                "text_color": TEXT_COLOR, "bg_opa": 0,
            })
            continue

        key, ent = slot
        slot_digit = min(render_index, 9)
        base = slot_digit * 10
        render_index += 1
        st = state_lookup(ent)
        label = st.attributes.get("friendly_name", ent) if st else ent
        special = spec.get("special")
        domain = ent.split(".")[0]

        if special == "shades":
            full_x = cell_xy(row, 0)[0]
            full_w = cell_wh(1, 3)[0]
            full_y = y + (h - 88) // 2
            mid = base + 7
            out.objects.append({"page": page, "obj": "obj", "id": base + 5, "x": full_x,
                                 "y": full_y, "w": full_w, "h": 88, "radius": 18, "bg_color": BG_COLOR})
            out.objects.append({"page": page, "obj": "label", "id": base + 6, "x": full_x + 18,
                                 "y": full_y + 12, "w": full_w - 36, "h": 24, "text": label,
                                 "text_font": 20, "text_color": LABEL_COLOR, "bg_opa": 0})
            out.objects.append({"page": page, "obj": "btnmatrix", "id": mid, "x": full_x + 30,
                                 "y": full_y + 42, "w": full_w - 60, "h": 56, "text_font": 28,
                                 "options": ["Up", "Pause", "Down"], "one_check": 0, "radius": 12})
            mi = {"type": "cover_cmd", "entity": ent}
            out.matrix_map[f"p{page}m{mid}"] = mi
            out.ent_matrix_map.setdefault(ent, []).append((page, mid, mi))
            continue

        out.objects.append({"page": page, "obj": "obj", "id": base + 1, "x": x, "y": y, "w": w,
                             "h": h, "radius": 14, "bg_color": TILE_BG, "bg_opa": 255, "click": False})
        out.objects.append({"page": page, "obj": "label", "id": base, "x": x + 8, "y": y + 6,
                             "w": max(112, w - 16), "h": 24, "text": label, "text_font": 18,
                             "text_color": LABEL_COLOR, "bg_opa": 0})

        bx = x + max(20, (w - 96) // 2)
        by = y + 36

        if domain in ("switch", "light", "fan"):
            icon_code = icon_overrides.get(key) or ("E210" if domain == "fan" else "E425")
            try:
                icon_value = int(icon_code, 16)
            except (TypeError, ValueError):
                icon_value = int("E425", 16)
            icon = chr(icon_value)
            out.objects.append({"page": page, "obj": "btn", "id": base + 2, "x": bx, "y": by,
                                 "w": 96, "h": 72, "text": icon, "text_font": 72, "toggle": True,
                                 "radius": 14, "bg_color": TILE_BG, "bg_opa": 255,
                                 "text_color": "#FFFFFF", "border_width": 0})
            out.ent_toggle_map.setdefault(ent, []).append((page, base + 2))

            is_fan = domain == "fan"
            has_color = False
            if domain == "light" and st:
                modes = st.attributes.get("supported_color_modes", [])
                mode_str = ",".join(modes).lower()
                has_color = any(m in mode_str for m in ("hs", "rgb", "rgbw", "rgbww"))

            if is_fan:
                trigger_btn_id = base + 4
                option_spec = {
                    "entity": ent, "type": "fan", "origin_page": page,
                    "page_id": alloc_option_page(), "friendly_name": label,
                    "trigger_topic": f"p{page}b{trigger_btn_id}",
                }
                out.option_specs.append(option_spec)
                status_id = base + 3
                out.objects.append({"page": page, "obj": "label", "id": status_id, "x": x + 8,
                                     "y": y + h - 36, "w": w - 16, "h": 28, "text": "Tap for speed",
                                     "text_font": 20, "align": "center", "text_color": LABEL_COLOR,
                                     "bg_opa": 0, "click": False})
                out.fan_status_map.setdefault(ent, []).append((page, ("l", status_id)))
                out.objects.append({"page": page, "obj": "btn", "id": trigger_btn_id, "x": x + 8,
                                     "y": y + h - 36, "w": w - 16, "h": 28, "text": "", "toggle": 0,
                                     "radius": 6, "bg_opa": 0, "border_width": 0})
            elif domain == "light" and has_color:
                trigger_btn_id = base + 4
                option_spec = {
                    "entity": ent, "type": "light_color", "origin_page": page,
                    "page_id": alloc_option_page(), "friendly_name": label,
                    "trigger_topic": f"p{page}b{trigger_btn_id}",
                }
                out.option_specs.append(option_spec)
                hint_id = base + 3
                out.objects.append({"page": page, "obj": "label", "id": hint_id, "x": x + 8,
                                     "y": y + h - 36, "w": w - 16, "h": 28, "text": "Tap for color",
                                     "text_font": 20, "align": "center", "text_color": LABEL_COLOR,
                                     "bg_opa": 0, "click": False})
                out.objects.append({"page": page, "obj": "btn", "id": trigger_btn_id, "x": x + 8,
                                     "y": y + h - 36, "w": w - 16, "h": 28, "text": "", "toggle": 0,
                                     "radius": 6, "bg_opa": 0, "border_width": 0})
        elif domain == "cover" and layout == "shades_row":
            # Overflow: more covers than shade slots, so this one lands in a
            # regular grid cell but still renders as a full-width shades bar.
            full_x = cell_xy(row, 0)[0]
            full_w = cell_wh(1, 3)[0]
            full_y = y + (h - 88) // 2
            mid = base + 7
            out.objects.append({"page": page, "obj": "obj", "id": base + 5, "x": full_x,
                                 "y": full_y, "w": full_w, "h": 88, "radius": 18, "bg_color": BG_COLOR})
            out.objects.append({"page": page, "obj": "label", "id": base + 6, "x": full_x + 18,
                                 "y": full_y + 12, "w": full_w - 36, "h": 24, "text": label,
                                 "text_font": 20, "text_color": LABEL_COLOR, "bg_opa": 0})
            out.objects.append({"page": page, "obj": "btnmatrix", "id": mid, "x": full_x + 30,
                                 "y": full_y + 42, "w": full_w - 60, "h": 56, "text_font": 28,
                                 "options": ["Up", "Pause", "Down"], "one_check": 0, "radius": 12})
            mi = {"type": "cover_cmd", "entity": ent}
            out.matrix_map[f"p{page}m{mid}"] = mi
            out.ent_matrix_map.setdefault(ent, []).append((page, mid, mi))
            out.ctrl_map[f"p{page}b{base + 2}"] = ent
        else:
            val = display_state(st)
            out.objects.append({"page": page, "obj": "btn", "id": base + 2, "x": bx, "y": by,
                                 "w": 88, "h": 64, "text": val, "text_font": 20, "toggle": False,
                                 "bg_opa": 0, "border_width": 0, "radius": 0})
            out.sensor_map.setdefault(ent, []).append((page, base + 2))

    return out


# ---------------------------------------------------------------------------
# Option pages (fan speed / light color) — dedicated sub-pages opened by
# tapping the "Tap for speed" / "Tap for color" trigger under a tile.
# ---------------------------------------------------------------------------

FAN_SPEED_OPTIONS = ["Off", "Low", "Med", "High"]

# (hex, HA service call payload, label) — the color swatches shown on both
# the on-device option page and the debug dump export.
LIGHT_COLOR_SWATCHES: list[tuple[str, dict, str]] = [
    ("#FFFFFF", {"rgb_color": [255, 255, 255]}, "White"),
    ("#FF0000", {"rgb_color": [255, 0, 0]}, "Red"),
    ("#00FF00", {"rgb_color": [0, 255, 0]}, "Green"),
    ("#0000FF", {"rgb_color": [0, 0, 255]}, "Blue"),
    ("#FDE68A", {"color_temp_kelvin": 2700}, "Warm"),
    ("#D0E1FF", {"color_temp_kelvin": 6500}, "Cool"),
]


@dataclass
class OptionPageRender:
    objects: list[dict]
    close_button_id: int
    fan_status_label_id: int | None = None
    fan_matrix_id: int | None = None
    power_button_id: int | None = None
    color_buttons: list[tuple[int, str, dict]] = field(default_factory=list)


def build_option_page(spec: dict) -> OptionPageRender:
    """Visual chrome + object ids for a fan-speed or light-color option page."""
    page_id = spec["page_id"]
    origin = spec["origin_page"]
    friendly = spec["friendly_name"]
    option_type = spec["type"]
    close_id = 190

    objects = [
        {"page": page_id, "id": 0, "obj": "page", "prev": origin, "next": origin},
        {"page": page_id, "obj": "obj", "id": 10, "x": 0, "y": 0, "w": 480, "h": 480,
         "bg_color": BG_COLOR, "bg_opa": 255, "click": False},
        {"page": page_id, "obj": "label", "id": 11, "x": 24, "y": 24, "w": 432, "h": 48,
         "text": friendly, "text_font": 36, "align": "center", "text_color": TEXT_COLOR, "bg_opa": 0},
        {"page": page_id, "obj": "btn", "id": close_id, "x": 360, "y": 24, "w": 96, "h": 48,
         "text": "Close", "text_font": 24, "radius": 12, "bg_color": "#1F2937",
         "text_color": "#FFFFFF", "border_width": 0},
    ]
    render = OptionPageRender(objects=objects, close_button_id=close_id)

    if option_type == "fan":
        status_id, matrix_id = 40, 60
        objects.append({"page": page_id, "obj": "label", "id": status_id, "x": 24, "y": 96,
                         "w": 432, "h": 36, "text": "--", "text_font": 28, "align": "center",
                         "text_color": LABEL_COLOR, "bg_opa": 0})
        objects.append({"page": page_id, "obj": "btnmatrix", "id": matrix_id, "x": 72, "y": 168,
                         "w": 336, "h": 144, "text_font": 32, "options": FAN_SPEED_OPTIONS,
                         "toggle": 1, "one_check": 1, "val": 0, "radius": 16})
        render.fan_status_label_id = status_id
        render.fan_matrix_id = matrix_id
    elif option_type == "light_color":
        power_id = 40
        objects.append({"page": page_id, "obj": "btn", "id": power_id, "x": 168, "y": 108,
                         "w": 144, "h": 72, "text": "Power", "text_font": 30, "toggle": 1,
                         "radius": 14, "bg_color": TILE_BG, "bg_opa": 255,
                         "text_color": "#FFFFFF", "border_width": 0})
        render.power_button_id = power_id
        btn_id = 80
        start_x, start_y, btn_w, btn_h, gap = 72, 216, 96, 96, 24
        for idx, (hexcol, payload, label_text) in enumerate(LIGHT_COLOR_SWATCHES):
            cx = start_x + (idx % 3) * (btn_w + gap)
            cy = start_y + (idx // 3) * (btn_h + 40)
            objects.append({"page": page_id, "obj": "btn", "id": btn_id, "x": cx, "y": cy,
                             "w": btn_w, "h": btn_h, "radius": 16, "bg_color": hexcol,
                             "text": label_text, "text_font": 22, "bg_grad_dir": "none",
                             "border_width": 0})
            render.color_buttons.append((btn_id, hexcol, payload))
            btn_id += 1

    return render
