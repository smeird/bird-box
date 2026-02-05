# Agent notes

## ESP32 power controller

The ESP32 firmware configuration for the bird box power controller is stored at `esphome/birdbox.yaml`. It is responsible for:

- Publishing battery voltage and percentage to MQTT.
- Responding to MQTT commands to toggle Raspberry Pi power.
- Enforcing automatic on/off thresholds using Home Assistant template sliders.

When updating the ESPHome configuration, keep MQTT topic names and the LC709203F fuel gauge settings aligned with the hardware setup.
