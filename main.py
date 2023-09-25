#!/usr/bin/env python3

from time import sleep
import datetime
import os
import logging
import json

# clients
from minio import Minio
from minio.error import S3Error
import paho.mqtt.client as mqtt


# RPI hardware suff
import board
import neopixel
from picamera import PiCamera
import adafruit_sht4x


pixels = neopixel.NeoPixel(board.D18, 8)

SLEEP_TIME = 10

BOX_NAME = os.getenv("BOX_NAME")

BLOB_STORAGE_URL = os.getenv("BLOB_STORAGE_URL")
BLOB_STORAGE_ACCESS_KEY = os.getenv("BLOB_STORAGE_ACCESS_KEY")
BLOB_STORAGE_SECRET_KEY = os.getenv("BLOB_STORAGE_SECRET_KEY")

BLOB_STORAGE_BUCKET = os.getenv("BLOB_STORAGE_BUCKET")
BLOB_STORAGE_PATH = os.getenv("BLOB_STORAGE_PATH")

MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL")
MQTT_BROKER_USERNAME = os.getenv("MQTT_BROKER_USERNAME")
MQTT_BROKER_PASSWORD = os.getenv("MQTT_BROKER_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")


def create_image(image_file_path):
    try:
        logging.info(f"creating image for file '{image_file_path}'.")

        def light_on():
            logging.info('Light on.')
            pixels.fill((255, 255, 255))

        def light_off():
            logging.info('Light off.')
            pixels.fill((0, 0, 0))

        camera = PiCamera()

        camera.iso = 800
        # Wait for the automatic gain control to settle
        sleep(2)
        # Now fix the values
        camera.shutter_speed = camera.exposure_speed
        camera.exposure_mode = 'off'
        g = camera.awb_gains
        camera.awb_mode = 'off'
        camera.awb_gains = g

        camera.start_preview()
        light_on()

        sleep(1)
        camera.capture(image_file_path)
        camera.stop_preview()

        light_off()
        camera.close()
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")

def get_env_data():
    logging.info('Getting box environment data.')
    sht = adafruit_sht4x.SHT4x(board.I2C())

    logging.info("Temperature: %.2f / humidity: %.2f." % (sht.temperature, sht.relative_humidity))

    return { "temp" : sht.temperature, "hum": sht.relative_humidity}

def create_metadata(metadata_file_path, bucket_image_path, bucket_metadata_path):
    try:
        logging.info(f"creating metadata for file '{metadata_file_path}'.")

        data = get_env_data()

        data["bucket_image_path"] = bucket_image_path
        data["bucket_metadata_path"] = bucket_metadata_path

        json_object = json.dumps(data)

        # Writing to sample.json
        with open(metadata_file_path, "w") as outfile:
            outfile.write(json_object)
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")

def publish_metadata(metadata_file_path):
    try:
        logging.info(f"publishing metadata: '{metadata_file_path}' to MQTT.")

        with open(metadata_file_path, "r") as file:
            metadata = json.load(file)

        client = mqtt.Client()

        if MQTT_BROKER_USERNAME and MQTT_BROKER_PASSWORD:
            client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)

        client.connect(MQTT_BROKER_URL)

        json_data = json.dumps(metadata)

        client.publish(MQTT_TOPIC, json_data)

        client.disconnect()
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")

def put_files(bucket_image_path, image_path, bucket_metadata_path, metadata_path):
    try:
        logging.info(f"saving files to blobstorage image: '{bucket_image_path}' and image: '{bucket_metadata_path}'.")

        client = Minio(
            BLOB_STORAGE_URL,
            access_key=BLOB_STORAGE_ACCESS_KEY,
            secret_key=BLOB_STORAGE_SECRET_KEY,
            secure=False
        )

        found = client.bucket_exists(BLOB_STORAGE_BUCKET)
        if not found:
            logging.info(f"Bucket '{BLOB_STORAGE_BUCKET}' not exists, creating new one.")
            client.make_bucket(BLOB_STORAGE_BUCKET)

        client.fput_object(BLOB_STORAGE_BUCKET, bucket_image_path, image_path)
        client.fput_object(BLOB_STORAGE_BUCKET, bucket_metadata_path, metadata_path)
    except Exception as ex:
        logging.error(f"Can't save files: {str(ex)}.")

def delete_files(image_path, metadata_path):
    os.remove(image_path)
    os.remove(metadata_path)

def main():
    while(True):
        now = datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
        image_file_name = f"image-{now}.jpg"
        metadata_file_name = f"metadata-{now}.json"

        image_local_path = f'/tmp/{image_file_name}'
        metadata_local_path = f'/tmp/{metadata_file_name}'

        bucket_image_path = f'{BLOB_STORAGE_PATH}/images/{image_file_name}'
        bucket_metadata_path = f'{BLOB_STORAGE_PATH}/metadata/{metadata_file_name}'

        create_image(image_local_path)
        create_metadata(metadata_local_path, bucket_image_path, bucket_metadata_path)

        publish_metadata(metadata_local_path)

        put_files(bucket_image_path, image_local_path, bucket_metadata_path, metadata_local_path)

        sleep(SLEEP_TIME)


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)