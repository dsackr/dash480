# Dash480 Custom Integration for Home Assistant

This custom integration provides seamless integration for an openHASP 480×480 panel ("Dash480") with Home Assistant. It provisions the screen layout over MQTT and exposes convenient config entities in HA to manage pages, tiles, and header content.

## Features

- **Simple Setup**: Add a Panel, then add Pages from the Integrations UI.
- **Header Controls**: Set Home Title and a Temp sensor for the header from HA.
- **Relay Switches**: Three switches for onboard relays (optional, if wired).
- **Popup Controls for Tiles**:
  - Fans: tapping the fan tile opens a popup with Off/Low/Med/High.
  - Color-capable lights: tapping the light tile opens a color popup (Off, Red, Green, Blue, Warm, Cool). The tile icon tint updates to the chosen color.
  - Switches and non-color lights: simple on/off toggle.
- **Add Entity Flow**: Create pages with a title only; then add entities later using a Page-level entity picker and an Add button.
- **Automatic Layout Push**: When the device comes online (MQTT LWT), the current layout is pushed.

## Prerequisites

1.  **Home Assistant**: A running instance of Home Assistant.
2.  **MQTT Broker**: An MQTT broker that is connected to your Home Assistant instance.
3.  **openHASP Device**: An ESP32-S3 480×480 panel flashed with openHASP, connected to your network and MQTT.

## Installation

1.  **Copy the Integration Files**:
    -   Navigate to the `dash480-py` project folder.
    -   Copy the entire `custom_components/dash480` directory into the `custom_components` directory of your Home Assistant configuration folder.
    -   If you do not have a `custom_components` directory, create it.

2.  (Optional) **Install via HACS**:
    - Add this repo as a custom repository in HACS (Integrations) and install "Dash480".
    - Or install manually as below.

3.  **Restart Home Assistant**:
    -   To make Home Assistant recognize the new integration, you must restart it.
    -   Go to **Developer Tools** > **YAML** and click **Restart**.

## Configuration

1.  **Add the Integration**:
    -   Go to **Settings** > **Devices & Services**.
    -   Click the **+ ADD INTEGRATION** button in the bottom right.
    -   Search for **"Dash480"** and select it.

2.  **Enter Node Name**:
    -   A configuration wizard will appear.
    -   You will be asked for the **Node Name**. This is the MQTT hostname of your openHASP device (e.g., `plate`).
    -   Click **Submit**.

3.  **Configure Header (Options)**:
    - Go to **Settings** > **Devices & Services** > Dash480 panel > **Configure**.
    - Set:
      - Home Title: center title in the header (defaults to node name).
      - Temp Entity: sensor to show at top-right (optional).
    - Save. The header will update; the full layout is pushed when the device comes online (MQTT LWT `online`).

4.  **Device Creation**:
    -   The integration will be added, and you will see a new "Dash480" device with its associated entities (relays and node name).

## Usage

### Add Pages

1. After adding the Panel, add one or more Pages from Integrations → Dash480 → Add → Page.
2. Page creation asks for: Panel, Page Order, and optional Title. No entities at creation time.

### Add Entities to a Page

On the Page device in HA, use:

- P{n} Title (text): sets the page title.
- P{n} Add Entity (select): choose any switch, light, fan, or sensor in HA that isn’t already on the page.
- Add Entity (button): assigns the selected entity to the first empty slot and refreshes the screen.
- Publish Page (button): republish the current layout for all pages on this panel (useful if you’ve changed multiple slots).

You can still edit specific slots via the Page’s Configure dialog if needed, but the above flow is simpler for most cases.

### On-Device Controls

- Switches and non-color lights: tap to toggle on/off.
- Fans: tap the fan tile to open a popup with Off/Low/Med/High. The selection sets fan percentage (0/33/66/100).
- Color-capable lights: tap the tile to open color options (Off, Red, Green, Blue, Warm, Cool). Choosing a color turns the light on and tints the tile icon to match.
- Brightness/preset rows under tiles have been removed in favor of popups.

### Changing the Node Name

On the Dash480 panel device page, set Node Name if needed. This changes the MQTT topic prefix used by the integration; it does not change the device’s own hostname.

### Physical Device Setup

For the relays to function, ensure you have configured the outputs in your openHASP device's web UI. The integration assumes the following mapping:

-   **Group 1** controls Relay 1
-   **Group 2** controls Relay 2
-   **Group 3** controls Relay 3

## How the layout is pushed

- When the device publishes `hasp/<node>/LWT` with payload `online`, the integration pushes a basic JSONL layout to `hasp/<node>/command/jsonl`.
- The layout is sent line-by-line (one JSON object per publish), which is compatible with openHASP’s JSONL command handling.

## Publish controls

- On the Panel device:
  - Publish All: clears the device and publishes the header/footer and all pages.
  - Publish Home: publishes only the header/footer and home relays.
- On each Page device:
  - Publish Page: republish all pages for the associated panel (handy after changing slots).

Tip: The Add Entity button already triggers a republish; you can use Publish Page to force a manual refresh any time.
## Branding (Icons)

This repo includes SVG sources you can export to PNG for Home Assistant Brands:

- `branding/icon.svg` → export as transparent `icon.png` 256×256 (and optional `icon@2x.png` 512×512)
- `branding/logo.svg` → export as transparent `logo.png` 256×256 (and optional `logo@2x.png` 512×512)

Export with Inkscape (example):

```
inkscape branding/icon.svg -w 256 -h 256 -o icon.png
inkscape branding/logo.svg -w 256 -h 256 -o logo.png
```

Submit to the Home Assistant Brands repo:

- Fork https://github.com/home-assistant/brands
- Add files under `custom_integrations/dash480/`: `icon.png`, `logo.png` (and optional `@2x` variants)
- Open a PR; once merged, HA will display the icon/logo in Integrations and HACS.
