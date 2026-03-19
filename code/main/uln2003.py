#!/usr/bin/python3

# testing stepper motor shit

import RPi.GPIO as GPIO
import time

in1 = 17
in2 = 18
in3 = 27
in4 = 22

stepSleep = 0.004

stepCount = 4096

direction = False

stepSequence = [[1,0,0,1],
                [1,0,0,0],
                [1,1,0,0],
                [0,1,0,0],
                [0,1,1,0],
                [0,0,1,0],
                [0,0,1,1],
                [0,0,0,1]]

GPIO.setmode(GPIO.BCM)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)

GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

motorPins = [in1, in2, in3, in4]
motorStepCounter = 0

def cleanup():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)
    GPIO.cleanup()

try:
    i = 0
    for i in range(stepCount):
        for pin in range(0, len(motorPins)):
            GPIO.output(motorPins[pin], stepSequence[motorStepCounter][pin])
        if direction == True:
            motorStepCounter = (motorStepCounter - 1) % 8
        elif direction == False:
            motorStepCounter = (motorStepCounter + 1) % 8
        else:
            print("For some reason, direction was neither true nor false, closing program...")
            cleanup()
            exit(1)
        time.sleep(stepSleep)

except KeyboardInterrupt:
    cleanup()
    exit(1)

exit(0)