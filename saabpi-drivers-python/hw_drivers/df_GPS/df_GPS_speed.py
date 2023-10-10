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

    def GetGPSkph(self):
        while(True):
            nmr = NMEAReader(stream)
            (raw_data, parsed_data) = nmr.read()
            parsed_string = str(parsed_data)
            message = parsed_string[6:11]
            if (message == "GPVTG"):
                VTGsogk = parsed_data.sogk
                return VTGsogk
            elif (message == "GPRMC"):
                RMCspd_knots = parsed_data.spd
                RMCspd = RMCspd_knots * 1.852
                return RMCspd
            else:
                continue