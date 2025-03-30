# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1
#
# Saabpi Project


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

time.sleep(1)

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
oledTT = ["Head", "I/Cooler", "Battery", "Outside"]
oledBT = ["Block", "Exhaust", "Turbo", "Not Used"]
#oledTTV = ["C/H", "I/C", "Bat", "Outside"]
#oledBTV = ["E/B", "Exh", "Tbo", "Not Used"]

# OLED display dimensions
oledWidth = 128
oledHeight = 64

# OLED display fonts & sizes
fontTemp = ImageFont.truetype("DejaVuSansMono.ttf", 28)
fontDec = ImageFont.truetype("DejaVuSans.ttf", 13)
fontTurbo = ImageFont.truetype("DejaVuSansMono.ttf", 32)
fontComp = ImageFont.truetype("DejaVuSansMono.ttf", 25)
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

# adjust brightness of displays according to time of day

#hour = int(time.strftime("%H"))
#if (hour > 18) or (hour < 7):
#    digitDisp[0].display_on(2)
#    digitDisp[1].display_on(2)
#    digitDisp[2].display_on(1)
#    digitDisp[3].display_on(1)
#    LEDBarBrightness = 130

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
oled = [0,0,0,0]                            # an array to put the OLED objects
image = [0,0,0,0]                           # an array to put the image buffer for each display
draw = [0,0,0,0]                            # an array to put the images to be written
for i in range(oledCount):
    mux2.select_port(i)                     
    oled[i] = SSD1306_128_64(rst=None)
    oled[i].begin()                                      # initialize graphics library for selected display module
    oled[i].clear()                                      # clear display buffer
    image[i] = Image.new('1', (oledWidth, oledHeight))   # create graphics library image buffer
    draw[i] = ImageDraw.Draw(image[i])                   # put a drawing module object in the array for this OLED

