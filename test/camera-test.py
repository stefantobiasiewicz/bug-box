import os
from time import sleep

from picamera import PiCamera

camera = PiCamera()
camera.start_preview()
sleep(1)

camera.capture('/tmp/image.jpeg')
camera.stop_preview()

os.remove('/tmp/image.jpeg')