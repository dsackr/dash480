"""Tests for the shared layout builder.

Run with: python3 -m unittest discover -s tests -v
No Home Assistant install required — layout.py is pure Python.
"""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "custom_components" / "dash480"))

import layout  # noqa: E402


def fake_state(state="on", friendly_name=None, **attrs):
    attributes = dict(attrs)
    if friendly_name is not None:
        attributes["friendly_name"] = friendly_name
    return SimpleNamespace(state=state, attributes=attributes)


class ResolveLayoutTests(unittest.TestCase):
    def test_defaults_to_grid_3x2_when_unset(self):
        self.assertEqual(layout.resolve_layout(None, [("s1", "switch.x")]), "grid_3x2")

    def test_auto_selects_shades_row_for_cover(self):
        slots = [("s1", "switch.x"), ("s2", "cover.blinds")]
        self.assertEqual(layout.resolve_layout("grid_3x2", slots), "shades_row")

    def test_explicit_shades_row_untouched_without_cover(self):
        self.assertEqual(layout.resolve_layout("shades_row", [("s1", "switch.x")]), "shades_row")

    def test_explicit_non_shades_row_preserved_without_cover(self):
        self.assertEqual(layout.resolve_layout("grid_3x3", [("s1", "switch.x")]), "grid_3x3")


class AssignSlotsTests(unittest.TestCase):
    def test_grid_fills_in_order(self):
        slots = [("s1", "switch.a"), ("s2", ""), ("s3", "light.b")]
        assignments = layout.assign_slots("grid_3x2", slots)
        filled = [(spec["row"], spec["col"], slot) for spec, slot in assignments if slot]
        self.assertEqual(filled, [(0, 0, ("s1", "switch.a")), (0, 1, ("s3", "light.b"))])

    def test_shades_row_special_slot_filled_when_regular_slots_saturated_first(self):
        # The "shades_row" template lists its 6 regular cells before the
        # special full-width cell, and assign_slots processes tiles in that
        # order. A cover only reaches the special slot if enough non-cover
        # entities exist to saturate all 6 regular cells first.
        slots = [(f"s{i}", "switch.a") for i in range(1, 7)] + [("s7", "cover.blinds")]
        assignments = layout.assign_slots("shades_row", slots)
        special_slot = next(slot for spec, slot in assignments if spec.get("special") == "shades")
        self.assertEqual(special_slot, ("s7", "cover.blinds"))

    def test_shades_row_special_slot_empty_when_regular_slots_not_saturated(self):
        # Pre-existing quirk, preserved as-is: with too few non-cover
        # entities, an earlier regular tile's fallback greedily consumes the
        # cover before the special (last-iterated) slot is reached.
        slots = [("s1", "switch.a"), ("s2", "cover.blinds")]
        assignments = layout.assign_slots("shades_row", slots)
        special_slot = next(slot for spec, slot in assignments if spec.get("special") == "shades")
        self.assertIsNone(special_slot)

    def test_shades_row_overflow_cover_lands_in_grid_cell(self):
        # Two covers, only one dedicated shades slot -> second cover overflows into a grid cell.
        slots = [("s1", "cover.a"), ("s2", "cover.b")]
        assignments = layout.assign_slots("shades_row", slots)
        assigned_slots = [slot for _, slot in assignments if slot]
        self.assertCountEqual(assigned_slots, [("s1", "cover.a"), ("s2", "cover.b")])


class GeometryTests(unittest.TestCase):
    def test_cell_xy_matches_known_live_values(self):
        # These numbers are load-bearing: they must match what was previously
        # hardcoded independently in the live-publish path.
        self.assertEqual(layout.cell_xy(0, 0), (24, 80))
        self.assertEqual(layout.cell_xy(0, 1), (176, 80))
        self.assertEqual(layout.cell_xy(1, 0), (24, 265))

    def test_cell_wh_matches_known_live_values(self):
        self.assertEqual(layout.cell_wh(1, 1), (128, 120))
        self.assertEqual(layout.cell_wh(1, 3), (432, 120))

    def test_ring_neighbors_wraps(self):
        ring = [1, 2, 3, 4]
        self.assertEqual(layout.ring_neighbors(ring, 1), (4, 2))
        self.assertEqual(layout.ring_neighbors(ring, 4), (3, 1))


