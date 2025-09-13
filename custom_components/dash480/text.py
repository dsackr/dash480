"""Text platform for Dash480."""
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dash480 text entities."""
    async_add_entities([Dash480NodeNameText(hass, config_entry)])


class Dash480NodeNameText(TextEntity):
    """Representation of the node name configuration text entity."""

    _attr_entity_category = "config"

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
