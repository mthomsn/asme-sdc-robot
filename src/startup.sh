#!/bin/bash

MACS=("28:EA:0B:DB:97:12" "40:8E:2C:34:8E:5A" "14:CB:65:F5:32:DC")

powered() {
	echo "show" | bluetoothctl show | grep "Powered" | awk '{print $2}'
}

connected() {
	bluetoothctl info "$1" | grep "Connected" | awk '{print $2}'
}

echo "connecting to controller..."

while true; do
	if [ "$(powered)" = "yes" ]; then

		for ADDR in "${MACS[@]}"; do
			if [ "$(connected "$ADDR")" = "yes" ]; then
				echo "controller $ADDR is connected"
				break 2
			fi

			echo "trying $ADDR"
			echo "connect $ADDR" | bluetoothctl
		done
	fi

	sleep 2
done

python ~/SDC-UR-DC/src/joystick.py
