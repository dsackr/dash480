"""Select platform for Dash480 (Entity Picker for pages)."""
from __future__ import annotations

from typing import List, Dict

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


ALLOWED_DOMAINS = {"switch", "light", "fan", "sensor"}

LAYOUT_OPTIONS = {
    "grid_3x3": "Grid 3×3",
    "clock_top": "Clock Top + 2 rows",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    role = config_entry.data.get("role", "panel")
    entities: List[SelectEntity] = []
    if role == "page":
        p = int(config_entry.data.get("page_order", 2))
        entities.append(Dash480PageLayoutSelect(hass, config_entry, p))
        entities.append(Dash480AddEntitySelect(hass, config_entry, p))
        entities.append(Dash480RemoveSlotSelect(hass, config_entry, p))
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
        self._current_entity: str | None = entry.options.get("pending_entity") or None
        self._current_label: str | None = None
        self._labels_to_ids: Dict[str, str] = {}
        self._unsub_update = None

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
        opts: list[tuple[str, str]] = []  # (label, entity_id)
        for st in self.hass.states.async_all():
            assert isinstance(st, State)
            d = st.entity_id.split(".")[0]
            if d in ALLOWED_DOMAINS and st.entity_id not in assigned:
                fname = st.attributes.get("friendly_name") or st.entity_id
                label = f"{fname} ({st.entity_id})"
                opts.append((label, st.entity_id))
        opts.sort(key=lambda x: x[0].lower())
        self._labels_to_ids = {label: eid for (label, eid) in opts}
        # refresh current label from current entity
        if self._current_entity:
            for label, eid in opts:
                if eid == self._current_entity:
                    self._current_label = label
                    break
        else:
            self._current_label = None
        return [label for (label, _) in opts]

    @property
    def current_option(self) -> str | None:
        return self._current_label

    async def async_select_option(self, option: str) -> None:
        # Persist selection and immediately add to first empty slot, then republish
        eid = self._labels_to_ids.get(option) or option
        self._current_entity = eid
        self._current_label = option
        opts = {**self._entry.options}
        # find first empty slot s1..s12
        slot: int | None = None
        for i in range(1, 13):
            key = f"s{i}"
            if not (opts.get(key) or "").strip():
                slot = i
                break
        if slot is None:
            # No available slots; just store pending
            opts["pending_entity"] = eid
            self.hass.config_entries.async_update_entry(self._entry, options=opts)
            self.async_write_ha_state()
            return
        # assign and clear pending
        opts[f"s{slot}"] = eid
        opts["pending_entity"] = ""
        self.hass.config_entries.async_update_entry(self._entry, options=opts)
        # trigger publish
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(
                DOMAIN,
                "publish_all",
                {"entry_id": panel_id},
                blocking=False,
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        async def _on_update(hass: HomeAssistant, updated: ConfigEntry):
            # Reflect when Add button clears pending_entity and when slots change (updates options list)
            self._current_entity = updated.options.get("pending_entity") or None
            self._current_label = None
            self.async_write_ha_state()
        self._unsub_update = self._entry.add_update_listener(_on_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_update:
            try:
                self._unsub_update()
            except Exception:
                pass
            self._unsub_update = None


class Dash480RemoveSlotSelect(SelectEntity):
    """List of populated slots to remove from this page."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, page: int) -> None:
        self.hass = hass
        self._entry = entry
        self._page = page
        self._device_identifier = f"dash480_page_{entry.entry_id}"
        self._device_name = f"Dash480 Page {page}"
        self._attr_name = f"P{page} Remove Slot"
        self._attr_icon = "mdi:minus-box-multiple"
        self._attr_unique_id = f"{self._device_identifier}_remove_picker"
        self._current_label: str | None = None
        self._labels_to_slot: Dict[str, int] = {}
        self._unsub_update = None

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
        labels: list[str] = []
        mapping: Dict[str, int] = {}
        for i in range(1, 13):
            eid = (self._entry.options.get(f"s{i}") or "").strip()
            if not eid:
                continue
            st = self.hass.states.get(eid)
            fname = st.attributes.get("friendly_name") if st else None
            lbl = f"Slot {i} — {fname or eid}"
            labels.append(lbl)
            mapping[lbl] = i
        self._labels_to_slot = mapping
        if self._current_label not in labels:
            self._current_label = None
        return labels

    @property
    def current_option(self) -> str | None:
        return self._current_label

    async def async_select_option(self, option: str) -> None:
        # Immediately remove the selected slot and republish
        self._current_label = option
        slot = self._labels_to_slot.get(option)
        opts = {**self._entry.options}
        if slot is None:
            opts["pending_remove_slot"] = None
            self.hass.config_entries.async_update_entry(self._entry, options=opts)
            self.async_write_ha_state()
            return
        opts[f"s{slot}"] = ""
        opts["pending_remove_slot"] = None
        self.hass.config_entries.async_update_entry(self._entry, options=opts)
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(
                DOMAIN,
                "publish_all",
                {"entry_id": panel_id},
                blocking=False,
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        async def _on_update(hass: HomeAssistant, updated: ConfigEntry):
            sel = updated.options.get("pending_remove_slot")
            if sel is None:
                self._current_label = None
            self.async_write_ha_state()
        self._unsub_update = self._entry.add_update_listener(_on_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_update:
            try:
                self._unsub_update()
            except Exception:
                pass
            self._unsub_update = None


class Dash480PageLayoutSelect(SelectEntity):
    """Select a layout template for this page."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, page: int) -> None:
        self.hass = hass
        self._entry = entry
        self._page = page
        self._device_identifier = f"dash480_page_{entry.entry_id}"
        self._device_name = f"Dash480 Page {page}"
        self._attr_name = f"P{page} Layout"
        self._attr_icon = "mdi:view-grid"
        self._attr_unique_id = f"{self._device_identifier}_layout"
        self._unsub_update = None

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
        return list(LAYOUT_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        key = self._entry.options.get("layout", "grid_3x3")
        return LAYOUT_OPTIONS.get(key)

    async def async_select_option(self, option: str) -> None:
        # Map back from label to key
        key = next((k for k, v in LAYOUT_OPTIONS.items() if v == option), None)
        if not key:
            return
        opts = {**self._entry.options, "layout": key}
        self.hass.config_entries.async_update_entry(self._entry, options=opts)
        # Republish this page
        panel_id = self._entry.data.get("panel_entry_id")
        if panel_id:
            await self.hass.services.async_call(DOMAIN, "publish_all", {"entry_id": panel_id}, blocking=False)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        async def _on_update(hass: HomeAssistant, updated: ConfigEntry):
            self.async_write_ha_state()
        self._unsub_update = self._entry.add_update_listener(_on_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_update:
            try:
                self._unsub_update()
            except Exception:
                pass
            self._unsub_update = None
