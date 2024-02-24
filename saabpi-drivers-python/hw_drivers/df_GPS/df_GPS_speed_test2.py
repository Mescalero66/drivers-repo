# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
#
# Python Driver to Read Speed from DFRobot USB GPS

import time
from serial import Serial
from pynmeagps import NMEAReader

stream = Serial('/dev/ttyACM0', 9600, timeout=3)

# connect to port, set baud rate, and timeout
serialport = '/dev/ttyACM0'
baud = 9600
timeout = 3

class test_USBGPS:
    def __init__(self, serialport='/dev/ttyACM0', baud=9600, timeout=3):
        stream = Serial(serialport, baud, timeout=3)
        

    def GetGPS(self):
        alt = 0
        heading = 0
        spd = 0
        while(True):
            nmr = NMEAReader(stream)
            (raw_data, parsed_data) = nmr.read()
            parsed_string = str(parsed_data)
            #print(parsed_string)
            message = parsed_string[6:11]
            if (message == "GPGGA"):   
                alt = parsed_data.alt 
            if (message == "GPRMC"):
                spd_knots = parsed_data.spd
                if spd_knots != "":
                    spd = float(spd_knots) * 1.852
                lat = parsed_data.lat
                latNS = parsed_data.NS
                lon = parsed_data.lon
                lonEW = parsed_data.EW
                latStr = ((str(format(lat, '.5f'))) + " " + latNS)
                lonStr = ((str(format(lon, '.5f'))) + " " + lonEW)
                heading = parsed_data.cog 
                return spd, latStr, lonStr, heading, alt
            else:
                continue

GPS = test_USBGPS(serialport, baud, timeout)

for i in range(0, 1000):
    GPSdata = GPS.GetGPS()
    i += 1
    GPSspeed = round(GPSdata[0],1)
    GPSlatcoords = GPSdata[1]
    GPSloncoords = GPSdata[2]

    if (GPSspeed != 0):
        print(GPSspeed)

    if (GPSdata[3] != ""):
        GPSheading = str.rjust((str(int(GPSdata[3]))), 3,)
        #print((GPSheading + "*"))
    
    if (GPSdata[4] != 0):
        GPSalt = GPSdata[4]
        #print((int(GPSalt)))
    
    if (GPSdata[1] != ""):
        global GPSlat
        GPSlat = GPSlatcoords
        #print(GPSlat)
        global GPSlon
        GPSlon = GPSloncoords
        #print(GPSlon)