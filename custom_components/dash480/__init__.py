"""The Dash480 integration."""
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

# List of platforms to support.
PLATFORMS = ["switch", "text"]

JSONL_PAYLOAD = """
{"page":1,"id":0,"obj":"page"}
{"page":1,"obj":"label","id":2,"x":0,"y":200,"w":480,"h":40,"text":"Waiting for Home Assistant…","align":"center","text_font":24}
{"page":1,"obj":"label","id":3,"x":0,"y":240,"w":480,"h":40,"text":"%Hostname%","align":"center","text_font":24,"text_color":"#9CA3AF","bg_opa":0}
{"page":1,"obj":"btn","id":12,"x":25,"y":300,"w":120,"h":60,"text":"Relay 1","text_font":26,"toggle":true,"groupid":1,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}
{"page":1,"obj":"btn","id":22,"x":175,"y":300,"w":120,"h":60,"text":"Relay 2","text_font":26,"toggle":true,"groupid":2,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}
{"page":1,"obj":"btn","id":32,"x":325,"y":300,"w":120,"h":60,"text":"Relay 3","text_font":26,"toggle":true,"groupid":3,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}
"""


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dash480 from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    node_name = entry.data["node_name"]

    # Define the callback for when the device comes online
    @callback
    def push_layout(msg):
        """Handle device online message and push layout."""
        if msg.payload == "online":
            # Publish JSONL lines individually
            for line in JSONL_PAYLOAD.strip().splitlines():
                hass.async_create_task(
                    mqtt.async_publish(
                        hass,
                        f"hasp/{node_name}/command/jsonl",
                        line,
                    )
                )

    # Subscribe to device LWT (online/offline)
    unsubscribe_handle = await mqtt.async_subscribe(
        hass,
        f"hasp/{node_name}/LWT",
        push_layout,
    )

    # Store the handle for later cleanup
    hass.data[DOMAIN][entry.entry_id]["unsubscribe"] = unsubscribe_handle

    # Forward the setup to the platforms.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from the MQTT topic
    unsubscribe_handle = hass.data[DOMAIN][entry.entry_id].get("unsubscribe")
    if unsubscribe_handle:
        unsubscribe_handle()

    # Forward the unload to the platforms.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up the hass.data entry
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