class RenderPageTests(unittest.TestCase):
    def setUp(self):
        self.states = {
            "switch.lamp": fake_state("on", friendly_name="Lamp"),
            "light.color": fake_state("on", friendly_name="Color Light", supported_color_modes=["rgb"]),
            "fan.bedroom": fake_state("on", friendly_name="Bedroom Fan"),
            "sensor.temp": fake_state("72"),
        }

    def lookup(self, entity_id):
        return self.states.get(entity_id)

    def test_switch_tile_no_option_page(self):
        slots = [("s1", "switch.lamp")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc)
        self.assertEqual(render.option_specs, [])
        self.assertIn("switch.lamp", render.ent_toggle_map)
        # Every emitted object must be JSON-serializable as-is.
        for obj in render.objects:
            json.dumps(obj)

    def test_fan_tile_registers_option_page(self):
        slots = [("s1", "fan.bedroom")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc)
        self.assertEqual(len(render.option_specs), 1)
        spec = render.option_specs[0]
        self.assertEqual(spec["type"], "fan")
        self.assertEqual(spec["page_id"], 50)
        self.assertIn("fan.bedroom", render.fan_status_map)

    def test_color_light_tile_registers_option_page(self):
        slots = [("s1", "light.color")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc)
        self.assertEqual(len(render.option_specs), 1)
        self.assertEqual(render.option_specs[0]["type"], "light_color")

    def test_sensor_tile_uses_display_state(self):
        slots = [("s1", "sensor.temp")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc)
        text_values = [o["text"] for o in render.objects if o.get("obj") == "btn" and "text" in o]
        self.assertIn("72", text_values)

    def test_unavailable_sensor_renders_dashes(self):
        self.states["sensor.temp"] = fake_state("unavailable")
        slots = [("s1", "sensor.temp")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc)
        text_values = [o["text"] for o in render.objects if o.get("obj") == "btn" and "text" in o]
        self.assertIn("--", text_values)

    def test_icon_override_survives_json_roundtrip(self):
        slots = [("s1", "switch.lamp")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {"s1": "E335"}, self.lookup, alloc)
        icon_obj = next(o for o in render.objects if o.get("obj") == "btn" and o.get("text_font") == 72)
        wire = json.dumps(icon_obj)
        self.assertIn("\\ue335", wire.lower())
        decoded = json.loads(wire)
        self.assertEqual(decoded["text"], chr(0xE335))

    def test_invalid_icon_override_falls_back(self):
        slots = [("s1", "switch.lamp")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {"s1": "not-hex"}, self.lookup, alloc)
        icon_obj = next(o for o in render.objects if o.get("obj") == "btn" and o.get("text_font") == 72)
        self.assertEqual(icon_obj["text"], chr(0xE425))

    def test_shades_row_cover_emits_matrix(self):
        slots = [("s1", "cover.blinds")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "shades_row", slots, {}, self.lookup, alloc)
        self.assertIn("cover.blinds", render.ent_matrix_map)
        matrix_objs = [o for o in render.objects if o.get("obj") == "btnmatrix"]
        self.assertEqual(len(matrix_objs), 1)
        self.assertEqual(matrix_objs[0]["options"], ["Up", "Pause", "Down"])


    def test_battery_sensor_tile_renders_battery_icon(self):
        self.states["sensor.living_room_frame_1_battery"] = fake_state("76.0", device_class="battery")
        slots = [("s1", "sensor.living_room_frame_1_battery")]
        alloc = layout.option_page_allocator(50)
        render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc, hass=None)
        
        # Verify that battery_map has mapped the entity
        self.assertIn("sensor.living_room_frame_1_battery", render.battery_map)
        
        # Since base for first slot starts at 10 (base = 10)
        obj_types = [o["obj"] for o in render.objects if o.get("id") in (12, 13, 14, 15)]
        self.assertCountEqual(obj_types, ["obj", "obj", "obj", "label"])

    def test_camera_tile_renders_generic_image(self):
        import sys
        from unittest.mock import MagicMock
        
        mock_network = MagicMock()
        mock_network.get_url.return_value = "http://localhost:8123"
        
        mock_helpers = MagicMock()
        mock_helpers.network = mock_network
        
        # Save original homeassistant modules if they exist
        orig_modules = {
            "homeassistant": sys.modules.get("homeassistant"),
            "homeassistant.helpers": sys.modules.get("homeassistant.helpers"),
            "homeassistant.helpers.network": sys.modules.get("homeassistant.helpers.network"),
        }
        
        try:
            sys.modules["homeassistant"] = MagicMock()
            sys.modules["homeassistant.helpers"] = mock_helpers
            sys.modules["homeassistant.helpers.network"] = mock_network
            
            slots = [("s1", "camera.living_room_frame_1_display")]
            alloc = layout.option_page_allocator(50)
            render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc, hass=MagicMock())
            
            # Verify that camera_map has mapped the entity
            self.assertIn("camera.living_room_frame_1_display", render.camera_map)
            
            # Verify that the image object was rendered
            img_objs = [o for o in render.objects if o.get("obj") == "img"]
            self.assertEqual(len(img_objs), 1)
            self.assertEqual(img_objs[0]["id"], 12)  # base + 2 (base = 10)
            self.assertIn("camera_thumbnail/camera.living_room_frame_1_display", img_objs[0]["src"])
        finally:
            # Restore original modules
            for k, v in orig_modules.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v


