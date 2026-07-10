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


class HomeLayoutTests(unittest.TestCase):
    def test_title_and_temp_survive_quotes(self):
        objects = layout.home_layout_objects("plate", 'Dash "Home"', "72°")
        for obj in objects:
            json.dumps(obj)  # must not raise
        title_obj = next(o for o in objects if o.get("id") == 2 and o.get("page") == 0)
        self.assertEqual(title_obj["text"], 'Dash "Home"')

    def test_nav_icons_survive_json_roundtrip(self):
        objects = layout.home_layout_objects("plate", "Dash", "--")
        nav_ids = {90: "", 91: "", 92: ""}
        for obj in objects:
            if obj.get("page") == 0 and obj.get("id") in nav_ids:
                wire = json.dumps(obj)
                decoded = json.loads(wire)
                self.assertEqual(decoded["text"], nav_ids[obj["id"]])


class OptionPageAllocatorTests(unittest.TestCase):
    def test_sequential_starting_point(self):
        alloc = layout.option_page_allocator(50)
        self.assertEqual([alloc(), alloc(), alloc()], [50, 51, 52])


if __name__ == "__main__":
    unittest.main()
