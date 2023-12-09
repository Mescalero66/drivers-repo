# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
#
# Python Driver to Read Speed from DFRobot USB GPS

from serial import Serial
from pynmeagps import NMEAReader

stream = Serial('/dev/ttyACM0', 9600, timeout=3)

class USBGPS:
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
            