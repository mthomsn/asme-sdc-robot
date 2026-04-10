import RPi.GPIO as GPIO
from time import sleep

SORT1 = 10
SORT2 = 9

GPIO.setmode(GPIO.BCM)

GPIO.setup(SORT1, GPIO.OUT)
GPIO.setup(SORT2, GPIO.OUT)
GPIO.output(SORT1, GPIO.LOW)
GPIO.output(SORT2, GPIO.LOW)

while True:
    GPIO.output(SORT2, GPIO.LOW)
    GPIO.output(SORT1, GPIO.LOW)
