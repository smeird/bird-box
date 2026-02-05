# bird-box

Bird Box is a lightweight, single-page web dashboard for a birdhouse camera. It renders live device status from MQTT topics (battery, LED, motion delta) and displays camera snapshots by reading the `/snapshots/` directory listing, showing each JPG with a timestamp caption and a modal preview. The page is styled with Tailwind via CDN and runs entirely in the browser with no build step.

## Platform diagram

```mermaid
flowchart TD
    Viewer[Viewer Browser] -->|Loads| Dashboard[Single-page Dashboard<br/>index.html + Tailwind CDN]
    Dashboard -->|Fetches snapshots| Snapshots[/snapshots/ directory]
    Dashboard -->|Subscribes via MQTT over WebSockets| Broker[(MQTT Broker)]
    ESP32[ESP32 Controller<br/>esphome/birdbox.yaml] -->|Telemetry + power state| Broker
    Broker -->|Battery / LED / motion / power topics| Dashboard
    ESP32 -->|Power control| Pi[Raspberry Pi Camera]
    Pi -->|Publishes delta + snapshots| Broker
    Pi -->|Captures JPGs| Snapshots
```

## ESPHome controller

The ESP32 configuration that manages battery monitoring and Raspberry Pi power control lives in `esphome/birdbox.yaml`. It publishes battery telemetry over MQTT, listens for Pi power commands, and uses configurable on/off thresholds exposed as Home Assistant sliders.

## Snapshots directory

Place camera images in `snapshots/` at the repository root so they are served at `/snapshots/`. The gallery expects JPG filenames in the format `YYYYMMDD_HHMMSS.jpg` so it can format timestamps in the UI. The directory is tracked in Git with a `.gitkeep` placeholder so it exists when you deploy.

## Raspberry Pi camera script

The Raspberry Pi publishes motion deltas and high-resolution snapshots using `pi/frame_differencing_trigger.py`. It runs Picamera2 in full-auto mode, performs frame differencing, turns on the LED strip over MQTT when motion crosses the threshold, and publishes JPEG bytes to the snapshot topic.

Key environment variables:

- `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`
- `MQTT_DELTA_TOPIC`, `MQTT_SNAP_TOPIC`
- `LED_BRIGHTNESS_TOPIC`, `LED_R_TOPIC`, `LED_G_TOPIC`, `LED_B_TOPIC`
- `LED_BRIGHTNESS_VALUE`, `LED_R_VALUE`, `LED_G_VALUE`, `LED_B_VALUE`, `LED_WARMUP_SEC`
- `MOTION_THRESHOLD`
