from evdev import categorize, InputDevice, ecodes
import subprocess
import os, time
import RPi.GPIO as GPIO
from time import sleep
import re
import math

# ============================================
# FINDING XBOX CONTROLLER
# ============================================
p = subprocess.run(["lsinput"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
xboxLine = str(next((ln for ln in p.stdout.splitlines() if "xbox" in ln.lower()), "")).strip()
print(xboxLine)

match = re.search(r"event(\d+)", xboxLine)  #Leigh
if match:  #Leigh
    event_num = match.group(1)  #Leigh
    print("xbox event is event number", event_num)  #Leigh
    device = InputDevice(f"/dev/input/event{event_num}")  #Leigh
else:  #Leigh
    raise RuntimeError("Xbox controller not found")  #Leigh

left_x = 0   # axis 0 = left stick x
left_y = 1   # axis 1 = left stick y
right_x = 2  # axis 2 = right stick x
right_y = 5  # axis 5 = right stick y

# ============================================
# MOTOR DRIVER SET UP
# ============================================
# motor_1 = front left
# motor_2 = back left
# motor_3 = back right
# motor_4 = front right

# define the pin for drv8833 #1
NSLEEP1 = 12  # Enabling signal pin for drv8833
motor_1_backward = 27
motor_1_forward = 17
motor_2_backward = 22
motor_2_forward = 23

# define the pin for drv8833 #2
NSLEEP2 = 13
motor_3_forward = 25
motor_3_backward = 24
motor_4_forward = 26
motor_4_backward = 16
temp1 = 1

GPIO.setmode(GPIO.BCM)

# Define pin as output signal
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

# Initialize the motor drive signal so that the motor is in a stopped state
GPIO.output(motor_1_backward, GPIO.LOW)
GPIO.output(motor_1_forward, GPIO.LOW)
GPIO.output(motor_2_backward, GPIO.LOW)
GPIO.output(motor_2_forward, GPIO.LOW)
GPIO.output(motor_3_forward, GPIO.LOW)
GPIO.output(motor_3_backward, GPIO.LOW)
GPIO.output(motor_4_forward, GPIO.LOW)
GPIO.output(motor_4_backward, GPIO.LOW)

# WE CAN GET EACH MOTOR TO BE PWM BY SETTING UP EACH PIN AS PWM
m1b = GPIO.PWM(motor_1_backward, 1000)
m1f = GPIO.PWM(motor_1_forward, 1000)
m2b = GPIO.PWM(motor_2_backward, 1000)
m2f = GPIO.PWM(motor_2_forward, 1000)
m3b = GPIO.PWM(motor_3_backward, 1000)
m3f = GPIO.PWM(motor_3_forward, 1000)
m4b = GPIO.PWM(motor_4_backward, 1000)
m4f = GPIO.PWM(motor_4_forward, 1000)

# nSLEEP should just be held HIGH to enable the driver, not PWM'd #Leigh
GPIO.output(NSLEEP1, GPIO.HIGH)  #Leigh
GPIO.output(NSLEEP2, GPIO.HIGH)  #Leigh

m1f.start(0)
m1b.start(0)
m2f.start(0)
m2b.start(0)
m3f.start(0)
m3b.start(0)
m4f.start(0)
m4b.start(0)

# ============================================
# NUMBER SCALING FUNCTIONS
# ============================================
scale_max = 1
scale_min = -1
analog_max = 32767
analog_min = -32768  #Leigh

# func to convert analog value range to range for pwm
def convert_range(value):
    value = int(value)
    old_range = (analog_max - analog_min)
    new_range = (scale_max - scale_min)
    new_value = (((value - analog_min) * new_range) / old_range) + scale_min
    return new_value

# Function to combine readings of right and left trigger and map to range
def convert_trigger(rightIn, leftIn):
    rightIn = int(rightIn)
    leftIn = int(leftIn)
    rightIn = rightIn + analog_max
    leftIn = leftIn + analog_max
    output_trigger = rightIn - leftIn
    output_trigger = (output_trigger * 100) / 65534
    return output_trigger

# Ignore tiny stick values so the robot does not drift when untouched #Leigh
def apply_deadzone(value, deadzone=0.12):  #Leigh
    if abs(value) < deadzone:  #Leigh
        return 0  #Leigh
    return value  #Leigh

# Ignore tiny trigger imbalance so the robot does not keep rotating #Leigh
def apply_deadzone_trigger(value, deadzone=8):  #Leigh
    if abs(value) < deadzone:  #Leigh
        return 0  #Leigh
    return value  #Leigh

# Explicit stop so stale PWM values do not keep motors running #Leigh
def stop_all():  #Leigh
    m1f.ChangeDutyCycle(0)  #Leigh
    m2f.ChangeDutyCycle(0)  #Leigh
    m3f.ChangeDutyCycle(0)  #Leigh
    m4f.ChangeDutyCycle(0)  #Leigh
    m1b.ChangeDutyCycle(0)  #Leigh
    m2b.ChangeDutyCycle(0)  #Leigh
    m3b.ChangeDutyCycle(0)  #Leigh
    m4b.ChangeDutyCycle(0)  #Leigh

print(f"Reading {device.name} ({device.path})")

# variables for running jstest as subprocess in order to get data from controller
cmd = "jstest /dev/input/js0"
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

# vectors for programing motors
forward_v = [1, 1, 1, 1, 0, 0, 0, 0]
backward_v = [0, 0, 0, 0, 1, 1, 1, 1]
right_v = [1, 0, 1, 0, 0, 1, 0, 1]
left_v = [0, 1, 0, 1, 1, 0, 1, 0]
clock_v = [1, 1, 0, 0, 0, 0, 1, 1]
counter_v = [0, 0, 1, 1, 1, 1, 0, 0]

working_v = [0, 0, 0, 0, 0, 0, 0, 0]
output_v = [0, 0, 0, 0, 0, 0, 0, 0]

# if yAxis scalar value is positive first 4 elements will be scalar range
# elif the yAxis scalar value is neg last 4 elements will be abs val of scalar range
# else all vals are equal

# if xAxis scalar value is positive first 4 elements will be scalar range
# elif the xAxis scalar value is neg last 4 elements will be abs val of scalar range
# else all vals are equal

# pythag on all elements of list

# format list
# if element 1 is larger then element 2

# take formated list and assign to each motor

# Remember to format vectors into original values

try:  #Leigh
    while True:
        # reset vectors for next reading
        forward_v = [1, 1, 1, 1, 0, 0, 0, 0]
        backward_v = [0, 0, 0, 0, 1, 1, 1, 1]
        right_v = [1, 0, 1, 0, 0, 1, 0, 1]
        left_v = [0, 1, 0, 1, 1, 0, 1, 0]
        clock_v = [1, 1, 0, 0, 0, 0, 1, 1]
        counter_v = [0, 0, 1, 1, 1, 1, 0, 0]

        working_v = [0] * 8  #Leigh
        output_v = [0] * 8  #Leigh

        # using jstest to read input from controller
        line = process.stdout.readline()

        # error handling if no output
        if not line:
            stop_all()  #Leigh
            break

        # breaking up line to array
        splitLine = re.split(r":\s*(-?\d+)", line)

        # if we have data we will access data we need and convert to normal range
        if len(splitLine) > 13:
            print(splitLine)

            xAxis = splitLine[3]
            yAxis = splitLine[5]
            rightRead = splitLine[11]   # Right Trigger
            leftRead = splitLine[13]    # Left Trigger

            xAxis = apply_deadzone(convert_range(xAxis))  #Leigh
            yAxis = apply_deadzone(convert_range(yAxis))  #Leigh
            zAxis = apply_deadzone_trigger(convert_trigger(rightRead, leftRead))  #Leigh

            print(f"scaled inputs -> xAxis={xAxis:.3f}, yAxis={yAxis:.3f}, zAxis={zAxis:.3f}")  #Leigh

            # If every input is neutral, explicitly stop all motors right away #Leigh
            if xAxis == 0 and yAxis == 0 and zAxis == 0:  #Leigh
                stop_all()  #Leigh
                print("stopped: all inputs inside deadzone")  #Leigh
                print(f"current motor output: {output_v}")  #Leigh
                time.sleep(0.05)  #Leigh
                continue  #Leigh

            # have to map to vector and use algo for clocksum

            # setting forward vector to yaxis vals
            if yAxis < 0:
                for i in range(8):
                    forward_v[i] = yAxis * forward_v[i]
                    backward_v[i] = 0
                print(f"forward_v {forward_v}")
            elif yAxis > 0:
                for i in range(8):
                    backward_v[i] = yAxis * backward_v[i]
                    forward_v[i] = 0
            else:
                for i in range(8):
                    backward_v[i] = 0
                    forward_v[i] = 0

            # setting lateral vector to xaxis vals
            if xAxis > 0:
                for i in range(8):
                    right_v[i] = xAxis * right_v[i]
                    left_v[i] = 0
            elif xAxis < 0:
                for i in range(8):
                    left_v[i] = xAxis * left_v[i]
                    right_v[i] = 0
                print(f"left {left_v}")
            else:
                for i in range(8):
                    left_v[i] = 0
                    right_v[i] = 0

            # setting moment vector to trigger vals
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

            # compute pythag vector
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

            # format output vector
            for i in range(4):
                if working_v[i] > working_v[i + 4]:
                    output_v[i] = working_v[i] - working_v[i + 4]
                    output_v[i + 4] = 0
                else:
                    output_v[i + 4] = working_v[i + 4] - working_v[i]
                    output_v[i] = 0

            # Turn override for output vector
            for i in range(8):
                output_v[i] = ((100 - abs(zAxis)) * output_v[i]) + clock_v[i] + counter_v[i]
            print(f"output_v {output_v}")

            # format output vector
            for i in range(4):
                if output_v[i] > output_v[i + 4]:
                    output_v[i] = output_v[i] - output_v[i + 4]
                    output_v[i + 4] = 0
                else:
                    output_v[i + 4] = output_v[i + 4] - output_v[i]
                    output_v[i] = 0

            # range conversion not working entirely as intended, if there are values above 100, we set them to 100
            for i in range(8):
                if output_v[i] > 100:
                    output_v[i] = 100

            # set motor values to value calculated using ChangeDutyCycle, not start #Leigh
            m1f.ChangeDutyCycle(output_v[0])  #Leigh
            m2f.ChangeDutyCycle(output_v[1])  #Leigh
            m3f.ChangeDutyCycle(output_v[2])  #Leigh
            m4f.ChangeDutyCycle(output_v[3])  #Leigh
            m1b.ChangeDutyCycle(output_v[4])  #Leigh
            m2b.ChangeDutyCycle(output_v[5])  #Leigh
            m3b.ChangeDutyCycle(output_v[6])  #Leigh
            m4b.ChangeDutyCycle(output_v[7])  #Leigh

        else:
            # If parsing fails, stop motors so old motor commands do not linger #Leigh
            stop_all()  #Leigh
            print("stopped: incomplete controller read", line.rstrip(), flush=True)  #Leigh

        print(f"current motor output: {output_v}")  #Leigh
        time.sleep(0.05)  #Leigh

finally:  #Leigh
    stop_all()  #Leigh
    process.terminate()  #Leigh
    GPIO.cleanup()  #Leigh
