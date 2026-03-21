import RPi.GPIO as GPIO
import time

IN1 = 17 # motor pin 1
IN2 = 27 # motor pin 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

item1 = 'trash'
item2 = 'recycling'

def right():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)

def left():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)

def sort(item):
    if item == 'trash':
        right()
        time.sleep(1)
        stop()
    if item == 'recycling':
        left()
        time.sleep(1)
        stop()


while True:
    sort(item1)
    sort(item2)
    break
