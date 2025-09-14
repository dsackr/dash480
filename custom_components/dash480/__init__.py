"""The Dash480 integration."""
from __future__ import annotations

import logging
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Top-level (component) setup: register services once and route by entry_id
async def async_setup(hass: HomeAssistant, config):
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("services_registered"):
        return True

    async def _pick_entry_id(call) -> str | None:
        eid = call.data.get("entry_id")
        if eid:
            return eid
        publishers = hass.data.get(DOMAIN, {}).get("publishers", {})
        if len(publishers) == 1:
            return next(iter(publishers.keys()))
        _LOGGER.warning("Dash480: entry_id required when multiple panels exist")
        return None

    async def svc_publish_all(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        pub = hass.data.get(DOMAIN, {}).get("publishers", {}).get(eid)
        if not pub or not pub.get("publish_all"):
            _LOGGER.warning("Dash480: no publisher for entry_id=%s", eid)
            return
        _LOGGER.info("Dash480: publish_all(entry_id=%s)", eid)
        try:
            await pub["publish_all"]()
        except Exception as exc:
            _LOGGER.exception("Dash480: publish_all failed for %s: %s", eid, exc)

    async def svc_publish_home(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        pub = hass.data.get(DOMAIN, {}).get("publishers", {}).get(eid)
        if not pub or not pub.get("publish_home"):
            _LOGGER.warning("Dash480: no home publisher for entry_id=%s", eid)
            return
        _LOGGER.info("Dash480: publish_home(entry_id=%s)", eid)
        try:
            await pub["publish_home"]()
        except Exception as exc:
            _LOGGER.exception("Dash480: publish_home failed for %s: %s", eid, exc)

    async def svc_set_home_title(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        title = str(call.data.get("home_title", "")).strip()
        entry = hass.config_entries.async_get_entry(eid)
        if not entry:
            _LOGGER.warning("Dash480: entry not found for set_home_title: %s", eid)
            return
        new_opts = {**entry.options, "home_title": title or entry.data.get("node_name", "Dash")}
        hass.config_entries.async_update_entry(entry, options=new_opts)

    async def svc_set_temp_entity(call):
        eid = await _pick_entry_id(call)
        if not eid:
            return
        ent = str(call.data.get("temp_entity", "")).strip()
        entry = hass.config_entries.async_get_entry(eid)
        if not entry:
            _LOGGER.warning("Dash480: entry not found for set_temp_entity: %s", eid)
            return
        new_opts = {**entry.options, "temp_entity": ent}
        hass.config_entries.async_update_entry(entry, options=new_opts)

    hass.services.async_register(DOMAIN, "publish_all", svc_publish_all)
    hass.services.async_register(DOMAIN, "publish_home", svc_publish_home)
    hass.services.async_register(DOMAIN, "set_home_title", svc_set_home_title)
    hass.services.async_register(DOMAIN, "set_temp_entity", svc_set_temp_entity)

    store["services_registered"] = True
    return True

# List of platforms to support.
PLATFORMS = ["switch", "text", "number", "button"]
PLATFORMS_PAGE = ["text", "button"]

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
    # Footer navigation (page 0) — span full 480px (3x160)
    lines.append('{"page":0,"id":90,"obj":"btn","action":{"down": "page prev"},"x":0,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE141","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    lines.append('{"page":0,"id":91,"obj":"btn","action":{"down": "page 1"},"x":160,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE2DC","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    lines.append('{"page":0,"id":92,"obj":"btn","action":{"down": "page next"},"x":320,"y":430,"w":160,"h":50,"bg_color":"#2C3E50","text":"\\uE142","text_color":"#FFFFFF","radius":0,"border_side":0,"text_font":48}')
    # Home page background area
    lines.append('{"page":1,"obj":"obj","id":800,"x":0,"y":56,"w":480,"h":424,"bg_color":"#0B1220"}')
    # Three relay buttons (IDs 12/22/32) using working layout
    lines.append('{"page":1,"obj":"btn","id":12,"x":25,"y":300,"w":120,"h":60,"text":"Relay 1","text_font":26,"toggle":true,"groupid":1,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":22,"x":175,"y":300,"w":120,"h":60,"text":"Relay 2","text_font":26,"toggle":true,"groupid":2,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    lines.append('{"page":1,"obj":"btn","id":32,"x":325,"y":300,"w":120,"h":60,"text":"Relay 3","text_font":26,"toggle":true,"groupid":3,"radius":8,"bg_color":"#374151","text_color":"#FFFFFF","border_width":0}')
    return lines


async def async_get_options_flow(entry: ConfigEntry):
    """Expose options flow to HA (wrapper around options_flow module)."""
    from .options_flow import Dash480OptionsFlowHandler  # local import

    return Dash480OptionsFlowHandler(entry)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dash480 from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    role = entry.data.get("role", "panel")
    # If this is a Page entry, set up page entities only and return early.
    if role == "page":
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_PAGE)
        return True
    # Panel entry setup
    node_name = entry.data["node_name"]
    home_title = entry.options.get("home_title", node_name)
    temp_entity = entry.options.get("temp_entity", "")
    # control map (id -> entity_id) and sensor text map (entity -> list of (page,id))
    hass.data[DOMAIN][entry.entry_id]["ctrl_map"] = {}
    hass.data[DOMAIN][entry.entry_id]["sensor_map"] = {}

    # helper to publish current temp to header right label (p0b3)
    async def _publish_temp(value: str) -> None:
        await mqtt.async_publish(
            hass,
            f"hasp/{node_name}/command/p0b3.text",
            value if value else "--",
        )

    async def _push_home_layout() -> None:
        """Clear and push header/footer + home relays."""
        # Clear existing pages first
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        temp_text = ""
        if temp_entity:
            st = hass.states.get(temp_entity)
            if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
                temp_text = str(st.state)
        lines = _home_layout_lines(node_name, home_title, temp_text)
        for line in lines:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", line)

    async def _publish_all() -> None:
        """Publish full layout based on config entities (pages, titles, slots)."""
        _LOGGER.info("Dash480: publishing all for node=%s", node_name)
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/clearpage", "all")
        # Header/footer
        st = hass.states.get(temp_entity) if temp_entity else None
        tval = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            tval = str(st.state)
        lines = _home_layout_lines(node_name, home_title, tval)
        for line in lines:
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", line)
        # Build page list from Page entries linked to this panel
        all_entries = hass.config_entries.async_entries(DOMAIN)
        page_entries = [e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == entry.entry_id]
        page_entries.sort(key=lambda e: int(e.data.get("page_order", 99)))
        page_numbers = [int(e.data.get("page_order", 99)) for e in page_entries]
        # include home page 1 at start for wrap math
        pages_ring = [1] + page_numbers
        # Update page 1 prev/next to wrap to first/last page if pages exist
        if page_numbers:
            prev_home = page_numbers[-1]
            next_home = page_numbers[0]
            await mqtt.async_publish(
                hass,
                f"hasp/{node_name}/command/jsonl",
                f'{{"page":1,"id":0,"obj":"page","prev":{prev_home},"next":{next_home}}}',
            )
        def pprev(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx - 1) % len(pages_ring)]
        def pnext(p):
            idx = pages_ring.index(p)
            return pages_ring[(idx + 1) % len(pages_ring)]
        # Draw each page
        ctrl_map: dict[str, str] = {}
        sensor_map: dict[str, list[tuple[int,int]]] = {}
        for pe in page_entries:
            p = int(pe.data.get("page_order", 99))
            title = pe.options.get("title", f"Page {p}")
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"id":0,"obj":"page","prev":{pprev(p)},"next":{pnext(p)}}}')
            await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"obj","id":800,"x":0,"y":56,"w":480,"h":424,"bg_color":"#0B1220"}}')
            # page title update will occur on page change via router
            # slots
            slot_keys = [k for k in pe.options.keys() if k.startswith("s")] or []
            # stable order s1..s12
            for idx in range(1, 13):
                key = f"s{idx}"
                ent = pe.options.get(key, "")
                if not ent:
                    continue
                i0 = idx - 1
                col = i0 % 3
                row = i0 // 3
                x = 40 + col * 160
                y = 120 + row * 140
                base = p * 1000 + i0 * 10
                st_ent = hass.states.get(ent)
                label = st_ent.attributes.get("friendly_name", ent) if st_ent else ent
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"obj","id":{base+1},"x":{x},"y":{y},"w":128,"h":120,"radius":14,"bg_color":"#1E293B"}}')
                await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"label","id":{base},"x":{x+8},"y":{y+8},"w":112,"h":22,"text":"{label}","text_font":18,"text_color":"#9CA3AF","bg_opa":0}}')
                domain = ent.split(".")[0]
                if domain in ("switch", "light", "fan"):
                    await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"btn","id":{base+2},"x":{x+20},"y":{y+40},"w":88,"h":64,"text":"\\uE425","text_font":64,"toggle":true,"radius":12,"bg_color":"#1E293B","text_color":"#FFFFFF","border_width":0}}')
                    ctrl_map[f"p{p}b{base+2}"] = ent
                elif domain == "sensor":
                    # invisible button to hold value text (more reliable updates than label)
                    val = st_ent.state if st_ent and st_ent.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                    await mqtt.async_publish(hass, f"hasp/{node_name}/command/jsonl", f'{{"page":{p},"obj":"btn","id":{base+2},"x":{x+20},"y":{y+40},"w":88,"h":64,"text":"{val}","text_font":20,"toggle":false,"bg_opa":0,"border_width":0,"radius":0}}')
                    sensor_map.setdefault(ent, []).append((p, base+2))
        hass.data[DOMAIN][entry.entry_id]["ctrl_map"] = ctrl_map
        hass.data[DOMAIN][entry.entry_id]["sensor_map"] = sensor_map
        # rewire sensor listeners
        # remove previous
        for key in list(hass.data[DOMAIN][entry.entry_id].keys()):
            if key.startswith("unsub_sensor_"):
                u = hass.data[DOMAIN][entry.entry_id].pop(key)
                try:
                    u()
                except Exception:
                    pass
        for ent, targets in sensor_map.items():
            async def _make_cb(eid: str):
                async def _cb(event):
                    st = hass.states.get(eid)
                    val = st.state if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "") else "--"
                    for (pnum, bid) in sensor_map.get(eid, []):
                        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p{pnum}b{bid}.text", val)
                return _cb
            cb = await _make_cb(ent)
            unsub = async_track_state_change_event(hass, [ent], cb)
            hass.data[DOMAIN][entry.entry_id][f"unsub_sensor_{ent}"] = unsub

    # Define the callback for when the device comes online
    @callback
    def push_layout(msg):
        """Handle device online message and push layout."""
        if msg.payload == "online":
            hass.async_create_task(_push_home_layout())

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
        data = None
        try:
            import json
            data = json.loads(msg.payload)
        except Exception:
            data = None
        if isinstance(data, dict):
            event = str(data.get("event", ""))
            val = data.get("val", -1)
        else:
            event = ""
            val = -1
        # Relay button routing on 'up'
        if event == "up":
            if topic_tail == "p1b12":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output1", payload))
            elif topic_tail == "p1b22":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output2", payload))
            elif topic_tail == "p1b32":
                payload = '{"state":"on"}' if val == 1 else '{"state":"off"}'
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/output40", payload))
            else:
                # Generic tile routing based on ctrl_map
                ent = hass.data[DOMAIN][entry.entry_id].get("ctrl_map", {}).get(topic_tail)
                if ent:
                    domain = ent.split(".")[0]
                    if domain == "switch":
                        svc = "turn_on" if val == 1 else "turn_off"
                        hass.async_create_task(hass.services.async_call("switch", svc, {"entity_id": ent}))
                    elif domain == "light":
                        svc = "turn_on" if val == 1 else "turn_off"
                        hass.async_create_task(hass.services.async_call("light", svc, {"entity_id": ent}))
                    elif domain == "fan":
                        if val == 1:
                            hass.async_create_task(hass.services.async_call("fan", "turn_on", {"entity_id": ent}))
                        else:
                            hass.async_create_task(hass.services.async_call("fan", "turn_off", {"entity_id": ent}))
        # Title on page change (only page 1 for now)
        if topic_tail == "page":
            page = str(msg.payload)
            if page.isdigit():
                p = int(page)
                # Resolve title from Page entries map
                all_entries = hass.config_entries.async_entries(DOMAIN)
                page_entry = next((e for e in all_entries if e.data.get("role") == "page" and e.data.get("panel_entry_id") == entry.entry_id and int(e.data.get("page_order", 0)) == p), None)
                title = home_title if p == 1 else (page_entry.options.get("title", f"Page {p}") if page_entry else f"Page {p}")
                hass.async_create_task(mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", title))

    unsub_events = await mqtt.async_subscribe(hass, f"hasp/{node_name}/state/#", _state_event)
    hass.data[DOMAIN][entry.entry_id]["unsub_events"] = unsub_events

    # Track temp entity changes
    async def _on_temp_change(event):
        if not temp_entity:
            return
        st = hass.states.get(temp_entity)
        val = "--"
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            val = str(st.state)
        await _publish_temp(val)

    if temp_entity:
        unsub_temp = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
        hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp

    # React to options changes (from Configure dialog or services)
    async def _options_updated(hass_: HomeAssistant, updated: ConfigEntry):
        nonlocal home_title, temp_entity
        home_title = updated.options.get("home_title", updated.data.get("node_name", "Dash"))
        new_temp = updated.options.get("temp_entity", "")
        if new_temp != temp_entity:
            # resubscribe to temp entity changes
            unsub_prev = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
            if unsub_prev:
                unsub_prev()
                hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = None
            temp_entity = new_temp
            if temp_entity:
                unsub_new = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
                hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_new
            # push current temp immediately
            st = hass.states.get(temp_entity) if temp_entity else None
            val = "--"
            if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
                val = str(st.state)
            await _publish_temp(val)
        # Update title immediately
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title)

    unsub_update = entry.add_update_listener(_options_updated)
    hass.data[DOMAIN][entry.entry_id]["unsub_update"] = unsub_update

    # Services: allow setting options and forcing a publish when UI Configure is unavailable
    async def _resolve_entry(call: ServiceCall) -> ConfigEntry | None:
        eid = call.data.get("entry_id")
        if eid:
            return hass.config_entries.async_get_entry(eid)
        # default to this entry if only one exists for our domain
        entries = [e for e in hass.config_entries.async_entries(DOMAIN)]
        if len(entries) == 1:
            return entries[0]
        return None

    async def _svc_set_home_title(call: ServiceCall):
        nonlocal home_title
        e = await _resolve_entry(call)
        if not e:
            return
        title = str(call.data.get("home_title", "")).strip()
        # Persist on entry options
        new_opts = {**e.options, "home_title": title or e.data.get("node_name", "Dash")}
        hass.config_entries.async_update_entry(e, options=new_opts)
        # Update local cache and live header immediately
        home_title = new_opts["home_title"]
        await mqtt.async_publish(hass, f"hasp/{node_name}/command/p0b2.text", home_title)

    async def _svc_set_temp_entity(call: ServiceCall):
        nonlocal temp_entity
        e = await _resolve_entry(call)
        if not e:
            return
        temp = str(call.data.get("temp_entity", "")).strip()
        new_opts = {**e.options, "temp_entity": temp}
        hass.config_entries.async_update_entry(e, options=new_opts)
        # Update subscription to new entity and push current value to header
        temp_entity = temp
        # tear down old tracker if present
        unsub_temp_prev = hass.data[DOMAIN][entry.entry_id].get("unsub_temp")
        if unsub_temp_prev:
            unsub_temp_prev()
            hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = None
        # publish current value
        val = "--"
        st = hass.states.get(temp_entity) if temp_entity else None
        if st and st.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            val = str(st.state)
        await _publish_temp(val)
        # re-subscribe for future updates
        if temp_entity:
            unsub_temp_new = async_track_state_change_event(hass, [temp_entity], _on_temp_change)
            hass.data[DOMAIN][entry.entry_id]["unsub_temp"] = unsub_temp_new

    async def _svc_publish_home(call: ServiceCall):
        await _push_home_layout()

    # Note: Services are registered at component level in async_setup().

    # Register publishers for component-level services
    hass.data[DOMAIN].setdefault("publishers", {})[entry.entry_id] = {
        "publish_all": _publish_all,
        "publish_home": _push_home_layout,
    }
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
    unsub_update = hass.data[DOMAIN][entry.entry_id].get("unsub_update")
    if unsub_update:
        unsub_update()
    # Remove publishers
    pubs = hass.data.get(DOMAIN, {}).get("publishers", {})
    if entry.entry_id in pubs:
        pubs.pop(entry.entry_id, None)

    # Forward the unload to the platforms.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up the hass.data entry
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
