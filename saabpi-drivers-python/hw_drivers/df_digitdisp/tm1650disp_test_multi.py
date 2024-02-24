# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Test Code for Python Driver for MULTIPLE DISPLAYS of:
# DFRobot DFR0645-R DFR0645-G

import time
from tm1650disp import dfDisp
import RPi.GPIO as GPIO

# connect to clockPin & dataPin
d1SDA = 24
d1SCL = 25
d2SDA = 26
d2SCL = 27
d3SDA = 16
d3SCL = 17
d4SDA = 18
d4SCL = 19

# create object
disp1 = dfDisp(1, d1SCL, d1SDA)
disp1.display_clear()
disp2 = dfDisp(2, d2SCL, d2SDA)
disp2.display_clear()
disp3 = dfDisp(3, d3SCL, d3SDA)
disp3.display_clear()
disp4 = dfDisp(4, d4SCL, d4SDA)
disp4.display_clear()
# disp1.sendStart()

# turn on with brightness (highest is 0, then 6 down to 1 lowest)
disp1.display_on(0)
disp2.display_on(0)
disp3.display_on(5)
disp4.display_on(5)

disp1.show_string("5aab")
disp2.show_string("5aab")
disp3.show_string("5aab")
disp4.show_string("5aab")
time.sleep(5)

disp1.display_on(2)
disp2.display_on(2)
disp3.display_on(1)
disp4.display_on(1)

disp1.show_string("5aab")
disp2.show_string("5aab")
disp3.show_string("5aab")
disp4.show_string("5aab")
time.sleep(5)

inta = 1
while inta < 50:
    for i in range(7):
        disp1.display_on(i)
        disp1.show_string(str(d1SDA) + "B" + str(i))
        disp2.display_on(i)
        disp2.show_string(str(d2SDA) + "B" + str(i))
        disp3.display_on(i)
        disp3.show_string(str(d3SDA) + "B" + str(i))
        disp4.display_on(i)
        disp4.show_string(str(d4SDA) + "B" + str(i))
        time.sleep(2)
    int =+ 1

disp1.show_string("5aab")
disp2.show_string("5aab")
time.sleep(2)
disp1.show_string("----")
disp2.show_string("----")
time.sleep(0.1)
disp1.show_string("grnd")
disp2.show_string("engn")

# display number
int = 1
while int < 9999:
    disp1.show_integer(int)
    disp2.show_integer(9999 - int)
    int += 1
    # time.sleep(0.5)

# display off
disp1.display_off()
disp2.display_off()