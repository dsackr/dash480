"""Switch platform for Dash480."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

# Relay definitions: (Display Name, Group ID, Output ID)
RELAYS = [
    ("Relay 1", 1, 1),
    ("Relay 2", 2, 2),
    ("Relay 3", 3, 40),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dash480 switches."""
    node_name = config_entry.data["node_name"]

    # The device identifier should be unique and stable
    device_identifier = f"dash480_{node_name}"

    entities: list[Dash480RelaySwitch] = []
    for name, group_id, output_id in RELAYS:
        entities.append(
            Dash480RelaySwitch(
                hass=hass,
                config_entry=config_entry,
                device_identifier=device_identifier,
                node_name=node_name,
                name=name,
                group_id=group_id,
                output_id=output_id,
            )
        )

    async_add_entities(entities)


class Dash480RelaySwitch(SwitchEntity):
    """Representation of a Dash480 relay switch."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device_identifier: str,
        node_name: str,
        name: str,
        group_id: int,
        output_id: int,
    ) -> None:
        self.hass = hass
        self._config_entry = config_entry
        self._dev_ident = device_identifier
        self._node = node_name
        self._name = name
        self._group_id = group_id
        self._output_id = output_id
        self._state = False
        self._attr_unique_id = f"{device_identifier}_relay_{group_id}"
        self._attr_name = name
        self._command_topic = f"hasp/{node_name}/command/group{group_id}"
        self._state_topic = f"hasp/{node_name}/state/output{output_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._dev_ident)},
            name=f"Dash480 ({self._node})",
            manufacturer="openHASP",
            model="ESP32-S3 480x480",
        )

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_added_to_hass(self) -> None:
        @callback
        def _message_received(msg) -> None:
            try:
                payload = msg.payload
                # state messages are JSON like {"state":"on"}
                if payload.startswith("{"):
                    # naive parse to avoid json import overhead
                    self._state = '"state":"on"' in payload or '"state": "on"' in payload
                else:
                    self._state = payload in ("1", "on", "ON", "true", "True")
            except Exception:
                return
            self.async_write_ha_state()

        # Subscribe to state updates
        self._unsub = await mqtt.async_subscribe(self.hass, self._state_topic, _message_received)

    async def async_will_remove_from_hass(self) -> None:
        unsub = getattr(self, "_unsub", None)
        if unsub:
            unsub()

    async def async_turn_on(self, **kwargs) -> None:
        await mqtt.async_publish(self.hass, self._command_topic, "1")

    async def async_turn_off(self, **kwargs) -> None:
        await mqtt.async_publish(self.hass, self._command_topic, "0")
