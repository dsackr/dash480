"""Options flow for Dash480."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class Dash480OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="Dash480 Options", data=user_input)

        options = {**self.config_entry.options}
        data_schema = vol.Schema(
            {
                vol.Optional(
                    "home_title", default=options.get("home_title", self.config_entry.data.get("node_name", "Dash"))
                ): selector({"text": {}}),
                vol.Optional(
                    "temp_entity", default=options.get("temp_entity", "")
                ): selector({"entity": {"domain": "sensor"}}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return Dash480OptionsFlowHandler(config_entry)
