# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Test Code for Python Driver for:
# DFRobot SEN0206 I2C Infrared Temperature Sensor (MLX90614) Chip
# <https://wiki.dfrobot.com/IR_Thermometer_Sensor_MLX90614_SKU__SEN0206>
#
# Shout outs to: 
# <https://github.com/CRImier/python-MLX90614>
# <https://github.com/sightsdev/PyMLX90614/>

from df_temp_ir import MLX90614
import time
import smbus2

i = 0

I2Caddress = 0x5A
I2Cbus = smbus2.SMBus(1)

thermometer = MLX90614(I2Cbus, I2Caddress)

while i < 1000:
    tempIR = round(thermometer.get_obj_temp(), 2)
    tempAM = round(thermometer.get_amb_temp(), 2)
    print("Obj: " + str(tempIR) + " Amb: " + str(tempAM))
    time.sleep(2)
    i += 1

I2Cbus.close()