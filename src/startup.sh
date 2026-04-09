#!/bin/bash

MAC=$CONTROLLER_MAC

powered() {
	echo "show" | bluetoothctl show | grep "Powered" | awk '{print $2}'
}

connected() {
	bluetoothctl info "$MAC" | grep "Connected" | awk '{print $2}'
}

echo "connecting to controller..."

while true; do
	if [ "$(powered)" = "yes" ]; then
		if [ "$(connected)" = "yes" ]; then
			echo "controller  connected..."
			break
		else
			echo "not connected"
			echo "attempting to connect to controller..."
			echo "connect $MAC" | bluetoothctl
			sleep 3
		fi

	fi

done

echo "starting robot in..."
for i in 5 4 3 2 1; do 
	echo $i
	sleep 1
done

python home/zero/SDC-UR-DC/src/combined.py
