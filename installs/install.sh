echo 'installin bug-box application'

echo "installing minio-py lib"
git clone https://github.com/minio/minio-py
cd minio-py
sudo python3 setup.py install
cd ..
sudo rm -rf minio-py

echo "installing: paho-mqtt"
pip3 install paho-mqtt

echo "installing: picamera"
sudo pip3 install picamera

echo "installing: rpi_ws281x adafruit-circuitpython-neopixel"
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel

echo "installing: adafruit-circuitpython-sht4x"
sudo pip3 install adafruit-circuitpython-sht4x

echo "testing hardware - pls look for"

cd ../test

echo "testing light"
python3 light-test.py
echo "testing sht sensor"
python3 sht-test.py
echo "testing camera"
python3 camera-test.py