import smbus
import time


bus = smbus.SMBus(1)
TCS_ADDR = 0x29

COMMAND = 0x80
ENABLE = 0x00
ATIME = 0x01
CONTROL = 0x0F
CDATAL = 0x14
RDATAL = 0x16
GDATAL = 0x18
BDATAL = 0x1A

PON = 0x01
AEN = 0x02


def write_register(reg, value):
    bus.write_byte_data(TCS_ADDR, COMMAND | reg, value)

def read_word(reg):
    low = bus.read_byte_data(TCS_ADDR, COMMAND | reg)
    high = bus.read_byte_data(TCS_ADDR, COMMAND | (reg + 1))
    return (high << 8) | low

def init_sensor():
    write_register(ENABLE, PON)
    
    write_register(ENABLE, PON | AEN)

    # 50 ms integration time
    write_register(ATIME, 0xEB)

    # 4x gain
    write_register(CONTROL, 0x01)

def get_raw_data():
    c = read_word(CDATAL)
    r = read_word(RDATAL)
    g = read_word(GDATAL)
    b = read_word(BDATAL)
    return r, g, b, c

def raw_to_rgb_bytes(r, g, b, c):
    if c == 0:
        return 0, 0, 0

    red = int((r / c) * 255)
    green = int((g / c) * 255)
    blue = int((b / c) * 255)

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return red, green, blue


def isGreenRGB(r, g, b, c):
    return (42 <= r <= 70) and \
           (110 <= g <= 155) and \
           (45 <= b <= 70) and \
           (c >= 900)

def isBlueRGB(r, g, b, c):
    return (25 <= r <= 65) and \
           (70 <= g <= 95) and \
           (110 <= b <= 170) and \
           (c >= 500)

def isBlackRGB(r, g, b, c):
    return (58 <= r < 100) and \
           (85 <= g <= 105) and \
           (60 <= b <= 85) and \
           (200 <= c <= 800)

def isGrayRGB(r, g, b, c):
    return (70 <= r <= 105) and \
           (90 <= g <= 96) and \
           (67 <= b <= 75) and \
           (900 <= c <= 4000)

def isBrownRGB(r, g, b, c):
    return (85 <= r <= 120) and \
           (85 <= g <= 105) and \
           (50 <= b <= 68) and \
           (500 <= c <= 2000)

def isRecyclable(r, g, b, c):
    return isGreenRGB(r, g, b, c) or isBlueRGB(r, g, b, c)

def isGarbage(r, g, b, c):
    return isBlackRGB(r, g, b, c) or isGrayRGB(r, g, b, c) or isBrownRGB(r, g, b, c)


try:
    init_sensor()
    print("Sensor workin")

    while True:
        time.sleep(0.6)
        raw_r, raw_g, raw_b, raw_c = get_raw_data()
        r, g, b = raw_to_rgb_bytes(raw_r, raw_g, raw_b, raw_c)

        print(f"R: {r}\tG: {g}\tB: {b}\tC: {raw_c}", end="")

        if isRecyclable(r, g, b, raw_c):
            print("\t=> RECYCLABLE")
            if isGreenRGB(r, g, b, raw_c):
                print(" (GREEN)")
            if isBlueRGB(r, g, b, raw_c):
                print(" (BLUE)")

        elif isGarbage(r, g, b, raw_c):
            print("\t=> GARBAGE")
            if isBlackRGB(r, g, b, raw_c):
                print(" (BLACK)")
            elif isGrayRGB(r, g, b, raw_c):
                print(" (GRAY)")
            elif isBrownRGB(r, g, b, raw_c):
                print(" (BROWN)")



        else:
            print("\t=> EMPTY")

    

except KeyboardInterrupt:
    print("\nStopp")
