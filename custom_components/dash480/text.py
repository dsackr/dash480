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
    """Set up the Dash480 text entities."""
    entities: list[TextEntity] = []
    entities.append(Dash480NodeNameText(hass, config_entry))
    entities.append(Dash480HomeTitleText(hass, config_entry))
    entities.append(Dash480TempEntityText(hass, config_entry))
    # Page titles and slots (1..6 pages, 6 slots each)
    for p in range(1, 7):
        entities.append(Dash480PageTitleText(hass, config_entry, p))
        for s in range(1, 7):
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
        node = config_entry.data["node_name"]
        self._device_identifier = f"dash480_{node}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            name=f"Dash480 ({self.config_entry.data['node_name']})",
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
        self._attr_unique_id = f"{self._device_identifier}_p{page}_title"
        self._attr_native_value = config_entry.options.get(f"p{page}_title", f"Page {page}")

    async def async_set_value(self, value: str) -> None:
        key = f"p{self.page}_title"
        opts = {**self.config_entry.options, key: value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()


class Dash480SlotEntityText(_BaseDashText):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, page: int, slot: int) -> None:
        super().__init__(hass, config_entry)
        self.page = page
        self.slot = slot
        self._attr_name = f"P{page} Slot {slot} Entity"
        self._attr_unique_id = f"{self._device_identifier}_p{page}_s{slot}"
        self._attr_native_value = config_entry.options.get(f"p{page}_s{slot}", "")

    async def async_set_value(self, value: str) -> None:
        key = f"p{self.page}_s{self.slot}"
        opts = {**self.config_entry.options, key: value}
        self.hass.config_entries.async_update_entry(self.config_entry, options=opts)
        self._attr_native_value = value
        self.async_write_ha_state()
