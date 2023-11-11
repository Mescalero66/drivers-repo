# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
#
# Saabpi Project 2023

import time
import threading
# import RPi.GPIO as GPIO
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from hw_drivers.df_tempprobe.df_tempprobe import tempprobe
from hw_drivers.ada_oled.SSD1306 import *
from hw_drivers.df_digitdisp.tm1650disp import dfDisp
from hw_drivers.ignitionpulsecounter.read_RPM import reader
from hw_drivers.grove_ledbar.grove_ledbar import *
from hw_drivers.df_GPS.df_GPS_speed import USBGPS
import pigpio

digitDispNo = 4
# DIO PINS FOR EACH DIGIT DISPLAY
d1SDA = 24
d1SCL = 25
d2SDA = 26
d2SCL = 27
d3SDA = 16
d3SCL = 17
d4SDA = 18
d4SCL = 19

# DIO PINS FOR LED BAR
LEDBarPin = 22

# Creadte LED Bar Object
LEDBar = GroveLedBar(LEDBarPin, True)
LEDBarBrightness = 255
LEDBar.level(0,LEDBarBrightness)

# specify GPIO Digital Pin of incoming Ignition Pulse Signal
RPM_GPIO = 6
SAMPLE_TIME = 0.02

# OLED Temp Reading Labels
oledTT = ["Top A", "Top B", "Top C", "Top D"]
oledBT = ["Bottom A", "Bottom B", "Bottom C", "Bottom D"]

# OLED display dimensions
oledWidth = 128
oledHeight = 64

# OLED display fonts & sizes
fontTemp = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 27)
fontDec = ImageFont.truetype("DejaVuSans.ttf", 13)
fontLbl = ImageFont.truetype("DejaVuSansMono.ttf", 9)

# add the DIGIT display objects to an array
digitDisp = []
digitDisp.append(dfDisp(1, d1SCL, d1SDA))
digitDisp.append(dfDisp(2, d2SCL, d2SDA))
digitDisp.append(dfDisp(3, d3SCL, d3SDA))
digitDisp.append(dfDisp(4, d4SCL, d4SDA))

# turn on each digit display (at brightness level 0 (highest))
for i in range(digitDispNo):
    digitDisp[i].display_on(0)
    digitDisp[i].display_clear()

# display the legends on the digit displays
digitDisp[0].show_string("5pd")        
digitDisp[1].show_string("EnGn")
digitDisp[2].show_string("hdng")
digitDisp[3].show_string("alt")

# MUX that hosts all the OLED displays
mux2addr = 0x74                             # Display MUX has an I2C address of 0x74
mux2 = i2cmultiplex(mux2addr)               # create the multiplexer object

# define OLED Displays
oledI2Caddr = 0x3C                          # I2C Address of the SSD1306 OLED
oledCount = 4                               # number of ^
oled = [0,0,0,0]                         # an array to put the OLED objects
image = [0,0,0,0]                           # an array to put the image buffer for each display
draw = [0,0,0,0]                            # an array to put the images to be written
for i in range(oledCount):
    mux2.select_port(i)                     
    oled[i] = SSD1306_128_64(rst=None)
    oled[i].begin()                     # initialize graphics library for selected display module
    oled[i].clear()                     # clear display buffer
    image[i] = Image.new('1', (oledWidth, oledHeight))   # create graphics library image buffer
    draw[i] = ImageDraw.Draw(image[i])                         # put a drawing module object in the array for this OLED

