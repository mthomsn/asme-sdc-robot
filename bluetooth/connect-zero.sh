#!/bin/bash

bluetoothctl power on
bluetoothctl agent on
bluetoothctl default-agent
bluetoothctl pairable on
bluetoothctl discoverable on
bluetoothctl pairable-timeout 0
bluetoothctl discoverable-timeout 0
bluetoothctl show
sleep infinity
