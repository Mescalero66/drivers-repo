# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224

import time
import pigpio

gpio = 12
level = 1           # rising edge
tickOld = 0
tickNew = 0
tickDiff = 0

pi = pigpio.pi()

if not pi.connected:
   exit()

pi.set_mode(gpio, pigpio.INPUT)

def cbf(gpio, level, tick):
    global tickOld
    if tick > tickOld:
        tickDiff = tick - tickOld
        print("diff: ", tickDiff)
        tickOld = tick

while True:
    cb1 = pi.callback(gpio, pigpio.RISING_EDGE, cbf)



