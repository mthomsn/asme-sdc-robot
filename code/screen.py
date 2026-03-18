import serial
import time

print("Open serial..")
ser = serial.Serial('/dev/serial0', 9600, timeout=1)
time.sleep(0.5)

value = 80085

cmd = f"n0.val={value}".encode('ascii') + b"\xff\xff\xff"
ser.write(cmd)
