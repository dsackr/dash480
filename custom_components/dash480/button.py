"""Button platform for Dash480 (Publish actions)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.components import mqtt
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
    role = config_entry.data.get("role", "panel")
    if role == "panel":
        async_add_entities(
            [
                Dash480PublishAllButton(hass, config_entry),
                Dash480PublishHomeButton(hass, config_entry),
                Dash480ShowGridOverlayButton(hass, config_entry),
                Dash480HideGridOverlayButton(hass, config_entry),
            ]
        )
    else:
        async_add_entities([
            Dash480PublishPageButton(hass, config_entry),
            Dash480AddEntityButton(hass, config_entry),
            Dash480RemoveEntityButton(hass, config_entry),
        ])


class _BaseDashButton(ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        role = entry.data.get("role", "panel")
        if role == "panel":
            node = entry.data["node_name"]
            self._device_identifier = f"dash480_{node}"
            self._device_name = f"Dash480 ({node})"
        else:
            p = int(entry.data.get("page_order", 2))
            self._device_identifier = f"dash480_page_{entry.entry_id}"
            self._device_name = f"Dash480 Page {p}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=self._device_name,
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
            blocking=True,
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
            blocking=True,
        )


class Dash480PublishPageButton(_BaseDashButton):
    _attr_name = "Publish Page"
    _attr_unique_id_suffix = "publish_page"
    _attr_icon = "mdi:page-next"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        # Call panel publish_all to rebuild complete layout consistently
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(
                DOMAIN,
                "publish_all",
                {"entry_id": panel_id},
                blocking=True,
            )


class Dash480ShowGridOverlayButton(_BaseDashButton):
    _attr_name = "Show Grid Overlay"
    _attr_unique_id_suffix = "show_grid_overlay"
    _attr_icon = "mdi:grid"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        # Draw 3x2 grid lines on page 0 using green lines
        node = self._entry.data.get("node_name")
        if not node:
            return
        # Geometry consistent with integration
        base_x = 20
        col_w = 128
        col_gap = 24
        xs = [base_x, base_x + col_w + col_gap, base_x + 2 * (col_w + col_gap), base_x + 3 * (col_w + col_gap)]
        base_y = 80
        row_gap = 20
        avail = 430 - base_y
        tile_h = (avail - row_gap) // 2
        ys = [base_y, base_y + tile_h, base_y + tile_h + row_gap + tile_h]
        # Vertical lines ids 240..243
        for i, x in enumerate(xs):
            await mqtt.async_publish(
                self.hass,
                f"hasp/{node}/command/jsonl",
                f'{{"page":0,"obj":"obj","id":{240+i},"x":{x},"y":{base_y},"w":1,"h":{ys[-1]-base_y},"bg_color":"#00FF00","bg_opa":255,"border_width":0}}',
            )
        # Horizontal lines ids 244..246
        for j, y in enumerate(ys):
            await mqtt.async_publish(
                self.hass,
                f"hasp/{node}/command/jsonl",
                f'{{"page":0,"obj":"obj","id":{244+j},"x":{xs[0]},"y":{y},"w":{xs[-1]-xs[0]},"h":1,"bg_color":"#00FF00","bg_opa":255,"border_width":0}}',
            )


class Dash480HideGridOverlayButton(_BaseDashButton):
    _attr_name = "Hide Grid Overlay"
    _attr_unique_id_suffix = "hide_grid_overlay"
    _attr_icon = "mdi:grid-off"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        node = self._entry.data.get("node_name")
        if not node:
            return
        # Hide ids 240..246
        for _id in range(240, 247):
            await mqtt.async_publish(
                self.hass,
                f"hasp/{node}/command/p0o{_id}.hidden",
                "1",
            )


class Dash480AddEntityButton(_BaseDashButton):
    _attr_name = "Add Entity"
    _attr_unique_id_suffix = "add_entity"
    _attr_icon = "mdi:plus-box-multiple"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        # Read selected pending entity from page options
        opts = {**self._entry.options}
        ent = (opts.get("pending_entity") or "").strip()
        if not ent:
            return
        # find first empty slot s1..s12
        slot = None
        for i in range(1, 13):
            key = f"s{i}"
            if not (opts.get(key) or "").strip():
                slot = i
                break
        # if all full or entity already present, bail
        if slot is None or ent in {opts.get(f"s{i}") for i in range(1, 13)}:
            return
        # update options: assign slot and clear pending
        opts[f"s{slot}"] = ent
        opts["pending_entity"] = ""
        self.hass.config_entries.async_update_entry(self._entry, options=opts)
        # Trigger panel publish_all to update device
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(
                DOMAIN,
                "publish_all",
                {"entry_id": panel_id},
                blocking=False,
            )


class Dash480RemoveEntityButton(_BaseDashButton):
    _attr_name = "Remove Entity"
    _attr_unique_id_suffix = "remove_entity"
    _attr_icon = "mdi:minus-box-multiple"

    @property
    def unique_id(self) -> str:
        return f"{self._device_identifier}_{self._attr_unique_id_suffix}"

    async def async_press(self) -> None:
        # Read selected slot from options; if none, remove the last populated slot
        opts = {**self._entry.options}
        sel = opts.get("pending_remove_slot")
        slot: int | None = None
        if isinstance(sel, int) and 1 <= sel <= 12:
            slot = sel
        else:
            # find last non-empty slot
            for i in range(12, 0, -1):
                if (opts.get(f"s{i}") or "").strip():
                    slot = i
                    break
        if slot is None:
            return
        opts[f"s{slot}"] = ""
        opts["pending_remove_slot"] = None
        self.hass.config_entries.async_update_entry(self._entry, options=opts)
        # Trigger panel publish_all to update device
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(
                DOMAIN,
                "publish_all",
                {"entry_id": panel_id},
                blocking=False,
            )
