"""Text platform for Dash480."""
from homeassistant.components.text import TextEntity
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
    """Set up text entities for Panel or Page entries."""
    role = config_entry.data.get("role", "panel")
    entities: list[TextEntity] = []
    if role == "panel":
        entities.append(Dash480NodeNameText(hass, config_entry))
        entities.append(Dash480HomeTitleText(hass, config_entry))
        entities.append(Dash480TempEntityText(hass, config_entry))
    else:
        # Page-specific title and slots
        p = int(config_entry.data.get("page_order", 2))
        entities.append(Dash480PageTitleText(hass, config_entry, p))
        # Provide 12 slots (auto-grid); options may be empty
        for s in range(1, 13):
            entities.append(Dash480SlotEntityText(hass, config_entry, p, s))
    async_add_entities(entities)


class Dash480NodeNameText(TextEntity):
    """Representation of the node name configuration text entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the text entity."""
        self.hass = hass
        self.config_entry = config_entry
        self._attr_name = "Node Name"

        node_name = config_entry.data["node_name"]
        self._device_identifier = f"dash480_{node_name}"
        self._attr_unique_id = f"{self._device_identifier}_nodename"
        self._attr_native_value = node_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=f"Dash480 ({self.native_value})",
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )

    async def async_set_value(self, value: str) -> None:
        """Set the new value (updates HA config only)."""
        current_name = self.native_value
        if current_name == value:
            return

        # Update the config entry in Home Assistant (no device hostname change)
        new_data = {**self.config_entry.data, "node_name": value}
        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

        # Integration reloads with the new node name
        self._attr_native_value = value
        self.async_write_ha_state()


class _BaseDashText(TextEntity):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        role = config_entry.data.get("role", "panel")
        if role == "panel":
            node = config_entry.data["node_name"]
            self._device_identifier = f"dash480_{node}"
            self._device_name = f"Dash480 ({node})"
        else:
            p = int(config_entry.data.get("page_order", 2))
            self._device_identifier = f"dash480_page_{config_entry.entry_id}"
            self._device_name = f"Dash480 Page {p}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=self._device_name,
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )


class Dash480HomeTitleText(_BaseDashText):
    """Header title text (center)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(hass, config_entry)
        self._attr_name = "Home Title"
        self._attr_unique_id = f"{self._device_identifier}_home_title"
        self._attr_native_value = config_entry.options.get(
            "home_title", config_entry.data.get("node_name", "Dash")
        )

    async def async_set_value(self, value: str) -> None:
        # Persist into options
        opts = {**self.config_entry.options, "home_title": value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()


class Dash480TempEntityText(_BaseDashText):
    """Header temperature entity (entity_id string)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(hass, config_entry)
        self._attr_name = "Temp Entity"
        self._attr_unique_id = f"{self._device_identifier}_temp_entity"
        self._attr_native_value = config_entry.options.get("temp_entity", "")

    async def async_set_value(self, value: str) -> None:
        opts = {**self.config_entry.options, "temp_entity": value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()


class Dash480PageTitleText(_BaseDashText):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, page: int) -> None:
        super().__init__(hass, config_entry)
        self.page = page
        self._attr_name = f"P{page} Title"
        self._attr_unique_id = f"{self._device_identifier}_title"
        self._attr_native_value = config_entry.options.get(f"p{page}_title", f"Page {page}")

    async def async_set_value(self, value: str) -> None:
        key = f"p{self.page}_title"
        opts = {**self.config_entry.options, key: value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()

        panel_entry_id = self.config_entry.data.get("panel_entry_id")
        if panel_entry_id:
            await self.hass.services.async_call(
                DOMAIN, "publish_all", {"entry_id": panel_entry_id}, blocking=False
            )

        panel_entry_id = self.config_entry.data.get("panel_entry_id")
        if panel_entry_id:
            await self.hass.services.async_call(
                DOMAIN, "publish_all", {"entry_id": panel_entry_id}, blocking=False
            )


class Dash480SlotEntityText(_BaseDashText):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, page: int, slot: int) -> None:
        super().__init__(hass, config_entry)
        self.page = page
        self.slot = slot
        self._attr_name = f"Slot {slot} Entity"
        self._attr_unique_id = f"{self._device_identifier}_s{slot}"
        # For page entries, options keys are s1..sN
        self._attr_native_value = config_entry.options.get(f"s{slot}", "")

    async def async_set_value(self, value: str) -> None:
        key = f"s{self.slot}"
        opts = {**self.config_entry.options, key: value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()
