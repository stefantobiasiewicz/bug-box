import sys
import neopixel
import board
from time import sleep


def main():
    try:
        pixels = neopixel.NeoPixel(board.D18, 32)
        pixels.fill((0, 0, 0))
        sys.exit(0)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        sys.exit(-1)

if __name__ == "__main__":
    main()