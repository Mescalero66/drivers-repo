# MIT License
# Copyright (c) 2025 Mescalero
# v0.8 - Released 20250724

import time
from led_4digit_tm1650 import LED4digdisp

#  state clockPin & dataPin
display_dataPin = 18
display_clockPin = 19
display_ID = 1

# create object
display = LED4digdisp(display_ID, display_clockPin, display_dataPin)

# turn on display
display.display_on(0)

# display string
display.show_string("TEST")
time.sleep(5)

display.display_clear()

# display integer
integ = 1
while integ < 2500:
    #print(integ)
    display.show_integer(integ)
    integ += 1

display.display_clear()