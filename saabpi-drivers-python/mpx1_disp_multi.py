# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
#
# Saabpi Project 2023
#
# Multiplexer #1 - Temp Sensors
# Test Code to Output Temp Readings to MULTIPLE 4Digit Displays

import time
import RPi.GPIO as GPIO
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from hw_drivers.df_tempprobe.df_tempprobe import tempprobe
from hw_drivers.df_digitdisp.tm1650disp import tm1650Disp

# DIO PINS FOR EACH DISPLAY
d1SDA = 24
d1SCL = 25
d2SDA = 17
d2SCL = 27
d3SDA = 22
d3SCL = 23
d4SDA = 5
d4SCL = 6

displays = []
displays.append(tm1650Disp(1, d1SCL, d1SDA))
displays.append(tm1650Disp(2, d2SCL, d2SDA))
displays.append(tm1650Disp(3, d3SCL, d3SDA))
displays.append(tm1650Disp(4, d4SCL, d4SDA))

for i in range(4):
    displays[i].display_on(0)               

mpx1Addr = 0x70                             # I2C address of the multiplexer
mpx1 = i2cmultiplex(mpx1Addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 4                          # number of temp probes connected
tempprobes = []                             # create empty array to store the objects
for i in range(tempprobeCount):             # for each array slot
    mpx1.select_port(i)                     # select that port of the mux
    tempprobes.append(tempprobe(i))         # create a tempprobe object with that ID, and append to the array

lastReadTime = time.time()                  # establish baseline time
while True:                                 # start the loop
    try:
        now = time.time()                                   # loop start time
        if (now - lastReadTime) > 2:                        # if it's 2+ seconds since the last loop
            for i in range(tempprobeCount):                 # for each tempprobe object
                mpx1.select_port(i)                         # select the correct mux port
                Temp = round(tempprobes[i].get_Temp(), 1)   # call the get_Temp function and put the rounded result in Temp
                #print("Temp #", i, "= ", Temp)             # print the result with tempprobe number
                out = str(Temp) + "*"                       # create the string to send to the display
                #print(out)
                displays[i].show_string(out)                # send Temp reading #i to display #1
            lastReadTime = now                              # loop end time
    except KeyboardInterrupt:                               
        displays[0,1,2,3].display_clear()
        break                                              

            

