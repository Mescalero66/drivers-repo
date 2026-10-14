# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Test Program for for:
# Seeeed Grove 3-Axis Compass (I2C)
# <https://wiki.seeedstudio.com/Grove-3-Axis_Digitial_Compass_v2.0/>
#
# Largely copied from DFRobot_BMM150
# <https://github.com/DFRobot/DFRobot_BMM150>

import sys
import os
from grove_compass import *

I2C_BUS         = 0x01   #default use I2C1
ADDRESS       = 0x13   # (CSB:1 SDO:1) default i2c address
bmm150 = BMM150_I2C(I2C_BUS, ADDRESS)
heading = 0
i = 0

def setup():
    bmm150.sensor_init()
    bmm150.set_operation_mode(bmm150.POWERMODE_NORMAL)
    bmm150.set_preset_mode(bmm150.PRESETMODE_HIGHACCURACY)
    bmm150.set_xy_rep(bmm150.PRESETMODE_ENHANCED)
    bmm150.set_rate(bmm150.RATE_02HZ)
    bmm150.set_measurement_xyz()

while True:
    for i in range(0, 100):
        # heading = bmm150.get_compass_degree()
        heading = round(bmm150.get_compass_degree())
        headout = str(heading) + "*"
        print("Heading: " + headout)
        time.sleep(1)
        i += 1
