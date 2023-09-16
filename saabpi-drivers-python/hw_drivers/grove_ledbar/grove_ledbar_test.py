# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>

import time
from grove_ledbar import GroveLedBar

# connect to pin 5 (slot D5)
PIN = 5

# reverse direction
rev = True

# create object
ledbar = GroveLedBar(PIN, rev)

# turn off
ledbar.level(0)

# set level and brightness
ledbar.level(10,128)

# auto climbing test in both level and brightness
while True:
        for i in range(0, 11):
            b = (i*12) + 128
            ledbar.level(i, b)
            time.sleep(0.1)
