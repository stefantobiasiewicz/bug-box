import sys
from time import sleep
from picamera import PiCamera
import neopixel
import board

def main():
    try:
        camera = PiCamera()

        pixels = neopixel.NeoPixel(board.D18, 8)

        camera.start_preview()

        for i in range(25):
            light = i * 10
            pixels.fill((light, light, light))
            sleep(1)
            camera.capture(f'/tmp/image-{i}.jpeg')
            print(f"Taking a picture to: '/tmp/image-{i}.jpeg'")

        camera.stop_preview()
        sys.exit(0)


        sys.exit(0)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        sys.exit(-1)

if __name__ == "__main__":
    main()