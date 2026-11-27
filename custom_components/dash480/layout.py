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

import json
import math
from dataclasses import dataclass, field
from typing import Any, Callable

# A "state" is anything with `.state: str` and `.attributes: Mapping` — this
# matches homeassistant.core.State without importing it.
StateLookup = Callable[[str], Any]

BG_COLOR = "#0B1220"
TILE_BG = "#1E293B"
LABEL_COLOR = "#9CA3AF"
TEXT_COLOR = "#E5E7EB"

# ---------------------------------------------------------------------------
# Themes — every chrome/structural color used anywhere in a rendered layout
# routes through one of these palettes, selected by resolve_palette(). Actual
# light colors (e.g. the color-picker swatches) are NOT theme-driven — they
# represent real colors a light can be set to, not UI chrome.
# ---------------------------------------------------------------------------

DARK_PALETTE = {
    "bg": BG_COLOR,
    "tile_bg": TILE_BG,
    "label": LABEL_COLOR,
    "text": TEXT_COLOR,
    "header_bg": "#1F2937",
    "header_title_text": "#FFFFFF",
    "nav_btn_bg": "#2C3E50",
    "nav_btn_text": "#FFFFFF",
    "secondary_btn_bg": "#374151",
    "secondary_btn_text": "#FFFFFF",
    "toggle_btn_text": "#FFFFFF",
    "option_close_bg": "#1F2937",
    "option_close_text": "#FFFFFF",
    "gauge_arc": "#38BDF8",
    "gauge_track": "#334155",
}

LIGHT_PALETTE = {
    "bg": "#F1F5F9",
    "tile_bg": "#FFFFFF",
    "label": "#64748B",
    "text": "#0F172A",
    "header_bg": "#E2E8F0",
    "header_title_text": "#0F172A",
    "nav_btn_bg": "#CBD5E1",
    "nav_btn_text": "#0F172A",
    "secondary_btn_bg": "#CBD5E1",
    "secondary_btn_text": "#0F172A",
    "toggle_btn_text": "#0F172A",
    "option_close_bg": "#E2E8F0",
    "option_close_text": "#0F172A",
    "gauge_arc": "#0284C7",
    "gauge_track": "#CBD5E1",
}

PALETTES = {"dark": DARK_PALETTE, "light": LIGHT_PALETTE}


def resolve_palette(theme: str | None, sun_above_horizon: bool | None) -> dict:
    """Resolve a theme option + current sun state into a concrete palette.

    Unknown/missing theme defaults to dark, matching pre-theme behavior
    exactly. "follow_sun" with an unknown sun state also defaults to dark
    (matches the overall default rather than guessing daytime).
    """
    if theme == "light":
        return LIGHT_PALETTE
    if theme == "follow_sun":
        return LIGHT_PALETTE if sun_above_horizon else DARK_PALETTE
    return DARK_PALETTE

# Mirrors homeassistant.const.STATE_UNKNOWN / STATE_UNAVAILABLE as plain
# strings so this module has no runtime dependency on Home Assistant.
UNAVAILABLE_STATES = (None, "", "unknown", "unavailable")


def display_state(state: Any) -> str:
    """Human-displayable text for an HA state object, or '--' if unset/unavailable."""
    return str(state.state) if state and state.state not in UNAVAILABLE_STATES else "--"


def gauge_display_value(state: Any) -> str:
    """'<state><unit>' for a gauge tile's centered value label, or '--' if unset/unavailable.

    Not always a percentage — a gauge is for any numeric sensor with a
    meaningful range, so this shows the entity's own unit_of_measurement
    (e.g. "72°F", "45%", "3.2 kWh"), not an assumed "%".
    """
    if not state or state.state in UNAVAILABLE_STATES:
        return "--"
    unit = state.attributes.get("unit_of_measurement") or ""
    return f"{state.state}{unit}"


def gauge_arc_value(state: Any, gmin: float, gmax: float) -> float:
    """Numeric value clamped to [gmin, gmax] for the arc's `val`, or gmin if unset/unavailable/non-numeric."""
    if state and state.state not in UNAVAILABLE_STATES:
        try:
            return max(gmin, min(gmax, float(state.state)))
        except (TypeError, ValueError):
            pass
    return gmin


# Home Assistant Lovelace gauge `severity` colors: success / warning / error.
# `--error-color` (#DB4437) is the red-orange HA uses for the `red` band.
GAUGE_SEVERITY_COLORS = {
    "green": "#43A047",
    "yellow": "#FFA600",
    "red": "#DB4437",
}
GAUGE_SEVERITY_KEYS = ("green", "yellow", "red")
# Near-black reads on all three band colors, matching HA's needle gauge.
GAUGE_NEEDLE_COLOR = "#111827"

# Classic openHASP gauge sweep: 135° (lower left) clockwise 270° to 45°
# (lower right). 0° is 3 o'clock and angles increase clockwise, so screen
# y grows with sin(angle).
GAUGE_START_ANGLE = 135
GAUGE_SWEEP = 270

# Per severity gauge, within TILE_ID_BUDGET (base .. base+7):
# base title, base+1 card, base+2..+4 band arcs, base+5 needle, base+6 value.
GAUGE_BAND_ID_OFFSETS = (2, 3, 4)
GAUGE_NEEDLE_ID_OFFSET = 5
GAUGE_VALUE_ID_OFFSET = 6


def _json_number(value: float) -> int | float:
    if value.is_integer() and abs(value) < 2**53:
        return int(value)
    return value


