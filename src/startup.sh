#!/bin/bash

RED_MAC="28:EA:0B:DB:97:12"

powered() {
	echo "show" | bluetoothctl show | grep "Powered" | awk '{print $2}'
}

connected() {
	echo "show ${RED_MAC}" | bluetoothctl info "$RED_MAC" | grep  "Connected" | awk '{print $2}'
}

while true; do
	IS_POWERED=$(powered)
	IS_CONNECTED=$(connected)

	if [ "$IS_POWERED" = "yes" ]; then
		if [ "$IS_CONNECTED" = "yes" ]; then
			echo "connected RED controller"
			break
		else
			echo "attempting connection..."
			echo "connect $RED_MAC" | bluetoothctl
			sleep 5
		fi
	fi
	sleep 1
done

python ~/SDC-UR-DC/src/joystick.py
