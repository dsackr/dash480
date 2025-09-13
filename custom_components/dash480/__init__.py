"""The Dash480 integration."""
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import DOMAIN

# List of platforms to support.
PLATFORMS = ["switch", "text"]

def _home_layout_lines(node_name: str, title: str, temp_text: str) -> list[str]:
    """Build JSONL lines for header/footer and home page with 3 relays."""
    lines: list[str] = []
    # Ensure page 0 and 1 exist
    lines.append('{"page":0,"id":0,"obj":"page"}')
    lines.append('{"page":1,"id":0,"obj":"page","prev":1,"next":1}')
    # Header (page 0)
    lines.append('{"page":0,"id":10,"obj":"obj","x":0,"y":0,"w":480,"h":56,"bg_color":"#1F2937"}')
    lines.append('{"page":0,"id":1,"obj":"label","x":12,"y":8,"w":120,"h":40,"text":"00:00","template":"%H:%M","text_font":24,"align":"left","text_color":"#E5E7EB","bg_opa":0}')
    # Center title (p0b2)
    t = title.replace('"', '\\"')
    lines.append(f'{{"page":0,"id":2,"obj":"btn","x":140,"y":8,"w":200,"h":40,"text":"{t}","text_font":22,"text_color":"#FFFFFF","bg_opa":0,"border_width":0,"radius":0,"outline_width":0,"shadow_width":0,"toggle":false}}')
    # Right temp (p0b3)
    tt = temp_text.replace('"', '\\"') if temp_text else "--"
    lines.append(f'{{"page":0,"id":3,"obj":"btn","x":320,"y":8,"w":148,"h":40,"text":"{tt}","text_font":24,"align":"right","text_color":"#E5E7EB","bg_opa":0,"border_width":0,"radius":0,"outline_width":0,"shadow_width":0,"toggle":false}}')
    # Footer navigation (page 0)
    lines.append('{"page":0,"id":90,"obj":"btn","action":{"down": "page prev"},"x":0,"y":430,"w":120,"h":50,"bg_color":"#2C3E50","text":"\\uE141","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    lines.append('{"page":0,"id":91,"obj":"btn","action":{"down": "page 1"},"x":120,"y":430,"w":240,"h":50,"bg_color":"#2C3E50","text":"\\uE2DC","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    lines.append('{"page":0,"id":92,"obj":"btn","action":{"down": "page next"},"x":340,"y":430,"w":120,"h":50,"bg_color":"#2C3E50","text":"\\uE142","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    # Home page background area
    lines.append('{"page":1,"obj":"obj","id":800,"x":0,"y":56,"w":480,"h":424,"bg_color":"#0B1220"}')
    # Three relay buttons (IDs 101/111/121)
    lines.append('{"page":1,"obj":"btn","id":101,"x":40,"y":120,"w":120,"h":72,"text":"Relay 1","text_font":22,"toggle":true,"radius":12,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":111,"x":180,"y":120,"w":120,"h":72,"text":"Relay 2","text_font":22,"toggle":true,"radius":12,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":121,"x":320,"y":120,"w":120,"h":72,"text":"Relay 3","text_font":22,"toggle":true,"radius":12,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    return lines


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dash480 from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    node_name = entry.data["node_name"]
    home_title = entry.options.get("home_title", node_name)
    temp_entity = entry.options.get("temp_entity", "")

    # helper to publish current temp to header right label (p0b3)
    async def _publish_temp(value: str) -> None:
        await mqtt.async_publish(
            hass,
            f"hasp/{node_name}/command/p0b3.text",
            value if value else "--",
        )

    # Define the callback for when the device comes online
    @callback
    def push_layout(msg):
        """Handle device online message and push layout."""
        if msg.payload == "online":
            # Build home layout with header/footer and 3 relays
            temp_text = ""
            if temp_entity:
                st = hass.states.get(temp_entity)
                if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
                    temp_text = str(st.state)
            lines = _home_layout_lines(node_name, home_title, temp_text)
            for line in lines:
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

    # Subscribe to touch events for home relay buttons and to page changes
    @callback
    def _state_event(msg):
        topic_tail = msg.topic.split("/")[-1]
        try:
            import json

            data = json.loads(msg.payload)
        except Exception:
            data = {}
        event = str(data.get("event", ""))
        val = data.get("val", -1)
        # Relay button routing on 'up'
        if event == "up":
            if topic_tail == "p1b101":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output1", payload))
            elif topic_tail == "p1b111":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output2", payload))
            elif topic_tail == "p1b121":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output40", payload))
        # Title on page change (only page 1 for now)
        if topic_tail == "page":
            page = str(msg.payload)
            if page == "1":
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title))

    unsub_events = await mqtt.async_subscribe(hass, f"hasp/{node_name}/state/#", _state_event)
    hass.data[DOMAIN][entry.entry_id]["unsub_events"] = unsub_events

    # Track temp entity changes
    def _on_temp_change(event):
        if not temp_entity:
            return
        st = hass.states.get(temp_entity)
        val = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            val = str(st.state)
        hass.async_create_task(_publish_temp(val))

    if temp_entity:
        unsub_temp = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
        hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp

    # Forward the setup to the platforms.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from the MQTT topic
    unsubscribe_handle = hass.data[DOMAIN][entry.entry_id].get("unsubscribe")
    if unsubscribe_handle:
        unsubscribe_handle()
    unsub_events = hass.data[DOMAIN][entry.entry_id].get("unsub_events")
    if unsub_events:
        unsub_events()
    unsub_temp = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
    if unsub_temp:
        unsub_temp()

    # Forward the unload to the platforms.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up the hass.data entry
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
