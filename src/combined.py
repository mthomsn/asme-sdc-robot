import subprocess
import RPi.GPIO as GPIO
from time import sleep
import re
import math
import threading

NSLEEP1 = 12
motor_1_backward = 27
motor_1_forward = 17
motor_2_backward = 22
motor_2_forward = 23

NSLEEP2 = 13
motor_3_forward = 25
motor_3_backward = 24
motor_4_forward = 26
motor_4_backward = 16

controls = [5, 6, 4, 19]

GPIO.setmode(GPIO.BCM)

GPIO.setup(NSLEEP1, GPIO.OUT)
GPIO.setup(NSLEEP2, GPIO.OUT)
GPIO.setup(motor_1_backward, GPIO.OUT)
GPIO.setup(motor_1_forward, GPIO.OUT)
GPIO.setup(motor_2_backward, GPIO.OUT)
GPIO.setup(motor_2_forward, GPIO.OUT)
GPIO.setup(motor_3_forward, GPIO.OUT)
GPIO.setup(motor_3_backward, GPIO.OUT)
GPIO.setup(motor_4_forward, GPIO.OUT)
GPIO.setup(motor_4_backward, GPIO.OUT)

GPIO.output(motor_1_backward, GPIO.LOW)
GPIO.output(motor_1_forward, GPIO.LOW)
GPIO.output(motor_2_backward, GPIO.LOW)
GPIO.output(motor_2_forward, GPIO.LOW)
GPIO.output(motor_3_forward, GPIO.LOW)
GPIO.output(motor_3_backward, GPIO.LOW)
GPIO.output(motor_4_forward, GPIO.LOW)
GPIO.output(motor_4_backward, GPIO.LOW)

m1b = GPIO.PWM(motor_1_backward, 1000)
m1f = GPIO.PWM(motor_1_forward, 1000)
m2b = GPIO.PWM(motor_2_backward, 1000)
m2f = GPIO.PWM(motor_2_forward, 1000)
m3b = GPIO.PWM(motor_3_backward, 1000)
m3f = GPIO.PWM(motor_3_forward, 1000)
m4b = GPIO.PWM(motor_4_backward, 1000)
m4f = GPIO.PWM(motor_4_forward, 1000)

p1 = GPIO.PWM(NSLEEP1, 1000)
p2 = GPIO.PWM(NSLEEP2, 1000)
p1.start(80)
p2.start(80)

m1f.start(0)
m1b.start(0)
m2f.start(0)
m2b.start(0)
m3f.start(0)
m3b.start(0)
m4f.start(0)
m4b.start(0)

for pin in controls:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

SERVO_PIN = 18
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

fullsteps = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]

current_step = 0

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

axis_state = {
    AXIS_X: 0,
    AXIS_Y: 0,
    AXIS_LT: -32767,
    AXIS_RT: -32767
}

AXIS_RIGHT_Y = 2
AXIS_LEFT_Y = 3

BUTTON_LEFT = 6
BUTTON_RIGHT = 7

axis_state_stepper = {
    AXIS_RIGHT_Y: 0,
    AXIS_LEFT_Y: 0
}

button6 = 0
button7 = 0
angle = 0

def convert_range(value):
    value = int(value)
    old_range = analog_max - analog_min
    new_range = scale_max - scale_min
    return (((value - analog_min) * new_range) / old_range) + scale_min

def convert_trigger(rightIn, leftIn):
    rightIn = int(rightIn) + analog_max
    leftIn = int(leftIn) + analog_max
    output_trigger = rightIn - leftIn
    return (output_trigger * 100) / 65534

def stop_motors():
    m1f.ChangeDutyCycle(0)
    m2f.ChangeDutyCycle(0)
    m3f.ChangeDutyCycle(0)
    m4f.ChangeDutyCycle(0)
    m1b.ChangeDutyCycle(0)
    m2b.ChangeDutyCycle(0)
    m3b.ChangeDutyCycle(0)
    m4b.ChangeDutyCycle(0)

def stop_stepper():
    for pin in controls:
        GPIO.output(pin, GPIO.LOW)

