#!/usr/bin/env python3
import datetime
import json
import logging
import os
import socket
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
IMAGE_CRON = os.getenv("IMAGE_CRON", "*/7 * * * *")
ENV_CRON = os.getenv("ENV_CRON", "*/1 * * * *")

COLOR_W = os.getenv("COLOR_W", "255, 255, 255")
COLOR_R = os.getenv("COLOR_R", "255, 0, 0")
COLOR_G = os.getenv("COLOR_G", "0, 255, 0")
COLOR_B = os.getenv("COLOR_B", "0, 0, 255")

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


def __get_ip():
    return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
            [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


def __create_image_files(files):
    try:
        logging.info(f"creating images for file's '{files}'.")

        def light_on(rgb_string):
            logging.info('Light on.')
            r, g, b = map(int, rgb_string.split(','))
            pixels.fill((r, g, b))

        def light_off():
            logging.info('Light off.')
            pixels.fill((0, 0, 0))

        camera = PiCamera()
        camera.resolution = (2592, 1944)

        camera.start_preview()
        light_on(COLOR_W)
        sleep(3)
        camera.capture(files["image"][1])

        light_on(COLOR_R)
        sleep(1)
        camera.capture(files["image-r"][1])

        light_on(COLOR_G)
        sleep(1)
        camera.capture(files["image-g"][1])

        light_on(COLOR_B)
        sleep(1)
        camera.capture(files["image-b"][1])

        camera.stop_preview()

        light_off()
        camera.close()
    except Exception as ex:
        logging.error(f"Can't prepare metadata: {str(ex)}.")


def __get_env_data():
    logging.info('Getting box environment data.')
    sht = adafruit_sht4x.SHT4x(board.I2C())

    logging.info("Temperature: %.2f / humidity: %.2f." % (sht.temperature, sht.relative_humidity))

    return {"temp": sht.temperature, "hum": sht.relative_humidity}


def __get_host_data():
    ip_address = os.popen('''hostname -I''').readline().replace('\n', '').replace(',', '.')[:-1]
    ip_address = os.popen('''hostname''').readline().replace('\n', '').replace(',', '.')[:-1]
    mac_address = os.popen('''cat /sys/class/net/wlan0/address''').readline().replace('\n', '').replace(',', '.')

    # Return network information as a tuple
    # Index 0: Hostname
    # Index 1: IP Address
    # Index 2: MAC Address
    def __get_network_info():
        hostname = os.popen('''hostname''').readline().replace('\n', '').replace(',', '.')
        ip_address = os.popen('''hostname -I''').readline().replace('\n', '').replace(',', '.')
        mac_address = os.popen('''cat /sys/class/net/wlan0/address''').readline().replace('\n', '').replace(',',
                                                                                                            '.')
        return (hostname, ip_address, mac_address)


    # Return CPU temperature as a character string
    def __get_cpu_temperature():
        res = os.popen('vcgencmd measure_temp').readline()
        return (res.replace("temp=", "").replace("'C\n", ""))

    # Return % of CPU used by user as a character string
    def __get_cpu_use():
        return (str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()))

    # Return RAM information (unit=kb) in a list
    # Index 0: total RAM
    # Index 1: used RAM
    # Index 2: free RAM
    def __get_ram_info():
        p = os.popen('free -h')
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                return (line.split()[1:4])

    # Return information about disk space as a list (unit included)
    # Index 0: total disk space
    # Index 1: used disk space
    # Index 2: remaining disk space
    # Index 3: percentage of disk used
    def __get_disk_space():
        p = os.popen("df -h /")
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                return (line.split()[1:5])

    def __get_boot_time():
        return os.popen('uptime -p').read()[:-1]

    return {
        'hostname': __get_network_info()[0],
        'ip-address': __get_network_info()[1],
        'macaddress': __get_network_info()[2],
        'cpu': {
            'usage': __get_cpu_use(),
            'temperature': __get_cpu_temperature()
        },
        'ram': {
            "total": __get_ram_info()[0],
            "used": __get_ram_info()[1],
            "free": __get_ram_info()[2]
        },
        'disk': {
            'total': __get_disk_space()[0],
            'used ': __get_disk_space()[1],
            'remaining ': __get_disk_space()[2],
            'percentage': __get_disk_space()[3]
        },
        'boot-time': __get_boot_time()
    }


