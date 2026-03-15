import time
import math
import board
import busio
import pwmio
import RPi.GPIO as GPIO
import adafruit_tcs34725
from adafruit_motor import servo

# ============================================
# PIN SETUP
# ============================================
RED_PIN = 3
GREEN_PIN = 5
BLUE_PIN = 6
SERVO_PIN = 9
COMMON_ANODE = True

# ============================================
# GPIO SETUP
# ============================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

red_pwm = GPIO.PWM(RED_PIN, 1000)
green_pwm = GPIO.PWM(GREEN_PIN, 1000)
blue_pwm = GPIO.PWM(BLUE_PIN, 1000)

red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

# ============================================
# I2C + COLOR SENSOR SETUP
# ============================================
i2c = busio.I2C(board.SCL, board.SDA)
tcs = adafruit_tcs34725.TCS34725(i2c)

# match your Arduino settings as closely as possible
tcs.integration_time = 50
tcs.gain = 4

# ============================================
# SERVO SETUP
# ============================================
servo_pwm = pwmio.PWMOut(board.D9, duty_cycle=0, frequency=50)
myservo = servo.Servo(servo_pwm)

# ============================================
# GAMMA TABLE
# ============================================
gammatable = [0] * 256

for i in range(256):
    x = i / 255.0
    x = math.pow(x, 2.5)
    x *= 255
    gammatable[i] = int(255 - x) if COMMON_ANODE else int(x)

# ============================================
# COLOR CHECK FUNCTIONS
# ============================================
def isGreenRGB(r, g, b):
    return (42 <= r <= 60) and (110 <= g <= 145) and (45 <= b <= 70)

def isBlueRGB(r, g, b):
    return (25 <= r <= 40) and (76 <= g <= 80) and (110 <= b <= 130)

def isBlackRGB(r, g, b):
    return (58 <= r < 85) and (95 <= g <= 100) and (65 <= b <= 85)

def isGrayRGB(r, g, b):
    return (70 <= r <= 85) and (90 <= g <= 96) and (67 <= b <= 75)

def isBrownRGB(r, g, b):
    return (85 <= r <= 120) and (75 <= g <= 97) and (60 <= b <= 70)

def isRecyclable(r, g, b):
    return isGreenRGB(r, g, b) or isBlueRGB(r, g, b)

def isGarbage(r, g, b):
    return isBlackRGB(r, g, b) or isGrayRGB(r, g, b) or isBrownRGB(r, g, b)

# ============================================
# HELPER FUNCTIONS
# ============================================
def set_rgb_led(r, g, b):
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    # Convert 0-255 to PWM duty cycle percentage (0-100)
    red_pwm.ChangeDutyCycle(gammatable[r] / 255.0 * 100)
    green_pwm.ChangeDutyCycle(gammatable[g] / 255.0 * 100)
    blue_pwm.ChangeDutyCycle(gammatable[b] / 255.0 * 100)

def move_servo_slow(start_angle, end_angle, step_delay=0.015):
    if start_angle < end_angle:
        step = 1
    else:
        step = -1

    for angle in range(start_angle, end_angle + step, step):
        myservo.angle = angle
        time.sleep(step_delay)

# ============================================
# MAIN LOOP
# ============================================
try:
    current_pos = 0
    myservo.angle = current_pos
    time.sleep(0.5)

    while True:
        # Read sensor
        r, g, b = tcs.color_rgb_bytes

        print(f"R: {r}\tG: {g}\tB: {b}", end="")

        if isRecyclable(r, g, b):
            print("\t=> RECYCLABLE", end="")
            if isGreenRGB(r, g, b):
                print(" (GREEN)", end="")
            if isBlueRGB(r, g, b):
                print(" (BLUE)", end="")

            move_servo_slow(current_pos, 90)
            current_pos = 90

        elif isGarbage(r, g, b):
            print("\t=> GARBAGE", end="")
            if isBlackRGB(r, g, b):
                print(" (BLACK)", end="")
            elif isGrayRGB(r, g, b):
                print(" (GRAY)", end="")
            elif isBrownRGB(r, g, b):
                print(" (BROWN)", end="")

            move_servo_slow(current_pos, 180)
            move_servo_slow(180, 90)
            current_pos = 90

        else:
            print("\t=> EMPTY")

        print()

        set_rgb_led(r, g, b)

        time.sleep(0.12)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
    servo_pwm.deinit()

