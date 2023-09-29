import subprocess
import paho.mqtt.client as mqtt
import time

# Konfiguracja MQTT
MQTT_BROKER_URL = "192.168.31.112"
MQTT_BROKER_PORT = 1883
mqtt_topic = "bug-box-logs"
MQTT_BROKER_USERNAME = "service"
MQTT_BROKER_PASSWORD = "master"

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
            mqtt_client.publish(mqtt_topic, line.strip())
        else:
            time.sleep(1)

if __name__ == "__main__":
    publish_logs()