def __create_metadata_file(files):
    try:
        logging.info(f"creating metadata for files '{files}'.")

        env_data = None
        try:
            env_data = __get_env_data()
        except Exception as e:
            logging.info(f"env sensor not work - env data null. '{e}'")

        metadata = {
            "name": BOX_NAME,
            "env-data": env_data,
            "images": {
                "image": files["image"][2],
                "image-r": files["image-r"][2],
                "image-g": files["image-g"][2],
                "image-b": files["image-b"][2]
            },
            "led-fill": {
                "R": COLOR_R,
                "G": COLOR_G,
                "B": COLOR_B
            },
            "device": __get_host_data(),
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


def __publish_metadata_to_mqtt(files):
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


def __put_files_to_minio_blob_storage(files):
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


def __delete_files(files):
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

    __create_image_files(files)
    __create_metadata_file(files)
    __publish_metadata_to_mqtt(files)

    __put_files_to_minio_blob_storage(files)

    __delete_files(files)


def env_job():
    logging.info(f"taking env data and publishing to MQTT.")

    env_data = None
    try:
        env_data = __get_env_data()
    except Exception as e:
        logging.warning(f"env sensor not work - env data null. '{e}'")

    metadata = {
        "name": BOX_NAME,
        "env-data": env_data,
        "device": __get_host_data()
    }

    client = mqtt.Client()
    client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    client.connect(MQTT_BROKER_URL, int(MQTT_BROKER_PORT))

    json_data = json.dumps(metadata)
    client.publish(f"{MQTT_TOPIC}/{BOX_NAME}/env", json_data, retain=True)

    client.disconnect()


def start_info():
    logging.info(f"publishing to MQTT startup info.")

    data = {
        "startup": datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S"),
        "device": __get_host_data()
    }

    client = mqtt.Client()
    client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    client.connect(MQTT_BROKER_URL, int(MQTT_BROKER_PORT))

    json_data = json.dumps(data)
    client.publish(f"{MQTT_TOPIC}/{BOX_NAME}/info", json_data, retain=True)

    client.disconnect()


def main():
    scheduler = BlockingScheduler()

    scheduler.add_job(image_job, CronTrigger.from_crontab(IMAGE_CRON))

    try:
        __get_env_data()
        scheduler.add_job(env_job, CronTrigger.from_crontab(ENV_CRON))
    except Exception as e:
        logging.error(
            f"exception during getting env data - env sensor may be not connected to system! environment procces "
            f"disable. '{e}'")

    start_info()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


def __check_variable(var, str):
    logging.info(f"str: {var}")
    if var is None:
        message = f"environment variable {str} is not set!"
        logging.error(message)
        raise Exception(message)


def __validate_env_var():
    logging.info(f"******************************")
    __check_variable(BOX_NAME, 'BOX_NAME')
    __check_variable(LED_PIXEL_COUNT, 'LED_PIXEL_COUNT')
    __check_variable(IMAGE_CRON, 'IMAGE_CRON')
    __check_variable(ENV_CRON, 'ENV_CRON')
    logging.info(f"******************************")
    __check_variable(COLOR_W, 'COLOR_W')
    __check_variable(COLOR_R, 'COLOR_R')
    __check_variable(COLOR_G, 'COLOR_G')
    __check_variable(COLOR_B, 'COLOR_B')
    logging.info(f"******************************")
    __check_variable(BLOB_STORAGE_URL, 'BLOB_STORAGE_URL')
    __check_variable(BLOB_STORAGE_ACCESS_KEY, 'BLOB_STORAGE_ACCESS_KEY')
    __check_variable(BLOB_STORAGE_SECRET_KEY, 'BLOB_STORAGE_SECRET_KEY')
    __check_variable(BLOB_STORAGE_BUCKET, 'BLOB_STORAGE_BUCKET')
    logging.info(f"******************************")
    __check_variable(MQTT_BROKER_URL, 'MQTT_BROKER_URL')
    __check_variable(MQTT_BROKER_PORT, 'MQTT_BROKER_PORT')
    __check_variable(MQTT_BROKER_USERNAME, 'MQTT_BROKER_USERNAME')
    __check_variable(MQTT_BROKER_PASSWORD, 'MQTT_BROKER_PASSWORD')
    __check_variable(MQTT_TOPIC, 'MQTT_TOPIC')
    logging.info(f"******************************")


if __name__ == "__main__":
    try:
        __validate_env_var()

        main()
    except S3Error as exc:
        print("error occurred.", exc)
