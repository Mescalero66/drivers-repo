# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# 
# Test Code for Python Driver for MULTIPLE DISPLAYS of:
# DFRobot DFR0645-R DFR0645-G

import time
from tm1650disp import tm1650Disp
import RPi.GPIO as GPIO

# connect to clockPin & dataPin
d1SDA = 24
d1SCL = 25
d2SDA = 17
d2SCL = 27
d3SDA = 22
d3SCL = 23
d4SDA = 5
d4SCL = 6

# create object
disp1 = tm1650Disp(1, d1SCL, d1SDA)
disp1.display_clear()
disp2 = tm1650Disp(2, d2SCL, d2SDA)
disp2.display_clear()
disp3 = tm1650Disp(3, d3SCL, d3SDA)
disp3.display_clear()
disp4 = tm1650Disp(4, d4SCL, d4SDA)
disp4.display_clear()
# disp1.sendStart()

# turn on with brightness (high 0 to low 7)
disp1.display_on(0)
disp2.display_on(0)
disp3.display_on(0)
disp4.display_on(0)

inta = 1
while inta < 10:
    disp1.show_string("Char")
    disp3.show_string("lie ")
    disp2.show_string("Cait")
    disp4.show_string("lin ")
    time.sleep(30)
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