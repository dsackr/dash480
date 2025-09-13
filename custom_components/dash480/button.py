"""Button platform for Dash480 (Publish actions)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities(
        [
            Dash480PublishAllButton(hass, config_entry),
            Dash480PublishHomeButton(hass, config_entry),
        ]
    )


class _BaseDashButton(ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        node = entry.data["node_name"]
        self._device_identifier = f"dash480_{node}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=f"Dash480 ({self._entry.data['node_name']})",
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )


class Dash480PublishAllButton(_BaseDashButton):
    _attr_name = "Publish All"
    _attr_unique_id_suffix = "publish_all"
    _attr_icon = "mdi:send"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN,
            "publish_all",
            {"entry_id": self._entry.entry_id},
            blocking=False,
        )


class Dash480PublishHomeButton(_BaseDashButton):
    _attr_name = "Publish Home"
    _attr_unique_id_suffix = "publish_home"
    _attr_icon = "mdi:home-export-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN,
            "publish_home",
            {"entry_id": self._entry.entry_id},
            blocking=False,
        )

