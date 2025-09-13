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

        role = self.config_entry.data.get("role", "panel")
        options = {**self.config_entry.options}
        if role == "panel":
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
        # Page options: order, title, slots
        data_schema = vol.Schema(
            {
                vol.Required("page_order", default=self.config_entry.data.get("page_order", 2)): selector({"number": {"min": 2, "max": 99, "mode": "box"}}),
                vol.Optional("title", default=options.get("title", "")): selector({"text": {}}),
                vol.Optional("s1", default=options.get("s1", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
                vol.Optional("s2", default=options.get("s2", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
                vol.Optional("s3", default=options.get("s3", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
                vol.Optional("s4", default=options.get("s4", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
                vol.Optional("s5", default=options.get("s5", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
                vol.Optional("s6", default=options.get("s6", "")): selector({"entity": {"domain": ["switch", "light", "fan", "sensor"]}}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return Dash480OptionsFlowHandler(config_entry)
