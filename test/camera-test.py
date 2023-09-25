
from time import sleep

from picamera import PiCamera

camera = PiCamera()
print("taking picture to: '/tmp/image.jpeg'")
camera.start_preview()
sleep(1)

camera.capture('/tmp/image.jpeg')
camera.stop_preview()
