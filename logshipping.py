import os
import subprocess
import paho.mqtt.client as mqtt
import time

# Konfiguracja MQTT
BOX_NAME = os.getenv("BOX_NAME")

MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL")
MQTT_BROKER_PORT = os.getenv("MQTT_BROKER_PORT")
MQTT_BROKER_USERNAME = os.getenv("MQTT_BROKER_USERNAME")
MQTT_BROKER_PASSWORD = os.getenv("MQTT_BROKER_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

# Funkcja do publikowania logów
def publish_logs():
    process = subprocess.Popen(["sudo", "journalctl", "-fu", "bug-box"], stdout=subprocess.PIPE)
    mqtt_client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Connection failed with code {rc}")


    mqtt_client.on_connect = on_connect
    mqtt_client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    mqtt_client.connect(MQTT_BROKER_URL, int(MQTT_BROKER_PORT))
    mqtt_client.loop_start()

    while True:
        line = process.stdout.readline()
        if line:
            mqtt_client.publish(f'{MQTT_TOPIC}/{BOX_NAME}/logs', line.strip(), retain=True)
        else:
            time.sleep(1)

if __name__ == "__main__":
    publish_logs()
