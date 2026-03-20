import subprocess
import os, time
import RPi.GPIO as GPIO
from time import sleep
import re
import select

GPIO.setmode(GPIO.BCM)

controls = [5, 6, 13, 19]

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

def get_step_delay(yAxis, yAxisL):
    speed = abs(yAxis) + abs(yAxisL)
    if speed > 1:
        speed = 1
    step_delay_max = 0.005
    step_delay_min = 0.0008
    return step_delay_max - (speed * (step_delay_max - step_delay_min))

def set_angle(angle):
    duty = 2.5 + (angle / 18.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.1)
    servo.ChangeDutyCycle(0)

cmd = "jstest --event /dev/input/js0"

AXIS_RIGHT_Y = 2
AXIS_LEFT_Y = 3
BUTTON_LEFT = 6
BUTTON_RIGHT = 7

axis_state = {
    AXIS_RIGHT_Y: 0,
    AXIS_LEFT_Y: 0
}

def update_stepper():
    yAxis_raw = axis_state[AXIS_RIGHT_Y]
    yAxis_l_raw = axis_state[AXIS_LEFT_Y]
    yAxis = convert_range(yAxis_raw)
    yAxisL = convert_range(yAxis_l_raw)
    print(yAxis)
    print(yAxisL)
    deadzone = 0.1

    if abs(yAxis) < deadzone and abs(yAxisL) < deadzone:
        stop_motor()
        return

    if yAxis == 0 and yAxisL == 0:
        stop_motor()
        return

    step_delay = get_step_delay(yAxis, yAxisL)

    if yAxisL < -deadzone:
        step_clockwise()
    elif yAxisL > deadzone:
        step_counterclockwise()
    else:
        stop_motor()
        return

    sleep(step_delay)

def run_grabpull_loop():
    button6 = 0
    button7 = 0
    angle = 0
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    )

    set_angle(angle)

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

                        if event_type == 1 and number == BUTTON_LEFT:
                            button6 = value

                        if event_type == 1 and number == BUTTON_RIGHT:
                            button7 = value

            old_angle = angle

            if button6 == 1:
                angle -= 20
            if button7 == 1:
                angle += 20

            if angle < 0:
                angle = 0
            if angle > 180:
                angle = 180

            if angle != old_angle:
                set_angle(angle)

            update_stepper()

    finally:
        stop_motor()
        servo.stop()

        try:
            process.terminate()
        except:
            pass

        GPIO.cleanup()


if __name__ == "__main__":
    run_grabpull_loop()