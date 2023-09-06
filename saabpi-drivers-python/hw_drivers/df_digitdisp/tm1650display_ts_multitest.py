# The MIT License (MIT)
# 
# Test Code for Python Driver for:
# DFRobot DFR0645-R DFR0645-G <https://wiki.dfrobot.com/4-Digital%20LED%20Segment%20Display%20Module%20%20SKU:%20DFR0645-G_DFR0645-R>
# THIS IS NOT AN I2C DEVICE - IT WAS FUCKING ANNOYING TO GET IT TO WORK
#
# Shout out to CarlWilliamsBristol <https://github.com/CarlWilliamsBristol/pxt-tm1650display>

import time
from tm1650display_ts import Tm1650DisplayClass
import RPi.GPIO as GPIO

# connect to clockPin & dataPin
d1clockPin = 6
d1dataPin = 5

d2clockPin = 23
d2dataPin = 22

# create object
disp1 = Tm1650DisplayClass(d1clockPin, d1dataPin)
disp1.display_clear()
disp2 = Tm1650DisplayClass(d2clockPin, d2dataPin)
disp2.display_clear()
# disp1.sendStart()

# turn on with brightness (high 0 to low 7)
disp1.display_on(0)
disp2.display_on(0)

inta = 1
while inta < 10:
    disp1.show_string("Char")
    disp2.show_string("Cait")
    time.sleep(3)
    disp1.show_string("harl")
    disp2.show_string("aitl")
    time.sleep(1)
    disp1.show_string("arli")
    disp2.show_string("itli")
    time.sleep(1)
    disp1.show_string("rlie")
    disp2.show_string("tlin")
    time.sleep(1)
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