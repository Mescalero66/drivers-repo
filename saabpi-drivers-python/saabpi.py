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
from hw_drivers.df_temp_IR.df_temp_ir import MLX90614
from hw_drivers.df_GPS.df_GPS_speed import USBGPS
import pigpio
import smbus2

time.sleep(2)

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
oledTT = ["Head", "Intercooler", "Turbo", "Outside"]
oledBT = ["Block", "Exhaust", "Radiator", "Not Used"]

# OLED display dimensions
oledWidth = 128
oledHeight = 64

# OLED display fonts & sizes
fontTemp = ImageFont.truetype("DejaVuSansMono.ttf", 28)
fontDec = ImageFont.truetype("DejaVuSans.ttf", 13)
fontLbl = ImageFont.truetype("DejaVuSans.ttf", 11)
fontHum = ImageFont.truetype("DejaVuSans.ttf", 15)
fontCoord = ImageFont.truetype("DejaVuSansMono.ttf", 17)

# add the DIGIT display objects to an array
digitDisp = []
digitDisp.append(dfDisp(1, d1SCL, d1SDA))
digitDisp.append(dfDisp(2, d2SCL, d2SDA))
digitDisp.append(dfDisp(3, d3SCL, d3SDA))
digitDisp.append(dfDisp(4, d4SCL, d4SDA))

digitDisp[0].display_on(0)
digitDisp[1].display_on(0)
digitDisp[2].display_on(5)
digitDisp[3].display_on(5)
# turn on each digit display (at brightness level 0 (highest))
for i in range(digitDispNo):
    digitDisp[i].display_clear()

hour = int(time.strftime("%H"))
if (hour > 18) or (hour < 7):
    digitDisp[0].display_on(2)
    digitDisp[1].display_on(2)
    digitDisp[2].display_on(1)
    digitDisp[3].display_on(1)
    LEDBarBrightness = 130

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

oledTGs = [0,0,0]                         # an array to hold the graphs for the "top half" of the OLEDs
oledBGs = [0,0,0]                         # an array to hold the graphs for the "bottom half" of the OLEDs

oledTGs[0] = graph2D(originX=0,originY=29,width=81,height=30,minValue=20,maxValue=70,c=1,bars=False)       # create a graph for the Cylinder Head
oledBGs[0] = graph2D(originX=0,originY=62,width=81,height=30,minValue=20,maxValue=70,c=1,bars=False)       # create a graph for the Engline Block
oledTGs[1] = graph2D(originX=0,originY=29,width=81,height=30,minValue=20,maxValue=70,c=1,bars=False)       # create a graph for the Intercooler
oledBGs[1] = graph2D(originX=0,originY=62,width=81,height=30,minValue=20,maxValue=70,c=1,bars=False)       # create a graph for the Exhaust
oledTGs[2] = graph2D(originX=0,originY=29,width=81,height=30,minValue=20,maxValue=100,c=1,bars=False)       # create a graph for the Turbo
oledBGs[2] = graph2D(originX=0,originY=62,width=81,height=30,minValue=20,maxValue=60,c=1,bars=False)       # create a graph for the Radiator

# set up PIGPIO
pi = pigpio.pi()                            # create the necessary PIGPIO objects
p = reader(pi, RPM_GPIO)                    # and again

# create IRThermo objects
I2CBus = smbus2.SMBus(1)
IRThermo = MLX90614(I2CBus, 0x5A)

