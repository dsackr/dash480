"""Storage-backed "visual pages" — the data model for the new sidebar-panel
page builder.

Deliberately NOT `homeassistant.helpers.collection` and NOT config entries:
the entire point of the visual builder is to stop creating per-tile native HA
entities. This is just a flat JSON list of page dicts, persisted via
`homeassistant.helpers.storage.Store` and mutated under an asyncio.Lock so
concurrent websocket calls can't race each other.

Existing legacy Page config entries (role == "page", per-slot s1..s12
options) are untouched by this module — see `legacy_page_orders()`, which
lets both worlds share one page_order allocator so a visual page and a
legacy Page can never claim the same page number on the same panel.
"""
from __future__ import annotations

import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_pages"

# Page-order allocation range — matches the legacy Page config-flow allocator
# (config_flow.py's async_step_page) so both models share one numbering space.
MIN_PAGE_ORDER = 1
MAX_PAGE_ORDER = 9

DEFAULT_COLUMNS = 3
DEFAULT_ROWS = 2


def legacy_page_orders(hass: HomeAssistant, panel_entry_id: str) -> set[int]:
    """Page-order numbers already claimed by legacy Page config entries for this panel."""
    orders: set[int] = set()
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get("role") == "page" and entry.data.get("panel_entry_id") == panel_entry_id:
            order = entry.data.get("page_order")
            if isinstance(order, int) or (isinstance(order, str) and order.isdigit()):
                orders.add(int(order))
    return orders


class VisualPagesStore:
    """In-memory list of visual pages, backed by a single Store file."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._pages: list[dict[str, Any]] = []
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        data = await self._store.async_load()
        self._pages = list((data or {}).get("pages", []))
        self._loaded = True

    async def _async_save(self) -> None:
        await self._store.async_save({"pages": self._pages})

    def all_pages(self) -> list[dict[str, Any]]:
        """Every visual page across every panel (already-loaded snapshot)."""
        return list(self._pages)

    def list_pages(self, panel_entry_id: str) -> list[dict[str, Any]]:
        return [p for p in self._pages if p.get("panel_entry_id") == panel_entry_id]

    def get_page(self, page_id: str) -> dict[str, Any] | None:
        return next((p for p in self._pages if p["id"] == page_id), None)

    def allocate_page_order(self, panel_entry_id: str) -> int | None:
        """First free page_order (1..9) for this panel, across legacy + visual pages."""
        used = legacy_page_orders(self.hass, panel_entry_id)
        used |= {int(p["page_order"]) for p in self.list_pages(panel_entry_id)}
        for candidate in range(MIN_PAGE_ORDER, MAX_PAGE_ORDER + 1):
            if candidate not in used:
                return candidate
        return None

    async def async_create_page(
        self,
        panel_entry_id: str,
        title: str,
        columns: int = DEFAULT_COLUMNS,
        rows: int = DEFAULT_ROWS,
        tiles: list[dict[str, Any]] | None = None,
        page_order: int | None = None,
    ) -> dict[str, Any]:
        if page_order is None:
            page_order = self.allocate_page_order(panel_entry_id)
            if page_order is None:
                raise ValueError(f"No free page_order (1..{MAX_PAGE_ORDER}) left for panel {panel_entry_id}")
        else:
            used = legacy_page_orders(self.hass, panel_entry_id)
            used |= {int(p["page_order"]) for p in self.list_pages(panel_entry_id)}
            if page_order in used:
                raise ValueError(f"page_order {page_order} is already in use for panel {panel_entry_id}")
        page = {
            "id": uuid.uuid4().hex,
            "panel_entry_id": panel_entry_id,
            "page_order": page_order,
            "title": title,
            "columns": columns,
            "rows": rows,
            "tiles": tiles or [],
        }
        self._pages.append(page)
        await self._async_save()
        return page

    async def async_update_page(self, page_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        page = self.get_page(page_id)
        if page is None:
            return None
        page.update({k: v for k, v in patch.items() if k not in ("id", "panel_entry_id")})
        await self._async_save()
        return page

    async def async_delete_page(self, page_id: str) -> bool:
        before = len(self._pages)
        self._pages = [p for p in self._pages if p["id"] != page_id]
        if len(self._pages) == before:
            return False
        await self._async_save()
        return True

    async def async_reorder(self, panel_entry_id: str, ordered_ids: list[str]) -> None:
        by_id = {p["id"]: p for p in self.list_pages(panel_entry_id)}
        for order, page_id in enumerate(ordered_ids, start=1):
            page = by_id.get(page_id)
            if page is not None:
                page["page_order"] = order
        await self._async_save()


def async_get_store(hass: HomeAssistant) -> VisualPagesStore:
    """Return the shared VisualPagesStore, creating it if this is the first call.

    Callers must still `await store.async_load()` before first use — this
    only guarantees a single shared instance across the whole integration.
    """
    store = hass.data.setdefault(DOMAIN, {}).get("visual_pages_store")
    if store is None:
        store = VisualPagesStore(hass)
        hass.data[DOMAIN]["visual_pages_store"] = store
    return store


async def async_allocate_page_order(hass: HomeAssistant, panel_entry_id: str) -> int | None:
    """First free page_order for `panel_entry_id`, across legacy Page entries and visual pages.

    Shared by config_flow.py's legacy Page creation step and the websocket
    API's visual-page creation, so the two models can never collide on the
    same page number for the same panel.
    """
    store = async_get_store(hass)
    await store.async_load()
    return store.allocate_page_order(panel_entry_id)
