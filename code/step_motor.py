import RPi.GPIO as GPIO
import time 

#GPIO: pins for ULN2003 driver 
# N1: 23
# N1: 24
# N1: 25
# N1: 8
pins = [5,6,13,19]



#Step squence: Full step
step_squence = [
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1]
   
]

#Sets the GPIO numbering to BCM
GPIO.setmode(GPIO.BCM)

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

#Activates the correct motor coils for a single steps
def set_step(step):
        for i in range (4):
            GPIO.output(pins[i], step[i])

def move_stepper(direction, step, delay=0.01):
    # directions options: in or out
    # steps: how many steps per cycles
    # delay: time steps
    
    if direction == "in":
        squence = step_squence
    elif direction == "out":
        squence = list(reversed(step_squence))
    else:
        print("input is in valid")
        return
    
    #Loop through the number of steps
    for _ in range(step):
        for step in squence:
            set_step(step)
            time.sleep(delay)
    
    #turns off the coil after moive.
    for pin in pins:
        GPIO.output(pin, 0)


# Main Loop
try:
    while True:
        
        direction = input("Enter direction (in/out) or 'q' to quite: ").strip().lower()

        if direction == "q":
            break

        step_input = input("Enter number of steps: ").strip()
        
        if not step_input.isdigit():
            print("Please enter valid whole number.")
            continue

        steps = int(step_input)
        move_stepper(direction, steps)

except KeyboardInterrupt:
    print("\nProgram stopped.")

finally:
    GPIO.cleanup()
    


