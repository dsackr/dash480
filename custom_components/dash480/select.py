"""Select platform for Dash480 (Entity Picker for pages)."""
from __future__ import annotations

from typing import List

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


ALLOWED_DOMAINS = {"switch", "light", "fan", "sensor"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    role = config_entry.data.get("role", "panel")
    entities: List[SelectEntity] = []
    if role == "page":
        p = int(config_entry.data.get("page_order", 2))
        entities.append(Dash480AddEntitySelect(hass, config_entry, p))
    async_add_entities(entities)


class Dash480AddEntitySelect(SelectEntity):
    """Dynamic list of HA entities to add to this page."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, page: int) -> None:
        self.hass = hass
        self._entry = entry
        self._page = page
        self._device_identifier = f"dash480_page_{entry.entry_id}"
        self._device_name = f"Dash480 Page {page}"
        self._attr_name = f"P{page} Add Entity"
        self._attr_icon = "mdi:playlist-plus"
        self._attr_unique_id = f"{self._device_identifier}_picker"
        self._current: str | None = entry.options.get("pending_entity") or None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=self._device_name,
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )

    @property
    def options(self) -> list[str]:
        # Dynamic list of candidate entities not already on this page
        page_opts = self._entry.options
        assigned = {str(page_opts.get(f"s{i}", "")).strip() for i in range(1, 13)}
        assigned = {a for a in assigned if a}
        items: list[str] = []
        # Note: Home Assistant's StateMachine returns a list of State objects
        for st in self.hass.states.async_all():
            assert isinstance(st, State)
            d = st.entity_id.split(".")[0]
            if d in ALLOWED_DOMAINS and st.entity_id not in assigned:
                items.append(st.entity_id)
        items.sort()
        return items

    @property
    def current_option(self) -> str | None:
        return self._current

    async def async_select_option(self, option: str) -> None:
        # Persist selected entity id as pending for the Add button
        self._current = option
        new_opts = {**self._entry.options, "pending_entity": option}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        self.async_write_ha_state()