tempRes = [0,0,0,0,0,0,0,0]                 # an array to store the temperature results when they come back
mux1addr = 0x70                             # Sensor MUX has an I2C address of 0x70
mux1 = i2cmultiplex(mux1addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 5                          # number of temp probes connected
tempprobes = []                             # create empty array to store the objects
for i in range(tempprobeCount):             # for each array slot
    mux1.select_port(i)                     # select that port of the mux
    tempprobes.append(tempprobe(i))         # create a tempprobe object with that ID, and append to the array

oledTGs = [0,0,0]                           # an array to hold the graphs for the "top half" of the OLEDs
oledBGs = [0,0,0]                           # an array to hold the graphs for the "bottom half" of the OLEDs
globalBars = True

oledTGs[0] = graph2D(originX=0,originY=32,width=62,height=31,minValue=50,maxValue=150,c=1,bars=False)       # create a graph for the Cylinder Head (20-140)
oledBGs[0] = graph2D(originX=0,originY=64,width=62,height=31,minValue=50,maxValue=150,c=1,bars=False)       # create a graph for the Engline Block
oledTGs[1] = graph2D(originX=0,originY=32,width=62,height=31,minValue=20,maxValue=100,c=1,bars=False)       # create a graph for the Intercooler
oledBGs[1] = graph2D(originX=0,originY=64,width=62,height=31,minValue=50,maxValue=150,c=1,bars=False)       # create a graph for the Exhaust
#oledTGs[2] = graph2D(originX=0,originY=32,width=62,height=31,minValue=20,maxValue=120,c=1,bars=globalBars)       # create a graph for the Battery
oledBGs[2] = graph2D(originX=0,originY=64,width=128,height=31,minValue=150,maxValue=320,c=1,bars=True)      # create a graph for the Turbo (150-320)

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
GPSheading = 0
GPSlat = "Saab 900"
GPSlon = "   Turbo"


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
                time.sleep(0.25)                                # wait a quarter of a second
                for i in range(tempprobeCount):                 # then, for each temperature probe
                    mux1.select_port(i)                         # select its mux channel
                    tempRes[i] = round(tempprobes[i].read_Temp(), 1)    # and read the temperature from its register, and put it in the corresponding tempRes
                mux1.select_port(7)
                tempRes[5] = round(IRThermo.get_obj_temp(), 1)  # get IR temp from IR thermometer
                #tempRes[6] = round(IRThermo.get_amb_temp(), 1) # get ambient temp from IR thermometer
                time.sleep(0.2)                                 # inserted here
                #mux1.select_port(4)                            # select 'Outside' temperature sensor channel
                #tempRes[7] = int(tempprobes[4].read_Humi())    # read humidity from 'Outside' temperature sensor
                
                tempTD = str(tempRes[0])[-2:]                                                                       # top decimal
                tempTV = str(tempRes[0])[:-2]                                                                       # top value
                tempBD = str(tempRes[1])[-2:]                                                                       # bottom decimal
                tempBV = str(tempRes[1])[:-2]                                                                       # bottom value

                draw[0].rectangle([0,0,127,63], fill=0)                                                             # black out the screen
                oledTGs[0].updateGraph2D(oledTGs[0], tempRes[0])                                                    # update the top graph with the temp value
                draw[0].line(oledTGs[0].coords, 1, 1)                                                               # now draw the graph
                oledBGs[0].updateGraph2D(oledBGs[0], tempRes[1])                                                    # update the bottom graph
                draw[0].line(oledBGs[0].coords, 1, 1)                                                               # and draw it
                draw[0].rectangle([0,10,32,16], fill=0)
                draw[0].text((0,10), text=oledTT[0], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half (11 was 3)
                #draw[0].text((0,4), text=oledTTV[0], font=fontLbl, fill=255, direction="ttb", anchor="la")         # write the label for the top half
                draw[0].text((114,1), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")             # write the value for the top half
                draw[0].text((126,2), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")              # write the decimal for the top half
                draw[0].rectangle([0,46,33,63], fill=0)
                draw[0].text((0,47), text=oledBT[0], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half (44 was 63)
                #draw[0].text((0,63), text=oledBTV[0], font=fontLbl, fill=255, direction="ttb", anchor="ls")        # write the label for the bottom half
                draw[0].text((114,38), text=tempBV, font=fontTemp, fill=255, align="right", anchor="ra")            # write the value for the bottom half
                draw[0].text((126,39), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")             # write the decimal for the bottom half            
                mux2.select_port(0)
                oled[0].image(image[0])                                                                             # get the drawn image in the array
                oled[0].display()                                                                                   # and display it

                tempTD = str(tempRes[2])[-2:]
                tempTV = str(tempRes[2])[:-2]
                tempBD = str(tempRes[3])[-2:]
                tempBV = str(tempRes[3])[:-2]

                draw[1].rectangle([0,0,127,63], fill=0)                                                             # black out the screen
                oledTGs[1].updateGraph2D(oledTGs[1], tempRes[2])                                                    # update the top graph with the temp value
                draw[1].line(oledTGs[1].coords, 1, 1)                                                               # now draw the graph
                oledBGs[1].updateGraph2D(oledBGs[1], tempRes[3])                                                    # update the bottom graph
                draw[1].line(oledBGs[1].coords, 1, 1)                                                               # and draw it
                draw[1].rectangle([0,10,46,16], fill=0)
                draw[1].text((0,10), text=oledTT[1], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                #draw[1].text((0,4), text=oledTTV[1], font=fontLbl, fill=255, direction="ttb", anchor="la")         # write the label for the top half
                draw[1].text((114,1), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")             # write the value for the top half
                draw[1].text((126,2), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")              # write the decimal for the top half
                draw[1].rectangle([0,46,48,63], fill=0)
                draw[1].text((0,47), text=oledBT[1], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the bottom half
                #draw[1].text((0,63), text=oledBTV[1], font=fontLbl, fill=255, direction="ttb", anchor="ls")        # write the label for the bottom half
                draw[1].text((114,38), text=tempBV, font=fontTemp, fill=255, align="right", anchor="ra")            # write the value for the bottom half
                draw[1].text((126,39), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")             # write the decimal for the bottom half
                mux2.select_port(1)
                oled[1].image(image[1])                                                                             # get the drawn image in the array
                oled[1].display()

                #tempTD = str(tempRes[6])[-2:]                                                                      # ignore 'Battery' measurement
                #tempTV = str(tempRes[6])[:-2]
                tempBD = str(tempRes[5])[-2:]
                tempBV = str(tempRes[5])[:-2]

                draw[2].rectangle([0,0,127,63], fill=0)                                                             # black out the screen
                #oledTGs[2].updateGraph2D(oledTGs[2], tempRes[6])                                                   # update the top graph with the temp value
                #draw[2].line(oledTGs[2].coords, 1, 1)                                                              # now draw the graph
                oledBGs[2].updateGraph2D(oledBGs[2], tempRes[5])                                                    # update the bottom graph
                draw[2].line(oledBGs[2].coords, 1, 1)                                                               # and draw it
                #draw[2].rectangle([0,11,44,16], fill=0)                                                              # black background for text label
                #draw[2].text((0,3), text=oledTT[2], font=fontLbl, fill=255, align="left", anchor="la")             # write the label for the top half
                draw[2].text((0,11), text=oledBT[2], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half (Turbo-relocated to top)
                #draw[2].text((0,4), text=oledTTV[2], font=fontLbl, fill=255, direction="ttb", anchor="la")         # write the label for the top half (obsolete x2)
                #draw[2].text((114,1), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")            # write the value for the top half
                #draw[2].text((126,2), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")             # write the decimal for the top half
                #draw[2].rectangle([0,51,36,63], fill=0)                                                            # black background for text label
                #draw[2].text((0,63), text=oledBT[2], font=fontLbl, fill=255, align="left", anchor="ls")            # write the label for the bottom half (Turbo deactivated at the bottom)
                #draw[2].text((0,63), text=oledBTV[2], font=fontLbl, fill=255, direction="ttb", anchor="ls")        # write the label for the bottom half (obsolete x2)
                draw[2].text((110,1), text=tempBV, font=fontTurbo, fill=255, align="right", anchor="ra")           # write the value for the bottom half (note the font change)
                draw[2].text((126,2), text=tempBD, font=fontDec, fill=255, align="right", anchor="ra")             # write the decimal for the bottom half (note the font change)
                mux2.select_port(2)
                oled[2].image(image[2])                                                                             # get the drawn image in the array
                oled[2].display()

                draw[3].rectangle([0,0,127,63], fill=0)                                                             # black out the screen
                # THE BLOCK BELOW PREVIOUSLY GRABBED TO AMBIENT TEMP AND HUMIDTY AND DISPLAYED IT.
                # IT HAS BEEN REMOVED IN ORDER TO IMPLEMENT THE COMPASS
                #tempTD = str(tempRes[4])[-2:]
                #tempTV = str(tempRes[4])[:-2]
                #tempHUM = (str(tempRes[7]) + "%H")
                
                #draw[3].text((0,3), text=oledTT[3], font=fontLbl, fill=255, align="left", anchor="la")              # write the label for the top half
                #draw[3].text((112,2), text=tempTV, font=fontTemp, fill=255, align="right", anchor="ra")             # write the value for the top half
                #draw[3].text((124,3), text=tempTD, font=fontDec, fill=255, align="right", anchor="ra")              # write the decimal for the top half 
                #draw[3].text((0,17), text=tempHUM, font=fontHum, fill=255, align="left", anchor="la")               # write the humidity value
                # END OF AMBIENT TEMP AND HUMIDTY CODE BLOCK

                #START OF COMPASS CODE BLOCK
                #global GPSheading                                                                                  # for testing porpoises
                #GPSheading = GPSheading + 10                                                                       # for testing porpoises

                if(GPSheading <=11):
                    draw[3].text((64,1), text=" - N - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING N
                elif(GPSheading <=34):
                    draw[3].text((64,1), text=" N - NE ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING NNE
                elif(GPSheading <=56):
                    draw[3].text((64,1), text=" - NE - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING NE
                elif(GPSheading <=79):
                    draw[3].text((64,1), text=" NE - E ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING ENE
                elif(GPSheading <=101):
                    draw[3].text((64,1), text=" - E - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING E
                elif(GPSheading <=124):
                    draw[3].text((64,1), text=" E - SE ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING ESE
                elif(GPSheading <=146):
                    draw[3].text((64,1), text=" - SE - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING SE
                elif(GPSheading <=169):
                    draw[3].text((64,1), text=" SE - S ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING SSE
                elif(GPSheading <=191):
                    draw[3].text((64,1), text=" - S - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING S
                elif(GPSheading <=214):
                    draw[3].text((64,1), text=" S - SW ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING SSW
                elif(GPSheading <=236):
                    draw[3].text((64,1), text=" - SW - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING SW
                elif(GPSheading <=259):
                    draw[3].text((64,1), text=" SW - W ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING WSW
                elif(GPSheading <=281):
                    draw[3].text((64,1), text=" - W - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING W
                elif(GPSheading <=304):
                    draw[3].text((64,1), text=" W - NW ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING WNW
                elif(GPSheading <=326):
                    draw[3].text((64,1), text=" - NW - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING NW
                elif(GPSheading <=349):
                    draw[3].text((64,1), text=" NW - N ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING NNW
                elif(GPSheading <=360):
                    draw[3].text((64,1), text=" - N - ", font=fontComp, fill=255, align="center", anchor="ma")           # COMPASS POINTING N AGAIN
                elif(GPSheading >360):
                    draw[3].text((64,1), text="Magnets?!?!", font=fontDec, fill=255, align="center", anchor="ma")        # something's gone wrong
                else:
                    draw[3].text((64,1), text="Finding North...", font=fontDec, fill=255, align="center", anchor="ma") # No Signal

                #END OF COMPASS CODE BLOCK

                global GPSlat
                draw[3].text((120,32), text=GPSlat, font=fontCoord, fill=255, align="right", anchor="ra")           # write the latitude
                global GPSlon
                draw[3].text((120,48), text=GPSlon, font=fontCoord, fill=255, align="right", anchor="ra")           # write the longitude
                mux2.select_port(3)
                oled[3].image(image[3])                                                                             # get the drawn image in the array
                oled[3].display()
        except KeyboardInterrupt:
            break
            print(str(time.time()) + "an error happened")
            #pass       

def GetGPSData(threadID):
    while True:
        try:
            GPSdata = GPSobject.GetGPS()
            GPSspeed = round(GPSdata[0],1)
            GPSlatcoords = GPSdata[1]
            GPSloncoords = GPSdata[2]

            if (GPSspeed != 0):
                digitDisp[0].show_integer(int(GPSspeed))

            if (GPSdata[3] != ""):
                global GPSheading
                GPSheading = int(GPSdata[3])
                GPSheadstr = str.rjust((str(int(GPSheading))), 3,)
                digitDisp[2].show_string(GPSheadstr + "*")       
            
            if (GPSdata[4] != 0):
                GPSalt = GPSdata[4]
                digitDisp[3].show_integer(int(GPSalt))
            
            if (GPSdata[1] != ""):
                global GPSlat
                GPSlat = GPSlatcoords
                global GPSlon
                GPSlon = GPSloncoords
        except KeyboardInterrupt:
            break
            print(str(time.time()) + "an error happened")
            #pass

# main section to start all the threads

if __name__ == "__main__":
    threadReadRPM = threading.Thread(target=ReadSaabRPM, args=(1,), daemon=False)
    threadReadRPM.start()
    #print("rpm thread started")
    time.sleep(5)
    threadTempDisp = threading.Thread(target=GetTempDisplay, args=(2,), daemon=False)
    threadTempDisp.start()
    #print("temp thread started")
    time.sleep(2)
    threadGPS = threading.Thread(target=GetGPSData, args=(3,), daemon=False)
    threadGPS.start()
    #print("GPS thread started")