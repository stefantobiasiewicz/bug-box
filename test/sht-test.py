import sys
import board
import adafruit_sht4x

def main():
    try:
        for i in range(10):
            sht = adafruit_sht4x.SHT4x(board.I2C())
            print("Temperature: %.2f / humidity: %.2f." % (sht.temperature, sht.relative_humidity))
        sys.exit(0)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        sys.exit(-1)

if __name__ == "__main__":
    main()