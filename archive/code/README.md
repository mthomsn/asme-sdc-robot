# SDC UR@DC

## Files
readxbox
- allows us to read inputs from xbox controller
- controlled with buttons
- hardcoded to read event08 but this may change when controller is reconnected

wasdcontrol
- allows us to control with wasd on keyboard

## Need to do
- need to read input from controller joysticks to get full control of omnidirectional abilities
	- read input from jstest to pipe directly into our control algorithm
	- we have been trying to use a subprocess and read the data log, has not worked
	- currently trying to use subprocess.Popen(...) to continiously read output of jstest
	- jstest has normalized values that will make it easier to deal with controller analog data
	- tried to read directly from the event object in /dev/input/event03 but I was getting weird data from joysticks