def set_step(step_index):
    for i in range(4):
        GPIO.output(controls[i], fullsteps[step_index][i])

def step_clockwise():
    global current_step
    set_step(current_step)
    current_step = (current_step + 1) % len(fullsteps)

def step_counterclockwise():
    global current_step
    set_step(current_step)
    current_step = (current_step - 1) % len(fullsteps)

def get_step_delay(yAxis, yAxisL):
    speed = abs(yAxis) + abs(yAxisL)
    if speed > 1:
        speed = 1
    step_delay_max = 0.002
    step_delay_min = 0.0005
    return step_delay_max - (speed * (step_delay_max - step_delay_min))

def set_angle(angle):
    duty = 2.5 + (angle / 18.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.02)
    servo.ChangeDutyCycle(0)

def compute_motor_output():
    with axis_lock:
        xAxis_raw = axis_state[AXIS_X]
        yAxis_raw = axis_state[AXIS_Y]
        leftRead = axis_state[AXIS_LT]
        rightRead = axis_state[AXIS_RT]

    xAxis = convert_range(xAxis_raw)
    yAxis = convert_range(yAxis_raw)
    zAxis = convert_trigger(rightRead, leftRead)

    deadzone = 0.08
    if abs(xAxis) < deadzone:
        xAxis = 0
    if abs(yAxis) < deadzone:
        yAxis = 0
    if abs(zAxis) < 2:
        zAxis = 0

    forward_v = [1, 1, 1, 1, 0, 0, 0, 0]
    backward_v = [0, 0, 0, 0, 1, 1, 1, 1]
    right_v = [1, 0, 1, 0, 0, 1, 0, 1]
    left_v = [0, 1, 0, 1, 1, 0, 1, 0]
    clock_v = [1, 1, 0, 0, 0, 0, 1, 1]
    counter_v = [0, 0, 1, 1, 1, 1, 0, 0]

    working_v = [0] * 8
    output_v = [0] * 8

    if xAxis == 0 and yAxis == 0 and zAxis == 0:
        return output_v

    if yAxis < 0:
        for i in range(8):
            forward_v[i] = yAxis * forward_v[i]
            backward_v[i] = 0
    elif yAxis > 0:
        for i in range(8):
            backward_v[i] = yAxis * backward_v[i]
            forward_v[i] = 0
    else:
        for i in range(8):
            backward_v[i] = 0
            forward_v[i] = 0

    if xAxis > 0:
        for i in range(8):
            right_v[i] = xAxis * right_v[i]
            left_v[i] = 0
    elif xAxis < 0:
        for i in range(8):
            left_v[i] = xAxis * left_v[i]
            right_v[i] = 0
    else:
        for i in range(8):
            left_v[i] = 0
            right_v[i] = 0

    if zAxis > 0:
        for i in range(8):
            clock_v[i] = abs(zAxis) * clock_v[i]
            counter_v[i] = 0
    elif zAxis < 0:
        for i in range(8):
            counter_v[i] = abs(zAxis) * counter_v[i]
            clock_v[i] = 0
    else:
        for i in range(8):
            counter_v[i] = 0
            clock_v[i] = 0

    for i in range(8):
        forward_v[i] = forward_v[i] * forward_v[i]
        backward_v[i] = backward_v[i] * backward_v[i]
        right_v[i] = right_v[i] * right_v[i]
        left_v[i] = left_v[i] * left_v[i]
        working_v[i] = math.sqrt(
            abs(forward_v[i]) +
            abs(backward_v[i]) +
            abs(left_v[i]) +
            abs(right_v[i])
        )

    for i in range(4):
        if working_v[i] > working_v[i + 4]:
            output_v[i] = working_v[i] - working_v[i + 4]
            output_v[i + 4] = 0
        else:
            output_v[i + 4] = working_v[i + 4] - working_v[i]
            output_v[i] = 0

    for i in range(8):
        output_v[i] = ((100 - abs(zAxis)) * output_v[i]) + clock_v[i] + counter_v[i]

    for i in range(4):
        if output_v[i] > output_v[i + 4]:
            output_v[i] = output_v[i] - output_v[i + 4]
            output_v[i + 4] = 0
        else:
            output_v[i + 4] = output_v[i + 4] - output_v[i]
            output_v[i] = 0

    for i in range(8):
        if output_v[i] > 100:
            output_v[i] = 100
        elif output_v[i] < 0:
            output_v[i] = 0

    return output_v

