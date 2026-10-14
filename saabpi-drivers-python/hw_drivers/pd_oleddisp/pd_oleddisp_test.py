# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Test Code for Python Driver for:
# PiicoDev OLED SSD1306 Display
# <https://core-electronics.com.au/piicodev-oled-display-module-128x64-ssd1306.html>
#
# Shout outs to: 
# <https://github.com/CoreElectronics/CE-PiicoDev-PyPI/tree/main>
# <https://core-electronics.com.au/guides/raspberry-pi/piicodev-oled-ssd1306-raspberry-pi-guide/>

from pd_oleddisp import *
from time import sleep
from math import sin, cos

display = create_pd_OLED()

r = 20 # radius of the path (px)

theta = 0
while True:
    
    display.fill(0)                 ### Clear the display ###
    
    ### Draw a frame ###    
    theta = theta + 0.2 # increment theta by a small amount
    
    # convert polar coordinates (r, theta) to cartesian coordinates (x, y)
    x = WIDTH/2  + r * cos(theta) 
    y = HEIGHT/2 + r * sin(theta)
    
    display.fill_rect(round(x), round(y), 10, 10, 1)
    display.line(round(WIDTH/2)+5, round(HEIGHT/2)+5, round(x+5), round(y+5), 1)
    
    ### Update display ###
    display.show()