# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
#
# Saabpi Project 2023
#
# Multiplexer #2 - Temp Sensors
# Test Code to Output Temp Readings to MULTIPLE OLED Screens

import time
import RPi.GPIO as GPIO
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from hw_drivers.df_tempprobe.df_tempprobe import tempprobe
from hw_drivers.ada_oled.SSD1306 import *
from hw_drivers.df_digitdisp.tm1650disp import dfDisp
from hw_drivers.ignitionpulsecounter.read_RPM import reader
import pigpio

# DIO PINS FOR EACH DIGIT DISPLAY
d1SDA = 24
d1SCL = 25
d2SDA = 17
d2SCL = 27
d3SDA = 22
d3SCL = 23
d4SDA = 5
d4SCL = 6

# specify GPIO Digital Pin of incoming Ignition Pulse Signal
RPM_GPIO = 6
RUN_TIME = 600.0
SAMPLE_TIME = 0.01

# OLED Temp Reading Labels
oledTT = ["Top A", "Top B", "Top C", "Top D"]
oledBT = ["Bottom A", "Bottom B", "Bottom C", "Bottom D"]

# OLED dimensions
displayWidth = 128
displayHeight = 64
fontTemp = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 27)
fontDec = ImageFont.truetype("DejaVuSans.ttf", 13)
fontLbl = ImageFont.truetype("DejaVuSansMono.ttf", 9)

# add the DIGIT display objects to an array
displays = []
displays.append(dfDisp(1, d1SCL, d1SDA))
displays.append(dfDisp(2, d2SCL, d2SDA))
displays.append(dfDisp(3, d3SCL, d3SDA))
displays.append(dfDisp(4, d4SCL, d4SDA))

mux2addr = 0x74                             # Display MUX has an I2C address of 0x74
mux2 = i2cmultiplex(mux2addr)               # create the multiplexer object

# define OLEDs
oledI2Caddr = 0x3C
oledCount = 4
display = [0,0,0,0]
image = [0,0,0,0]
draw = [0,0,0,0]
for i in range(oledCount):
    mux2.select_port(i)
    display[i] = SSD1306_128_64(rst=None)
    display[i].begin()                     # initialize graphics library for selected display module
    display[i].clear()                     # clear display buffer
    image[i] = Image.new('1', (displayWidth, displayHeight))   # create graphics library image buffer

tempRes = [0,0,0,0,0,0,0,0]
mux1addr = 0x70                             # Sensor MUX has an I2C address of 0x70
mux1 = i2cmultiplex(mux1addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 5                          # number of temp probes connected
tempprobes = []                             # create empty array to store the objects
for i in range(tempprobeCount):             # for each array slot
    mux1.select_port(i)                     # select that port of the mux
    tempprobes.append(tempprobe(i))         # create a tempprobe object with that ID, and append to the array

oledTGs = [0,0,0,0,0,0,0,0]
oledBGs = [0,0,0,0,0,0,0,0]
for i in range(oledCount):
    oledTGs[i] = graph2D(originX=0,originY=29,width=84,height=30,minValue=10,maxValue=110,c=1,bars=False)
    oledBGs[i] = graph2D(originX=0,originY=62,width=84,height=30,minValue=10,maxValue=110,c=1,bars=False)

pi = pigpio.pi()
p = reader(pi, RPM_GPIO)

lastReadTime = time.time()                  # establish baseline time
while True:                                 # start the loop
    try:
        now = time.time()                   # loop start time
        if (now - lastReadTime) > 2:                        # if it's 1+ seconds since the last loop            
            for i in range(tempprobeCount):
                mux1.select_port(i)
                tempprobes[i].req_Temp()
            time.sleep(0.25)
            for i in range(tempprobeCount):
                mux1.select_port(i)
                tempRes[i] = round(tempprobes[i].read_Temp(), 1)
            for i in range(oledCount):
                mux2.select_port(i)
                TempA = tempRes[i]
                try:
                    TempB = tempRes[i+4]
                except:
                    pass
                TempADec = str(TempA)[2:]
                TempAVal = str(TempA)[:-2]
                TempBDec = str(TempB)[2:]
                TempBVal = str(TempB)[:-2]
                draw[i] = ImageDraw.Draw(image[i])
                draw[i].rectangle([0,0,127,63], fill=0)
                draw[i].text((0,0), text=oledTT[i], font=fontLbl, fill=255, align="left", anchor="la")
                draw[i].text((116,-2), text=TempAVal, font=fontTemp, fill=255, align="right", anchor="ra")
                draw[i].text((128,0), text=TempADec, font=fontDec, fill=255, align="right", anchor="ra")
                draw[i].text((0,32), text=oledBT[i], font=fontLbl, fill=255, align="left", anchor="la")
                draw[i].text((116,30), text=TempBVal, font=fontTemp, fill=255, align="right", anchor="ra")
                draw[i].text((128,32), text=TempBDec, font=fontDec, fill=255, align="right", anchor="ra")
                oledTGs[i].updateGraph2D(oledTGs[i], TempA)
                draw[i].line(oledTGs[i].coords, 1, 1)
                oledBGs[i].updateGraph2D(oledBGs[i], TempB)
                draw[i].line(oledBGs[i].coords, 1, 1)
                display[i].image(image[i])
                display[i].display()
    except KeyboardInterrupt:                               
        for i in range(oledCount):
            mux2.select_port(i)
            display[i].clear()
        break            

