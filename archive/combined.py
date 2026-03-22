import subprocess
import RPi.GPIO as GPIO
from time import sleep
import re
import math
import threading

NSLEEP1 = 12  #Enabling signal pin for drv8833
motor_1_backward = 27
motor_1_forward = 17
motor_2_backward = 22
motor_2_forward = 23

NSLEEP2 = 13
motor_3_forward = 25
motor_3_backward = 24
motor_4_forward = 26
motor_4_backward = 16
temp1=1

controls = [5, 6, 4, 19]

GPIO.setmode(GPIO.BCM)

#Define pin as output signal
GPIO.setup(NSLEEP1,GPIO.OUT)
GPIO.setup(NSLEEP2,GPIO.OUT)
GPIO.setup(motor_1_backward,GPIO.OUT)
GPIO.setup(motor_1_forward,GPIO.OUT)
GPIO.setup(motor_2_backward,GPIO.OUT)
GPIO.setup(motor_2_forward,GPIO.OUT)
GPIO.setup(motor_3_forward,GPIO.OUT)
GPIO.setup(motor_3_backward,GPIO.OUT)
GPIO.setup(motor_4_forward,GPIO.OUT)
GPIO.setup(motor_4_backward,GPIO.OUT)
#Initialize the motor drive signal so that the motor is in a stopped state
GPIO.output(motor_1_backward,GPIO.LOW)
GPIO.output(motor_1_forward,GPIO.LOW)
GPIO.output(motor_2_backward,GPIO.LOW)
GPIO.output(motor_2_forward,GPIO.LOW)
GPIO.output(motor_3_forward,GPIO.LOW)
GPIO.output(motor_3_backward,GPIO.LOW)
GPIO.output(motor_4_forward,GPIO.LOW)
GPIO.output(motor_4_backward,GPIO.LOW)
# WE CAN GET EACH MOTOR TO BE PWM BY SETTING UP EACH PIN AS PWM
m1b = GPIO.PWM(motor_1_backward,1000)
m1f = GPIO.PWM(motor_1_forward,1000)
m2b = GPIO.PWM(motor_2_backward,1000)
m2f = GPIO.PWM(motor_2_forward,1000)
m3b = GPIO.PWM(motor_3_backward,1000)
m3f = GPIO.PWM(motor_3_forward,1000)
m4b = GPIO.PWM(motor_4_backward,1000)
m4f = GPIO.PWM(motor_4_forward,1000)

p1=GPIO.PWM(NSLEEP1,1000)#Define p1 as a pulse signal of 1000 Hz
p2=GPIO.PWM(NSLEEP2,1000)#Define p2 as a pulse signal of 1000 Hz
p1.start(80)#P1 defaults to a duty cycle of 30%
p2.start(80)#P2 defaults to a duty cycle of 30%
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

# vectors for programing motors
forward_v = [ 1, 1, 1, 1, 0, 0, 0, 0]
backward_v = [ 0, 0, 0, 0, 1, 1, 1, 1]
right_v = [ 1, 0, 1, 0, 0, 1, 0, 1]
left_v = [ 0, 1, 0, 1, 1, 0, 1, 0]
clock_v = [ 1, 1, 0, 0, 0, 0, 1, 1]
counter_v = [ 0, 0, 1, 1, 1, 1, 0, 0]

working_v = [ 0, 0, 0, 0, 0, 0, 0, 0]
output_v = [ 0, 0, 0, 0, 0, 0, 0, 0]
    

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

# func to convert analog value range to range for pwm
def convert_range(value):
    value = int(value)
    old_range = (analog_max - analog_min)
    new_range = (scale_max - scale_min)
    new_value = (((value - analog_min) * new_range) / old_range) + scale_min
    return new_value
    
# Function to combine readings of right and left trigger and map to range
def convert_trigger(rightIn, leftIn):
    rightIn= int(rightIn)
    leftIn= int(leftIn)
    rightIn = rightIn + analog_max
    leftIn = leftIn + analog_max
    output_trigger = rightIn - leftIn
    output_trigger = (((output_trigger) * 100) / 65534)
    return output_trigger
 
def stop_motors():
    m1f.ChangeDutyCycle(0)
    m2f.ChangeDutyCycle(0)
    m3f.ChangeDutyCycle(0)
    m4f.ChangeDutyCycle(0)
    m1b.ChangeDutyCycle(0)
    m2b.ChangeDutyCycle(0)
    m3b.ChangeDutyCycle(0)
    m4b.ChangeDutyCycle(0)

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

# variables for running jstest as subprocess in order to get data from controller
cmd = "jstest --event /dev/input/js0"
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

def start_motor():
    global running

    deadzone = 0.1

    while running:
        with axis_lock:
            yAxis_raw = axis_state_stepper[AXIS_RIGHT_Y]
            yAxis_l_raw = axis_state_stepper[AXIS_LEFT_Y]

        yAxis = convert_range(yAxis_raw)
        yAxisL = convert_range(yAxis_l_raw)

        #print(yAxis, "bruh")
        #print(yAxisL, "bruh pt2")

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

