from evdev import categorize, InputDevice, ecodes
import subprocess
import RPi.GPIO as GPIO
from time import sleep

p = subprocess.run(["lsinput"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

xboxLine = str(next((ln for ln in p.stdout.splitlines() if "xbox" in ln.lower()), "")).strip()

print(xboxLine)

event = xboxLine[0]
print("xbox event is event number", event)

#Use lsinput to check which event controller is associated with
device = InputDevice('/dev/input/event8')

#define the pin for drv8833#1
NSLEEP1 = 12  #Enabling signal pin for drv8833
motor_1_backward = 27
motor_1_forward = 17
motor_2_backward = 22
motor_2_forward = 23
#define the pin for drv8833#2
NSLEEP2 = 13
motor_3_forward = 25
motor_3_backward = 24
motor_4_forward = 26
motor_4_backward = 16
temp1=1

#test modifying duty cycle -Alex
dutyCycle = 80 #Allowed values are 0-100

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
p1=GPIO.PWM(NSLEEP1,1000)#Define p1 as a pulse signal of 1000 Hz
p2=GPIO.PWM(NSLEEP2,1000)#Define p2 as a pulse signal of 1000 Hz
p1.start(dutyCycle)#P1 defaults to a duty cycle of 30%
p2.start(dutyCycle)#P2 defaults to a duty cycle of 30%

print("\n")
print("The default speed & direction of motor is LOW & Forward rotation")
print("o-stop w-forward d-rotate_right a-rotate_left s-reverse l-low m-medium h-high e-exit")
print("\n")

print(f"Reading {device.name} ({device.path})")
while(1):
	for event in device.read_loop():
		if event.type == ecodes.EV_KEY:
			# Handle key events
			key_event = categorize(event)
			if key_event.keystate == key_event.key_down:
				print(f"Key down: {key_event.keycode}")
				if 'BTN_Y' in key_event.keycode:
					print("forward")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.HIGH)# front right forward
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.HIGH)# front left forward
					GPIO.output(motor_3_forward,GPIO.HIGH)
					GPIO.output(motor_3_backward,GPIO.LOW)#backleft backwards
					GPIO.output(motor_4_forward,GPIO.HIGH)
					GPIO.output(motor_4_backward,GPIO.LOW)#Backright backwards
					temp1=0
					x='z'
				if "BTN_A" in key_event.keycode:
					print("reversal")
					GPIO.output(motor_1_backward,GPIO.HIGH)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.HIGH)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.HIGH)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.HIGH)
					temp1=1
					x='z'
				if "BTN_X" in key_event.keycode:
					print("left")
					GPIO.output(motor_1_backward,GPIO.HIGH)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.HIGH)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.HIGH)
					GPIO.output(motor_4_forward,GPIO.HIGH)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_B" in key_event.keycode:
					print("right")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.HIGH)
					GPIO.output(motor_2_backward,GPIO.HIGH)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.HIGH)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.HIGH)
					temp1=1
					x='z'
				if "BTN_TR" in key_event.keycode:
					print("clockwise rotate")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.HIGH)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.HIGH)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.HIGH)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.HIGH)
					temp1=1
					x='z'
				if "BTN_TL" in key_event.keycode:
					print("counterclockwise rotate")
					GPIO.output(motor_1_backward,GPIO.HIGH)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.HIGH)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.HIGH)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.HIGH)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_START" in key_event.keycode:
					print("Increasing Speed")
					if dutyCycle <= 90:
						dutyCycle += 5
						p1.ChangeDutyCycle(dutyCycle)
						p2.ChangeDutyCycle(dutyCycle)
					temp1=1
					x='z'
				if "BTN_SELECT" in key_event.keycode:
					print("Decreasing Speed")
					if dutyCycle >= 50:
						dutyCycle -= 5
						print(dutyCycle)
						p1.ChangeDutyCycle(dutyCycle)
						p2.ChangeDutyCycle(dutyCycle)
					temp1=1
					x='z'
			elif key_event.keystate == key_event.key_up:
				print(f"Key up: {key_event.keycode}")
				if 'BTN_WEST' in key_event.keycode:
					print("stopped forwards")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)# front right forward
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)# front left forward
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)#backleft backwards
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)#Backright backwards
					temp1=0
					x='z'
				if "BTN_A" in key_event.keycode:
					print("stopped reversal")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_B" in key_event.keycode:
					print("stopped right")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_X" in key_event.keycode:
					print("stopped left")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_TR" in key_event.keycode:
					print("stopped clockwise rotate")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
				if "BTN_TL" in key_event.keycode:
					print("stopped counterclockwise rotate")
					GPIO.output(motor_1_backward,GPIO.LOW)
					GPIO.output(motor_1_forward,GPIO.LOW)
					GPIO.output(motor_2_backward,GPIO.LOW)
					GPIO.output(motor_2_forward,GPIO.LOW)
					GPIO.output(motor_3_forward,GPIO.LOW)
					GPIO.output(motor_3_backward,GPIO.LOW)
					GPIO.output(motor_4_forward,GPIO.LOW)
					GPIO.output(motor_4_backward,GPIO.LOW)
					temp1=1
					x='z'
		elif event.type == ecodes.EV_REL:
			# Handle relative axis events (e.g., mouse movement)
			if event.code == ecodes.REL_X:
				print(f"Mouse X movement: {event.value}")
			elif event.code == ecodes.REL_Y:
				print(f"Mouse Y movement: {event.value}")
		# Add more conditions to handle other event types as needed




		#x=input()

		# if x=='r':
			# print("run")
			# if(temp1==1):
			 # GPIO.output(motor_1_backward,GPIO.HIGH)
			 # GPIO.output(motor_1_forward,GPIO.LOW)
			 # GPIO.output(motor_2_backward,GPIO.HIGH)
			 # GPIO.output(motor_2_forward,GPIO.LOW)
			 # GPIO.output(motor_3_forward,GPIO.HIGH)
			 # GPIO.output(motor_3_backward,GPIO.LOW)
			 # GPIO.output(motor_4_forward,GPIO.HIGH)
			 # GPIO.output(motor_4_backward,GPIO.LOW)
			 # print("reversal")
			 # x='z'
			# else:
			 # GPIO.output(motor_1_backward,GPIO.LOW)
			 # GPIO.output(motor_1_forward,GPIO.HIGH)
			 # GPIO.output(motor_2_backward,GPIO.LOW)
			 # GPIO.output(motor_2_forward,GPIO.HIGH)
			 # GPIO.output(motor_3_forward,GPIO.LOW)
			 # GPIO.output(motor_3_backward,GPIO.HIGH)
			 # GPIO.output(motor_4_forward,GPIO.LOW)
			 # GPIO.output(motor_4_backward,GPIO.HIGH)
			 # print("forward")
			 # x='z'


		# elif x=='o':
			# print("stop")
			# GPIO.output(motor_1_backward,GPIO.LOW)
			# GPIO.output(motor_1_forward,GPIO.LOW)
			# GPIO.output(motor_2_backward,GPIO.LOW)
			# GPIO.output(motor_2_forward,GPIO.LOW)
			# GPIO.output(motor_3_forward,GPIO.LOW)
			# GPIO.output(motor_3_backward,GPIO.LOW)
			# GPIO.output(motor_4_forward,GPIO.LOW)
			# GPIO.output(motor_4_backward,GPIO.LOW)
			# x='z'

		# elif x=='w':
			# print("forward")
			# GPIO.output(motor_1_backward,GPIO.LOW)
			# GPIO.output(motor_1_forward,GPIO.HIGH)# front right forward
			# GPIO.output(motor_2_backward,GPIO.LOW)
			# GPIO.output(motor_2_forward,GPIO.HIGH)# front left forward
			# GPIO.output(motor_3_forward,GPIO.HIGH)
			# GPIO.output(motor_3_backward,GPIO.LOW)#backleft backwards
			# GPIO.output(motor_4_forward,GPIO.HIGH)
			# GPIO.output(motor_4_backward,GPIO.LOW)#Backright backwards
			# temp1=0
			# x='z'

		# elif x=='s':
			# print("reversal")
			# GPIO.output(motor_1_backward,GPIO.HIGH)
			# GPIO.output(motor_1_forward,GPIO.LOW)
			# GPIO.output(motor_2_backward,GPIO.HIGH)
			# GPIO.output(motor_2_forward,GPIO.LOW)
			# GPIO.output(motor_3_forward,GPIO.LOW)
			# GPIO.output(motor_3_backward,GPIO.HIGH)
			# GPIO.output(motor_4_forward,GPIO.LOW)
			# GPIO.output(motor_4_backward,GPIO.HIGH)
			# temp1=1
			# x='z'

		# elif x=='d':
			# print("right")
			# GPIO.output(motor_1_backward,GPIO.HIGH)
			# GPIO.output(motor_1_forward,GPIO.LOW)
			# GPIO.output(motor_2_backward,GPIO.LOW)
			# GPIO.output(motor_2_forward,GPIO.HIGH)
			# GPIO.output(motor_3_forward,GPIO.HIGH)
			# GPIO.output(motor_3_backward,GPIO.LOW)
			# GPIO.output(motor_4_forward,GPIO.LOW)
			# GPIO.output(motor_4_backward,GPIO.HIGH)
			# temp1=1
			# x='z'

		# elif x=='a':
			# print("left")
			# GPIO.output(motor_1_backward,GPIO.LOW)
			# GPIO.output(motor_1_forward,GPIO.HIGH)
			# GPIO.output(motor_2_backward,GPIO.HIGH)
			# GPIO.output(motor_2_forward,GPIO.LOW)
			# GPIO.output(motor_3_forward,GPIO.LOW)
			# GPIO.output(motor_3_backward,GPIO.HIGH)
			# GPIO.output(motor_4_forward,GPIO.HIGH)
			# GPIO.output(motor_4_backward,GPIO.LOW)
			# temp1=1
			# x='z'

		# elif x=='l':
			# print("low")
			# p1.ChangeDutyCycle(30)#Set the P1 pulse signal duty cycle to 30%
			# p2.ChangeDutyCycle(30)#Set the P2 pulse signal duty cycle to 30%
			# x='z'
		# elif x=='m':
			# print("medium")
			# p1.ChangeDutyCycle(60)#Set the P1 pulse signal duty cycle to 60%
			# p2.ChangeDutyCycle(60)#Set the P2 pulse signal duty cycle to 60%
			# x='z'
		# elif x=='h':
			# print("high")
			# p1.ChangeDutyCycle(90)#Set the P1 pulse signal duty cycle to 90%
			# p2.ChangeDutyCycle(90)#Set the P2 pulse signal duty cycle to 90%
			# x='z'
		# elif x=='e':
			# GPIO.cleanup()
			# print("GPIO Clean up")
			# break

		# else:
			# print("<<<  wrong data  >>>")
			# print("please enter the defined data to continue.....")
