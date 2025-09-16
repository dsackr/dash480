"""Config flow for Dash480."""
from __future__ import annotations

from typing import Any, List

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import selector

from .const import DOMAIN


class Dash480ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dash480."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """First step: choose what to add (Panel or Page)."""
        if user_input is not None:
            role = user_input.get("role")
            if role == "panel":
                return await self.async_step_panel()
            if role == "page":
                return await self.async_step_page()

        data_schema = vol.Schema(
            {
                vol.Required("role", default="panel"): selector(
                    {"select": {"options": [
                        {"label": "Panel (screen)", "value": "panel"},
                        {"label": "Page (tiles for a panel)", "value": "page"},
                    ]}}
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_panel(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            node = (user_input.get("node_name") or "").strip()
            if not node:
                errors["node_name"] = "invalid_node"
            else:
                return self.async_create_entry(
                    title=f"Dash480 ({node})",
                    data={"role": "panel", "node_name": node},
                )
        schema = vol.Schema({vol.Required("node_name"): selector({"text": {}})})
        return self.async_show_form(step_id="panel", data_schema=schema, errors=errors)

    async def async_step_page(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        # Collect existing panels
        panels: List[config_entries.ConfigEntry] = [
            e for e in self._async_current_entries() if e.data.get("role") == "panel"
        ]
        if not panels:
            errors["base"] = "no_panels"
        panel_options = [
            {"label": e.title or e.data.get("node_name", e.entry_id), "value": e.entry_id}
            for e in panels
        ]

        if user_input is not None and not errors:
            panel_id = user_input.get("panel")
            order = int(user_input.get("page_order") or 2)
            title = (user_input.get("title") or "").strip() or f"Page {order}"
            # Only set the title on creation; entities can be added later
            opts = {"title": title}
            return self.async_create_entry(
                title=f"Page {order}: {title}",
                data={"role": "page", "panel_entry_id": panel_id, "page_order": order},
                options=opts,
            )

        schema = vol.Schema(
            {
                vol.Required("panel"): selector({"select": {"options": panel_options}}),
                # Limit to 8 user pages: 2..9 (page 1 is Home)
                vol.Required("page_order", default=2): selector({"number": {"min": 2, "max": 9, "mode": "box"}}),
                vol.Optional("title", default=""): selector({"text": {}}),
            }
        )
        return self.async_show_form(step_id="page", data_schema=schema, errors=errors)
