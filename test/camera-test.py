import sys
from time import sleep
from picamera import PiCamera

def main():
    try:
        camera = PiCamera()
        print("Taking a picture to: '/tmp/image.jpeg'")
        camera.start_preview()
        sleep(1)
        camera.capture('/tmp/image.jpeg')
        camera.stop_preview()
        sys.exit(0)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        sys.exit(-1)

if __name__ == "__main__":
    main()