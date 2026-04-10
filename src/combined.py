import subprocess
import RPi.GPIO as GPIO
from time import sleep
import re
import math
import threading
import time
import smbus
import statistics

# =========================
# PIN SETUP
# =========================

# TT DRIVE MOTORS
NSLEEP1 = 12
NSLEEP2 = 13

# Front Left
TT_FRONT_LEFT_BACKWARD = 27
TT_FRONT_LEFT_FORWARD = 17

# Back Left
TT_BACK_LEFT_BACKWARD = 22
TT_BACK_LEFT_FORWARD = 23

# Back Right
TT_BACK_RIGHT_FORWARD = 25
TT_BACK_RIGHT_BACKWARD = 24

# Front Right
TT_FRONT_RIGHT_FORWARD = 26
TT_FRONT_RIGHT_BACKWARD = 16

tt_motor_pins = [
    TT_FRONT_LEFT_BACKWARD, TT_FRONT_LEFT_FORWARD,
    TT_BACK_LEFT_BACKWARD, TT_BACK_LEFT_FORWARD,
    TT_BACK_RIGHT_FORWARD, TT_BACK_RIGHT_BACKWARD,
    TT_FRONT_RIGHT_FORWARD, TT_FRONT_RIGHT_BACKWARD
]

# FLIPPER MOTOR
SORTING_MOTOR_RIGHT = 10
SORTING_MOTOR_LEFT = 9

# N20 MOTOR PINS
N20_IN1 = 5
N20_IN2 = 6

# TT LIFTING MOTOR
TT_LIFT_UP = 20
TT_LIFT_DOWN = 21

# TT WHEEL
WHEEL_FORWARD = 18
WHEEL_BACKWARD = 15

# =========================
# COLOR SENSOR SETUP
# =========================
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

# =========================
# GPIO SETUP
# =========================
GPIO.setmode(GPIO.BCM)

# TT MOTORS
GPIO.setup(NSLEEP1, GPIO.OUT)
GPIO.setup(NSLEEP2, GPIO.OUT)

for pin in tt_motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# N20 MOTOR
GPIO.setup(N20_IN1, GPIO.OUT)
GPIO.setup(N20_IN2, GPIO.OUT)
GPIO.output(N20_IN1, GPIO.LOW)
GPIO.output(N20_IN2, GPIO.LOW)

# SORTING MOTOR
GPIO.setup(SORTING_MOTOR_RIGHT, GPIO.OUT)
GPIO.setup(SORTING_MOTOR_LEFT, GPIO.OUT)
GPIO.output(SORTING_MOTOR_RIGHT, GPIO.LOW)
GPIO.output(SORTING_MOTOR_LEFT, GPIO.LOW)

# TT LIFTING
GPIO.setup(TT_LIFT_UP, GPIO.OUT)
GPIO.setup(TT_LIFT_DOWN, GPIO.OUT)
GPIO.output(TT_LIFT_UP, GPIO.LOW)
GPIO.output(TT_LIFT_DOWN, GPIO.LOW)

# TT WHEEL
GPIO.setup(WHEEL_FORWARD, GPIO.OUT)
GPIO.setup(WHEEL_BACKWARD, GPIO.OUT)
GPIO.output(WHEEL_FORWARD, GPIO.LOW)
GPIO.output(WHEEL_BACKWARD, GPIO.LOW)

# =========================
# PWM SETUP
# =========================
# TT MOTORS
tt_fl_b = GPIO.PWM(TT_FRONT_LEFT_BACKWARD, 1000)
tt_fl_f = GPIO.PWM(TT_FRONT_LEFT_FORWARD, 1000)

tt_bl_b = GPIO.PWM(TT_BACK_LEFT_BACKWARD, 1000)
tt_bl_f = GPIO.PWM(TT_BACK_LEFT_FORWARD, 1000)

tt_br_b = GPIO.PWM(TT_BACK_RIGHT_BACKWARD, 1000)
tt_br_f = GPIO.PWM(TT_BACK_RIGHT_FORWARD, 1000)

tt_fr_b = GPIO.PWM(TT_FRONT_RIGHT_BACKWARD, 1000)
tt_fr_f = GPIO.PWM(TT_FRONT_RIGHT_FORWARD, 1000)

