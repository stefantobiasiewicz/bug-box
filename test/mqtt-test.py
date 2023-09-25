import paho.mqtt.client as mqtt

client = mqtt.Client()

client.username_pw_set("service", "master")
client.connect('192.168.31.112:')


a =2