def drive_dc_motors():
    global running
    while running:
        output_v = compute_motor_output()

        m1f.ChangeDutyCycle(output_v[0])
        m2f.ChangeDutyCycle(output_v[1])
        m3f.ChangeDutyCycle(output_v[2])
        m4f.ChangeDutyCycle(output_v[3])
        m1b.ChangeDutyCycle(output_v[4])
        m2b.ChangeDutyCycle(output_v[5])
        m3b.ChangeDutyCycle(output_v[6])
        m4b.ChangeDutyCycle(output_v[7])

       # sleep(0.01)

def drive_stepper():
    global running
    deadzone = 0.1

    while running:
        with axis_lock:
            yAxis_raw = axis_state_stepper[AXIS_RIGHT_Y]
            yAxis_l_raw = axis_state_stepper[AXIS_LEFT_Y]

        yAxis = convert_range(yAxis_raw)
        yAxisL = convert_range(yAxis_l_raw)

        if abs(yAxis) < deadzone and abs(yAxisL) < deadzone:
            stop_stepper()
            sleep(0.01)
            continue

        step_delay = get_step_delay(yAxis, yAxisL)

        if yAxisL < -deadzone:
            step_clockwise()
        elif yAxisL > deadzone:
            step_counterclockwise()
        else:
            stop_stepper()
            sleep(0.01)
            continue

        sleep(step_delay)

def drive_servo():
    global running
    global angle

    while running:
        with button_lock:
            left_pressed = button6
            right_pressed = button7

        changed = False

        with angle_lock:
            old_angle = angle

            if left_pressed == 1 and right_pressed != 1:
                angle -= 20
            elif right_pressed == 1 and left_pressed != 1:
                angle += 20

            if angle < 0:
                angle = 0
            if angle > 180:
                angle = 180

            if angle != old_angle:
                changed = True
                current_angle = angle

        if changed:
            set_angle(current_angle)
            sleep(0.03)
        else:
            sleep(0.01)

set_angle(angle)

cmd = "jstest --event /dev/input/js0"
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True,
    text=True
)

dc_thread = threading.Thread(target=drive_dc_motors, daemon=True)
stepper_thread = threading.Thread(target=drive_stepper, daemon=True)
servo_thread = threading.Thread(target=drive_servo, daemon=True)

dc_thread.start()
stepper_thread.start()
servo_thread.start()

try:
    while True:
        line = process.stdout.readline()
        if not line:
            break

        line = line.strip()

        match = re.search(
            r"type\s+(\d+),\s*time\s+\d+,\s+number\s+(\d+),\s+value\s+(-?\d+)",
            line
        )

        if not match:
            continue

        event_type = int(match.group(1))
        number = int(match.group(2))
        value = int(match.group(3))

        if event_type == 2 and number in (AXIS_X, AXIS_Y, AXIS_LT, AXIS_RT):
            with axis_lock:
                axis_state[number] = value

        elif event_type == 2 and number in (AXIS_RIGHT_Y, AXIS_LEFT_Y):
            with axis_lock:
                axis_state_stepper[number] = value

        elif event_type == 1 and number == BUTTON_LEFT:
            with button_lock:
                button6 = value

        elif event_type == 1 and number == BUTTON_RIGHT:
            with button_lock:
                button7 = value

finally:
    running = False
    sleep(0.05)

    stop_motors()
    stop_stepper()

    servo.stop()

    try:
        m1f.stop()
        m2f.stop()
        m3f.stop()
        m4f.stop()
        m1b.stop()
        m2b.stop()
        m3b.stop()
        m4b.stop()
        p1.stop()
        p2.stop()
    except:
        pass

    try:
        process.terminate()
    except:
        pass

    GPIO.cleanup()