p1 = GPIO.PWM(NSLEEP1, 1000)
p2 = GPIO.PWM(NSLEEP2, 1000)

p1.start(80)
p2.start(80)

for pwm in [tt_fl_f, tt_fl_b, tt_bl_f, tt_bl_b, tt_br_f, tt_br_b, tt_fr_f, tt_fr_b]:
    pwm.start(0)

# TT LIFTING
tt_lift_up_pwm = GPIO.PWM(TT_LIFT_UP, 1000)
tt_lift_down_pwm = GPIO.PWM(TT_LIFT_DOWN, 1000)

tt_lift_up_pwm.start(0)
tt_lift_down_pwm.start(0)

wheel_forward_pwm = GPIO.PWM(WHEEL_FORWARD, 1000)
wheel_backward_pwm = GPIO.PWM(WHEEL_BACKWARD, 1000)

wheel_forward_pwm.start(0)
wheel_backward_pwm.start(0)

wheel_speed = 60

# =========================
# LOCKS + GLOBAL STATE
# =========================
scale_max = 1.0
scale_min = -1.0
analog_max = 32767
analog_min = -32767

running = True

axis_lock = threading.Lock()
button_lock = threading.Lock()
sorting_lock = threading.Lock()
sensor_lock = threading.Lock()

AXIS_X = 0
AXIS_Y = 1
AXIS_LT = 4
AXIS_RT = 5

AXIS_RIGHT_Y = 2
AXIS_LEFT_Y = 3

BUTTON_LEFT = 6
BUTTON_RIGHT = 7

axis_state = {
    AXIS_X: 0,
    AXIS_Y: 0,
    AXIS_LT: -32767,
    AXIS_RT: -32767,
}

axis_state_lifter = {
    AXIS_RIGHT_Y: 0,
    AXIS_LEFT_Y: 0,
}

BUTTON_ARROW_X = 6
BUTTON_ARROW_Y = 7
SortTrash = False
SortAll = False

BUTTON_X = 3
BUTTON_A = 0
BUTTON_B = 1

button_left = 0
button_right = 0

# =========================
# UTILITY FUNCTIONS
# =========================
def convert_range(value):
    value = int(value)
    return (((value - analog_min) * (scale_max - scale_min)) / (analog_max - analog_min)) + scale_min

def convert_trigger(rt, lt):
    rt = int(rt) + analog_max
    lt = int(lt) + analog_max
    return ((rt - lt) * 100) / 65534

# =========================
# TT MOTOR CONTROL
# =========================
def stop_tt_motors():
    for pwm in [tt_fl_f, tt_bl_f, tt_br_f, tt_fr_f, tt_fl_b, tt_bl_b, tt_br_b, tt_fr_b]:
        pwm.ChangeDutyCycle(0)

def compute_tt_output():
    with axis_lock:
        x = convert_range(axis_state[AXIS_X])
        y = convert_range(axis_state[AXIS_Y])
        z = convert_trigger(axis_state[AXIS_RT], axis_state[AXIS_LT])

    deadzone = 0
    if abs(x) < deadzone:
        x = 0
    if abs(y) < deadzone:
        y = 0
    if abs(z) < 2:
        z = 0

    backward_v = [1, 1, 1, 1, 0, 0, 0, 0]
    forward_v = [0, 0, 0, 0, 1, 1, 1, 1]
    right_v = [1, 0, 1, 0, 0, 1, 0, 1]
    left_v = [0, 1, 0, 1, 1, 0, 1, 0]
    counter_v = [1, 1, 0, 0, 0, 0, 1, 1]
    clock_v = [0, 0, 1, 1, 1, 1, 0, 0]

    working_v = [0] * 8
    output_v = [0] * 8

    if x == 0 and y == 0 and z == 0:
        return output_v

    if y < 0:
        for i in range(8):
            forward_v[i] *= y
            backward_v[i] = 0
    elif y > 0:
        for i in range(8):
            backward_v[i] *= y
            forward_v[i] = 0
    else:
        for i in range(8):
            forward_v[i] = 0
            backward_v[i] = 0

    if x > 0:
        for i in range(8):
            right_v[i] *= x
            left_v[i] = 0
    elif x < 0:
        for i in range(8):
            left_v[i] *= x
            right_v[i] = 0
    else:
        for i in range(8):
            left_v[i] = 0
            right_v[i] = 0

    if z > 0:
        for i in range(8):
            clock_v[i] *= abs(z)
            counter_v[i] = 0
    elif z < 0:
        for i in range(8):
            counter_v[i] *= abs(z)
            clock_v[i] = 0
    else:
        for i in range(8):
            counter_v[i] = 0
            clock_v[i] = 0

    for i in range(8):
        working_v[i] = math.sqrt(
            abs(forward_v[i] ** 2) +
            abs(backward_v[i] ** 2) +
            abs(left_v[i] ** 2) +
            abs(right_v[i] ** 2)
        )

    for i in range(4):
        if working_v[i] > working_v[i + 4]:
            output_v[i] = working_v[i] - working_v[i + 4]
        else:
            output_v[i + 4] = working_v[i + 4] - working_v[i]

    for i in range(8):
        output_v[i] = ((100 - abs(z)) * output_v[i]) + clock_v[i] + counter_v[i]
        output_v[i] = min(max(output_v[i], 0), 100)

    return output_v

