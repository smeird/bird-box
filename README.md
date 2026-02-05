# bird-box

Bird Box is a lightweight, single-page web dashboard for a birdhouse camera. It renders live device status from MQTT topics (battery, LED, motion delta) and displays camera snapshots by reading the `/snapshots/` directory listing, showing each JPG with a timestamp caption and a modal preview. The page is styled with Tailwind via CDN and runs entirely in the browser with no build step.

## Platform diagram

```mermaid
flowchart TD
    Viewer[Viewer Browser] -->|Loads| Dashboard[Single-page Dashboard<br/>index.html + Tailwind CDN]
    Dashboard -->|Fetches snapshots| Snapshots[/snapshots/ directory]
    Dashboard -->|Subscribes via MQTT over WebSockets| Broker[MQTT Broker]
    ESP32[ESP32 Controller<br/>esphome/birdbox.yaml] -->|Telemetry + power state| Broker
    Broker -->|Battery / LED / motion / power topics| Dashboard
    ESP32 -->|Power control| Pi[Raspberry Pi Camera]
    Pi -->|Captures JPGs| Snapshots
```

## ESPHome controller

The ESP32 configuration that manages battery monitoring and Raspberry Pi power control lives in `esphome/birdbox.yaml`. It publishes battery telemetry over MQTT, listens for Pi power commands, and uses configurable on/off thresholds exposed as Home Assistant sliders.

## Snapshots directory

Place camera images in `snapshots/` at the repository root so they are served at `/snapshots/`. The gallery expects JPG filenames in the format `YYYYMMDD_HHMMSS.jpg` so it can format timestamps in the UI. The directory is tracked in Git with a `.gitkeep` placeholder so it exists when you deploy.
