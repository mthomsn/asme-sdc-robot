import subprocess
import os, time
import RPi.GPIO as GPIO
from time import sleep
import re
import select


GPIO.setmode(GPIO.BOARD)

controls = [29, 31, 33, 35]

for pin in controls:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

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

scale_max = 1.0
scale_min = -1.0
analog_max = 32767
analog_min = -32767

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
    set_step(current_step)
    current_step = (current_step + 1) % len(fullsteps)

def step_counterclockwise():
    global current_step
    set_step(current_step)
    current_step = (current_step - 1) % len(fullsteps)

def get_step_delay(yAxis):
    speed = abs(yAxis)
    if speed > 1:
        speed = 1
    step_delay_max = 0.005
    step_delay_min = 0.0008
    return step_delay_max - (speed * (step_delay_max - step_delay_min))

cmd = "jstest --event /dev/input/js0"
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True,
    text=True
)

AXIS_RIGHT_Y = 3
BUTTON_LEFT = 6
BUTTON_RIGHT = 7

axis_state = {
    AXIS_RIGHT_Y: 0
}

def start_motor():
    yAxis_raw = axis_state[AXIS_RIGHT_Y]
    yAxis = convert_range(yAxis_raw)

    deadzone = 0.2


    if abs(yAxis) < deadzone:
        stop_motor() 
        return

    step_delay = get_step_delay(yAxis)

    if yAxis <= 0:
        step_clockwise()
    elif yAxis >= 0:
        step_counterclockwise()

    sleep(step_delay)

try:
    while True:
        ready, _, _ = select.select([process.stdout], [], [], 0)

        if ready:
            line = process.stdout.readline()

            if line:
                line = line.strip()
                print(f"jstest output: {line}")

                match = re.search(r"type\s+(\d+),\s*time\s+\d+,\s+number\s+(\d+),\s+value\s+(-?\d+)", line)

                if match:
                    event_type = int(match.group(1))
                    number = int(match.group(2))
                    value = int(match.group(3))

                    if event_type == 2 and number in axis_state:
                        axis_state[number] = value
                    else:
                        stop_motor()
                else:
                    stop_motor()
            else:
                stop_motor()
        start_motor()

finally:
    stop_motor()

    try:
        process.terminate()
    except:
        pass

    GPIO.cleanup()
