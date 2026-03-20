import os
import re 
import subprocess
import sys
import joystickdebug as drive
import grabpull as grab

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(CURRENT_DIR)
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)



class DriveSubsystem:
    def handle_axis(self, number: int, value: int):
        if number in (drive.AXIS_X, drive.AXIS_Y, drive.AXIS_RT, drive.AXIS_LT):
            drive.axis_state[number] = value
            drive.start_motors()
    
    def stop(self):
        drive.stop_motors()


class GrabberSystem:
    def __init__(self):
        self.angle = 0
        grab.start_background_control(self.angle)
    
    def handle_axis(self, number: int, value: int):
        if number in (grab.AXIS_RIGHT_Y, grab.AXIS_LEFT_Y):
            grab.set_axis_value(number, value)

    def handle_button(self, number: int, value: int):
        if number in (grab.BUTTON_LEFT, grab.BUTTON_RIGHT):
            grab.set_button_value(number, value)
    
    def stop(self):
        grab.stop_background_control()
        grab.servo.stop()


class RobotFacade:
    EVENT_RE = re.compile(
    r"type\s+(\d+),\s*time\s+\d+,\s+number\s+(\d+),\s+value\s+(-?\d+)"
 )

    def __init__(self):
        self.drive = DriveSubsystem()
        self.grab = GrabberSystem()
        self.process = None
    
    def start_input(self):
        self.process = subprocess.Popen(
            "jstest --event /dev/input/js0",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell = True,
            text= True
        )

    def process_line(self, line: str):
        match = self.EVENT_RE.search(line.strip())
        if not match:
            return
        
        event_type = int(match.group(1))
        number = int(match.group(2))
        value = int(match.group(3))

        if event_type == 2: # controlls the axis
            self.drive.handle_axis(number, value)
            self.grab.handle_axis(number, value)
        elif event_type == 1: # controlls the button
            self.grab.handle_button(number, value)
        
    def shutdown(self):
        self.drive.stop()
        self.grab.stop()
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
    
    def run(self):
        self.start_input()
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.process_line(line)
        finally:
            self.shutdown()



        


    


