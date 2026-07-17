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

    def test_camera_tile_renders_fraimic_image(self):
        import sys
        from unittest.mock import MagicMock
        
        mock_registry = MagicMock()
        mock_reg_entry = MagicMock()
        mock_reg_entry.platform = "fraimic"
        mock_reg_entry.domain = "camera"
        mock_reg_entry.config_entry_id = "test_entry_id"
        mock_registry.async_get.return_value = mock_reg_entry
        
        mock_er = MagicMock()
        mock_er.async_get.return_value = mock_registry
        
        mock_network = MagicMock()
        mock_network.get_url.return_value = "http://localhost:8123"
        
        mock_helpers = MagicMock()
        mock_helpers.entity_registry = mock_er
        mock_helpers.network = mock_network
        
        # Save original homeassistant modules if they exist
        orig_modules = {
            "homeassistant": sys.modules.get("homeassistant"),
            "homeassistant.helpers": sys.modules.get("homeassistant.helpers"),
            "homeassistant.helpers.entity_registry": sys.modules.get("homeassistant.helpers.entity_registry"),
            "homeassistant.helpers.network": sys.modules.get("homeassistant.helpers.network"),
        }
        
        try:
            sys.modules["homeassistant"] = MagicMock()
            sys.modules["homeassistant.helpers"] = mock_helpers
            sys.modules["homeassistant.helpers.entity_registry"] = mock_er
            sys.modules["homeassistant.helpers.network"] = mock_network
            
            slots = [("s1", "camera.living_room_frame_1_display")]
            alloc = layout.option_page_allocator(50)
            render = layout.render_page(2, "grid_3x2", slots, {}, self.lookup, alloc, hass=MagicMock())
            
            # Verify that fraimic_map has mapped the entity
            self.assertIn("camera.living_room_frame_1_display", render.fraimic_map)
            
            # Verify that the image object was rendered
            img_objs = [o for o in render.objects if o.get("obj") == "img"]
            self.assertEqual(len(img_objs), 1)
            self.assertEqual(img_objs[0]["id"], 12)  # base + 2 (base = 10)
            self.assertIn("fraimic_thumbnail/test_entry_id", img_objs[0]["src"])
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


if __name__ == "__main__":
    unittest.main()
