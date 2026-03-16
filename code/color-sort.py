import smbus
import time
import RPi.GPIO as GPIO

# motor control pins
IN1 = 17
IN2 = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

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

PRESENCE_THRESHOLD = 150


def write_register(reg, value):
    bus.write_byte_data(TCS_ADDR, COMMAND | reg, value)

def read_word(reg):
    low = bus.read_byte_data(TCS_ADDR, COMMAND | reg)
    high = bus.read_byte_data(TCS_ADDR, COMMAND | reg + 1)
    return (high << 8) | low


def init_sensor():
    write_register(ENABLE, PON)
    time.sleep(0.01)
    write_register(ENABLE, PON | AEN)

    write_register(ATIME, 0xEB)  # ~50ms integration
    write_register(CONTROL, 0x01)  # 4x gain


def get_rgb_values():
    c = read_word(CDATAL)
    r = read_word(RDATAL)
    g = read_word(GDATAL)
    b = read_word(BDATAL)

    return r, g, b, c


def object_detected(c):
    return c > PRESENCE_THRESHOLD


def get_color_name(r, g, b, c):

    if c == 0:
        return "Unknown"

    r_ratio = r / c
    g_ratio = g / c
    b_ratio = b / c

    total = r + g + b + c
    c_ratio = c / total

    if (g_ratio > r_ratio) and (g_ratio > b_ratio) and (g_ratio > 0.40):
        return "Green"

    elif (b_ratio > r_ratio) and (b_ratio > g_ratio) and (b_ratio > 0.40):
        return "Blue"

    elif (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (1600 <= c <= 2500):
        return "Brown"

    elif (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (1000 <= c <= 3000):
        return "Gray"

    elif (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (c > 650):
        return "Black"

    else:
        return "Unknown"


def get_type(name):

    if name == "Green" or name == "Blue":
        return "Recycle"

    elif name == "Black" or name == "Gray" or name == "Brown":
        return "Trash"

    else:
        return "Unknown"

# motor control
def right():
    print('right')
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)

def left():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print('left')

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)

def sort(item):
    print(item)
    if item == 'Trash':
        right()
        time.sleep(0.1)
        left()
        time.sleep(0.05)
    if item == 'Recycle':
        left()
        time.sleep(0.1)
        right()
        time.sleep(0.05)
    stop()

init_sensor()

while True:

    r, g, b, c = get_rgb_values()

    if object_detected(c):

        color_name = get_color_name(r, g, b, c)
        type_name = get_type(color_name)

        print("R:", r, "G:", g, "B:", b, "C:", c,
              "Color:", color_name,
              "Type:", type_name)
        sort(type_name)

    else:
        print("No object detected")

    time.sleep(0.5)