# define GPS-related variables
GPSserialport = '/dev/ttyACM0'
GPSbaud = 9600
GPStimeout = 3
GPSlat = "Saab 900 Turbo"
GPSlon = "Acquiring GPS....."

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
            if (now - lastReadTime) > 1:                        # if it's 1+ seconds since the last loop            
                for i in range(tempprobeCount):                 # for each temperature probe
                    mux1.select_port(i)                         # select its mux channel
                    tempprobes[i].req_Temp()                    # and request the temperature
                time.sleep(0.2)                                   # wait a quarter of a second
                for i in range(tempprobeCount):                 # then, for each temperature probe
                    mux1.select_port(i)                         # select its mux channel
                    tempRes[i] = round(tempprobes[i].read_Temp(), 1)        # and read the temperature from its register, and put it in the corresponding tempRes
                mux1.select_port(7)
                tempRes[5] = round(IRThermo.get_obj_temp(), 1)
                tempRes[6] = round(IRThermo.get_amb_temp(), 1)
                mux1.select_port(4)
                tempRes[7] = int(tempprobes[4].read_Humi())
                
                tempTD = str(tempRes[0])[2:]
                tempTV = str(tempRes[0])[:-2]
                tempBD = str(tempRes[1])[2:]
                tempBV = str(tempRes[1])[:-2]

                draw[0].rectangle([0,0,127,63], fill=0)
                draw[0].text((0,0), text=oledTT[0], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                draw[0].text((116,-2), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the top half
                draw[0].text((128,0), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")            # write the decimal for the top half
                draw[0].text((0,32), text=oledBT[0], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half
                draw[0].text((116,30), text=tempBV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the bottom half
                draw[0].text((128,32), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")           # write the decimal for the bottom half
                oledTGs[0].updateGraph2D(oledTGs[0], tempRes[0])                                                         # update the top graph with the temp value
                draw[0].line(oledTGs[0].coords, 1, 1)                                                               # now draw the graph
                oledBGs[0].updateGraph2D(oledBGs[0], tempRes[1])                                                         # update the bottom graph
                draw[0].line(oledBGs[0].coords, 1, 1)                                                               # and draw it
                mux2.select_port(0)
                oled[0].image(image[0])                                                                          # get the drawn image in the array
                oled[0].display()                                                                                # and display it

                tempTD = str(tempRes[2])[2:]
                tempTV = str(tempRes[2])[:-2]
                tempBD = str(tempRes[3])[2:]
                tempBV = str(tempRes[3])[:-2]

                draw[1].rectangle([0,0,127,63], fill=0)
                draw[1].text((0,0), text=oledTT[1], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                draw[1].text((116,-2), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the top half
                draw[1].text((128,0), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")            # write the decimal for the top half
                draw[1].text((0,32), text=oledBT[1], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half
                draw[1].text((116,30), text=tempBV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the bottom half
                draw[1].text((128,32), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")           # write the decimal for the bottom half
                oledTGs[1].updateGraph2D(oledTGs[1], tempRes[2])                                                         # update the top graph with the temp value
                draw[1].line(oledTGs[1].coords, 1, 1)                                                               # now draw the graph
                oledBGs[1].updateGraph2D(oledBGs[1], tempRes[3])                                                         # update the bottom graph
                draw[1].line(oledBGs[1].coords, 1, 1)                                                               # and draw it
                mux2.select_port(1)
                oled[1].image(image[1])                                                                          # get the drawn image in the array
                oled[1].display()

                tempTD = str(tempRes[5])[2:]
                tempTV = str(tempRes[5])[:-2]
                tempBD = str(tempRes[6])[2:]
                tempBV = str(tempRes[6])[:-2]

                draw[2].rectangle([0,0,127,63], fill=0)
                draw[2].text((0,0), text=oledTT[2], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                draw[2].text((116,-2), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the top half
                draw[2].text((128,0), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")            # write the decimal for the top half
                draw[2].text((0,32), text=oledBT[2], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half
                draw[2].text((116,30), text=tempBV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the bottom half
                draw[2].text((128,32), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")           # write the decimal for the bottom half
                oledTGs[2].updateGraph2D(oledTGs[2], tempRes[5])                                                         # update the top graph with the temp value
                draw[2].line(oledTGs[2].coords, 1, 1)                                                               # now draw the graph
                oledBGs[2].updateGraph2D(oledBGs[2], tempRes[6])                                                         # update the bottom graph
                draw[2].line(oledBGs[2].coords, 1, 1)                                                               # and draw it
                mux2.select_port(2)
                oled[2].image(image[2])                                                                          # get the drawn image in the array
                oled[2].display()

                tempTD = str(tempRes[4])[2:]
                tempTV = str(tempRes[4])[:-2]
                tempHUM = (str(tempRes[7]) + "%")
                draw[3].rectangle([0,0,127,63], fill=0)
                draw[3].text((0,0), text=oledTT[3], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                draw[3].text((116,-2), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")          # write the value for the top half
                draw[3].text((128,0), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")            # write the decimal for the top half 
                draw[3].text((0,14), text=tempHUM, font=fontHum, fill=255, align="left", anchor="la")              # write the humidity value
                global GPSlat
                draw[3].text((127,30), text=GPSlat, font=fontCoord, fill=255, align="right", anchor="ra")           # write the latitude
                global GPSlon
                draw[3].text((127,46), text=GPSlon, font=fontCoord, fill=255, align="right", anchor="ra")           # write the longitude
                mux2.select_port(3)
                oled[3].image(image[3])                                                                             # get the drawn image in the array
                oled[3].display()
        except KeyboardInterrupt:
            break
            print(str(time.time()) + "an error happened")
            #pass       

def GetGPSData(threadID):
    while True:
        GPSdata = GPSobject.GetGPS()
        GPSspeed = round(GPSdata[0],1)
        GPSlatcoords = GPSdata[1]
        GPSloncoords = GPSdata[2]

        if (GPSspeed != 0):
            digitDisp[0].show_integer(int(GPSspeed))

        if (GPSdata[3] != ""):
            GPSheading = str.rjust((str(int(GPSdata[3]))), 3,)
            digitDisp[2].show_string(GPSheading + "*")
        
        if (GPSdata[4] != 0):
            GPSalt = GPSdata[4]
            digitDisp[3].show_integer(int(GPSalt))
        
        if (GPSdata[1] != ""):
            global GPSlat
            GPSlat = GPSlatcoords
            global GPSlon
            GPSlon = GPSloncoords

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