# MIT License
# Copyright (c) 2025 Mescalero
# v1.0 - Released 2025xxxx

import time
from led_4digit_tm1650 import LED4digdisp

#  state clockPin & dataPin
display_dataPin = 0
display_clockPin = 1
display_ID = 1

# create object
display = LED4digdisp(display_ID, display_clockPin, display_dataPin)

# turn on display
display.display_on(0)

# display string
display.show_string("HALO")
time.sleep(10)

# display int
int = 125
while int < 250:
    print(int)
    display.show_integer(int)
    int += 1
    time.sleep(0.1)