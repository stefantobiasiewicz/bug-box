import board
import adafruit_sht4x

while(True):
    sht = adafruit_sht4x.SHT4x(board.I2C())
    print("Temperature: %.2f / humidity: %.2f." % (sht.temperature, sht.relative_humidity))
