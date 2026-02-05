#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera-side MQTT publisher for Birdbox (FULL AUTO)

This file is **pure ASCII** and declares UTF-8 encoding, so it loads cleanly on
any system. The camera runs in full-auto mode; no manual exposure or colour
settings are applied.

OpenCV expects BGR while Picamera2 returns RGB, therefore frames are converted
before JPEG encoding.

Environment variables
---------------------
MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, MQTT_PASSWORD
LED_BRIGHTNESS_VALUE, LED_R_VALUE, LED_G_VALUE, LED_B_VALUE, LED_WARMUP_SEC
MOTION_THRESHOLD
"""

from __future__ import annotations

import os
import time
from typing import Optional

import cv2
import numpy as np
import paho.mqtt.client as mqtt
from picamera2 import Picamera2

# -----------------------------------------------------------------------------
# Configuration from environment
# -----------------------------------------------------------------------------
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "homeassistant.smeird.com")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "smeird")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "92987974")

DELTA_TOPIC = os.getenv("MQTT_DELTA_TOPIC", "Birdbox/1/delta")
SNAP_TOPIC = os.getenv("MQTT_SNAP_TOPIC", "Birdbox/1/snapshot")

# LED topics
LED_BRIGHTNESS_TOPIC = os.getenv("LED_BRIGHTNESS_TOPIC", "Birdbox/1/LED/Brightness")
LED_R_TOPIC = os.getenv("LED_R_TOPIC", "Birdbox/1/LED/R")
LED_G_TOPIC = os.getenv("LED_G_TOPIC", "Birdbox/1/LED/G")
LED_B_TOPIC = os.getenv("LED_B_TOPIC", "Birdbox/1/LED/B")

QOS = 1

# Motion detection
MOTION_THRESHOLD = int(os.getenv("MOTION_THRESHOLD", "35000"))

# LED values (0-255)
LED_BRIGHTNESS_VALUE = int(os.getenv("LED_BRIGHTNESS_VALUE", "50"))
LED_R_VALUE = int(os.getenv("LED_R_VALUE", "255"))
LED_G_VALUE = int(os.getenv("LED_G_VALUE", "255"))
LED_B_VALUE = int(os.getenv("LED_B_VALUE", "255"))
LED_WARMUP_SEC = float(os.getenv("LED_WARMUP_SEC", "0.6"))

# -----------------------------------------------------------------------------
# Camera setup (full auto)
# -----------------------------------------------------------------------------

picam2 = Picamera2()

low_res_config = picam2.create_still_configuration(
    main={"size": (320, 240)},
    controls={"NoiseReductionMode": 1},  # fast denoise
)

high_res_config = picam2.create_still_configuration(
    main={"size": (4608, 2592)},
    controls={"NoiseReductionMode": 2},  # balanced denoise
)

# -----------------------------------------------------------------------------
# MQTT client setup
# -----------------------------------------------------------------------------

def _on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT} (rc={rc})")


auth_client = mqtt.Client(client_id="birdbox-camera")
auth_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
auth_client.on_connect = _on_connect
auth_client.connect(BROKER_HOST, BROKER_PORT)
auth_client.loop_start()

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _publish(topic: str, value: int) -> None:
    """Publish an integer as a string (retain=False)."""
    auth_client.publish(topic, str(value), qos=QOS, retain=False)


def led_on() -> None:
    _publish(LED_BRIGHTNESS_TOPIC, LED_BRIGHTNESS_VALUE)
    _publish(LED_R_TOPIC, LED_R_VALUE)
    _publish(LED_G_TOPIC, LED_G_VALUE)
    _publish(LED_B_TOPIC, LED_B_VALUE)
    time.sleep(LED_WARMUP_SEC)


def led_off() -> None:
    for t in (LED_BRIGHTNESS_TOPIC, LED_R_TOPIC, LED_G_TOPIC, LED_B_TOPIC):
        _publish(t, 0)

# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------

picam2.configure(low_res_config)
picam2.start()

time.sleep(2)  # sensor warm-up
prev_gray: Optional[np.ndarray] = None

try:
    while True:
        # Capture a low-resolution frame for motion analysis (RGB)
        frame_rgb = picam2.capture_array()
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if prev_gray is None:
            prev_gray = gray
            continue

        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        delta = int(np.count_nonzero(thresh))

        _publish(DELTA_TOPIC, delta)

        if delta > MOTION_THRESHOLD:
            led_on()

            # Switch to high-resolution mode
            picam2.stop()
            picam2.configure(high_res_config)
            picam2.start()
            time.sleep(2.0)  # allow auto algorithms to settle

            high_rgb = picam2.capture_array()
            high_bgr = cv2.cvtColor(high_rgb, cv2.COLOR_RGB2BGR)
            ok, jpeg = cv2.imencode(".jpg", high_bgr)
            if ok:
                auth_client.publish(SNAP_TOPIC, jpeg.tobytes(), qos=QOS)
                print(f"Snapshot published (delta={delta}, size={len(jpeg)} bytes)")

            # Restore low-resolution mode
            picam2.stop()
            picam2.configure(low_res_config)
            picam2.start()
            led_off()
            prev_gray = None  # reset baseline
        else:
            prev_gray = gray
            time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopping camera (CTRL+C)")
finally:
    try:
        led_off()
    finally:
        picam2.stop()
        auth_client.loop_stop()
