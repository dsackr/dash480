"""Persistence of gauge severity through the visual page store.

pages_store imports Home Assistant, which these tests stub. The package
itself is pre-registered so importing the store does not execute
dash480/__init__.py (that module needs a running HA instance).
"""
import asyncio
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = ROOT / "custom_components" / "dash480"


def _install_import_stubs():
    ha = types.ModuleType("homeassistant")
    core = types.ModuleType("homeassistant.core")
    helpers = types.ModuleType("homeassistant.helpers")
    storage = types.ModuleType("homeassistant.helpers.storage")

    class Store:
        def __init__(self, hass, version, key):
            self.hass = hass
            self.version = version
            self.key = key
            self.saved = None

        async def async_load(self):
            return self.saved

        async def async_save(self, data):
            self.saved = data

    core.HomeAssistant = object
    storage.Store = Store
    ha.core = core
    ha.helpers = helpers
    helpers.storage = storage
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.storage"] = storage

    components = types.ModuleType("custom_components")
    components.__path__ = [str(ROOT / "custom_components")]
    dash = types.ModuleType("custom_components.dash480")
    dash.__path__ = [str(PKG_DIR)]
    dash.__package__ = "custom_components.dash480"
    sys.modules["custom_components"] = components
    sys.modules["custom_components.dash480"] = dash


_install_import_stubs()

from custom_components.dash480 import pages_store  # noqa: E402


class _Entries:
    def async_entries(self, domain):
        return []


class GaugeSeverityPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.hass = SimpleNamespace(data={}, config_entries=_Entries())
        self.store = pages_store.VisualPagesStore(self.hass)

    def _run(self, coro):
        return asyncio.run(coro)

    def test_create_and_update_round_trip_severity(self):
        async def scenario():
            await self.store.async_load()
            page = await self.store.async_create_page(
                "panel1",
                "Home",
                tiles=[{
                    "id": "litter",
                    "type": "gauge",
                    "entity_id": "sensor.zander_waste",
                    "row": 0,
                    "col": 0,
                    "min": 0,
                    "max": 100,
                    "severity": {"red": "80", "green": 0, "yellow": 50, "nope": 1},
                }],
            )
            created = page["tiles"][0]["severity"]
            updated = await self.store.async_update_page(page["id"], {"tiles": [{
                "id": "salt",
                "type": "gauge",
                "entity_id": "sensor.garage_salt",
                "row": 0,
                "col": 1,
                "min": 0,
                "max": 18,
                "severity": {"green": 10, "yellow": "3", "red": 0, "blue": 4},
            }, {
                "id": "plain",
                "type": "gauge",
                "entity_id": "sensor.temp",
                "severity": {"blue": "nope"},
                "min": 0,
                "max": 100,
            }]})
            return created, updated

        created, updated = self._run(scenario())
        self.assertEqual(created, {"green": 0, "yellow": 50, "red": 80})
        tiles = {tile["id"]: tile for tile in updated["tiles"]}
        self.assertEqual(tiles["salt"]["severity"], {"green": 10, "yellow": 3, "red": 0})
        self.assertEqual(tiles["salt"]["max"], 18)
        self.assertNotIn("severity", tiles["plain"])
        # What was written to the Store is the same canonical page the API returns.
        saved = self.store._store.saved["pages"]
        self.assertEqual(saved[0]["tiles"][0]["severity"], {"green": 10, "yellow": 3, "red": 0})


if __name__ == "__main__":
    unittest.main()
