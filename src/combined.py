import subprocess
import RPi.GPIO as GPIO
from time import sleep
import re
import math
import threading

# =========================
# TT DRIVE MOTORS
# =========================
NSLEEP1 = 12
NSLEEP2 = 13

# Front Left
tt_front_left_backward = 27
tt_front_left_forward  = 17

# Back Left
tt_back_left_backward  = 22
tt_back_left_forward   = 23

# Back Right
tt_back_right_forward  = 25
tt_back_right_backward = 24

# Front Right
tt_front_right_forward  = 26
tt_front_right_backward = 16

GPIO.setmode(GPIO.BCM)

# =========================
# GPIO SETUP
# =========================
GPIO.setup(NSLEEP1, GPIO.OUT)
GPIO.setup(NSLEEP2, GPIO.OUT)

tt_motor_pins = [
    tt_front_left_backward, tt_front_left_forward,
    tt_back_left_backward, tt_back_left_forward,
    tt_back_right_forward, tt_back_right_backward,
    tt_front_right_forward, tt_front_right_backward
]

for pin in tt_motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# =========================
# PWM SETUP (TT MOTORS)
# =========================
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

# =========================
# STEPPER MOTOR
# =========================
stepper_pins = [5, 6, 4, 19]

for pin in stepper_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

fullsteps = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]

current_step = 0

# =========================
# SERVO MOTOR
# =========================
servo_pin = 18
GPIO.setup(servo_pin, GPIO.OUT)

servo = GPIO.PWM(servo_pin, 50)
servo.start(0)

# =========================
# GLOBAL STATE
# =========================
scale_max = 1.0
scale_min = -1.0
analog_max = 32767
analog_min = -32767

running = True

axis_lock = threading.Lock()
button_lock = threading.Lock()
angle_lock = threading.Lock()

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

axis_state_stepper = {
    AXIS_RIGHT_Y: 0,
    AXIS_LEFT_Y: 0,
}

button_left = 0
button_right = 0
servo_angle = 0

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
    if abs(x) < deadzone: x = 0
    if abs(y) < deadzone: y = 0
    if abs(z) < 2: z = 0

    forward_v  = [1,1,1,1,0,0,0,0]
    backward_v = [0,0,0,0,1,1,1,1]
    right_v    = [1,0,1,0,0,1,0,1]
    left_v     = [0,1,0,1,1,0,1,0]
    clock_v    = [1,1,0,0,0,0,1,1]
    counter_v  = [0,0,1,1,1,1,0,0]

    working_v = [0]*8
    output_v  = [0]*8

    if x == 0 and y == 0 and z == 0:
        return output_v

    # SAME VECTOR LOGIC (UNCHANGED)
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
            forward_v[i] = backward_v[i] = 0

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
            left_v[i] = right_v[i] = 0

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
            counter_v[i] = clock_v[i] = 0

    for i in range(8):
        working_v[i] = math.sqrt(
            abs(forward_v[i]**2) +
            abs(backward_v[i]**2) +
            abs(left_v[i]**2) +
            abs(right_v[i]**2)
        )

    for i in range(4):
        if working_v[i] > working_v[i+4]:
            output_v[i] = working_v[i] - working_v[i+4]
        else:
            output_v[i+4] = working_v[i+4] - working_v[i]

    for i in range(8):
        output_v[i] = ((100 - abs(z)) * output_v[i]) + clock_v[i] + counter_v[i]
        output_v[i] = min(max(output_v[i], 0), 100)

    return output_v


# =========================
# STEPPER CONTROL
# =========================
def stop_stepper():
    for pin in stepper_pins:
        GPIO.output(pin, GPIO.LOW)


def set_step(index):
    for i in range(4):
        GPIO.output(stepper_pins[i], fullsteps[index][i])


def step_clockwise():
    global current_step
    set_step(current_step)
    current_step = (current_step + 1) % len(fullsteps)


def step_counterclockwise():
    global current_step
    set_step(current_step)
    current_step = (current_step - 1) % len(fullsteps)


def get_step_delay(y_r, y_l):
    speed = min(abs(y_r) + abs(y_l), 1)
    return 0.002 - (speed * (0.002 - 0.0005))


# =========================
# SERVO CONTROL
# =========================
def set_servo_angle(angle):
    duty = 2.5 + (angle / 18.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.02)
    servo.ChangeDutyCycle(0)


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


def drive_stepper():
    deadzone = 0.1
    while running:
        with axis_lock:
            y_r = convert_range(axis_state_stepper[AXIS_RIGHT_Y])
            y_l = convert_range(axis_state_stepper[AXIS_LEFT_Y])

        if abs(y_r) < deadzone and abs(y_l) < deadzone:
            stop_stepper()
            sleep(0.01)
            continue

        delay = get_step_delay(y_r, y_l)

        if y_l < -deadzone:
            step_clockwise()
        elif y_l > deadzone:
            step_counterclockwise()

        sleep(delay)


def drive_servo():
    global servo_angle
    while running:
        with button_lock:
            l = button_left
            r = button_right

        if l == 1 and r != 1:
            servo_angle -= 20
        elif r == 1 and l != 1:
            servo_angle += 20

        servo_angle = max(0, min(180, servo_angle))
        set_servo_angle(servo_angle)
        sleep(0.03)


# =========================
# START THREADS
# =========================
threading.Thread(target=drive_tt, daemon=True).start()
threading.Thread(target=drive_stepper, daemon=True).start()
threading.Thread(target=drive_servo, daemon=True).start()

set_servo_angle(servo_angle)

# =========================
# CONTROLLER INPUT
# =========================
process = subprocess.Popen("jstest --event /dev/input/js0", stdout=subprocess.PIPE, shell=True, text=True)

try:
    while True:
        line = process.stdout.readline()
        if not line:
            break

        match = re.search(r"type\s+(\d+),.*number\s+(\d+),\s+value\s+(-?\d+)", line)
        if not match:
            continue

        t, n, v = int(match.group(1)), int(match.group(2)), int(match.group(3))

        if t == 2:
            with axis_lock:
                if n in axis_state:
                    axis_state[n] = v
                if n in axis_state_stepper:
                    axis_state_stepper[n] = v

        elif t == 1:
            with button_lock:
                if n == BUTTON_LEFT:
                    button_left = v
                elif n == BUTTON_RIGHT:
                    button_right = v

finally:
    running = False
    sleep(0.05)

    stop_tt_motors()
    stop_stepper()
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