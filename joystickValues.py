from evdev import categorize, InputDevice, ecodes
import subprocess
import os, time
import RPi.GPIO as GPIO
from time import sleep

p = subprocess.run(["lsinput"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

xboxLine = str(next((ln for ln in p.stdout.splitlines() if "xbox" in ln.lower()), "")).strip()

print(xboxLine)

event = xboxLine[0]
print("xbox event is event number", event)

#axis 0 = left stick x
#axis 1 = left stick y
#axis 2 = right stick x
#axis 3 = right stick y

#Use lsinput to check which event controller is associated with
device = InputDevice('/dev/input/event4')

#start jstest and save output into data.log
#we should be able to use subprocess.Popen instead, i just cant get it to work
#subprocess.run(['sudo', 'jstest', '/dev/input/js0', ' >data.log'], shell=True)
#read data.log
#data = open("data.log", "r")

# messing with functions to read output of jstest
# def read_xbox_data(filepath):
    # with open(filepath, "r") as log_file:
        # log_file.seek(0,2)
        # while True:
            # line = log_file.readline()
            # if not line:
                # continue
            # yield line.strip()
            
# def tail_log_file(file_path):
    # tail_cmd = ["tail", "-f", file_path]
    # tail_process = subprocess.Popen(tail_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # while True:
        # line = tail_process.stdout.readline().decode("utf-8")
        # if not line:
            # continue
        # yield line.strip()

# # for line in tail_log_file("data.log"):
    # # print(line)
# def follow(output_file):
    # output_file.seek(0, os.SEEK_END)
    # while True:
        # line = output_file.readline()
        # if not line:
            # time.sleep(0.1)
        # yield line

# log_file = open("data.log", "r")
# log_output = follow(log_file)
# for line in log_output:
    # print(line)

#while True:
#    print(result.stdout.read())

print(f"Reading {device.name} ({device.path})")
while(1):
    for event in device.read_loop():
        if (event.type == 3):
            value = event.value - 32767
            print()
            if (event.code == 0):
                if (value > 0):
                    print("Left X+")
                if (value < 0):
                    print("Left X-")
            if (event.code == 1):
                if (value < 0):
                    print("Left Y+")
                if (value > 0):
                    print("Left Y-")
            if (event.code == 2):
                if (value > 0):
                    print("Right X+")
                if (value < 0):
                    print("Right X-")
            if (event.code == 5):
                if (value < 0):
                    print("Right Y+")
                if (value > 0):
                    print("Right Y-")

            print(f"Value: {value}")
            

