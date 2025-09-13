"""Number platform for Dash480 (pages count)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # Only for Panel entries
    if config_entry.data.get("role", "panel") == "panel":
        async_add_entities([Dash480PagesNumber(hass, config_entry)])


class Dash480PagesNumber(NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        node = config_entry.data["node_name"]
        self._device_identifier = f"dash480_{node}"
        self._attr_name = "Pages"
        self._attr_unique_id = f"{self._device_identifier}_pages"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 6
        self._attr_native_step = 1
        self._attr_native_value = int(config_entry.options.get("pages", 1))

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=f"Dash480 ({self.config_entry.data['node_name']})",
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )

    async def async_set_native_value(self, value: float) -> None:
        val = max(1, min(6, int(value)))
        opts = {**self.config_entry.options, "pages": val}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = val
        self.async_write_ha_state()