tempRes = [0,0,0,0,0,0,0,0]                 # an array to store the temperature results when they come back
mux1addr = 0x70                             # Sensor MUX has an I2C address of 0x70
mux1 = i2cmultiplex(mux1addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 5                          # number of temp probes connected
tempprobes = []                             # create empty array to store the objects
for i in range(tempprobeCount):             # for each array slot
    mux1.select_port(i)                     # select that port of the mux
    tempprobes.append(tempprobe(i))         # create a tempprobe object with that ID, and append to the array

oledTGs = [0,0,0,0]                         # an array to hold the graphs for the "top half" of the OLEDs
oledBGs = [0,0,0,0]                         # an array to hold the graphs for the "bottom half" of the OLEDs
for i in range(oledCount):
    oledTGs[i] = graph2D(originX=0,originY=29,width=84,height=30,minValue=10,maxValue=110,c=1,bars=False)       # create a graph for the top half of a given display
    oledBGs[i] = graph2D(originX=0,originY=62,width=84,height=30,minValue=10,maxValue=110,c=1,bars=False)       # create a graph for the bottom half of a given display

pi = pigpio.pi()                            # create the necessary PIGPIO objects
p = reader(pi, RPM_GPIO)                    # and again

# define GPS-related variables
GPSserialport = '/dev/ttyACM0'
GPSbaud = 9600
GPStimeout = 3

# create GPS Object
GPSobject = USBGPS(GPSserialport, GPSbaud, GPStimeout)


# actual code starts here

def ReadSaabRPM(threadID):
    while True:
        RPM = p.RPM()
        digitDisp[1].show_string(format(int(RPM)))
        LEDBar.level(((RPM/500)-1), LEDBarBrightness)
        time.sleep(SAMPLE_TIME)

def GetTempDisplay(threadID):
    lastReadTime = time.time()                                  # establish baseline time
    while True:                                                 # start the loop
        try:
            now = time.time()                                   # loop start time
            if (now - lastReadTime) > 2:                        # if it's 1+ seconds since the last loop            
                for i in range(tempprobeCount):                 # for each temperature probe
                    mux1.select_port(i)                         # select its mux channel
                    tempprobes[i].req_Temp()                    # and request the temperature
                time.sleep(1)                                   # wait a quarter of a second
                for i in range(tempprobeCount):                 # then, for each temperature probe
                    mux1.select_port(i)                         # select its mux channel
                    tempRes[i] = round(tempprobes[i].read_Temp(), 1)        # and read the temperature from its register, and put it in the corresponding tempRes
                for i in range(oledCount):                                  # for each OLED display
                    mux2.select_port(i)                                     # select its mux channel
                    TempA = tempRes[i]                                      # get the result and put it into TempA
                    try:                                                    # if you can,
                        TempB = tempRes[i+4]                                # grab the result of the temp probe +4 addresses away
                    except:                                                 # if not,
                        pass                                                # don't worry about it
                    TempADec = str(TempA)[2:]                               # split the decimal place and digit into TempADec                             
                    TempAVal = str(TempA)[:-2]                              # split the whole numbers  into TempAVal
                    TempBDec = str(TempB)[2:]                               # same for TempB
                    TempBVal = str(TempB)[:-2]                              # same for TempB
                    draw[i].rectangle([0,0,127,63], fill=0)                                                             # now black out the display
                    draw[i].text((0,0), text=oledTT[i], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                    draw[i].text((116,-2), text=TempAVal, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the top half
                    draw[i].text((128,0), text=TempADec, font=fontDec, fill=255, align="right", anchor="ra")            # write the decimal for the top half
                    draw[i].text((0,32), text=oledBT[i], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half
                    draw[i].text((116,30), text=TempBVal, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the bottom half
                    draw[i].text((128,32), text=TempBDec, font=fontDec, fill=255, align="right", anchor="ra")           # write the decimal for the bottom half
                    oledTGs[i].updateGraph2D(oledTGs[i], TempA)                                                         # update the top graph with the temp value
                    draw[i].line(oledTGs[i].coords, 1, 1)                                                               # now draw the graph
                    oledBGs[i].updateGraph2D(oledBGs[i], TempB)                                                         # update the bottom graph
                    draw[i].line(oledBGs[i].coords, 1, 1)                                                               # and draw it
                    oled[i].image(image[i])                                                                          # get the drawn image in the array
                    oled[i].display()                                                                                # and display it
        except KeyboardInterrupt:                               
            for i in range(oledCount):
                mux2.select_port(i)
                oled[i].clear()
            break            

def GetGPSData(threadID):
    while True:
        GPSdata = GPSobject.GetGPS()
        GPSspeed = round(GPSdata[0],1)
        GPSlat = GPSdata[1]
        GPSlon = GPSdata[2]

        if (GPSspeed != 0):
            digitDisp[0].show_integer(int(GPSspeed))

        if (GPSdata[3] != ""):
            GPSheading = int(round(GPSdata[3],0))
            digitDisp[2].show_string(str(GPSheading) + "*")
            print(str(GPSheading) + "*")
        
        if (GPSdata[4] != 0):
            if (GPSdata[4] > 999.9):
                GPSalt = round(GPSdata[4],0)
            else:
                GPSalt = round(GPSdata[4],1)
            digitDisp[3].show_integer(int(GPSalt))
    

# main section to start all the threads

if __name__ == "__main__":
    time.sleep(3)
    threadReadRPM = threading.Thread(target=ReadSaabRPM, args=(1,), daemon=False)
    threadReadRPM.start()
    print("rpm thread started")
    threadTempDisp = threading.Thread(target=GetTempDisplay, args=(2,), daemon=False)
    threadTempDisp.start()
    print("temp thread started")
    threadGPS = threading.Thread(target=GetGPSData, args=(3,), daemon=False)
    threadGPS.start()
    print("GPS thread started")