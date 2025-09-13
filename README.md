# Dash480 Custom Integration for Home Assistant

This custom integration provides seamless integration for a 480x480 openHASP display panel (referred to as Dash480) into Home Assistant. It creates a single device with entities to control the onboard relays and configure the device name directly from the Home Assistant UI.

## Features

- **Simple UI Setup**: A configuration wizard (config flow) on the Integrations page to get you started.
- **Device Control**: Creates a single "Dash480" device in Home Assistant, which contains all related entities.
- **Relay Switches**: Provides three `switch` entities to control the three onboard relays.
- **Node Name Control**: Adds a "Node Name" control to the device page. Changing this updates the integration (HA will listen/publish on the new node), but it does not change the physical device’s hostname.
- **Automatic Screen Layout**: Automatically pushes a default screen layout with controls for the three relays to your device when it connects to MQTT.

## Prerequisites

1.  **Home Assistant**: A running instance of Home Assistant.
2.  **MQTT Broker**: An MQTT broker that is connected to your Home Assistant instance.
3.  **openHASP Device**: An ESP32-S3 480x480 panel flashed with the openHASP firmware. Ensure it is connected to your network.

## Installation

1.  **Copy the Integration Files**:
    -   Navigate to the `dash480-py` project folder.
    -   Copy the entire `custom_components/dash480` directory into the `custom_components` directory of your Home Assistant configuration folder.
    -   If you do not have a `custom_components` directory, create it.

2.  **Restart Home Assistant**:
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

3.  **Device Creation**:
    -   The integration will be added, and you will see a new "Dash480" device with its associated entities (relays and node name).

## Usage

### Controlling the Relays

Once installed, you will find three new switch entities:

-   `switch.relay_1`
-   `switch.relay_2`
-   `switch.relay_3`

You can add these to your dashboards or use them in automations just like any other switch.

### Changing the Node Name

If you need to change the node name Home Assistant uses for this device:

1.  Go to the **Dash480** device page (**Settings** > **Devices & Services** > **Dash480**).
2.  Under the **Controls** section, you will find a text box for **Node Name**.
3.  Enter the new node name and press Enter.

This updates the integration to listen/publish on the new `hasp/<node>/...` topics. It does not attempt to change the physical device’s hostname.

### Physical Device Setup

For the relays to function, ensure you have configured the outputs in your openHASP device's web UI. The integration assumes the following mapping:

-   **Group 1** controls Relay 1
-   **Group 2** controls Relay 2
-   **Group 3** controls Relay 3

## How the welcome layout is pushed

- When the device publishes `hasp/<node>/LWT` with payload `online`, the integration pushes a basic JSONL layout to `hasp/<node>/command/jsonl`.
- The layout is sent line-by-line (one JSON object per publish), which is compatible with openHASP’s JSONL command handling.