# =========================
# N20 CONTROL
# =========================
def n20_up(speed=80):
    GPIO.output(N20_IN1, GPIO.HIGH)
    GPIO.output(N20_IN2, GPIO.LOW)

def n20_down(speed=80):
    GPIO.output(N20_IN1, GPIO.LOW)
    GPIO.output(N20_IN2, GPIO.HIGH)

def stop_n20():
    GPIO.output(N20_IN1, GPIO.LOW)
    GPIO.output(N20_IN2, GPIO.LOW)

def drive_n20():
    while running:
        with button_lock:
            l = button_left
            r = button_right

        if l == 1 and r != 1:
            n20_up(80)
        elif r == 1 and l != 1:
            n20_down(80)
        else:
            stop_n20()

        sleep(0.03)

# =========================
# SORTING CONTROL
# =========================
def sorting_right():
    GPIO.output(SORTING_MOTOR_RIGHT, GPIO.HIGH)
    GPIO.output(SORTING_MOTOR_LEFT, GPIO.LOW)

def sorting_left():
    GPIO.output(SORTING_MOTOR_RIGHT, GPIO.LOW)
    GPIO.output(SORTING_MOTOR_LEFT, GPIO.HIGH)

def stop_sorting_motor():
    GPIO.output(SORTING_MOTOR_RIGHT, GPIO.LOW)
    GPIO.output(SORTING_MOTOR_LEFT, GPIO.LOW)

def sort_item(item):
    with sorting_lock:
        if SortAll:
            item = "All"

        def go_right():
            sorting_left() if SortTrash else sorting_right()
        def go_left():
            sorting_right() if SortTrash else sorting_left()

        if item == "Trash":
            go_right()
            time.sleep(0.05)

        elif item == "Recycle":
            go_left()
            time.sleep(0.05)
          
        elif item == "All":
            sorting_right()
            time.sleep(0.05)

        elif item == "Flap":
            sorting_right()
            time.sleep(0.03)

        stop_sorting_motor()

# =========================
# TT WHEEL CONTROL
# =========================
def set_wheel_speed(speed):
    global wheel_speed
    wheel_speed = max(0, min(100, speed))
    print(f"Wheel speed set to {wheel_speed}")

def wheel_spin_forward(speed=None):
    if speed is None:
        speed = wheel_speed
    speed = max(0, min(100, speed))
    wheel_backward_pwm.ChangeDutyCycle(0)
    wheel_forward_pwm.ChangeDutyCycle(speed)

def wheel_spin_backward(speed=None):
    if speed is None:
        speed = wheel_speed
    speed = max(0, min(100, speed))
    wheel_forward_pwm.ChangeDutyCycle(0)
    wheel_backward_pwm.ChangeDutyCycle(speed)

def stop_wheel():
    wheel_forward_pwm.ChangeDutyCycle(0)
    wheel_backward_pwm.ChangeDutyCycle(0)

