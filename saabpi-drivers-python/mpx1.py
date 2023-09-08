# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
#
# Saabpi Project 2023
#
# Multiplexer #1 - Temp Sensors

import time
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from hw_drivers.df_tempprobe.df_tempprobe import tempprobe

mpx1Addr = 0x70                             # I2C address of the multiplexer
mpx1 = i2cmultiplex(mpx1Addr)               # create the multiplexer object
tempprobeI2CAddr = 0x40                     # I2C address of the temperature probe
tempprobeCount = 5                          # number of temp probes connected
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
                print("Temp #", i, "= ", Temp)              # print the result with tempprobe number
            lastReadTime = now                              # loop end time
    except KeyboardInterrupt:                               # continue loop unless keyboard
        break                                               # kill loop

            

