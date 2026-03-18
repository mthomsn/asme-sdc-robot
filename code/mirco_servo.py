import RPi.GPIO as GPIO
import time

servo_pin = 18
angle = 90

GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)

pwm = GPIO.PWM(servo_pin, 50)
pwm.start(0)

def set_angle(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

try:
    print("Servo control started")
    print("Press 'a' to move left and 'd' to move right, 'q' to quite")
    set_angle(angle)

    while True:
        key = input("Enter key: ").lower()

        if key == "a":
            angle -= 10
            if angle < 0:
                angle = 0
            print(f"Angle: {angle}")
            set_angle(angle)

        elif key == "d":
            angle += 10
            if angle > 180:
                angle = 180
            print(f"Angle: {angle}")
            set_angle(angle)
        
        elif key == "q":
            print("Exiting Program")
            break

        else:
            print("Invalid key. Use 'a', 'd', or 'q' ")



except KeyboardInterrupt:
    print("Program Stop")

finally:
    pwm.stop()
    GPIO.cleanup()
