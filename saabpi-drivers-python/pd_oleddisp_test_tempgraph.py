# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# 
# Test Code to Read and Graph Temp Sensor
# for Python Driver for:
# PiicoDev OLED SSD1306 Display
# <https://core-electronics.com.au/piicodev-oled-display-module-128x64-ssd1306.html>
#
# Shout outs to: 
# <https://github.com/CoreElectronics/CE-PiicoDev-PyPI/tree/main>
# <https://core-electronics.com.au/guides/raspberry-pi/piicodev-oled-ssd1306-raspberry-pi-guide/>

import smbus2
from time import sleep
from math import sin, cos
from hw_drivers.df_temp_IR.df_temp_ir import MLX90614
from hw_drivers.pd_oleddisp.pd_oleddisp import *

TempI2Caddress = 0x5A
TempI2Cbus = smbus2.SMBus(1)

thermometer = MLX90614(TempI2Cbus, TempI2Caddress)
display = create_pd_OLED()
distanceGraph = display.graph2D(height=HEIGHT, minValue=10, maxValue=40)
display.invert(0)

while True:
    tempAM = round(thermometer.get_amb_temp(), 2)
    display.fill(0)
    # display.hline(0,HEIGHT-1,WIDTH,1); display.vline(0,0,HEIGHT,1) # draw some axes
    tempIR = round(thermometer.get_obj_temp(), 2)
    display.bigtext(str(tempIR),95,3,1) # print the distance in the top right
    display.updateGraph2D(distanceGraph, tempIR) # plot the distance
    display.show()