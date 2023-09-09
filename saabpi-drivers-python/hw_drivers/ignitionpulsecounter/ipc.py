# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>

import time
import pigpio

pi = pigpio.pi()

inputPulsePin = 12        #read GPIO 12
inputPulseEdge = 1        #read rising edges

class ignitionPulseCounter:
    def __init__(self, ID, inputPulsePin=12, inputPulseEdge=1):
        if not pi.connected:
           exit()
        else:
            cb = pi.callback(inputPulsePin, inputPulseEdge, ignitionPulseCounter)
            while True:
                time.sleep(1)
                print(cb.tally())
                cb.reset_tally()
pi.stop()
