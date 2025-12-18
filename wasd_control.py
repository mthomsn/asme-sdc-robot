# Python Script
# https://www.electronicshub.org/raspberry-pi-l298n-interface-tutorial-control-dc-motor-l298n-raspberry-pi/

import RPi.GPIO as GPIO          
from time import sleep

#motor_1 = front left
#motor_2 = back left
#motor_3 = back right
#motor_4 = front right
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

print("\n")
print("The default speed & direction of motor is LOW & Forward rotation")
print("o-stop w-forward d-right a-left s-reverse g-clockwise h-counterclockwise y-diagonal l-low m-medium h-high e-exit")
print("\n")    

while(1):

    x=input()
    
    if x=='r':
        print("run")
        if(temp1==1):
         GPIO.output(motor_1_backward,GPIO.HIGH)
         GPIO.output(motor_1_forward,GPIO.LOW)
         GPIO.output(motor_2_backward,GPIO.HIGH)
         GPIO.output(motor_2_forward,GPIO.LOW)
         GPIO.output(motor_3_forward,GPIO.HIGH)
         GPIO.output(motor_3_backward,GPIO.LOW)
         GPIO.output(motor_4_forward,GPIO.HIGH)
         GPIO.output(motor_4_backward,GPIO.LOW)
         print("reversal")
         x='z'
        else:
         GPIO.output(motor_1_backward,GPIO.LOW)
         GPIO.output(motor_1_forward,GPIO.HIGH)
         GPIO.output(motor_2_backward,GPIO.LOW)
         GPIO.output(motor_2_forward,GPIO.HIGH)
         GPIO.output(motor_3_forward,GPIO.LOW)
         GPIO.output(motor_3_backward,GPIO.HIGH)
         GPIO.output(motor_4_forward,GPIO.LOW)
         GPIO.output(motor_4_backward,GPIO.HIGH)
         print("forward")
         x='z'


    elif x=='o':
        print("stop")
        #GPIO.output(motor_1_backward,GPIO.LOW)
        #GPIO.output(motor_1_forward,GPIO.LOW)
        #GPIO.output(motor_2_backward,GPIO.LOW)
        #GPIO.output(motor_2_forward,GPIO.LOW)
        #GPIO.output(motor_3_forward,GPIO.LOW)
        #GPIO.output(motor_3_backward,GPIO.LOW)
        #GPIO.output(motor_4_forward,GPIO.LOW)
        #GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(0)
        m1b.start(0)
        m2f.start(0)
        m2b.start(0)
        m3f.start(0)
        m3b.start(0)
        m4f.start(0)
        m4b.start(0)
        x='z'
    
    elif x=='t':
        print("stop")
        #GPIO.output(motor_1_backward,GPIO.LOW)
        #GPIO.output(motor_1_forward,GPIO.LOW)
        #GPIO.output(motor_2_backward,GPIO.LOW)
        #GPIO.output(motor_2_forward,GPIO.LOW)
        #GPIO.output(motor_3_forward,GPIO.LOW)
        #GPIO.output(motor_3_backward,GPIO.HIGH)
        #GPIO.output(motor_4_forward,GPIO.LOW)
        #GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(100)
        m1b.start(0)
        m2f.start(70)
        m2b.start(0)
        m3f.start(0)
        m3b.start(0)
        m4f.start(0)
        m4b.start(70)        
        x='z'
        
    elif x=='g':
        print("clockwise")
        #GPIO.output(motor_1_backward,GPIO.LOW)
        #GPIO.output(motor_1_forward,GPIO.LOW)
        #GPIO.output(motor_2_backward,GPIO.LOW)
        #GPIO.output(motor_2_forward,GPIO.LOW)
        #GPIO.output(motor_3_forward,GPIO.LOW)
        #GPIO.output(motor_3_backward,GPIO.HIGH)
        #GPIO.output(motor_4_forward,GPIO.LOW)
        #GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(100)
        m2f.start(100)
        m3f.start(0)
        m4f.start(0)
        m1b.start(0)
        m2b.start(0)
        m3b.start(100)
        m4b.start(100)
        
        x='z'
                
    elif x=='h':
        print("counter-clockwise")
        #GPIO.output(motor_1_backward,GPIO.LOW)
        #GPIO.output(motor_1_forward,GPIO.LOW)
        #GPIO.output(motor_2_backward,GPIO.LOW)
        #GPIO.output(motor_2_forward,GPIO.LOW)
        #GPIO.output(motor_3_forward,GPIO.LOW)
        #GPIO.output(motor_3_backward,GPIO.HIGH)
        #GPIO.output(motor_4_forward,GPIO.LOW)
        #GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(0)
        m2f.start(0)
        m3f.start(100)
        m4f.start(100)
        m1b.start(100)
        m2b.start(100)
        m3b.start(0)
        m4b.start(0)

        x='z'
        
    elif x=='y':
        print("Diagonal: foward and right")
        #GPIO.output(motor_1_backward,GPIO.LOW)
        #GPIO.output(motor_1_forward,GPIO.LOW)
        #GPIO.output(motor_2_backward,GPIO.LOW)
        #GPIO.output(motor_2_forward,GPIO.LOW)
        #GPIO.output(motor_3_forward,GPIO.LOW)
        #GPIO.output(motor_3_backward,GPIO.HIGH)
        #GPIO.output(motor_4_forward,GPIO.LOW)
        #GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(100)
        m2f.start(0)
        m3f.start(100)
        m4f.start(0)
        m1b.start(0)
        m2b.start(0)
        m3b.start(0)
        m4b.start(0)

        x='z'        

    elif x=='w':
        print("forward")
        # GPIO.output(motor_1_backward,GPIO.LOW)
        # GPIO.output(motor_1_forward,GPIO.HIGH)
        # GPIO.output(motor_2_backward,GPIO.LOW)
        # GPIO.output(motor_2_forward,GPIO.HIGH) 
        # GPIO.output(motor_3_forward,GPIO.HIGH)
        # GPIO.output(motor_3_backward,GPIO.LOW)
        # GPIO.output(motor_4_forward,GPIO.HIGH)
        # GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(100)
        m2f.start(100)
        m3f.start(100)
        m4f.start(100)
        m1b.start(0)
        m2b.start(0)
        m3b.start(0)
        m4b.start(0)
        temp1=0
        x='z'

    elif x=='u':
        print("turn right")
        # GPIO.output(motor_1_backward,GPIO.LOW)
        # GPIO.output(motor_1_forward,GPIO.HIGH)
        # GPIO.output(motor_2_backward,GPIO.LOW)
        # GPIO.output(motor_2_forward,GPIO.HIGH) 
        # GPIO.output(motor_3_forward,GPIO.HIGH)
        # GPIO.output(motor_3_backward,GPIO.LOW)
        # GPIO.output(motor_4_forward,GPIO.HIGH)
        # GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(100)
        m2f.start(100)
        m3f.start(0)
        m4f.start(0)
        m1b.start(0)
        m2b.start(0)
        m3b.start(0)
        m4b.start(0)
        temp1=0
        x='z'

    elif x=='s':
        print("reversal")
        #GPIO.output(motor_1_backward,GPIO.HIGH)
        # GPIO.output(motor_1_forward,GPIO.LOW)
        # GPIO.output(motor_2_backward,GPIO.HIGH)
        # GPIO.output(motor_2_forward,GPIO.LOW)
        # GPIO.output(motor_3_forward,GPIO.LOW)
        # GPIO.output(motor_3_backward,GPIO.HIGH)
        # GPIO.output(motor_4_forward,GPIO.LOW)
        # GPIO.output(motor_4_backward,GPIO.HIGH)
        m1f.start(0)
        m2f.start(0)
        m3f.start(0)
        m4f.start(0)
        m1b.start(100)
        m2b.start(100)
        m3b.start(100)
        m4b.start(100)
        temp1=1
        x='z'
    
    elif x=='d':
        print("right")
        #GPIO.output(motor_1_backward,GPIO.HIGH)
        # GPIO.output(motor_1_forward,GPIO.LOW)
        # GPIO.output(motor_2_backward,GPIO.LOW)
        # GPIO.output(motor_2_forward,GPIO.HIGH)
        # GPIO.output(motor_3_forward,GPIO.HIGH)
        # GPIO.output(motor_3_backward,GPIO.LOW)
        # GPIO.output(motor_4_forward,GPIO.LOW)
        # GPIO.output(motor_4_backward,GPIO.HIGH)
        m1f.start(100)
        m2f.start(0)
        m3f.start(100)
        m4f.start(0)
        m1b.start(0)
        m2b.start(100)
        m3b.start(0)
        m4b.start(100)
        temp1=1
        x='z'

    elif x=='a':
        print("left")
        # GPIO.output(motor_1_backward,GPIO.LOW)
        # GPIO.output(motor_1_forward,GPIO.HIGH)
        # GPIO.output(motor_2_backward,GPIO.HIGH)
        # GPIO.output(motor_2_forward,GPIO.LOW)
        # GPIO.output(motor_3_forward,GPIO.LOW)
        # GPIO.output(motor_3_backward,GPIO.HIGH)
        # GPIO.output(motor_4_forward,GPIO.HIGH)
        # GPIO.output(motor_4_backward,GPIO.LOW)
        m1f.start(0)
        m2f.start(100)
        m3f.start(0)
        m4f.start(100)
        m1b.start(100)
        m2b.start(0)
        m3b.start(100)
        m4b.start(0)
        temp1=1
        x='z'
        
    elif x=='l':
        print("low")
        p1.ChangeDutyCycle(30)#Set the P1 pulse signal duty cycle to 30%
        p2.ChangeDutyCycle(30)#Set the P2 pulse signal duty cycle to 30%
        x='z'
    elif x=='m':
        print("medium")
        p1.ChangeDutyCycle(60)#Set the P1 pulse signal duty cycle to 60%
        p2.ChangeDutyCycle(60)#Set the P2 pulse signal duty cycle to 60%
        x='z'
    elif x=='h':
        print("high")
        p1.ChangeDutyCycle(90)#Set the P1 pulse signal duty cycle to 90%
        p2.ChangeDutyCycle(90)#Set the P2 pulse signal duty cycle to 90%
        x='z'
    elif x=='e':
        GPIO.cleanup()
        print("GPIO Clean up")
        break
    
    else:
        print("<<<  wrong data  >>>")
        print("please enter the defined data to continue.....")

