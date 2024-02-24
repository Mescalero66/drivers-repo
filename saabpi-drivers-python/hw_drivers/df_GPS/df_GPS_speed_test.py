# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Test Code for Python Driver for:
# DFRobot USBGPS

import time
from df_GPS_speed import USBGPS
import RPi.GPIO as GPIO

# connect to port, set baud rate, and timeout
serialport = '/dev/ttyACM0'
baud = 9600
timeout = 3

# create object
GPS = USBGPS(serialport, baud, timeout)

#get speed reading
for i in range(0, 100):
    GPSdata = GPS.GetGPS()
    print(GPSdata[0])
    i += 1
    time.sleep(0.5)