import sys
import neopixel
import board
from time import sleep


def main():
    try:
        pixels = neopixel.NeoPixel(board.D18, 8)

        def light_on():
            pixels.fill((255, 255, 255))

        def light_off():
            pixels.fill((0, 0, 0))

        for i in range(3):
            light_on()
            sleep(1)
            light_off()
            sleep(1)

        sys.exit(0)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        sys.exit(-1)

if __name__ == "__main__":
    main()