# =========================
# COLOR SENSOR FUNCTIONS
# =========================
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
    write_register(ATIME, 0xD5)
    write_register(CONTROL, 0x01)
    write_register(ENABLE, PON | AEN)
    time.sleep(0.2)

def wait_for_data():
    while running:
        status = read_byte(STATUS)
        if status & AVALID:
            break
        time.sleep(0.005)

def get_raw_data():
    with sensor_lock:
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
           (110 <= g <= 155) and \
           (35 <= b <= 85) and \
           (c >= 400) and \
           (rg >= 0.30 and rg <= 0.90) and \
           (bg >= 0.30 and bg <= 0.85) and \
           (gr >= 1.0)

def isBlueRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (25 <= r <= 65) and \
           (70 <= g <= 100) and \
           (78 <= b <= 170) and \
           (c >= 500) and \
           (br >= 1.5) and \
           (rb >= 0.20 and rb <= 0.70) and \
           (gb >= 0.45 and gb <= 1.25)

def isBlackRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (58 <= r <= 110) and \
           (78 <= g <= 105) and \
           (55 <= b <= 95) and \
           (700 <= c <= 1900) and \
           (0.55 <= rg <= 1.30) and \
           (0.65 <= rb <= 1.85) 

def isGrayRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (64 <= r <= 105) and \
           (86 <= g <= 105) and \
           (40 <= b <= 75) and \
           (600 <= c) and \
           (0.70 <= rg <= 1.15) and \
           (0.85 <= rb <= 2.45)

def isBrownRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (85 <= r <= 120) and \
           (70 <= g <= 100) and \
           (42 <= b <= 68) and \
           (650 <= c) and \
           (0.90 <= rg <= 1.45) and \
           (1.30 <= rb <= 2.40)

def isRecyclable(r, g, b, c):
    return isGreenRGB(r, g, b, c) or isBlueRGB(r, g, b, c)

def isGarbage(r, g, b, c):
    return isBlackRGB(r, g, b, c) or isGrayRGB(r, g, b, c) or isBrownRGB(r, g, b, c)