def normalize_gauge_severity(severity: Any) -> dict[str, int | float] | None:
    """Canonical `{green, yellow, red}` map, or None when nothing usable remains.

    Unknown keys and non-numeric values are dropped. Key order is the HA
    order (green, yellow, red), not threshold order — rendering sorts by
    value so inverted maps (red below green) still work. Whole numbers stay
    ints so a saved page doesn't grow `.0` suffixes.
    """
    if not isinstance(severity, dict):
        return None
    by_key: dict[str, Any] = {}
    for key, raw in severity.items():
        if isinstance(raw, bool) or raw is None or raw == "":
            continue
        name = str(key).lower()
        if name in GAUGE_SEVERITY_COLORS and name not in by_key:
            by_key[name] = raw
    cleaned: dict[str, int | float] = {}
    for key in GAUGE_SEVERITY_KEYS:
        if key not in by_key:
            continue
        try:
            cleaned[key] = _json_number(float(by_key[key]))
        except (TypeError, ValueError):
            continue
    return cleaned or None


def normalize_tile(tile: dict) -> dict:
    """Copy a gauge tile with its `severity` map normalized. Other tiles pass through.

    Empty or invalid severity is removed so the renderer falls back to the
    single-color arc. Called from pages_store on create and update.
    """
    if not isinstance(tile, dict) or tile.get("type") != "gauge" or "severity" not in tile:
        return tile
    tile = dict(tile)
    cleaned = normalize_gauge_severity(tile.get("severity"))
    if cleaned:
        tile["severity"] = cleaned
    else:
        tile.pop("severity", None)
    return tile


def gauge_value_angle(value: float, gmin: float, gmax: float) -> float:
    """openHASP angle (degrees, clockwise from 3 o'clock) for `value` on the gauge sweep."""
    span = gmax - gmin
    if span <= 0:
        frac = 0.0
    else:
        frac = (float(value) - gmin) / span
    frac = min(1.0, max(0.0, frac))
    return (GAUGE_START_ANGLE + frac * GAUGE_SWEEP) % 360.0


@dataclass(frozen=True)
class GaugeBand:
    """One colored slice of a severity gauge, in threshold order."""

    key: str
    color: str
    start_value: float
    end_value: float
    start_angle: int
    end_angle: int


def gauge_severity_bands(severity: Any, gmin: float, gmax: float) -> list[GaugeBand]:
    """Severity bands across [gmin, gmax], matching HA's gauge severity semantics.

    Each recognized key colors the range from its threshold up to the next
    higher threshold (or `gmax` for the last). Thresholds are sorted by value,
    so `{red: 0, yellow: 3, green: 10}` and `{green: 0, yellow: 50, red: 80}`
    both work, as does any subset of the three keys. A leading gap (the first
    threshold above `gmin`) is left uncolored — the tile background shows
    through — because a fourth arc would not fit in the tile id budget.
    Zero-width slices (duplicate thresholds, or a threshold at/above `gmax`)
    are omitted. Returns [] when severity is missing or has no usable keys,
    which the renderer treats as a plain single-color gauge.
    """
    cleaned = normalize_gauge_severity(severity)
    if not cleaned or gmax <= gmin:
        return []
    points = sorted((float(level), key) for key, level in cleaned.items())
    bands: list[GaugeBand] = []
    for index, (level, key) in enumerate(points):
        start = min(gmax, max(gmin, level))
        if index + 1 < len(points):
            end = min(gmax, max(gmin, points[index + 1][0]))
        else:
            end = gmax
        if end <= start:
            continue
        start_angle = int(round(gauge_value_angle(start, gmin, gmax))) % 360
        end_angle = int(round(gauge_value_angle(end, gmin, gmax))) % 360
        if start_angle == end_angle:
            continue
        bands.append(GaugeBand(
            key=key,
            color=GAUGE_SEVERITY_COLORS[key],
            start_value=start,
            end_value=end,
            start_angle=start_angle,
            end_angle=end_angle,
        ))
    return bands


def gauge_needle_points(
    center_x: float,
    center_y: float,
    inner_radius: float,
    outer_radius: float,
    value: float,
    gmin: float,
    gmax: float,
) -> list[list[int]]:
    """Line endpoints (object-local pixels) for the needle at `value`.

    openHASP `line` points are relative to the line object. 0° points right
    and angles increase clockwise, which is `x + r*cos`, `y + r*sin` in
    screen space (y grows downward).
    """
    angle = math.radians(gauge_value_angle(value, gmin, gmax))
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return [
        [int(round(center_x + inner_radius * cos_a)), int(round(center_y + inner_radius * sin_a))],
        [int(round(center_x + outer_radius * cos_a)), int(round(center_y + outer_radius * sin_a))],
    ]


@dataclass(frozen=True)
class GaugeTarget:
    """One gauge tile's live-update target.

    A plain gauge sets `arc_id` (the single arc's `.val`). A severity gauge
    sets `needle_id` plus the line object's local geometry; its band arcs are
    static and are not updated when the sensor changes.
    """

    page: int
    label_id: int
    gmin: float
    gmax: float
    arc_id: int | None = None
    needle_id: int | None = None
    center_x: float = 0.0
    center_y: float = 0.0
    inner_radius: float = 0.0
    outer_radius: float = 0.0


