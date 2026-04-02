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
tt_front_left_backward = 27
tt_front_left_forward = 17

# Back Left
tt_back_left_backward = 22
tt_back_left_forward = 23

# Back Right
tt_back_right_forward = 25
tt_back_right_backward = 24

# Front Right
tt_front_right_forward = 26
tt_front_right_backward = 16

tt_motor_pins = [
    tt_front_left_backward, tt_front_left_forward,
    tt_back_left_backward, tt_back_left_forward,
    tt_back_right_forward, tt_back_right_backward,
    tt_front_right_forward, tt_front_right_backward
]

# TT Lifting
# tt_lift_up = 0
# tt_lift_down = 0
# tt_lifting_motor_pins = [tt_lift_up, tt_lift_down]

# SERVO MOTOR PIN
servo_pin = 18

# SORTING MOTOR
sorting_motor_right = 10
sorting_motor_left = 9

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

# TT LIFTING
# for pin in tt_lifting_motor_pins:
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.LOW)

# SERVO MOTOR
GPIO.setup(servo_pin, GPIO.OUT)

# SORTING MOTOR
GPIO.setup(sorting_motor_right, GPIO.OUT)
GPIO.setup(sorting_motor_left, GPIO.OUT)
GPIO.output(sorting_motor_right, GPIO.LOW)
GPIO.output(sorting_motor_left, GPIO.LOW)

# =========================
# PWM SETUP
# =========================
# TT MOTORS
tt_fl_b = GPIO.PWM(tt_front_left_backward, 1000)
tt_fl_f = GPIO.PWM(tt_front_left_forward, 1000)

tt_bl_b = GPIO.PWM(tt_back_left_backward, 1000)
tt_bl_f = GPIO.PWM(tt_back_left_forward, 1000)

tt_br_b = GPIO.PWM(tt_back_right_backward, 1000)
tt_br_f = GPIO.PWM(tt_back_right_forward, 1000)

tt_fr_b = GPIO.PWM(tt_front_right_backward, 1000)
tt_fr_f = GPIO.PWM(tt_front_right_forward, 1000)

p1 = GPIO.PWM(NSLEEP1, 1000)
p2 = GPIO.PWM(NSLEEP2, 1000)

p1.start(80)
p2.start(80)

for pwm in [tt_fl_f, tt_fl_b, tt_bl_f, tt_bl_b, tt_br_f, tt_br_b, tt_fr_f, tt_fr_b]:
    pwm.start(0)

# TT LIFTING
# tt_lift_up_pwm = GPIO.PWM(tt_lift_up, 1000)
# tt_lift_down_pwm = GPIO.PWM(tt_lift_down, 1000)
# tt_lift_up_pwm.start(0)
# tt_lift_down_pwm.start(0)

# SERVO MOTOR
servo = GPIO.PWM(servo_pin, 50)
servo.start(0)

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
angle_lock = threading.Lock()
sorting_lock = threading.Lock()
sensor_lock = threading.Lock()

AXIS_X = 0
AXIS_Y = 1
AXIS_LT = 4
AXIS_RT = 5

toggleGrab = False

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

button_left = 0
button_right = 0
servo_angle = 0

# =========================
# SORTING MOTOR FUNCTIONS
# =========================
def sorting_right():
    GPIO.output(sorting_motor_right, GPIO.HIGH)
    GPIO.output(sorting_motor_left, GPIO.LOW)

def sorting_left():
    GPIO.output(sorting_motor_right, GPIO.LOW)
    GPIO.output(sorting_motor_left, GPIO.HIGH)

def stop_sorting_motor():
    GPIO.output(sorting_motor_right, GPIO.LOW)
    GPIO.output(sorting_motor_left, GPIO.LOW)

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

    deadzone = 0.08
    if abs(x) < deadzone:
        x = 0
    if abs(y) < deadzone:
        y = 0
    if abs(z) < 2:
        z = 0

    forward_v = [1, 1, 1, 1, 0, 0, 0, 0]
    backward_v = [0, 0, 0, 0, 1, 1, 1, 1]
    right_v = [1, 0, 1, 0, 0, 1, 0, 1]
    left_v = [0, 1, 0, 1, 1, 0, 1, 0]
    clock_v = [1, 1, 0, 0, 0, 0, 1, 1]
    counter_v = [0, 0, 1, 1, 1, 1, 0, 0]

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
# SERVO CONTROL
# =========================
def set_servo_angle(angle):
    duty = 2.5 + (angle / 18.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.02)
    servo.ChangeDutyCycle(0)

