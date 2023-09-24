import neopixel
import board
from time import sleep

pixels = neopixel.NeoPixel(board.D18, 8)

def light_on():
    pixels.fill((255, 255, 255))


def light_off():
    pixels.fill((0, 0, 0))

while(True):
    light_on()
    sleep(1)
    light_off()
    sleep(1)