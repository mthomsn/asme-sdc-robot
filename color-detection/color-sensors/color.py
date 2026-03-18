import smbus
import time
import statistics
import RPi.GPIO as GPIO

mp1 = 17 #motor pin 1
mp2 = 27 #motor pin 2
GPIO.setmode(GPIO.BCM)
GPIO.setup(mp1, GPIO.OUT)
GPIO.setup(mp2, GPIO.OUT)

def right():
    GPIO.output(mp1, GPIO.HIGH)
    GPIO.output(mp2, GPIO.LOW)

def left():
    GPIO.output(mp1, GPIO.LOW)
    GPIO.output(mp2, GPIO.HIGH)

def stop():
    GPIO.output(mp1, GPIO.LOW)
    GPIO.output(mp2, GPIO.LOW)

def sort(item):
    if item == 'Trash':
        right()
        time.sleep(0.05)
    if item == 'Recycle':
        left()
        time.sleep(0.05)
    stop()

bus = smbus.SMBus(1)
TCS_ADDR = 0x29

COMMAND = 0x80
ENABLE = 0x00
ATIME = 0x01
CONTROL = 0x0F
STATUS = 0x13
CDATAL = 0x14
RDATAL = 0x16
GDATAL = 0x18
BDATAL = 0x1A

PON = 0x01
AEN = 0x02
AVALID = 0x01



def write_register(reg, value):
    bus.write_byte_data(TCS_ADDR, COMMAND | reg, value)

def read_byte(reg):
    return bus.read_byte_data(TCS_ADDR, COMMAND | reg)

def read_word(reg):
    low = bus.read_byte_data(TCS_ADDR, COMMAND | reg)
    high = bus.read_byte_data(TCS_ADDR, COMMAND | (reg + 1))
    return (high << 8) | low

def init_sensor():
    write_register(ENABLE, PON)
    time.sleep(0.01)

    # longer integration time for more stable readings
    write_register(ATIME, 0xD5)   # ~101 ms

    # 4x gain
    write_register(CONTROL, 0x01)

    write_register(ENABLE, PON | AEN)
    time.sleep(0.2)

def wait_for_data():
    while True:
        status = read_byte(STATUS)
        if status & AVALID:
            break
        time.sleep(0.005)

def get_raw_data():
    wait_for_data()
    c = read_word(CDATAL)
    r = read_word(RDATAL)
    g = read_word(GDATAL)
    b = read_word(BDATAL)
    return r, g, b, c

def get_averaged_data(samples=7, delay=0.02):
    r_vals = []
    g_vals = []
    b_vals = []
    c_vals = []

    for _ in range(samples):
        r, g, b, c = get_raw_data()
        r_vals.append(r)
        g_vals.append(g)
        b_vals.append(b)
        c_vals.append(c)
        time.sleep(delay)

    r = int(statistics.median(r_vals))
    g = int(statistics.median(g_vals))
    b = int(statistics.median(b_vals))
    c = int(statistics.median(c_vals))

    return r, g, b, c

def raw_to_rgb_bytes(r, g, b, c):
    if c <= 0:
        return 0, 0, 0

    red = int((r / c) * 255)
    green = int((g / c) * 255)
    blue = int((b / c) * 255)

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return red, green, blue

def get_ratios(r, g, b):
    rg = r / g if g != 0 else 999
    bg = b / g if g != 0 else 999
    rb = r / b if b != 0 else 999
    br = b / r if r != 0 else 999
    gb = g / b if b != 0 else 999
    gr = g / r if r != 0 else 999
    return rg, bg, rb, br, gb, gr

def isGreenRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (42 <= r <= 105) and \
           (105 <= g <= 155) and \
           (45 <= b <= 85) and \
           (c >= 400) and \
           (rg >= 0.30 and rg <= 0.90) and \
           (bg >= 0.30 and bg <= 0.85) and \
           (gr >= 1.0)

def isBlueRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (25 <= r <= 65) and \
           (70 <= g <= 100) and \
           (90 <= b <= 170) and \
           (c >= 500) and \
           (br >= 1.5) and \
           (rb >= 0.20 and rb <= 0.70) and \
           (gb >= 0.45 and gb <= 1.00)

def isBlackRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (58 <= r <= 110) and \
           (85 <= g <= 105) and \
           (60 <= b <= 95) and \
           (200 <= c <= 1900) and \
           (0.55 <= rg <= 1.15) and \
           (0.60 <= rb <= 1.65)

def isGrayRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (70 <= r <= 105) and \
           (90 <= g <= 105) and \
           (67 <= b <= 75) and \
           (900 <= c) and \
           (0.70 <= rg <= 1.15) and \
           (0.85 <= rb <= 1.45)

def isBrownRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (85 <= r <= 120) and \
           (85 <= g <= 105) and \
           (50 <= b <= 68) and \
           (500 <= c) and \
           (0.90 <= rg <= 1.35) and \
           (1.30 <= rb <= 2.30)

def isRecyclable(r, g, b, c):
    return isGreenRGB(r, g, b, c) or isBlueRGB(r, g, b, c)

def isGarbage(r, g, b, c):
    return isBlackRGB(r, g, b, c) or isGrayRGB(r, g, b, c) or isBrownRGB(r, g, b, c)


try:
    init_sensor()
    print("Sensor workin")

    while True:
        #time.sleep(0.01)

        raw_r, raw_g, raw_b, raw_c = get_averaged_data(samples=7, delay=0.01)

        if raw_c < 250:
            print(f"R: 0\tG: 0\tB: 0\tC: {raw_c}\t=> EMPTY / TOO DARK")
            continue

        r, g, b = raw_to_rgb_bytes(raw_r, raw_g, raw_b, raw_c)
        rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

        print(
            f"R: {r}\tG: {g}\tB: {b}\tC: {raw_c}"
            f"\tRG: {rg:.2f}\tBG: {bg:.2f}\tRB: {rb:.2f} \tBR: {br:.2f} \tGB: {gb:.2f} \tGR: {gr:.2f}"
            f"\trawR: {raw_r} \trawG: {raw_g} \trawB: {raw_b} \trawC: {raw_c}",
            end=""
        )

        if isRecyclable(r, g, b, raw_c):
            sort('Recycle')
            print("\t=> RECYCLABLE")
            if isGreenRGB(r, g, b, raw_c):
                print(" (GREEN)")
            if isBlueRGB(r, g, b, raw_c):
                print(" (BLUE)")

        elif isGarbage(r, g, b, raw_c):
            sort('Trash')
            print("\t=> GARBAGE")
            if isBlackRGB(r, g, b, raw_c):
                print(" (BLACK)")
            elif isGrayRGB(r, g, b, raw_c):
                print(" (GRAY)")
            elif isBrownRGB(r, g, b, raw_c):
                print(" (BROWN)")
        else:
            print("\t=> EMPTY / UNKNOWN")

except KeyboardInterrupt:
    print("\nStopp")