class OptionPageTests(unittest.TestCase):
    def test_fan_option_page_ids(self):
        spec = {"page_id": 50, "origin_page": 2, "friendly_name": "Bedroom Fan", "type": "fan"}
        render = layout.build_option_page(spec)
        self.assertEqual(render.fan_matrix_id, 60)
        self.assertEqual(render.fan_status_label_id, 40)
        for obj in render.objects:
            json.dumps(obj)

    def test_light_color_option_page_swatches(self):
        spec = {"page_id": 51, "origin_page": 2, "friendly_name": "Color Light", "type": "light_color"}
        render = layout.build_option_page(spec)
        self.assertEqual(render.power_button_id, 40)
        self.assertEqual(len(render.color_buttons), 6)
        ids = [b[0] for b in render.color_buttons]
        self.assertEqual(ids, [80, 81, 82, 83, 84, 85])


class HeaderFooterTests(unittest.TestCase):
    def test_title_and_temp_survive_quotes(self):
        objects = layout.header_footer_objects("plate", 'Dash "Home"', "72°")
        for obj in objects:
            json.dumps(obj)  # must not raise
        title_obj = next(o for o in objects if o.get("id") == 2 and o.get("page") == 0)
        self.assertEqual(title_obj["text"], 'Dash "Home"')

    def test_nav_icons_survive_json_roundtrip(self):
        objects = layout.header_footer_objects("plate", "Dash", "--")
        nav_objs = [o for o in objects if o.get("page") == 0 and o.get("id") in (90, 91, 92)]
        self.assertEqual(len(nav_objs), 3)
        for obj in nav_objs:
            # HASP-font glyphs are private-use-area chars; they must decode
            # back identically from the JSON wire format.
            self.assertTrue(obj["text"])
            decoded = json.loads(json.dumps(obj))
            self.assertEqual(decoded["text"], obj["text"])


class OptionPageAllocatorTests(unittest.TestCase):
    def test_sequential_starting_point(self):
        alloc = layout.option_page_allocator(50)
        self.assertEqual([alloc(), alloc(), alloc()], [50, 51, 52])


