from evdev import categorize, InputDevice, ecodes
import subprocess
import os, time
import RPi.GPIO as GPIO
from time import sleep
import re
import select
import threading

GPIO.setmode(GPIO.BOARD)

controls = [29, 31, 33, 35]

for pin in controls:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

SERVO_PIN = 18
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

halfsteps = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

fullsteps = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]

current_step = 0
#last_step = 0

scale_max = 1.0
scale_min = -1.0
analog_max = 32767
analog_min = -32767

running = True
axis_lock = threading.Lock()
button_lock = threading.Lock()
angle_lock = threading.Lock()

def convert_range(value):
    value = int(value)
    old_range = analog_max - analog_min
    new_range = scale_max - scale_min
    new_value = (((value - analog_min) * new_range) / old_range) + scale_min
    return new_value

def stop_motor():
    for pin in controls:
        GPIO.output(pin, GPIO.LOW)

def set_step(step_index):
    for i in range(4):
        GPIO.output(controls[i], fullsteps[step_index][i])

def step_clockwise():
    global current_step
    #global last_step
    #print(current_step, "clockwise")
    set_step(current_step)
    current_step = (current_step + 1) % len(fullsteps)
    #last_step = current_step

def step_counterclockwise():
    global current_step
    #global last_step
    #print(current_step, "counter")
    set_step(current_step)
    current_step = (current_step - 1) % len(fullsteps)
    #last_step = current_step

def get_step_delay(yAxis, yAxisL):
    speed = abs(yAxis) + abs(yAxisL)
    if speed > 1:
        speed = 1
   # print(speed, "speed")
    step_delay_max = 0.005
    step_delay_min = 0.0008
    return step_delay_max - (speed * (step_delay_max - step_delay_min))

def set_angle(angle):
    duty = 2.5 + (angle / 18.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.02)
    servo.ChangeDutyCycle(0)

cmd = "jstest --event /dev/input/js0"
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True,
    text=True
)

AXIS_RIGHT_Y = 2
AXIS_LEFT_Y = 3

BUTTON_LEFT = 6
BUTTON_RIGHT = 7

axis_state = {
    AXIS_RIGHT_Y: 0,
    AXIS_LEFT_Y: 0
}

button6 = 0
button7 = 0
angle = 0

def start_motor():
    global running

    deadzone = 0.1

    while running:
        with axis_lock:
            yAxis_raw = axis_state[AXIS_RIGHT_Y]
            yAxis_l_raw = axis_state[AXIS_LEFT_Y]

        yAxis = convert_range(yAxis_raw)
        yAxisL = convert_range(yAxis_l_raw)

        print(yAxis, "bruh")
        print(yAxisL, "bruh pt2")

        if abs(yAxis) < deadzone and abs(yAxisL) < deadzone:
            stop_motor()
            sleep(0.01)
            continue

        if yAxis == 0 and yAxisL == 0:
            stop_motor()
            sleep(0.01)
            continue

        step_delay = get_step_delay(yAxis, yAxisL)

        if yAxisL < -deadzone:
            step_clockwise()
        elif yAxisL > deadzone:
            step_counterclockwise()
        else:
            stop_motor()
            sleep(0.01)
            continue

        sleep(step_delay)

def start_servo():
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
            if right_pressed == 1 and left_pressed != 1:
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

motor_thread = threading.Thread(target=start_motor, daemon=True)
servo_thread = threading.Thread(target=start_servo, daemon=True)

motor_thread.start()
servo_thread.start()

try:
    while True:
        line = process.stdout.readline()
        line = line.strip()
        print(f"jstest output: {line}")

        if not line:
            break

        match = re.search(r"type\s+(\d+),\s*time\s+\d+,\s+number\s+(\d+),\s+value\s+(-?\d+)", line)

        if not match:
            continue

        event_type = int(match.group(1))
        number = int(match.group(2))
        value = int(match.group(3))

        #print(value)

        if event_type == 2 and number in axis_state:
            with axis_lock:
                axis_state[number] = value
            print("access")
            #start_motor()
            #val_store = value

        if event_type == 1 and number == BUTTON_LEFT:
            with button_lock:
                button6 = value

        if event_type == 1 and number == BUTTON_RIGHT:
            with button_lock:
                button7 = value
                    #if value == 0:
                        #stop_motor()
                        #break

                #break
       # elif not line:
           # break
        
        #if not line:
            #break
        #if current_step == last_step:
        #if value != 0:
        #start_motor()

        #start_motor()

finally:
    running = False
    sleep(0.05)

    stop_motor()
    servo.stop()

    try:
        process.terminate()
    except:
        pass

    GPIO.cleanup()