def start_motors():
    global forward_v, backward_v, right_v, left_v, clock_v, counter_v, working_v, output_v
    
    # reset vectors for next reading
    forward_v = [ 1, 1, 1, 1, 0, 0, 0, 0]
    backward_v = [ 0, 0, 0, 0, 1, 1, 1, 1]
    right_v = [ 1, 0, 1, 0, 0, 1, 0, 1]
    left_v = [ 0, 1, 0, 1, 1, 0, 1, 0]
    clock_v = [ 1, 1, 0, 0, 0, 0, 1, 1]
    counter_v = [ 0, 0, 1, 1, 1, 1, 0, 0]
        
    xAxis_raw = axis_state[AXIS_X]
    yAxis_raw = axis_state[AXIS_Y]
    leftRead = axis_state[AXIS_LT]
    rightRead = axis_state[AXIS_RT]

    xAxis = convert_range(xAxis_raw)
    yAxis = convert_range(yAxis_raw)
    zAxis = convert_trigger(rightRead, leftRead)
    
    if xAxis == 0 and yAxis == 0 and zAxis == 0:
        stop_motors()
        return
    
    #have to map to vector and use algo for clocksum
    
    #setting forward vector to yaxis vals
    if (yAxis < 0):
        for i in range(8):
            forward_v[i] = (yAxis * forward_v[i])
            backward_v[(i)] = 0
        #print(f"forward_v {forward_v}")
    elif (yAxis > 0):
        for i in range(8):
            backward_v[(i)] = (yAxis * backward_v[i])
            forward_v[(i)] = 0
    else:
        for i in range(8):
            backward_v[(i)] = 0
            forward_v[(i)] = 0
            
    #setting lateral vector to xaxis vals        
    if (xAxis > 0):
        for i in range(8):
            right_v[i] = (xAxis * right_v[i])
            left_v[i] = 0
    elif (xAxis < 0):
        for i in range(8):
            left_v[i] = (xAxis * left_v[i])
            right_v[i] = 0
        #print(f"left {left_v}")
    else:
        for i in range(8):
            left_v[i] = 0
            right_v[i] = 0
            
    #setting moment vector to trigger vals        
    if (zAxis > 0):
        for i in range(8):
            clock_v[i] = (abs(zAxis) * clock_v[i])
            counter_v[i] = 0
    elif (zAxis < 0):
        for i in range(8):
            counter_v[i] = (abs(zAxis) * counter_v[i])
            clock_v[i] = 0
    else:
        for i in range(8):
            counter_v[i] = 0
            clock_v[i] = 0
    
    # compute pythag vector
    for i in range(8):
        forward_v[i] = (forward_v[i] * forward_v[i])
        backward_v[i] = (backward_v[i] * backward_v[i])
        right_v[i] = (right_v[i] * right_v[i])
        left_v[i] = (left_v[i] * left_v[i])
        #print(f"left {left_v}")
        working_v[i] = math.sqrt(abs(forward_v[i]) + abs(backward_v[i]) + abs(left_v[i]) + abs(right_v[i]))
    
    # format output vector
    for i in range(4):
        if (working_v[i] > working_v[i+4]):
            output_v[i] = working_v[i] - working_v[i+4]
            output_v[i+4] = 0
        else:
            output_v[i+4] = working_v[i+4] - working_v[i]
            output_v[i] = 0
            
    #Turn override for output vector
    for i in range(8):
        output_v[i] = ((100 - abs(zAxis)) * output_v[i]) + clock_v[i] + counter_v[i]
    #print(f"output_v {output_v}")
    
    # format output vector
    for i in range(4):
        if (output_v[i] > output_v[i+4]):
            output_v[i] = output_v[i] - output_v[i+4]
            output_v[i+4] = 0
        else:
            output_v[i+4] = output_v[i+4] - output_v[i]
            output_v[i] = 0
            
    # range conversion not working entirely as intented, if there are values above 100, we set them to 100
    for i in range(8):
        if (output_v[i] > 100):
            output_v[i] = 100
            
    # set motor values to value calculated
    m1f.ChangeDutyCycle(output_v[0])
    m2f.ChangeDutyCycle(output_v[1])
    m3f.ChangeDutyCycle(output_v[2])
    m4f.ChangeDutyCycle(output_v[3])
    m1b.ChangeDutyCycle(output_v[4])
    m2b.ChangeDutyCycle(output_v[5])
    m3b.ChangeDutyCycle(output_v[6])
    m4b.ChangeDutyCycle(output_v[7])
        
motor_thread = threading.Thread(target=start_motor, daemon=True)
servo_thread = threading.Thread(target=start_servo, daemon=True)


motor_thread.start()
servo_thread.start()

try:
    while True:
        # using jstest to read input from controller:\s*(-?\d+)|(\d+):(on|off)
        line = process.stdout.readline()
        print(f"jstest output: {line}")
        
        
        # error handling if no output
        if not line:
            break

        line = line.strip()
        #print(line)

        match = re.search(r"type\s+(\d+),\s*time\s+\d+,\s+number\s+(\d+),\s+value\s+(-?\d+)", line)
        print(match)

        if not match:
            continue

        event_type = int(match.group(1))
        number = int(match.group(2))
        value = int(match.group(3))

        if event_type == 2 and (number == 1 or number == 0 or number == 4 or number == 5):
            axis_state[number] = value
            # print("access")
            start_motors()
            print("wheels")

        if event_type == 2 and (number == 2 or number == 3):
            with axis_lock:
                axis_state_stepper[number] = value
            # print("access")
            print("stepper motor")
            print(axis_state_stepper)

        if event_type == 1 and number == BUTTON_LEFT:
            with button_lock:
                button6 = value
            print("servo left")

        if event_type == 1 and number == BUTTON_RIGHT:
            with button_lock:
                button7 = value
            print("servo right")

            
finally:
    stop_motors()
    running = False
    sleep(0.05)

    stop_motor()
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