def isFlap(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

    return (145 <= r <= 170) and \
           (50 <= g <= 60) and \
           (30 <= b <= 40) and \
           (500 <= c) and \
           (2.60 <= rg <= 3.50) and \
           (3.00 <= rb <= 6.00)

# =========================
# THREADS
# =========================
def drive_tt():
    while running:
        out = compute_tt_output()

        tt_fl_f.ChangeDutyCycle(out[0])
        tt_bl_f.ChangeDutyCycle(out[1])
        tt_br_f.ChangeDutyCycle(out[2])
        tt_fr_f.ChangeDutyCycle(out[3])

        tt_fl_b.ChangeDutyCycle(out[4])
        tt_bl_b.ChangeDutyCycle(out[5])
        tt_br_b.ChangeDutyCycle(out[6])
        tt_fr_b.ChangeDutyCycle(out[7])

        time.sleep(0.005)

def drive_lift_motor():
    deadzone = 0

    while running:
        with axis_lock:
            y = convert_range(axis_state_lifter[AXIS_LEFT_Y])

        if abs(y) < deadzone:
            tt_lift_up_pwm.ChangeDutyCycle(0)
            tt_lift_down_pwm.ChangeDutyCycle(0)
            time.sleep(0.01)
            continue

        speed = min(abs(y) * 100, 100)

        if y < 0:
            tt_lift_up_pwm.ChangeDutyCycle(speed)
            tt_lift_down_pwm.ChangeDutyCycle(0)
        else:
            tt_lift_up_pwm.ChangeDutyCycle(0)
            tt_lift_down_pwm.ChangeDutyCycle(speed)

        time.sleep(0.01)

def run_color_sensor_and_sorter():
    while running:
        try:
            raw_r, raw_g, raw_b, raw_c = get_averaged_data(samples=7, delay=0.01)

            if raw_c < 250:
                print(f"R: 0\tG: 0\tB: 0\tC: {raw_c}\t=> EMPTY / TOO DARK")
                time.sleep(0.02)
                continue

            r, g, b = raw_to_rgb_bytes(raw_r, raw_g, raw_b, raw_c)
            rg, bg, rb, br, gb, gr = get_ratios(r, g, b)

            print(
                f"R: {r}\tG: {g}\tB: {b}\tC: {raw_c}"
                f"\tRG: {rg:.2f}\tBG: {bg:.2f}\tRB: {rb:.2f}\tBR: {br:.2f}\tGB: {gb:.2f}\tGR: {gr:.2f}"
                f"\trawR: {raw_r}\trawG: {raw_g}\trawB: {raw_b}\trawC: {raw_c}",
                end=""
            )

            if isRecyclable(r, g, b, raw_c):
                sort_item("Recycle")
                print("\t=> RECYCLABLE")
                if isGreenRGB(r, g, b, raw_c):
                    print("\t GREEN")
                elif isBlueRGB(r, g, b, raw_c):
                    print("\t BLUE")
            elif isGarbage(r, g, b, raw_c):
                sort_item("Trash")
                print("\t=> GARBAGE")
                if isBlackRGB(r, g, b, raw_c):
                    print("\t BLACK")
                elif isGrayRGB(r, g, b, raw_c):
                    print("\t GRAY")
                elif isBrownRGB(r, g, b, raw_c):
                    print("\t BROWN")
            elif isFlap(r, g, b, raw_c):
                sort_item("Flap")
                print("\t=> RED FLAP")
            else:
                print("\t=> EMPTY / UNKNOWN")

            time.sleep(0.02)

        except Exception as e:
            print(f"Sensor/sorter error: {e}")
            time.sleep(0.05)

# =========================
# STARTUP
# =========================

init_sensor()
threading.Thread(target=drive_tt, daemon=True).start()
threading.Thread(target=drive_lift_motor, daemon=True).start()
threading.Thread(target=run_color_sensor_and_sorter, daemon=True).start()
threading.Thread(target=drive_n20, daemon=True).start()

# =========================
# CONTROLLER INPUT
# =========================
process = subprocess.Popen(
    "jstest --event /dev/input/js0",
    stdout=subprocess.PIPE,
    shell=True,
    text=True
)

try:
    while True:
        line = process.stdout.readline()
        if not line:
            break

        match = re.search(r"type\s+(\d+),.*number\s+(\d+),\s+value\s+(-?\d+)", line)
        print(match)
        if not match:
            continue

        t = int(match.group(1))
        n = int(match.group(2))
        v = int(match.group(3))

        if t == 2:
            with axis_lock:
                if n in axis_state:
                    axis_state[n] = v
                if n in axis_state_lifter:
                    axis_state_lifter[n] = v

            if n == BUTTON_ARROW_X and v == 32767:
                SortTrash = True
                SortAll = False
                print("Sort mode: Trash flipped")

            elif n == BUTTON_ARROW_Y:
                if v == 32767:
                    SortAll = True
                    SortTrash = False
                    print("Sort mode: All")
                elif v == -32767:
                    SortTrash = False
                    SortAll = False
                    print("Sort mode: Normal")

        elif t == 1:
            with button_lock:
                if n == BUTTON_LEFT:
                    button_left = v
                elif n == BUTTON_RIGHT:
                    button_right = v

            if v == 1:
                if n == BUTTON_X:
                    wheel_spin_forward()
                    print("Wheel spinning forward")

                elif n == BUTTON_A:
                    stop_wheel()
                    print("Wheel stopped")

                elif n == BUTTON_B:
                    wheel_spin_backward()
                    print("Wheel spinning backward")

finally:
    running = False
    sleep(0.05)

    stop_tt_motors()
    stop_sorting_motor()
    stop_n20()
    tt_lift_up_pwm.ChangeDutyCycle(0)
    tt_lift_down_pwm.ChangeDutyCycle(0)
    tt_lift_up_pwm.stop()
    tt_lift_down_pwm.stop()

    for pwm in [tt_fl_f, tt_fl_b, tt_bl_f, tt_bl_b, tt_br_f, tt_br_b, tt_fr_f, tt_fr_b, p1, p2]:
        try:
            pwm.stop()
        except:
            pass

    try:
        process.terminate()
    except:
        pass


    GPIO.cleanup()
