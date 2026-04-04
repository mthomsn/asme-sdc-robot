import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
pin = 18
GPIO.setup(pin, GPIO.OUT)

try:
    while True:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
finally:
    GPIO.output(pin, GPIO.LOW)
