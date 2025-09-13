"""Switch platform for Dash480."""
from homeassistant.components.mqtt.switch import MqttSwitch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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

    switches = []
    for name, group_id, output_id in RELAYS:
        switches.append(
            Dash480RelaySwitch(
                hass,
                config_entry,
                device_identifier,
                node_name,
                name,
                group_id,
                output_id,
            )
        )

    async_add_entities(switches)


class Dash480RelaySwitch(MqttSwitch):
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
        """Initialize the switch."""
        # This is the configuration object that MqttSwitch expects.
        # It's equivalent to the YAML configuration for an MQTT switch.
        config = {
            "name": name,
            "unique_id": f"{device_identifier}_relay_{group_id}",
            "command_topic": f"hasp/{node_name}/command/group{group_id}",
            "state_topic": f"hasp/{node_name}/state/output{output_id}",
            "payload_on": "1",
            "payload_off": "0",
            "state_on": "on",
            "state_off": "off",
            "value_template": "{{ value_json.state }}",
            "device": {"identifiers": [device_identifier]},
        }

        # Call the MqttSwitch constructor
        super().__init__(hass, config, config_entry, None)
