#!/bin/bash

export BOX_NAME="box-1"
export LED_PIXEL_COUNT=8
export IMAGE_CRON="*/2 * * * *"
export ENV_CRON="*/1 * * * *"

export BLOB_STORAGE_URL="192.168.31.111:9000"
export BLOB_STORAGE_ACCESS_KEY="EWl5gjA3EteIp9cf8s77"
export BLOB_STORAGE_SECRET_KEY="Zj0KRckm4yR5IvKPWbCRY9QpfRAJzD6kGo2v7ts7"
export BLOB_STORAGE_BUCKET="bug-box.v2"

export MQTT_BROKER_URL="192.168.31.112"
export MQTT_BROKER_PORT=1883
export MQTT_BROKER_USERNAME="service"
export MQTT_BROKER_PASSWORD="master"
export MQTT_TOPIC="bug-box"
