# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
#
# Saabpi Project 2023
#
# Multiplexer #2 - Temp Sensors
# Test Code to Output Temp Readings to MULTIPLE OLED Screens

import time
import RPi.GPIO as GPIO
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from hw_drivers.df_tempprobe.df_tempprobe import tempprobe
from hw_drivers.pd_oleddisp.pd_oleddisp import *
from hw_drivers.df_digitdisp.tm1650disp import dfDisp

# DIO PINS FOR EACH DIGIT DISPLAY
d1SDA = 24
d1SCL = 25
d2SDA = 17
d2SCL = 27
d3SDA = 22
d3SCL = 23
d4SDA = 5
d4SCL = 6

# OLED Temp Reading Labels
oledTT = ["Top A", "Top B", "Top C", "Top D"]
oledBT = ["Bottom A", "Bottom B", "Bottom C", "Bottom D"]

# add the DIGIT display objects to an array
displays = []
displays.append(dfDisp(1, d1SCL, d1SDA))
displays.append(dfDisp(2, d2SCL, d2SDA))
displays.append(dfDisp(3, d3SCL, d3SDA))
displays.append(dfDisp(4, d4SCL, d4SDA))

# Display MUX has an I2C address of 0x74
mux2addr = 0x74                             # I2C address of the multiplexer
mux2 = i2cmultiplex(mux2addr)               # create the multiplexer object

# define OLEDs
oledI2Caddr = 0x3C
oledCount = 4                             
display = [0,0,0,0]
for i in range(oledCount):
    mux2.select_port(i)
    display[i] = create_pd_OLED()

tempRes = [0,0,0,0]
# Sensor MUX has an I2C address of 0x70
mux1addr = 0x70                             # I2C address of the multiplexer
mux1 = i2cmultiplex(mux1addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 5                          # number of temp probes connected
tempprobes = []                             # create empty array to store the objects
for i in range(tempprobeCount):             # for each array slot
    mux1.select_port(i)                     # select that port of the mux
    tempprobes.append(tempprobe(i))          # create a tempprobe object with that ID, and append to the array
    tempRes.append("0")

oledTGs = [0,0,0,0,0,0,0,0]
oledBGs = [0,0,0,0,0,0,0,0]
for i in range(oledCount):
    graphObj = display[i].graph2D(originX=0,originY=29,width=79,height=30,minValue=0,maxValue=100,c=1,bars=False)
    oledTGs[i] = graphObj
    graphObj = display[i].graph2D(originX=0,originY=62,width=79,height=30,minValue=0,maxValue=100,c=1,bars=False)
    oledBGs[i] = graphObj

lastReadTime = time.time()                  # establish baseline time
while True:                                 # start the loop
    try:
        now = time.time()                                   # loop start time
        if (now - lastReadTime) > 2:                        # if it's 1+ seconds since the last loop            
            for i in range(tempprobeCount):
                try:
                    mux1.select_port(i)
                    tempprobes[i].req_Temp()
                    print(str(time.time()) + ",Requested Temp,#" + str(i))
                except:
                    pass
            for i in range(oledCount):
                mux2.select_port(i)
                mux1.select_port(i*2)
                try:
                    TempA = round(tempprobes[(i*2)].read_Temp(), 1)
                    print(str(time.time()) + ",Received Temp Top,#" + str(i))
                    #display[i].temptext(str(TempA), oledTT[i], 0)
                    display[i].bigtext(str(TempA), x=83, y=10, c=1)
                    print(str(time.time()) + ",Updated Top Num,#" + str(i))
                    display[i].updateGraph2D(oledTGs[i], TempA)
                    print(str(time.time()) + ",Updated Top Graph,#" + str(i))
                    mux1.select_port((i*2)+1)
                    TempB = round(tempprobes[(i*2)+1].read_Temp(), 1)
                    print(str(time.time()) + ",Received Temp Bot,#" + str(i))
                    #display[i].temptext(str(TempB), oledBT[i], 1)
                    display[i].bigtext(str(TempB), x=83, y=43, c=1)
                    print(str(time.time()) + ",Updated Bot Num,#" + str(i))
                    display[i].updateGraph2D(oledBGs[i], TempB)
                    print(str(time.time()) + ",Updated Bot Graph,#" + str(i))
                except:
                    pass
                display[i].show()
                print(str(time.time()) + ",Show Display,#" + str(i))
                display[i].fill(0)
                print(str(time.time()) + ",Fill Display,#" + str(i))
    except KeyboardInterrupt:                               
        for i in range(oledCount):
            mux2.select_port(i)
            display.fill(0)
        break            

