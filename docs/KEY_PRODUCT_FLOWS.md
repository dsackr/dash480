# Key Product Flows (KPFs) — Dash480

This document defines the Key Product Flows (KPFs) for the `dash480` Home Assistant custom integration. It serves as the source of truth for the user-facing capabilities provided by this integration, detailing their entry points, failure consequences, and current test coverage.

All contributors must keep this document up-to-date when introducing or modifying user-facing features.

---

## 1. Panel Discovery & Configuration
Allows the user to add a Dash480 panel configuration entry and customize the Node Name (MQTT topic identifier), Home Title, and Temperature Sensor entity for the panel header.
- **Entry points**: `config_flow.py` (`Dash480ConfigFlow`), `__init__.py` (`_options_updated`).
- **If it silently breaks**: Users cannot add panels, or changes to the Node Name, Home Title, or Temperature Sensor do not propagate to the header objects.
- **Test status**: **Gap** (tested manually).

## 2. Page Management (Add/Remove Page)
Allows the user to add multiple page configuration entries under a single panel. Each page configuration entry holds configuration options for its layout type and slot entity assignments.
- **Entry points**: `__init__.py` (`async_setup_entry`), `select.py` (`Dash480PageLayoutSelect`).
- **If it silently breaks**: Adding pages fails, page orders collide, or page configurations do not persist.
- **Test status**: **Gap** (tested manually).

## 3. Entity picker & dynamic slot assignment (Add/Remove Entity)
Allows the user to dynamically add Home Assistant entities to a specific page's slots using helper select entities and the "Add Entity" button, or clear slots.
- **Entry points**: `select.py` (`Dash480AddEntitySelect`, `Dash480RemoveSlotSelect`), `button.py` (`Dash480AddEntityButton`, `Dash480RemoveSlotButton`).
- **If it silently breaks**: Dropdowns fail to list entities, slot assignments are not saved, or the screen doesn't update upon slot changes.
- **Test status**: **Gap** (tested manually).

## 4. MQTT Layout Publishing (LWT & online push)
Publishes the full JSONL layout template over MQTT whenever the openHASP device connects and publishes `online` to its LWT (Last Will and Testament) topic, ensuring the screen layout is synchronized.
- **Entry points**: `__init__.py` (`push_layout`, `_publish_all`, `_publish_page_num`).
- **If it silently breaks**: The screen remains blank or displays the "Waiting on Home Assistant..." screen indefinitely upon rebooting.
- **Test status**: **Gap** (tested manually).

## 5. Basic Tile Layout & Geometry
Resolves the appropriate layout template (3x2 grid, 3x3 grid, clock top, shades row) based on cover occupancy, and allocates slot dimensions, coordinates, and label positions.
- **Entry points**: `layout.py` (`resolve_layout`, `assign_slots`, `cell_xy`, `cell_wh`, `render_page`, `render_tile_page`).
- **If it silently breaks**: Tiles overlap, labels render in incorrect positions, or layouts default incorrectly.
- **Test status**: **Backend-tested** — `tests/test_layout.py` (`ResolveLayoutTests`, `AssignSlotsTests`, `GeometryTests`).

## 6. Domain-specific Tile Dispatch (Switch, Light, Cover, Fan, Sensor)
Draws the default visual controls (toggle buttons, labels, and icons) for standard Home Assistant domains.
- **Entry points**: `layout.py` (`_dispatch_entity_content`).
- **If it silently breaks**: Light toggles, switch buttons, or sensor values are missing from tiles or display the wrong icons.
- **Test status**: **Backend-tested** — `tests/test_layout.py` (`RenderPageTests`, `WeatherTests`).

## 7. Interactive Popup Controls (Fan Speed & Light Color)
Intercepts touch events on the openHASP device for fan and color-capable light tiles, displaying popup menus to adjust fan speeds (Off/Low/Med/High) or light colors (Off/Red/Green/Blue/Warm/Cool).
- **Entry points**: `layout.py` (`_dispatch_entity_content`), `__init__.py` (`_state_event`, `_publish_option_pages`).
- **If it silently breaks**: Tapping a tile does not open the popup, color changes do not tint the icon, or MQTT commands fail to propagate adjustments back to Home Assistant.
- **Test status**: **Gap** (tested manually).

## 8. Gauge Tile Integration
Renders numeric sensors as graphical gauge rings on the panel screen, translating numerical values to circle arc sizes and labels.
- **Entry points**: `layout.py` (`_dispatch_entity_content`), `__init__.py` (`_make_gauge_cb`).
- **If it silently breaks**: Gauge tiles render blank, or the arc shape does not update when sensor values change.
- **Test status**: **Backend-tested** — `tests/test_layout.py` (`GaugeTests`).

## 9. Weather Tile Integration
Renders weather entities as summary condition text/icon tiles and maps state updates to dynamic weather icon strings.
- **Entry points**: `layout.py` (`_dispatch_entity_content`), `__init__.py` (`_make_weather_cb`).
- **If it silently breaks**: Weather tiles do not display or weather conditions/temperatures fail to sync.
- **Test status**: **Backend-tested** — `tests/test_layout.py` (`WeatherTests`).

## 10. Generic Camera Thumbnail Integration
Detects any Home Assistant camera entity, rendering it as an unauthenticated PNG image object, and pushes cache-busted source updates when the camera state or snapshot changes.
- **Entry points**: `layout.py` (`_dispatch_entity_content`), `__init__.py` (`Dash480CameraThumbnailView`, `_make_camera_cb`).
- **If it silently breaks**: Camera display tiles are blank or fail to update when the camera receives a new snapshot.
- **Test status**: **Backend-tested** — `tests/test_layout.py` (`test_camera_tile_renders_generic_image`).

## 11. Custom Battery Progress Icon
Renders battery level sensors as graphical battery shapes (border outline, terminal cap, color thresholds, and inner progress fill) instead of a simple text percentage value.
- **Entry points**: `layout.py` (`_dispatch_entity_content`), `__init__.py` (`_make_battery_cb`).
- **If it silently breaks**: Battery levels render as simple numbers, or progress bar sizes and colors do not match the percentage thresholds.
- **Test status**: **Gap** (tested manually).

## 12. Visual Builder Mockup & Live Preview
Renders interactive mockups of tiles, gauges, weather icons, camera snapshots, and battery icons inside the Home Assistant dashboard visual editor.
- **Entry points**: `frontend/src/preview-canvas.ts` (`_renderTile`), `websocket_api.py` (`ws_render_preview`).
- **If it silently breaks**: The visual editor mockup does not match the on-screen layout, or camera snapshots and battery fills do not render in the preview.
- **Test status**: **Gap** (tested manually).
