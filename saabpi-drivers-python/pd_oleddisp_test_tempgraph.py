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
#distanceGraph = display.graph2D(height=HEIGHT, minValue=10, maxValue=40)
topGraph = display.graph2D(originX=0,originY=29,width=79,height=30,minValue=0,maxValue=100,c=1,bars=True)
botGraph = display.graph2D(originX=0,originY=62,width=79,height=30,minValue=0,maxValue=100,c=1,bars=True)
#display.invert(0)

while True:
    #tempAM = round(thermometer.get_amb_temp(), 2)
    display.fill(0)
    #display.hline(0,30,127,1)
    #display.hline(0,63,127,1)
    tempIR = round(thermometer.get_obj_temp(), 1)
    tempStr = (str(tempIR))
    #display.bigtext(tempStr,x=0,y=3,c=1)
    display.temptext(tempStr, key=0, lbl="Exhaust")
    display.updateGraph2D(topGraph, tempIR)
    tempIR = round(thermometer.get_obj_temp(), 1) + 65
    tempStr = (str(tempIR))
    display.temptext(tempStr, key=1, lbl="Manifold")
    display.updateGraph2D(botGraph, tempIR)
    display.show()
    #display.text(tempStr,x=0,y=32,c=1)
    
    
    