class GridSpecTests(unittest.TestCase):
    """Geometry for the new visual-builder grid — independent of, and must
    not affect, the legacy cell_xy/cell_wh used by render_page()."""

    def test_cells_stay_within_device_bounds(self):
        grid = layout.GridSpec(columns=3, rows=2)
        w, h = grid.wh(1, 1)
        for row in range(2):
            for col in range(3):
                x, y = grid.xy(row, col)
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, 480)
                self.assertLessEqual(y + h, layout.GRID_FOOTER_Y)

    def test_columns_do_not_overlap(self):
        grid = layout.GridSpec(columns=4, rows=1)
        w, _ = grid.wh(1, 1)
        xs = [grid.xy(0, c)[0] for c in range(4)]
        for a, b in zip(xs, xs[1:]):
            self.assertGreaterEqual(b, a + w)

    def test_span_covers_multiple_cells(self):
        grid = layout.GridSpec(columns=3, rows=2)
        single_w, _ = grid.wh(1, 1)
        span_w, _ = grid.wh(1, 3)
        self.assertGreater(span_w, single_w * 2)


class RenderTilePageTests(unittest.TestCase):
    def setUp(self):
        self.states = {
            "switch.lamp": fake_state("on", friendly_name="Lamp"),
            "light.color": fake_state("on", friendly_name="Color Light", supported_color_modes=["rgb"]),
            "fan.bedroom": fake_state("on", friendly_name="Bedroom Fan"),
            "sensor.temp": fake_state("72"),
            "cover.blinds": fake_state("open", friendly_name="Blinds"),
        }

    def lookup(self, entity_id):
        return self.states.get(entity_id)

    def _page(self, tiles, columns=3, rows=2):
        return {"columns": columns, "rows": rows, "tiles": tiles}

    def test_entity_tile_json_roundtrip(self):
        page = self._page([{"id": "t1", "type": "entity", "entity_id": "switch.lamp", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertIn("switch.lamp", render.ent_toggle_map)
        for obj in render.objects:
            json.dumps(obj)

    def test_sensor_tile_uses_display_state(self):
        page = self._page([{"id": "t1", "type": "entity", "entity_id": "sensor.temp", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        text_values = [o["text"] for o in render.objects if o.get("obj") == "btn" and "text" in o]
        self.assertIn("72", text_values)

    def test_cover_tile_renders_within_own_rect(self):
        # Unlike render_page's legacy shades_row (a hardcoded full-width bar),
        # a tile-page cover must stay inside its own cell so arbitrary grids
        # don't get surprise full-row overlays.
        page = self._page([{"id": "t1", "type": "entity", "entity_id": "cover.blinds", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertIn("cover.blinds", render.ent_matrix_map)
        matrix_objs = [o for o in render.objects if o.get("obj") == "btnmatrix"]
        self.assertEqual(len(matrix_objs), 1)
        cell_w, _ = layout.GridSpec(columns=3, rows=2).wh(1, 1)
        self.assertLessEqual(matrix_objs[0]["w"], cell_w)

    def test_fan_tile_registers_option_page(self):
        page = self._page([{"id": "t1", "type": "entity", "entity_id": "fan.bedroom", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertEqual(len(render.option_specs), 1)
        self.assertEqual(render.option_specs[0]["type"], "fan")

    def test_unknown_tile_type_skipped_without_error(self):
        page = self._page([{"id": "t1", "type": "bogus", "entity_id": "sensor.temp", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertEqual(render.objects, [])

    def test_gauge_tile_json_roundtrip_and_arc_value(self):
        page = self._page([{"id": "t1", "type": "gauge", "entity_id": "sensor.temp", "row": 0, "col": 0,
                             "min": 0, "max": 100}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertIn("sensor.temp", render.gauge_map)
        for obj in render.objects:
            json.dumps(obj)
        arc = next(o for o in render.objects if o.get("obj") == "arc")
        self.assertEqual(arc["min"], 0)
        self.assertEqual(arc["max"], 100)
        self.assertEqual(arc["val"], 72)
        value_label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(value_label["text"], "72")

    def test_gauge_tile_clamps_out_of_range_value(self):
        self.states["sensor.temp"] = fake_state("999")
        page = self._page([{"id": "t1", "type": "gauge", "entity_id": "sensor.temp", "row": 0, "col": 0,
                             "min": 0, "max": 100}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        arc = next(o for o in render.objects if o.get("obj") == "arc")
        self.assertEqual(arc["val"], 100)

    def test_gauge_tile_unavailable_renders_dashes_and_min_value(self):
        self.states["sensor.temp"] = fake_state("unavailable")
        page = self._page([{"id": "t1", "type": "gauge", "entity_id": "sensor.temp", "row": 0, "col": 0,
                             "min": 10, "max": 100}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        arc = next(o for o in render.objects if o.get("obj") == "arc")
        self.assertEqual(arc["val"], 10)
        value_label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(value_label["text"], "--")

    def test_gauge_tile_shows_unit_of_measurement(self):
        self.states["sensor.temp"] = fake_state("72", unit_of_measurement="°F")
        page = self._page([{"id": "t1", "type": "gauge", "entity_id": "sensor.temp", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        value_label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(value_label["text"], "72°F")

    def test_weather_tile_json_roundtrip_and_icon(self):
        self.states["weather.home"] = fake_state("sunny", friendly_name="Home", temperature=72, temperature_unit="°F")
        page = self._page([{"id": "t1", "type": "weather", "entity_id": "weather.home", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        self.assertIn("weather.home", render.weather_map)
        for obj in render.objects:
            json.dumps(obj)
        icon_obj = next(o for o in render.objects if o.get("text_font") == 48)
        self.assertEqual(icon_obj["text"], chr(0xE599))
        temp_obj = next(o for o in render.objects if o.get("text_font") == 24)
        self.assertEqual(temp_obj["text"], "72°F")

    def test_weather_tile_unknown_condition_falls_back_to_default_icon(self):
        self.states["weather.home"] = fake_state("exceptional", temperature=50, temperature_unit="°F")
        page = self._page([{"id": "t1", "type": "weather", "entity_id": "weather.home", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        icon_obj = next(o for o in render.objects if o.get("text_font") == 48)
        self.assertEqual(icon_obj["text"], chr(int(layout.DEFAULT_WEATHER_ICON, 16)))

    def test_weather_tile_unavailable_renders_dashes(self):
        self.states["weather.home"] = fake_state("unavailable")
        page = self._page([{"id": "t1", "type": "weather", "entity_id": "weather.home", "row": 0, "col": 0}])
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        temp_obj = next(o for o in render.objects if o.get("text_font") == 24)
        self.assertEqual(temp_obj["text"], "--")

    def test_tile_ids_do_not_collide_across_tiles(self):
        tiles = [
            {"id": f"t{i}", "type": "entity", "entity_id": "switch.lamp", "row": 0, "col": i % 3}
            for i in range(5)
        ]
        page = self._page(tiles)
        alloc = layout.option_page_allocator(50)
        render = layout.render_tile_page(2, page, self.lookup, alloc)
        ids = [o["id"] for o in render.objects]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tile_base_id_sequential_and_clear_of_popup_overlay_range(self):
        bases = [layout.tile_base_id(i) for i in range(layout.MAX_TILES_PER_PAGE)]
        self.assertEqual(bases[0], 1)
        self.assertEqual(bases[1], 1 + layout.TILE_ID_BUDGET)
        # __init__.py pre-arms popup-overlay chrome at ids 193..197 on every
        # page (see _publish_page_num) — the highest id used by the last
        # tile (base + budget - 1) must never reach that far.
        self.assertLess(bases[-1] + layout.TILE_ID_BUDGET - 1, 193)


class GaugeSeverityTests(unittest.TestCase):
    def test_litter_waste_bands_are_green_yellow_red(self):
        bands = layout.gauge_severity_bands({"green": 0, "yellow": 50, "red": 80}, 0, 100)
        self.assertEqual([(b.key, b.start_value, b.end_value, b.start_angle, b.end_angle) for b in bands], [
            ("green", 0, 50, 135, 270),
            ("yellow", 50, 80, 270, 351),
            ("red", 80, 100, 351, 45),
        ])
        self.assertEqual([b.color for b in bands], [
            layout.GAUGE_SEVERITY_COLORS["green"],
            layout.GAUGE_SEVERITY_COLORS["yellow"],
            layout.GAUGE_SEVERITY_COLORS["red"],
        ])

    def test_inverted_salt_bands_put_red_at_the_low_end(self):
        bands = layout.gauge_severity_bands({"red": 0, "yellow": 3, "green": 10}, 0, 18)
        self.assertEqual([(b.key, b.start_value, b.end_value, b.start_angle, b.end_angle) for b in bands], [
            ("red", 0, 3, 135, 180),
            ("yellow", 3, 10, 180, 285),
            ("green", 10, 18, 285, 45),
        ])

    def test_subset_and_unsorted_keys(self):
        only_red = layout.gauge_severity_bands({"red": 80}, 0, 100)
        self.assertEqual([(b.key, b.start_value, b.end_value) for b in only_red], [("red", 80, 100)])
        # Leading gap (nothing from 0 to 20) stays uncolored — no extra band.
        gapped = layout.gauge_severity_bands({"red": 80, "green": 20}, 0, 100)
        self.assertEqual([(b.key, b.start_value, b.end_value) for b in gapped], [
            ("green", 20, 80),
            ("red", 80, 100),
        ])

    def test_invalid_entries_are_ignored(self):
        bands = layout.gauge_severity_bands(
            {"green": 0, "yellow": "nope", "red": None, "blue": 10, "orange": 40}, 0, 100
        )
        self.assertEqual([b.key for b in bands], ["green"])
        self.assertEqual(bands[0].end_value, 100)
        self.assertEqual(layout.gauge_severity_bands(None, 0, 100), [])
        self.assertEqual(layout.gauge_severity_bands({}, 0, 100), [])
        self.assertEqual(layout.gauge_severity_bands({"red": True}, 0, 100), [])

    def test_thresholds_outside_the_range_collapse(self):
        # Below min clamps to the start; at/above max has no width and is dropped.
        bands = layout.gauge_severity_bands({"green": -10, "yellow": 50, "red": 150}, 0, 100)
        self.assertEqual([(b.key, b.start_value, b.end_value) for b in bands], [
            ("green", 0, 50),
            ("yellow", 50, 100),
        ])

    def test_duplicate_thresholds_drop_the_zero_width_slice(self):
        bands = layout.gauge_severity_bands({"green": 50, "yellow": 50, "red": 80}, 0, 100)
        self.assertEqual([(b.key, b.start_value, b.end_value) for b in bands], [
            ("yellow", 50, 80),
            ("red", 80, 100),
        ])

    def test_needle_points_follow_the_sweep(self):
        # Mid-scale (50 of 0..100) is openHASP 270°, straight up: tip above the hub.
        up = layout.gauge_needle_points(50, 50, 10, 40, 50, 0, 100)
        self.assertEqual(up[1][0], 50)
        self.assertLess(up[1][1], 50)
        # Minimum parks at 135°, down-left.
        low = layout.gauge_needle_points(50, 50, 10, 40, 0, 0, 100)
        self.assertLess(low[1][0], 50)
        self.assertGreater(low[1][1], 50)
        # Maximum is 45°, down-right.
        high = layout.gauge_needle_points(50, 50, 10, 40, 100, 0, 100)
        self.assertGreater(high[1][0], 50)
        self.assertGreater(high[1][1], 50)

    def test_normalize_severity_keeps_known_numeric_levels(self):
        self.assertEqual(
            layout.normalize_gauge_severity({"green": 0, "yellow": "50", "red": 80.5, "blue": 1, "Green": 9}),
            {"green": 0, "yellow": 50, "red": 80.5},
        )
        self.assertIsNone(layout.normalize_gauge_severity({"blue": 1}))
        self.assertIsNone(layout.normalize_gauge_severity("nope"))
        tile = {"id": "t1", "type": "gauge", "entity_id": "sensor.waste", "min": 0, "max": 100,
                "severity": {"red": "80", "green": 0, "yellow": 50, "nope": 1}}
        normalized = layout.normalize_tile(tile)
        self.assertEqual(normalized["severity"], {"green": 0, "yellow": 50, "red": 80})
        self.assertEqual(normalized["entity_id"], "sensor.waste")
        self.assertNotIn("severity", layout.normalize_tile({"type": "gauge", "severity": {"blue": 1}}))
        entity = {"type": "entity", "entity_id": "switch.lamp"}
        self.assertIs(layout.normalize_tile(entity), entity)


class GaugeSeverityRenderTests(unittest.TestCase):
    def setUp(self):
        self.states = {"sensor.waste": fake_state("72", friendly_name="Zander Litter", unit_of_measurement="%")}

    def lookup(self, entity_id):
        return self.states.get(entity_id)

    def _render(self, tile):
        page = {"columns": 3, "rows": 2, "tiles": [tile]}
        return layout.render_tile_page(2, page, self.lookup, layout.option_page_allocator(50))

    def _litter_tile(self, **extra):
        tile = {
            "id": "t1", "type": "gauge", "entity_id": "sensor.waste", "row": 0, "col": 0,
            "min": 0, "max": 100, "severity": {"green": 0, "yellow": 50, "red": 80},
        }
        tile.update(extra)
        return tile

    def test_severity_gauge_draws_three_bands_a_needle_and_the_value(self):
        render = self._render(self._litter_tile())
        for obj in render.objects:
            json.dumps(obj)
        self.assertEqual(len(render.objects), 7)
        arcs = [o for o in render.objects if o.get("obj") == "arc"]
        self.assertEqual([(a["line_color"], a["start_angle"], a["end_angle"]) for a in arcs], [
            (layout.GAUGE_SEVERITY_COLORS["green"], 135, 270),
            (layout.GAUGE_SEVERITY_COLORS["yellow"], 270, 351),
            (layout.GAUGE_SEVERITY_COLORS["red"], 351, 45),
        ])
        for arc in arcs:
            # Indicator stroke matches the band so the slice is solid whichever part openHASP paints.
            self.assertEqual(arc["line_color10"], arc["line_color"])
            self.assertEqual(arc["start_angle10"], arc["start_angle"])
            self.assertEqual(arc["end_angle10"], arc["end_angle"])
            self.assertEqual(arc["val"], 100)
            self.assertFalse(arc["adjustable"])
        needle = next(o for o in render.objects if o.get("obj") == "line")
        self.assertEqual(needle["line_color"], layout.GAUGE_NEEDLE_COLOR)
        self.assertEqual(needle["auto_size"], 0)
        self.assertEqual(needle["y_invert"], 0)
        label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(label["text"], "72%")
        target = render.gauge_map["sensor.waste"][0]
        self.assertEqual(needle["points"], layout.gauge_needle_points(
            target.center_x, target.center_y, target.inner_radius, target.outer_radius, 72, 0, 100,
        ))
        self.assertIsNone(target.arc_id)
        self.assertEqual(target.needle_id, needle["id"])

    def test_severity_objects_stay_inside_the_tile_id_budget(self):
        render = self._render(self._litter_tile())
        base = layout.tile_base_id(0)
        ids = [o["id"] for o in render.objects]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(base <= i <= base + layout.TILE_ID_BUDGET - 1 for i in ids))
        self.assertLessEqual(max(ids), base + layout.GAUGE_VALUE_ID_OFFSET)
        tiles = [
            {"id": f"t{i}", "type": "gauge", "entity_id": "sensor.waste",
             "row": 0, "col": 0, "severity": {"green": 0, "yellow": 50, "red": 80}}
            for i in range(layout.MAX_TILES_PER_PAGE)
        ]
        full = layout.render_tile_page(
            2, {"columns": 3, "rows": 2, "tiles": tiles}, self.lookup, layout.option_page_allocator(50),
        )
        self.assertLess(max(o["id"] for o in full.objects), 193)

    def test_inverted_thresholds_render_red_then_green(self):
        self.states["sensor.waste"] = fake_state("4", unit_of_measurement="in")
        render = self._render({
            "id": "t1", "type": "gauge", "entity_id": "sensor.waste", "row": 0, "col": 0,
            "min": 0, "max": 18, "severity": {"red": 0, "yellow": 3, "green": 10},
        })
        arcs = [o for o in render.objects if o.get("obj") == "arc"]
        self.assertEqual([a["line_color"] for a in arcs], [
            layout.GAUGE_SEVERITY_COLORS["red"],
            layout.GAUGE_SEVERITY_COLORS["yellow"],
            layout.GAUGE_SEVERITY_COLORS["green"],
        ])
        self.assertEqual(arcs[0]["start_angle"], 135)
        self.assertEqual(arcs[-1]["end_angle"], 45)
        label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(label["text"], "4in")

    def test_unavailable_parks_the_needle_and_shows_dashes(self):
        self.states["sensor.waste"] = fake_state("unavailable")
        render = self._render(self._litter_tile())
        needle = next(o for o in render.objects if o.get("obj") == "line")
        target = render.gauge_map["sensor.waste"][0]
        parked = layout.gauge_needle_points(
            target.center_x, target.center_y, target.inner_radius, target.outer_radius, 0, 0, 100,
        )
        self.assertEqual(needle["points"], parked)
        label = next(o for o in render.objects if o.get("obj") == "label" and o.get("align") == "center")
        self.assertEqual(label["text"], "--")

    def test_missing_severity_keeps_the_single_arc(self):
        render = self._render({
            "id": "t1", "type": "gauge", "entity_id": "sensor.waste", "row": 0, "col": 0,
            "min": 0, "max": 100,
        })
        arcs = [o for o in render.objects if o.get("obj") == "arc"]
        self.assertEqual(len(arcs), 1)
        self.assertNotIn("line", {o.get("obj") for o in render.objects})
        self.assertEqual(arcs[0]["arc_color"], layout.DARK_PALETTE["gauge_arc"])
        self.assertEqual(arcs[0]["val"], 72)
        target = render.gauge_map["sensor.waste"][0]
        self.assertEqual(target.arc_id, arcs[0]["id"])
        self.assertIsNone(target.needle_id)

    def test_live_update_moves_the_needle_and_the_label(self):
        render = self._render(self._litter_tile())
        target = render.gauge_map["sensor.waste"][0]
        low = dict(layout.gauge_live_updates(target, fake_state("40", unit_of_measurement="%")))
        high = dict(layout.gauge_live_updates(target, fake_state("90", unit_of_measurement="%")))
        points_key = f"p2b{target.needle_id}.points"
        text_key = f"p2b{target.label_id}.text"
        self.assertEqual(set(low), {points_key, text_key})
        self.assertEqual(low[text_key], "40%")
        self.assertEqual(high[text_key], "90%")
        self.assertNotEqual(low[points_key], high[points_key])
        self.assertEqual(
            json.loads(high[points_key]),
            layout.gauge_needle_points(
                target.center_x, target.center_y, target.inner_radius, target.outer_radius, 90, 0, 100,
            ),
        )
        unavailable = dict(layout.gauge_live_updates(target, fake_state("unavailable")))
        self.assertEqual(unavailable[text_key], "--")
        self.assertEqual(
            json.loads(unavailable[points_key]),
            layout.gauge_needle_points(
                target.center_x, target.center_y, target.inner_radius, target.outer_radius, 0, 0, 100,
            ),
        )

    def test_live_update_plain_gauge_still_publishes_arc_val(self):
        render = self._render({
            "id": "t1", "type": "gauge", "entity_id": "sensor.waste", "row": 0, "col": 0,
            "min": 0, "max": 100,
        })
        target = render.gauge_map["sensor.waste"][0]
        updates = dict(layout.gauge_live_updates(target, fake_state("72", unit_of_measurement="%")))
        self.assertEqual(float(updates[f"p2b{target.arc_id}.val"]), 72)
        self.assertEqual(updates[f"p2b{target.label_id}.text"], "72%")
        self.assertFalse(any(key.endswith(".points") for key in updates))


if __name__ == "__main__":
    unittest.main()
