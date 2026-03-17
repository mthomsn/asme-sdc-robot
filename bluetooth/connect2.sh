#!/bin/bash

PI="B8:27:EB:44:E3:D3"

bluetoothctl << EOF
power on
pairable on
discoverable on
scan on
pair $PI
connect $PI
quit
EOF
