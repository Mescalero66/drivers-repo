# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>

import time
import pigpio

inputPulsePin = 12        #read GPIO 12
inputPulseEdge = 1        #read rising edges
last = [None]*32
cb = []


def cbf(GPIO, level, tick):
   if last[GPIO] is not None:
      diff = pigpio.tickDiff(last[GPIO], tick)
      print("d={}".format(diff))
      RPM = 30000000 / diff
      print("RPM: ", RPM)
   last[GPIO] = tick

pi = pigpio.pi()

cb.append(pi.callback(inputPulsePin, pigpio.RISING_EDGE, cbf))

try:
   while True:
      time.sleep(60)
except KeyboardInterrupt:
   print("\nTidying up")
   for c in cb:
      c.cancel()

pi.stop()

