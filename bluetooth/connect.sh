#!/bin/bash

PI="DC:A6:32:65:85:0B"

bluetoothctl << EOF
power on
agent on
pairable on
discoverable on
scan on
connect $PI
quit
EOF