# =========================
# SORTING CONTROL
# =========================
def sort_item(item):
    with sorting_lock:
        if item == "Trash":
            sorting_right()
            time.sleep(0.05)
        elif item == "Recycle":
            sorting_left()
            time.sleep(0.05)
        elif item == "Flap":
            sorting_right()
            time.sleep(0.03)

        stop_sorting_motor()

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
    return (
        (42 <= r <= 105) and
        (105 <= g <= 155) and
        (45 <= b <= 85) and
        (c >= 400) and
        (0.30 <= rg <= 0.90) and
        (0.30 <= bg <= 0.85) and
        (gr >= 1.0)
    )

def isBlueRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)
    return (
        (25 <= r <= 65) and
        (70 <= g <= 100) and
        (90 <= b <= 170) and
        (c >= 500) and
        (br >= 1.5) and
        (0.20 <= rb <= 0.70) and
        (0.45 <= gb <= 1.00)
    )

def isBlackRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)
    return (
        (58 <= r <= 110) and
        (80 <= g <= 105) and
        (55 <= b <= 95) and
        (200 <= c <= 1900) and
        (0.55 <= rg <= 1.30) and
        (0.60 <= rb <= 1.85)
    )

def isGrayRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)
    return (
        (70 <= r <= 105) and
        (90 <= g <= 105) and
        (67 <= b <= 75) and
        (c >= 900) and
        (0.70 <= rg <= 1.15) and
        (0.85 <= rb <= 1.45)
    )

def isBrownRGB(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)
    return (
        (85 <= r <= 120) and
        (85 <= g <= 105) and
        (50 <= b <= 68) and
        (c >= 500) and
        (0.90 <= rg <= 1.35) and
        (1.30 <= rb <= 2.30)
    )

def isRecyclable(r, g, b, c):
    return isGreenRGB(r, g, b, c) or isBlueRGB(r, g, b, c)

def isGarbage(r, g, b, c):
    return isBlackRGB(r, g, b, c) or isGrayRGB(r, g, b, c) or isBrownRGB(r, g, b, c)

def isFlap(r, g, b, c):
    rg, bg, rb, br, gb, gr = get_ratios(r, g, b)
    return (
        (145 <= r <= 170) and
        (50 <= g <= 60) and
        (30 <= b <= 40) and
        (c >= 500) and
        (2.60 <= rg <= 3.50) and
        (3.00 <= rb <= 6.00)
    )

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

# def drive_lift_motor():
#     deadzone = 0.1
#     while running:
#         with axis_lock:
#             y = convert_range(axis_state_lifter[AXIS_LEFT_Y])

#         if abs(y) < deadzone:
#             tt_lift_up.ChangeDutyCycle(0)
#             tt_lift_down.ChangeDutyCycle(0)
#             time.sleep(0.01)
#             continue

#         speed = abs(y) * 100

#         if y < 0:
#             # lift up
#             tt_lift_up.ChangeDutyCycle(speed)
#             tt_lift_down.ChangeDutyCycle(0)
#         else:
#             # lift down
#             tt_lift_up.ChangeDutyCycle(0)
#             tt_lift_down.ChangeDutyCycle(speed)

#         time.sleep(0.01)

def drive_servo():
    global servo_angle
    last_angle = servo_angle
    print("moving servo")
    while running:
        with button_lock:
            l = button_left
            r = button_right

        if l == 1 and r != 1:
            servo_angle -= 5
        elif r == 1 and l != 1:
            servo_angle += 5

        servo_angle = max(0, min(180, servo_angle))

        if servo_angle != last_angle:
            set_servo_angle(servo_angle)
            last_angle = servo_angle

        sleep(0.03)

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
            elif isGarbage(r, g, b, raw_c):
                sort_item("Trash")
                print("\t=> GARBAGE")
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
set_servo_angle(servo_angle)

threading.Thread(target=drive_tt, daemon=True).start()
threading.Thread(target=drive_lift_motor, daemon=True).start()
threading.Thread(target=drive_servo, daemon=True).start()
threading.Thread(target=run_color_sensor_and_sorter, daemon=True).start()

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

        if t == 1 and n == 10 and v == 1:
            #print(t, n)
            if toggleGrab is True:
                toggleGrab = False
                #print(toggleGrab)
            elif toggleGrab is False:
                toggleGrab = True
                #print(toggleGrab)

        if t == 2:
            with axis_lock:
                if n in axis_state:
                    axis_state[n] = v
                # if n in axis_state_lifter and toggleGrab is True:
                #     axis_state_lifter[n] = v

        elif t == 1 and toggleGrab is True:
            with button_lock:
                if n == BUTTON_LEFT:
                    button_left = v
                elif n == BUTTON_RIGHT:
                    button_right = v

finally:
    running = False
    sleep(0.05)

    stop_tt_motors()
    # tt_lift_up.ChangeDutyCycle(0)
    # tt_lift_down.ChangeDutyCycle(0)
    # tt_lift_up.stop()
    # tt_lift_down.stop()
    stop_sorting_motor()
    servo.stop()

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
