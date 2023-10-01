#!/bin/bash

echo 'installin bug-box application'

echo "installing minio-py lib"
git clone https://github.com/minio/minio-py
cd minio-py
sudo python3 setup.py install
cd ..
sudo rm -rf minio-py

echo "installing: apscheduler"
sudo pip3 install apscheduler

echo "installing: paho-mqtt"
sudo pip3 install paho-mqtt

echo "installing: picamera"
sudo pip3 install picamera

echo "installing: rpi_ws281x adafruit-circuitpython-neopixel"
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel

echo "installing: adafruit-circuitpython-sht4x"
sudo pip3 install adafruit-circuitpython-sht4x

echo "enabling raspberry pi board-hardware"
echo "enable I2C"
sudo raspi-config nonint do_i2c 0
echo "enable camera"
sudo raspi-config nonint do_camera 0
echo "enable legacy-camera"
sudo raspi-config nonint do_legacy 0

echo "testing hardware - pls look for"

cd ../test

echo "testing light"
python3 light-test.py
echo "testing sht sensor"
python3 sht-test.py
echo "testing camera"
python3 camera-test.py

echo "instaling app to '/opt/bug-box'"

cd ..
chmod +x run.sh
chmod +x run-log-shipping.sh
sudo cp -r $(pwd) /opt/bug-box
sudo cp installs/bug-box.service /etc/systemd/system/bug-box.service

sudo systemctl daemon-reload
sudo systemctl enable bug-box

sudo systemctl start bug-box

echo "installing done"
