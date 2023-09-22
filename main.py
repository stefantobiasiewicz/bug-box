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

LED_PIN = 25
SLEEP_TIME = 60

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

def create_metadata(metadata_file_path):
    try:
        logging.info(f"creating metadata for file '{metadata_file_path}'.")

        data = get_env_data()

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

def put_files(image_file_name, image_path, metadata_file_name, metadata_path):
    try:
        logging.info(f"saving files to blobstorage image: '{image_path}' and image: '{metadata_path}'.")

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

            bucket_image_path = f'{BLOB_STORAGE_PATH}/images/{image_file_name}'
            bucket_metadata_path = f'{BLOB_STORAGE_PATH}/metadata/{metadata_file_name}'

            client.fput_object(BLOB_STORAGE_BUCKET, bucket_image_path, image_path)
            client.fput_object(BLOB_STORAGE_BUCKET, bucket_metadata_path, metadata_path)
    except Exception as ex:
        logging.error(f"Can't save files: {str(ex)}.")

def delete_files(image_path, metadata_path):
    os.remove(image_path)
    os.remove(metadata_path)

def pre_main():
    while(True):
        now = datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
        image_file_name = f"image-{now}.jpg"
        metadata_file_name = f"metadata-{now}.json"

        image_local_path = f'/tmp/{image_file_name}'
        metadata_local_path = f'/tmp/{metadata_file_name}'

        create_image(image_local_path)
        create_metadata(metadata_local_path)

        publish_metadata(metadata_local_path)

        put_files(image_file_name, image_local_path, metadata_file_name, metadata_local_path)

        sleep(1800)


def main():
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio(
        "192.168.31.111:9000",
        access_key="EWl5gjA3EteIp9cf8s77",
        secret_key="Zj0KRckm4yR5IvKPWbCRY9QpfRAJzD6kGo2v7ts7",
        secure=False
    )

    bucket_name = 'bug-box'

    # Make 'asiatrip' bucket if not exist.
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
    else:
        print(f"Bucket '{bucket_name}' already exists")

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.HIGH)

    while (1):
        now = datetime.datetime.now()
        formatted_date = now.strftime("%d.%m.%Y-%H:%M:%S")
        file_name = f"image-{formatted_date}.jpg"

        local_path = f'/tmp/{file_name}'
        print(
            f"crating picture {local_path}"
        )

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
        GPIO.output(LED_PIN, GPIO.LOW)
        sleep(1)

        camera.capture(local_path)
        camera.stop_preview()
        GPIO.output(LED_PIN, GPIO.HIGH)

        camera.close()

        client.fput_object(bucket_name, file_name, local_path, )
        print(
            f"picture was pushed to {bucket_name} and {file_name}"
        )

        print(
            f"deleting {local_path}"
        )
        os.remove(local_path)
        sleep(SLEEP_TIME)


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)