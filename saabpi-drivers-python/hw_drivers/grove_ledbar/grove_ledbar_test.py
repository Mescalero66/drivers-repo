# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224

import time
from grove_ledbar import GroveLedBar

# connect to pin 5 (slot D5)
PIN = 22

# reverse direction
rev = True

# create object
ledbar = GroveLedBar(PIN, rev)

# turn off
ledbar.level(0)

# set level and brightness
ledbar.level(10,255)
time.sleep(10)

# auto climbing test in both level and brightness
while True:
        for i in range(0, 11):
            b = (i*12) + 128
            ledbar.level(i, b)
            time.sleep(0.1)
