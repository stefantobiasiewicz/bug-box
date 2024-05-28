#!/bin/bash

export BOX_NAME="simple-green"
export LED_PIXEL_COUNT="8"
export IMAGE_CRON="*/1 * * * *"
export ENV_CRON="*/1 * * * *"

export COLOR_W="30, 30, 30"

export BLOB_STORAGE_URL="192.168.31.112:9001"
export BLOB_STORAGE_ACCESS_KEY="JxFg74nEbV0PbKcTcAvs"
export BLOB_STORAGE_SECRET_KEY="iNjnd0Yais0mOKlVGJer5ko119KswwOUpWpqpyzu"
export BLOB_STORAGE_BUCKET="greenhouse"

export MQTT_BROKER_URL="192.168.31.112"
export MQTT_BROKER_PORT="1883"
export MQTT_BROKER_USERNAME="service"
export MQTT_BROKER_PASSWORD="master"
export MQTT_TOPIC="greenhouse"
