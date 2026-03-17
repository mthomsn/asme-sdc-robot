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


def get_color_ratios(r, g, b, c):

    if c == 0:
        return "Unknown"

    r_ratio = r / c
    g_ratio = g / c
    b_ratio = b / c

    total = r + g + b + c
    c_ratio = c / total

    return r_ratio, g_ratio, b_ratio, c_ratio



def get_type(name):

    if name == "Green" or name == "Blue":
        return "Recycle"

    elif name == "Black" or name == "Gray" or name == "Brown":
        return "Trash"

    else:
        return "Unknown"


def isGreenRGB(r_ratio, g_ratio, b_ratio, c_ratio):
    return (g_ratio > r_ratio) and (g_ratio > b_ratio) and (g_ratio > 0.40)

def isBlueRGB(r_ratio, g_ratio, b_ratio, c_ratio):
    return (b_ratio > r_ratio) and (b_ratio > g_ratio) and (b_ratio > 0.30)

def isBlackRGB(r_ratio, g_ratio, b_ratio, c_ratio):
    return (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (c > 350)

def isGrayRGB(r_ratio, g_ratio, b_ratio, c_ratio):
    return (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (1000 <= c <= 3000)

def isBrownRGB(r_ratio, g_ratio, b_ratio, c_ratio):
    return (r_ratio < c_ratio) and (g_ratio < c_ratio) and (b_ratio < c_ratio) and (1600 <= c <= 2500)

def isRecyclable(r_ratio, g_ratio, b_ratio, c_ratio):
    return isGreenRGB(r_ratio, g_ratio, b_ratio, c_ratio) or isBlueRGB(r_ratio, g_ratio, b_ratio, c_ratio)

def isGarbage(r_ratio, g_ratio, b_ratio, c_ratio):
    return isBlackRGB(r_ratio, g_ratio, b_ratio, c_ratio) or isGrayRGB(r_ratio, g_ratio, b_ratio, c_ratio) or isBrownRGB(r_ratio, g_ratio, b_ratio, c_ratio)

init_sensor()


while True:

    r, g, b, c = get_rgb_values()

    if object_detected(c):

        ratios = get_color_ratios(r, g, b, c)
        r_ratio = ratios[0]
        g_ratio = ratios[1]
        b_ratio = ratios[2]
        c_ratio = ratios[3]

       #  print("R:", r, "G:", g, "B:", b, "C:", c)
            #   "Color:", color_name,
            #   "Type:", type_name)
        
        if isRecyclable(r_ratio, g_ratio, b_ratio, c_ratio):
            print("R:", r, "G:", g, "B:", b, "C:", c, "RRatio: ", r_ratio, "GRatio: ", g_ratio, "BRatio: ", b_ratio, "CRatio: ", c_ratio, "RECYCLABLE")
            if isGreenRGB(r_ratio, g_ratio, b_ratio, c_ratio):
                print(" (GREEN)")
            if isBlueRGB(r_ratio, g_ratio, b_ratio, c_ratio):
                print(" (BLUE)")

        elif isGarbage(r_ratio, g_ratio, b_ratio, c_ratio):
            print("R:", r, "G:", g, "B:", b, "C:", c, "RRatio: ", r_ratio, "GRatio: ", g_ratio, "BRatio: ", b_ratio, "CRatio: ", c_ratio, "GARBAGE")
            if isBlackRGB(r_ratio, g_ratio, b_ratio, c_ratio):
                print(" (BLACK)")
            elif isGrayRGB(r_ratio, g_ratio, b_ratio, c_ratio):
                print(" (GRAY)")
            elif isBrownRGB(r_ratio, g_ratio, b_ratio, c_ratio):
                print(" (BROWN)")
        

        else:
            print("R:", r, "G:", g, "B:", b, "C:", c, "RRatio: ", r_ratio, "GRatio: ", g_ratio, "BRatio: ", b_ratio, "CRatio: ", c_ratio, "UNKNOWN")

    else:
        print("No object")

    
    time.sleep(0.7)