def gauge_live_updates(target: GaugeTarget, state: Any) -> list[tuple[str, str]]:
    """MQTT command suffixes and payloads for one gauge after a state change.

    Suffixes are relative to `hasp/<node>/command/` (for example `p2b5.points`).
    The needle payload is an openHASP `points` JSON array. The value label is
    always published; a plain gauge also publishes the arc `.val`.
    """
    clamped = gauge_arc_value(state, target.gmin, target.gmax)
    updates: list[tuple[str, str]] = []
    if target.arc_id is not None:
        updates.append((f"p{target.page}b{target.arc_id}.val", str(clamped)))
    if target.needle_id is not None:
        points = gauge_needle_points(
            target.center_x, target.center_y, target.inner_radius, target.outer_radius,
            clamped, target.gmin, target.gmax,
        )
        updates.append((
            f"p{target.page}b{target.needle_id}.points",
            json.dumps(points, separators=(",", ":")),
        ))
    updates.append((f"p{target.page}b{target.label_id}.text", gauge_display_value(state)))
    return updates


def _gauge_stroke(arc_size: int) -> int:
    return max(6, min(18, arc_size // 8))


# MDI codepoints (from openHASP's font reference) for HA's standard weather
# entity condition strings. Verified live against the physical panel for
# sunny/cloudy/rainy before use (same discovery pattern as DEFAULT_CALENDAR_ICON);
# the rest come from the same official reference table and were not each
# individually re-verified — correct here if any renders wrong.
WEATHER_CONDITION_ICONS = {
    "sunny": "E599",
    "clear-night": "E594",
    "cloudy": "E590",
    "partlycloudy": "E595",
    "pouring": "E596",
    "rainy": "E597",
    "snowy": "E598",
    "snowy-rainy": "E598",
    "fog": "E591",
    "hail": "E592",
    "lightning": "E593",
    "lightning-rainy": "E67E",
    "windy": "E59E",
    "windy-variant": "E59E",
}
DEFAULT_WEATHER_ICON = "E590"  # weather-cloudy — fallback for "exceptional"/unknown conditions


def weather_icon_codepoint(condition: Any) -> str:
    return WEATHER_CONDITION_ICONS.get(condition, DEFAULT_WEATHER_ICON)


def weather_temperature_text(state: Any) -> str:
    """'<temperature><unit>' for a weather tile, or '--' if unset/unavailable."""
    if not state or state.state in UNAVAILABLE_STATES:
        return "--"
    temp = state.attributes.get("temperature")
    if temp is None:
        return "--"
    unit = state.attributes.get("temperature_unit") or ""
    return f"{temp}{unit}"


# Placeholder codepoint (unverified against the actual font flashed to the
# device) — correctable per-slot via the existing icon picker (select.py's
# ICON_CHOICES) without a code release, same as every other icon.
DEFAULT_CALENDAR_ICON = "E1C0"

# A calendar tile has no reserved space to wrap/scroll text, so the summary
# is manually truncated rather than relying on LVGL long_mode support.
CALENDAR_SUMMARY_MAX_CHARS = 20


def format_calendar_summary(state: Any) -> str:
    """One-line 'next/current event' text for a calendar entity's compact tile."""
    if not state or state.state in UNAVAILABLE_STATES:
        return "No events"
    message = state.attributes.get("message")
    if not message:
        return "No events"
    all_day = state.attributes.get("all_day", False)
    time_str = "All day" if all_day else ""
    if not all_day:
        start_time = state.attributes.get("start_time")
        if start_time:
            try:
                time_str = str(start_time).split(" ")[1][:5]
            except Exception:
                time_str = ""
    label = f"{message} {time_str}".strip() if time_str else str(message)
    if len(label) <= CALENDAR_SUMMARY_MAX_CHARS:
        return label
    return label[: CALENDAR_SUMMARY_MAX_CHARS - 1].rstrip() + "…"


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


def page_background(page: int, obj_id: int = 80, palette: dict = DARK_PALETTE) -> dict:
    return {"page": page, "obj": "obj", "id": obj_id, "x": 0, "y": 0, "w": 480, "h": 480,
            "bg_color": palette["bg"], "bg_opa": 255, "click": False}


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

def header_footer_objects(
    node_name: str, title: str, temp_text: str, palette: dict = DARK_PALETTE
) -> list[dict]:
    """Persistent page-0 chrome: header bar (date/title/temp) + nav footer.

    Always drawn regardless of what page 1 shows — this is independent of
    whether page 1 is the hardcoded fallback or a user-configured Page entry.
    """
    return [
        {"page": 0, "id": 0, "obj": "page"},
        {"page": 0, "id": 10, "obj": "obj", "x": 0, "y": 0, "w": 480, "h": 56,
         "bg_color": palette["header_bg"], "bg_opa": 255, "radius": 0, "border_width": 0,
         "bg_grad_dir": "none", "outline_width": 0, "shadow_width": 0},
        {"page": 0, "id": 1, "obj": "label", "x": 12, "y": 8, "w": 120, "h": 40,
         "text": "--", "template": "%b %d", "text_font": 35, "align": "left",
         "text_color": palette["text"], "bg_opa": 0},
        {"page": 0, "id": 2, "obj": "btn", "x": 140, "y": 8, "w": 200, "h": 40,
         "text": title, "text_font": 35, "text_color": palette["header_title_text"], "bg_opa": 0,
         "border_width": 0, "radius": 0, "outline_width": 0, "shadow_width": 0,
         "toggle": False, "mode": "dots", "align": "center"},
        {"page": 0, "id": 3, "obj": "btn", "x": 320, "y": 8, "w": 148, "h": 40,
         "text": temp_text or "--", "text_font": 24, "align": "right",
         "text_color": palette["text"], "bg_opa": 0, "border_width": 0, "radius": 0,
         "outline_width": 0, "shadow_width": 0, "toggle": False},
        {"page": 0, "id": 90, "obj": "btn", "action": {"down": "page prev"}, "x": 0, "y": 430,
         "w": 160, "h": 50, "bg_color": palette["nav_btn_bg"], "text": "",
         "text_color": palette["nav_btn_text"],
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
        {"page": 0, "id": 91, "obj": "btn", "action": {"down": "page 1"}, "x": 160, "y": 430,
         "w": 160, "h": 50, "bg_color": palette["nav_btn_bg"], "text": "",
         "text_color": palette["nav_btn_text"],
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
        {"page": 0, "id": 92, "obj": "btn", "action": {"down": "page next"}, "x": 320, "y": 430,
         "w": 160, "h": 50, "bg_color": palette["nav_btn_bg"], "text": "",
         "text_color": palette["nav_btn_text"],
         "radius": 0, "border_side": 0, "border_width": 0, "bg_grad_dir": "none",
         "outline_width": 0, "shadow_width": 0, "text_font": 48},
    ]


def home_fallback_objects(
    prev_page: int, next_page: int, palette: dict = DARK_PALETTE
) -> list[dict]:
    """Default page-1 content: a clock + 3 relay buttons.

    A safe working default so the panel isn't blank before Home Assistant
    takes over. Only drawn when no Page config entry claims page_order == 1
    — once one exists, it fully replaces this instead.
    """
    return [
        page_nav(1, prev_page, next_page),
        {"page": 1, "obj": "obj", "id": 180, "x": 0, "y": 0, "w": 480, "h": 480,
         "bg_color": palette["bg"], "bg_opa": 255, "click": False},
        {"page": 1, "obj": "label", "id": 100, "x": 0, "y": 72, "w": 480, "h": 96,
         "text": "00:00", "template": "%H:%M", "text_font": 96, "align": "center",
         "text_color": palette["text"], "bg_opa": 0},
        {"page": 1, "obj": "btn", "id": 112, "x": 25, "y": 300, "w": 120, "h": 60,
         "text": "Relay 1", "text_font": 26, "toggle": True, "groupid": 1, "radius": 8,
         "bg_color": palette["secondary_btn_bg"], "text_color": palette["secondary_btn_text"],
         "border_width": 0},
        {"page": 1, "obj": "btn", "id": 122, "x": 175, "y": 300, "w": 120, "h": 60,
         "text": "Relay 2", "text_font": 26, "toggle": True, "groupid": 2, "radius": 8,
         "bg_color": palette["secondary_btn_bg"], "text_color": palette["secondary_btn_text"],
         "border_width": 0},
        {"page": 1, "obj": "btn", "id": 132, "x": 325, "y": 300, "w": 120, "h": 60,
         "text": "Relay 3", "text_font": 26, "toggle": True, "groupid": 3, "radius": 8,
         "bg_color": palette["secondary_btn_bg"], "text_color": palette["secondary_btn_text"],
         "border_width": 0},
    ]


def build_page_ring(page_numbers: list[int]) -> list[int]:
    """Wraparound page ring including the home page.

    Page 1 is only implicitly prepended when no real Page entry has claimed
    it — once one has, `page_numbers` already contains it, and prepending
    again would duplicate it and corrupt `ring_neighbors`.
    """
    return page_numbers if 1 in page_numbers else [1] + page_numbers


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
    # entity -> gauge live-update targets. A plain gauge publishes the arc's
    # .val; a severity gauge publishes the needle line's .points. Both also
    # publish the value label's .text. Band arcs are static.
    gauge_map: dict[str, list[GaugeTarget]] = field(default_factory=dict)
    # entity -> list of (page, icon_label_id, temp_label_id) — a weather
    # tile's live-update needs both the condition icon and the temperature
    # text kept in sync, same shape as gauge_map.
    weather_map: dict[str, list[tuple[int, int, int]]] = field(default_factory=dict)
    # entity -> list of (page, img_id, entity_id) — a camera tile
    # uses an img object to render the camera's live proxy URL.
    camera_map: dict[str, list[tuple[int, int, str]]] = field(default_factory=dict)
    # entity -> list of (page, text_id, bar_id) — a battery tile's live-update
    # needs to update the percentage text, the inner bar width, and the color.
    battery_map: dict[str, list[tuple[int, int, int]]] = field(default_factory=dict)


def render_page(
    page: int,
    layout: str,
    slot_defs: list[tuple[str, str]],
    icon_overrides: dict[str, str],
    state_lookup: StateLookup,
    alloc_option_page: Callable[[], int],
    palette: dict = DARK_PALETTE,
    hass: Any = None,
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
                "text_color": palette["text"], "bg_opa": 0,
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
                                 "y": full_y, "w": full_w, "h": 88, "radius": 18, "bg_color": palette["bg"]})
            out.objects.append({"page": page, "obj": "label", "id": base + 6, "x": full_x + 18,
                                 "y": full_y + 12, "w": full_w - 36, "h": 24, "text": label,
                                 "text_font": 20, "text_color": palette["label"], "bg_opa": 0, "mode": "dots"})
            out.objects.append({"page": page, "obj": "btnmatrix", "id": mid, "x": full_x + 30,
                                 "y": full_y + 42, "w": full_w - 60, "h": 56, "text_font": 28,
                                 "options": ["Up", "Pause", "Down"], "one_check": 0, "radius": 12})
            mi = {"type": "cover_cmd", "entity": ent}
            out.matrix_map[f"p{page}m{mid}"] = mi
            out.ent_matrix_map.setdefault(ent, []).append((page, mid, mi))
            continue

        out.objects.append({"page": page, "obj": "obj", "id": base + 1, "x": x, "y": y, "w": w,
                             "h": h, "radius": 14, "bg_color": palette["tile_bg"], "bg_opa": 255, "click": False})
        out.objects.append({"page": page, "obj": "label", "id": base, "x": x + 8, "y": y + 6,
                             "w": max(112, w - 16), "h": 24, "text": label, "text_font": 18,
                             "text_color": palette["label"], "bg_opa": 0, "mode": "dots"})

        bx = x + max(20, (w - 96) // 2)
        by = y + 36

        if domain == "cover" and layout == "shades_row":
            # Overflow: more covers than shade slots, so this one lands in a
            # regular grid cell but still renders as a full-width shades bar.
            # This legacy full-row-width behavior is specific to the
            # template-slot renderer, so it's kept inline here rather than in
            # the shared _dispatch_entity_content (which has its own, more
            # generalized, in-own-rect cover rendering for render_tile_page).
            full_x = cell_xy(row, 0)[0]
            full_w = cell_wh(1, 3)[0]
            full_y = y + (h - 88) // 2
            mid = base + 7
            out.objects.append({"page": page, "obj": "obj", "id": base + 5, "x": full_x,
                                 "y": full_y, "w": full_w, "h": 88, "radius": 18, "bg_color": palette["bg"]})
            out.objects.append({"page": page, "obj": "label", "id": base + 6, "x": full_x + 18,
                                 "y": full_y + 12, "w": full_w - 36, "h": 24, "text": label,
                                 "text_font": 20, "text_color": palette["label"], "bg_opa": 0, "mode": "dots"})
            out.objects.append({"page": page, "obj": "btnmatrix", "id": mid, "x": full_x + 30,
                                 "y": full_y + 42, "w": full_w - 60, "h": 56, "text_font": 28,
                                 "options": ["Up", "Pause", "Down"], "one_check": 0, "radius": 12})
            mi = {"type": "cover_cmd", "entity": ent}
            out.matrix_map[f"p{page}m{mid}"] = mi
            out.ent_matrix_map.setdefault(ent, []).append((page, mid, mi))
            out.ctrl_map[f"p{page}b{base + 2}"] = ent
        else:
            _dispatch_entity_content(out, page, base, x, y, w, h, bx, by, ent, st, label,
                                      icon_overrides.get(key), domain, alloc_option_page, palette, hass)

    return out


def _dispatch_entity_content(
    out: "PageRender",
    page: int,
    base: int,
    x: int,
    y: int,
    w: int,
    h: int,
    bx: int,
    by: int,
    ent: str,
    st: Any,
    label: str,
    icon_code: str | None,
    domain: str,
    alloc_option_page: Callable[[], int],
    palette: dict,
    hass: Any = None,
) -> None:
    """Domain-specific tile content (toggle/popup/sensor/calendar/cover),
    appended in place to `out`. The tile's own background+label must already
    be drawn by the caller before calling this.

    Shared by render_page() (which intercepts domain == "cover" itself for
    its legacy shades_row full-width bar and never reaches the cover branch
    here) and render_tile_page() (whose free-grid tiles use the cover branch
    here, drawn inside the tile's own rect instead of a hardcoded full width).
    """
    if domain == "camera":
        from homeassistant.helpers.network import get_url
        try:
            ha_url = get_url(hass) if hass is not None else "http://localhost:8123"
        except Exception:
            ha_url = "http://localhost:8123"
        img_src = f"{ha_url}/api/dash480/camera_thumbnail/{ent}"
        img_w = w - 16
        img_h = h - 38
        img_x = x + 8
        img_y = y + 30
        if img_w > 0 and img_h > 0:
            out.objects.append({
                "page": page,
                "obj": "img",
                "id": base + 2,
                "x": img_x,
                "y": img_y,
                "w": img_w,
                "h": img_h,
                "src": img_src,
                "auto_size": 0,
            })
            out.camera_map.setdefault(ent, []).append((page, base + 2, ent))
            return

    is_battery = False
    if domain == "sensor":
        if "battery" in ent.lower():
            is_battery = True
        elif label and "battery" in label.lower():
            is_battery = True
        elif st and st.attributes.get("device_class") == "battery":
            is_battery = True

    if is_battery:
        try:
            pct = int(float(st.state)) if st and st.state not in (None, "unknown", "unavailable") else 50
        except (ValueError, TypeError):
            pct = 50
        pct = max(0, min(100, pct))
        
        # Center the battery outline and text label horizontally inside the tile
        cx = x + max(8, (w - 116) // 2)
        cy = y + 36 + max(0, (h - 36 - 24) // 2)
        
        bar_w = int((pct / 100) * 42)
        bar_color = "#EF4444" if pct < 15 else ("#F59E0B" if pct < 50 else "#10B981")
        
        # Outer outline
        out.objects.append({
            "page": page,
            "obj": "obj",
            "id": base + 2,
            "x": cx,
            "y": cy,
            "w": 48,
            "h": 24,
            "radius": 4,
            "border_width": 2,
            "border_color": palette["text"],
            "bg_opa": 0,
        })
        # Terminal cap
        out.objects.append({
            "page": page,
            "obj": "obj",
            "id": base + 3,
            "x": cx + 48,
            "y": cy + 7,
            "w": 4,
            "h": 10,
            "radius": 1,
            "bg_color": palette["text"],
            "border_width": 0,
        })
        # Inner bar
        out.objects.append({
            "page": page,
            "obj": "obj",
            "id": base + 4,
            "x": cx + 3,
            "y": cy + 3,
            "w": bar_w,
            "h": 18,
            "radius": 2,
            "bg_color": bar_color,
            "border_width": 0,
        })
        # Percentage text label
        out.objects.append({
            "page": page,
            "obj": "label",
            "id": base + 5,
            "x": cx + 60,
            "y": cy - 2,
            "w": 52,
            "h": 28,
            "text": f"{pct}%",
            "text_font": 20,
            "text_color": palette["text"],
            "bg_opa": 0,
            "align": "left",
        })
        out.battery_map.setdefault(ent, []).append((page, base + 5, base + 4))
        return

    if domain in ("switch", "light", "fan"):
        icon_default = "E210" if domain == "fan" else "E425"
        icon_resolved = icon_code or icon_default
        try:
            icon_value = int(icon_resolved, 16)
        except (TypeError, ValueError):
            icon_value = int("E425", 16)
        icon = chr(icon_value)
        out.objects.append({"page": page, "obj": "btn", "id": base + 2, "x": bx, "y": by,
                             "w": 96, "h": 72, "text": icon, "text_font": 72, "toggle": True,
                             "radius": 14, "bg_color": palette["tile_bg"], "bg_opa": 255,
                             "text_color": palette["toggle_btn_text"], "border_width": 0})
        out.ent_toggle_map.setdefault(ent, []).append((page, base + 2))
        out.ctrl_map[f"p{page}b{base + 2}"] = ent

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
                                 "text_font": 20, "align": "center", "text_color": palette["label"],
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
                                 "text_font": 20, "align": "center", "text_color": palette["label"],
                                 "bg_opa": 0, "click": False})
            out.objects.append({"page": page, "obj": "btn", "id": trigger_btn_id, "x": x + 8,
                                 "y": y + h - 36, "w": w - 16, "h": 28, "text": "", "toggle": 0,
                                 "radius": 6, "bg_opa": 0, "border_width": 0})
    elif domain == "cover":
        # Generalized in-own-rect cover control (arbitrary grid tiles have no
        # concept of a hardcoded full-width "shades row").
        mid = base + 7
        matrix_y = min(y + max(36, (h - 40) // 2 + 18), y + h - 48)
        out.objects.append({"page": page, "obj": "btnmatrix", "id": mid, "x": x + 12,
                             "y": matrix_y, "w": max(60, w - 24), "h": 40, "text_font": 18,
                             "options": ["Up", "Pause", "Down"], "one_check": 0, "radius": 10})
        mi = {"type": "cover_cmd", "entity": ent}
        out.matrix_map[f"p{page}m{mid}"] = mi
        out.ent_matrix_map.setdefault(ent, []).append((page, mid, mi))
    elif domain == "calendar":
        icon_resolved = icon_code or DEFAULT_CALENDAR_ICON
        try:
            icon_value = int(icon_resolved, 16)
        except (TypeError, ValueError):
            icon_value = int(DEFAULT_CALENDAR_ICON, 16)
        icon = chr(icon_value)
        out.objects.append({"page": page, "obj": "label", "id": base + 3, "x": x + 8,
                             "y": y + 34, "w": 32, "h": 32, "text": icon, "text_font": 28,
                             "text_color": palette["text"], "bg_opa": 0, "click": False})
        summary_text = format_calendar_summary(st)
        out.objects.append({"page": page, "obj": "btn", "id": base + 2, "x": x + 44, "y": y + 36,
                             "w": w - 52, "h": 44, "text": summary_text, "text_font": 16,
                             "text_color": palette["text"], "toggle": False, "bg_opa": 0,
                             "border_width": 0, "click": False})
        out.sensor_map.setdefault(ent, []).append((page, base + 2))
    else:
        val = display_state(st)
        out.objects.append({"page": page, "obj": "btn", "id": base + 2, "x": bx, "y": by,
                             "w": 88, "h": 64, "text": val, "text_font": 20, "toggle": False,
                             "bg_opa": 0, "border_width": 0, "radius": 0, "mode": "dots"})
        out.sensor_map.setdefault(ent, []).append((page, base + 2))


# ---------------------------------------------------------------------------
# Generalized grid + tile-list rendering — the new visual-builder model.
# Pages here are plain dicts from pages_store.py (columns/rows/tiles), not
# config entries. Geometry is intentionally separate from cell_xy/cell_wh
# above (which stay fixed at the legacy 3x2 grid — existing tests assert
# their literal output).
# ---------------------------------------------------------------------------

GRID_MARGIN_X = 24
GRID_COL_GAP = 24
GRID_ROW_GAP = 20

# 8 ids reserved per tile (bg, label, control, hint/status, trigger, ...),
# leaving 1..192 safely below the fixed 193..197 popup-overlay range that
# __init__.py pre-arms on every page (see _publish_page_num).
TILE_ID_BUDGET = 8
MAX_TILES_PER_PAGE = 24


@dataclass(frozen=True)
class GridSpec:
    """Pixel geometry for an arbitrary columns x rows grid on the tile-page
    content area (the same header/footer bounds as the legacy grid)."""

    columns: int
    rows: int

    def _col_width(self) -> float:
        avail = 480 - 2 * GRID_MARGIN_X
        return (avail - (self.columns - 1) * GRID_COL_GAP) / self.columns

    def _row_height(self) -> float:
        avail = GRID_FOOTER_Y - GRID_BASE_Y
        return (avail - (self.rows - 1) * GRID_ROW_GAP) / self.rows

    def xy(self, row: int, col: int) -> tuple[int, int]:
        col_w = self._col_width()
        row_h = self._row_height()
        x = GRID_MARGIN_X + col * (col_w + GRID_COL_GAP)
        y = GRID_BASE_Y + row * (row_h + GRID_ROW_GAP)
        return (round(x), round(y))

    def wh(self, rs: int, cs: int) -> tuple[int, int]:
        col_w = self._col_width()
        row_h = self._row_height()
        w = col_w * cs + GRID_COL_GAP * (cs - 1)
        h = row_h * rs + GRID_ROW_GAP * (rs - 1)
        return (round(w), round(h))


def tile_base_id(tile_index: int) -> int:
    return 1 + tile_index * TILE_ID_BUDGET


def _render_gauge(
    out: "PageRender",
    page: int,
    base: int,
    x: int,
    y: int,
    w: int,
    h: int,
    ent: str,
    st: Any,
    tile: dict,
    palette: dict,
) -> None:
    """Append a gauge tile: a severity needle gauge, or the plain single arc.

    The needle gauge is three stacked openHASP arcs (one per severity band,
    each spanning its share of the 270° sweep) plus a `line` needle and the
    value label. That is 7 objects with the card background and title already
    drawn by the caller: base+1 card, base title, base+2..+4 bands, base+5
    needle, base+6 value — inside TILE_ID_BUDGET. Bands are fully filled
    (`val` at max) and colored on both the background stroke (`line_color`)
    and the indicator stroke (`line_color10`); openHASP 0.7 paints an arc
    with those properties, not `arc_color`.

    Tiles with no usable `severity` keep the original single arc so existing
    gauges look the same.
    """
    gmin = float(tile.get("min", 0))
    gmax = float(tile.get("max", 100))
    if gmax <= gmin:
        gmax = gmin + 1  # defensive: never emit a zero/negative arc span
    val = gauge_arc_value(st, gmin, gmax)

    arc_size = max(40, min(w, h - 34) - 20)
    arc_x = x + (w - arc_size) // 2
    arc_y = y + 34
    bands = gauge_severity_bands(tile.get("severity"), gmin, gmax)

    if not bands:
        arc_id = base + 2
        out.objects.append({"page": page, "obj": "arc", "id": arc_id, "x": arc_x, "y": arc_y,
                             "w": arc_size, "h": arc_size, "min": gmin, "max": gmax, "val": val,
                             "start_angle": GAUGE_START_ANGLE,
                             "end_angle": (GAUGE_START_ANGLE + GAUGE_SWEEP) % 360, "rotation": 0,
                             "type": "normal", "arc_color": palette["gauge_arc"],
                             "bg_color": palette["gauge_track"]})
        value_label_id = base + 3
        out.objects.append({"page": page, "obj": "label", "id": value_label_id, "x": arc_x,
                             "y": arc_y + arc_size // 2 - 14, "w": arc_size, "h": 28,
                             "text": gauge_display_value(st), "text_font": 24, "align": "center",
                             "text_color": palette["text"], "bg_opa": 0, "mode": "dots"})
        out.gauge_map.setdefault(ent, []).append(GaugeTarget(
            page=page, label_id=value_label_id, gmin=gmin, gmax=gmax, arc_id=arc_id,
        ))
        return

    stroke = _gauge_stroke(arc_size)
    for band, offset in zip(bands, GAUGE_BAND_ID_OFFSETS):
        out.objects.append({
            "page": page, "obj": "arc", "id": base + offset, "x": arc_x, "y": arc_y,
            "w": arc_size, "h": arc_size, "min": 0, "max": 100, "val": 100,
            "start_angle": band.start_angle, "end_angle": band.end_angle,
            "start_angle10": band.start_angle, "end_angle10": band.end_angle,
            "rotation": 0, "type": 0, "adjustable": False,
            "line_width": stroke, "line_width10": stroke,
            "line_color": band.color, "line_color10": band.color,
            "line_rounded": 0, "bg_opa": 0, "border_side": 0, "click": False,
        })

    center = arc_size / 2.0
    inner_radius = arc_size * 0.12
    outer_radius = max(inner_radius + 4, center - stroke / 2.0)
    needle_id = base + GAUGE_NEEDLE_ID_OFFSET
    points = gauge_needle_points(center, center, inner_radius, outer_radius, val, gmin, gmax)
    out.objects.append({
        "page": page, "obj": "line", "id": needle_id, "x": arc_x, "y": arc_y,
        "w": arc_size, "h": arc_size, "points": points, "auto_size": 0, "y_invert": 0,
        "line_width": max(2, arc_size // 28), "line_color": GAUGE_NEEDLE_COLOR,
        "line_rounded": 1, "click": False,
    })

    value_label_id = base + GAUGE_VALUE_ID_OFFSET
    out.objects.append({"page": page, "obj": "label", "id": value_label_id, "x": arc_x,
                         "y": arc_y + int(arc_size * 0.58), "w": arc_size, "h": 28,
                         "text": gauge_display_value(st), "text_font": 20, "align": "center",
                         "text_color": palette["text"], "bg_opa": 0, "mode": "dots"})
    out.gauge_map.setdefault(ent, []).append(GaugeTarget(
        page=page, label_id=value_label_id, gmin=gmin, gmax=gmax, needle_id=needle_id,
        center_x=center, center_y=center, inner_radius=inner_radius, outer_radius=outer_radius,
    ))


def render_tile_page(
    page: int,
    page_item: dict,
    state_lookup: StateLookup,
    alloc_option_page: Callable[[], int],
    palette: dict = DARK_PALETTE,
    hass: Any = None,
) -> PageRender:
    """Render a visual-builder page (arbitrary grid, explicit tile list) —
    the new-model counterpart to render_page()'s template-slot rendering.
    `page_item` is a plain dict from pages_store.py: {columns, rows, tiles}.
    Returns the same PageRender shape as render_page() so __init__.py's
    publish plumbing doesn't care which renderer produced a given page.
    """
    out = PageRender()
    columns = int(page_item.get("columns") or 3)
    rows = int(page_item.get("rows") or 2)
    grid = GridSpec(columns=columns, rows=rows)
    tiles = page_item.get("tiles") or []

    for tile_index, tile in enumerate(tiles[:MAX_TILES_PER_PAGE]):
        tile_type = tile.get("type")
        if tile_type not in ("entity", "gauge", "weather"):
            continue
        ent = tile.get("entity_id")
        if not ent:
            continue

        row = int(tile.get("row", 0))
        col = int(tile.get("col", 0))
        rs = int(tile.get("rs", 1))
        cs = int(tile.get("cs", 1))
        x, y = grid.xy(row, col)
        w, h = grid.wh(rs, cs)
        base = tile_base_id(tile_index)

        st = state_lookup(ent)
        label = st.attributes.get("friendly_name", ent) if st else ent

        out.objects.append({"page": page, "obj": "obj", "id": base + 1, "x": x, "y": y, "w": w,
                             "h": h, "radius": 14, "bg_color": palette["tile_bg"], "bg_opa": 255, "click": False})
        out.objects.append({"page": page, "obj": "label", "id": base, "x": x + 8, "y": y + 6,
                             "w": max(112, w - 16), "h": 24, "text": label, "text_font": 18,
                             "text_color": palette["label"], "bg_opa": 0, "mode": "dots"})

        if tile_type == "gauge":
            _render_gauge(out, page, base, x, y, w, h, ent, st, tile, palette)
            continue

        if tile_type == "weather":
            icon_code = weather_icon_codepoint(st.state if st else None)
            try:
                icon_value = int(icon_code, 16)
            except (TypeError, ValueError):
                icon_value = int(DEFAULT_WEATHER_ICON, 16)
            icon_id = base + 2
            out.objects.append({"page": page, "obj": "label", "id": icon_id, "x": x, "y": y + 34,
                                 "w": w, "h": 56, "text": chr(icon_value), "text_font": 48,
                                 "align": "center", "text_color": palette["text"], "bg_opa": 0})
            temp_id = base + 3
            out.objects.append({"page": page, "obj": "label", "id": temp_id, "x": x, "y": y + 96,
                                 "w": w, "h": 28, "text": weather_temperature_text(st), "text_font": 24,
                                 "align": "center", "text_color": palette["text"], "bg_opa": 0, "mode": "dots"})
            out.weather_map.setdefault(ent, []).append((page, icon_id, temp_id))
            continue

        domain = ent.split(".")[0]
        bx = x + max(20, (w - 96) // 2)
        by = y + 36
        _dispatch_entity_content(out, page, base, x, y, w, h, bx, by, ent, st, label,
                                  tile.get("icon"), domain, alloc_option_page, palette, hass)

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


def build_option_page(spec: dict, palette: dict = DARK_PALETTE) -> OptionPageRender:
    """Visual chrome + object ids for a fan-speed or light-color option page."""
    page_id = spec["page_id"]
    origin = spec["origin_page"]
    friendly = spec["friendly_name"]
    option_type = spec["type"]
    close_id = 190

    objects = [
        {"page": page_id, "id": 0, "obj": "page", "prev": origin, "next": origin},
        {"page": page_id, "obj": "obj", "id": 10, "x": 0, "y": 0, "w": 480, "h": 480,
         "bg_color": palette["bg"], "bg_opa": 255, "click": False},
        {"page": page_id, "obj": "label", "id": 11, "x": 24, "y": 24, "w": 432, "h": 48,
         "text": friendly, "text_font": 36, "align": "center", "text_color": palette["text"], "bg_opa": 0},
        {"page": page_id, "obj": "btn", "id": close_id, "x": 360, "y": 24, "w": 96, "h": 48,
         "text": "Close", "text_font": 24, "radius": 12, "bg_color": palette["option_close_bg"],
         "text_color": palette["option_close_text"], "border_width": 0},
    ]
    render = OptionPageRender(objects=objects, close_button_id=close_id)

    if option_type == "fan":
        status_id, matrix_id = 40, 60
        objects.append({"page": page_id, "obj": "label", "id": status_id, "x": 24, "y": 96,
                         "w": 432, "h": 36, "text": "--", "text_font": 28, "align": "center",
                         "text_color": palette["label"], "bg_opa": 0})
        objects.append({"page": page_id, "obj": "btnmatrix", "id": matrix_id, "x": 72, "y": 168,
                         "w": 336, "h": 144, "text_font": 32, "options": FAN_SPEED_OPTIONS,
                         "toggle": 1, "one_check": 1, "val": 0, "radius": 16})
        render.fan_status_label_id = status_id
        render.fan_matrix_id = matrix_id
    elif option_type == "light_color":
        power_id = 40
        objects.append({"page": page_id, "obj": "btn", "id": power_id, "x": 168, "y": 108,
                         "w": 144, "h": 72, "text": "Power", "text_font": 30, "toggle": 1,
                         "radius": 14, "bg_color": palette["tile_bg"], "bg_opa": 255,
                         "text_color": palette["toggle_btn_text"], "border_width": 0})
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
