"""Config flow for Dash480."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class Dash480ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dash480."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            node_name = user_input["node_name"].strip()
            if not node_name:
                errors["node_name"] = "invalid_node"
            else:
                # Create the entry
                return self.async_create_entry(title=f"Dash480 ({node_name})", data={"node_name": node_name})

        data_schema = vol.Schema({vol.Required("node_name"): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
