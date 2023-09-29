#!/usr/bin/env python3
import datetime
import json
import logging
import os
import sys
from time import sleep

import adafruit_sht4x
# RPI hardware stuff
import board
import neopixel
import paho.mqtt.client as mqtt
# scheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
# clients
from minio import Minio
from minio.error import S3Error
from picamera import PiCamera

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

BOX_NAME = os.getenv("BOX_NAME")
LED_PIXEL_COUNT = os.getenv("LED_PIXEL_COUNT", 8)
IMAGE_CRON = os.getenv("IMAGE_CORN", "*/2 * * * *")
ENV_CRON = os.getenv("ENV_CRON", "*/1 * * * *")

BLOB_STORAGE_URL = os.getenv("BLOB_STORAGE_URL")
BLOB_STORAGE_ACCESS_KEY = os.getenv("BLOB_STORAGE_ACCESS_KEY")
BLOB_STORAGE_SECRET_KEY = os.getenv("BLOB_STORAGE_SECRET_KEY")

BLOB_STORAGE_BUCKET = os.getenv("BLOB_STORAGE_BUCKET")

MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL")
MQTT_BROKER_PORT = os.getenv("MQTT_BROKER_PORT")
MQTT_BROKER_USERNAME = os.getenv("MQTT_BROKER_USERNAME")
MQTT_BROKER_PASSWORD = os.getenv("MQTT_BROKER_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

pixels = neopixel.NeoPixel(board.D18, int(LED_PIXEL_COUNT))


def create_image(files):
    try:
        logging.info(f"creating images for file's '{files}'.")

        def light_on(r, g, b):
            logging.info('Light on.')
            pixels.fill((r, g, b))

        def light_off():
            logging.info('Light off.')
            pixels.fill((0, 0, 0))

        camera = PiCamera()
        camera.start_preview()
        light_on(255, 255, 255)
        sleep(3)
        camera.capture(files["image"][1])

        light_on(255, 0, 0)
        sleep(1)
        camera.capture(files["image-r"][1])

        light_on(0, 255, 0)
        sleep(1)
        camera.capture(files["image-g"][1])

        light_on(0, 0, 255)
        sleep(1)
        camera.capture(files["image-b"][1])

        camera.stop_preview()

        light_off()
        camera.close()
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")


def get_env_data():
    logging.info('Getting box environment data.')
    sht = adafruit_sht4x.SHT4x(board.I2C())

    logging.info("Temperature: %.2f / humidity: %.2f." % (sht.temperature, sht.relative_humidity))

    return {"temp": sht.temperature, "hum": sht.relative_humidity}


def create_metadata(files):
    try:
        logging.info(f"creating metadata for files '{files}'.")

        metadata = {
            "name": BOX_NAME,
            "env-data": get_env_data(),
            "images": {
                "image": files["image"][2],
                "image-r": files["image-r"][2],
                "image-g": files["image-g"][2],
                "image-b": files["image-b"][2]
            },
            "image-cron": IMAGE_CRON,
            "env-cron": ENV_CRON,
            "led-count": LED_PIXEL_COUNT
        }

        json_object = json.dumps(metadata)

        # Writing to sample.json
        with open(files["metadata"][1], "w") as outfile:
            outfile.write(json_object)
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")


def publish_metadata(files):
    try:
        logging.info(f"publishing metadata: '{files}' to MQTT.")

        with open(files["metadata"][1], "r") as file:
            metadata = json.load(file)

        client = mqtt.Client()

        client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
        client.connect(MQTT_BROKER_URL, int(MQTT_BROKER_PORT))

        json_data = json.dumps(metadata)

        client.publish(f"{MQTT_TOPIC}/{BOX_NAME}", json_data, retain=True)

        client.disconnect()
    except Exception as ex:
        logging.error(f"Can't publish metadata: {str(ex)}.")


def put_files(files):
    try:
        logging.info(f"saving files to blob storage {files}.")

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

        client.fput_object(BLOB_STORAGE_BUCKET, files["metadata"][2], files["metadata"][1])
        client.fput_object(BLOB_STORAGE_BUCKET, files["image"][2], files["image"][1])
        client.fput_object(BLOB_STORAGE_BUCKET, files["image-r"][2], files["image-r"][1])
        client.fput_object(BLOB_STORAGE_BUCKET, files["image-g"][2], files["image-g"][1])
        client.fput_object(BLOB_STORAGE_BUCKET, files["image-b"][2], files["image-b"][1])
    except Exception as ex:
        logging.error(f"Can't save files: {str(ex)}.")


def delete_files(files):
    os.remove(files["metadata"][1])
    os.remove(files["image"][1])
    os.remove(files["image-r"][1])
    os.remove(files["image-g"][1])
    os.remove(files["image-b"][1])


def image_job():
    now = datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
    image_file_name = f"image-{now}.jpg"
    image_r_file_name = f"image-r-{now}.jpg"
    image_g_file_name = f"image-g-{now}.jpg"
    image_b_file_name = f"image-b-{now}.jpg"
    metadata_file_name = f"metadata-{now}.json"

    files = {
        'image': (image_file_name, f'/tmp/{image_file_name}', f'{BOX_NAME}/images/{image_file_name}'),
        'image-r': (image_r_file_name, f'/tmp/{image_r_file_name}', f'{BOX_NAME}/images/color/{image_r_file_name}'),
        'image-g': (image_g_file_name, f'/tmp/{image_g_file_name}', f'{BOX_NAME}/images/color/{image_g_file_name}'),
        'image-b': (image_b_file_name, f'/tmp/{image_b_file_name}', f'{BOX_NAME}/images/color/{image_b_file_name}'),
        'metadata': (metadata_file_name, f'/tmp/{metadata_file_name}', f'{BOX_NAME}/metadata/{metadata_file_name}')
    }

    create_image(files)
    create_metadata(files)
    publish_metadata(files)

    put_files(files)

    delete_files(files)


def env_job():
    logging.info(f"taking env data and publishing to MQTT.")

    env_data = None
    try:
        env_data = get_env_data()
    except Exception as e:
        logging.warning(f"env sensor not work - env data null. '{e}'")

    metadata = {
        "name": BOX_NAME,
        "env-data": env_data
    }

    client = mqtt.Client()
    client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    client.connect(MQTT_BROKER_URL, int(MQTT_BROKER_PORT))

    json_data = json.dumps(metadata)
    client.publish(f"{MQTT_TOPIC}/{BOX_NAME}/env", json_data, retain=True)

    client.disconnect()


def main():
    scheduler = BlockingScheduler()

    scheduler.add_job(image_job, CronTrigger.from_crontab(IMAGE_CRON))

    try:
        get_env_data()
        scheduler.add_job(env_job, CronTrigger.from_crontab(ENV_CRON))
    except Exception as e:
        logging.error(
            f"exception during getting env data - env sensor may be not connected to system! environment procces "
            f"disable. '{e}'")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    try:
        logging.info(f"******************************")
        logging.info(f"BOX_NAME: {BOX_NAME}")
        logging.info(f"LED_PIXEL_COUNT: {LED_PIXEL_COUNT}")
        logging.info(f"IMAGE_CRON: {IMAGE_CRON}")
        logging.info(f"ENV_CRON: {ENV_CRON}")
        logging.info(f"******************************")
        logging.info(f"BLOB_STORAGE_URL: {BLOB_STORAGE_URL}")
        logging.info(f"BLOB_STORAGE_ACCESS_KEY: {BLOB_STORAGE_ACCESS_KEY}")
        logging.info(f"BLOB_STORAGE_SECRET_KEY: {BLOB_STORAGE_SECRET_KEY}")
        logging.info(f"BLOB_STORAGE_BUCKET: {BLOB_STORAGE_BUCKET}")
        logging.info(f"******************************")
        logging.info(f"MQTT_BROKER_URL: {MQTT_BROKER_URL}")
        logging.info(f"MQTT_BROKER_PORT: {MQTT_BROKER_PORT}")
        logging.info(f"MQTT_BROKER_USERNAME: {MQTT_BROKER_USERNAME}")
        logging.info(f"MQTT_BROKER_PASSWORD: {MQTT_BROKER_PASSWORD}")
        logging.info(f"MQTT_TOPIC: {MQTT_TOPIC}")
        logging.info(f"******************************")

        main()
    except S3Error as exc:
        print("error occurred.", exc)
