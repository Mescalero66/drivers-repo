# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.0 - Released 20231209
# 
# Test Code to Read and Graph Temp Sensor
# for Python Driver for:
# PiicoDev OLED SSD1306 Display
# <https://core-electronics.com.au/piicodev-oled-display-module-128x64-ssd1306.html>
#

import smbus2
from hw_drivers.df_temp_IR.df_temp_ir import MLX90614
from hw_drivers.ada_oled.SSD1306 import *
from hw_drivers.df_multiplexer.df_multiplexer import i2cmultiplex
from PIL import Image, ImageDraw, ImageFont

TempI2Caddress = 0x5A
TempI2Cbus = smbus2.SMBus(1)

thermometer = MLX90614(TempI2Cbus, TempI2Caddress)

# Display MUX has an I2C address of 0x74
mux2addr = 0x74                             # I2C address of the multiplexer
mux2 = i2cmultiplex(mux2addr)               # create the multiplexer object
mux2.select_port(0)

display = SSD1306_128_64(rst=None)  # 128x64 display with hardware I2C and no reset pin
display.begin()                     # initialize graphics library for selected display module
display.clear()                     # clear display buffer
display.display()                   # write display buffer to physical display
displayWidth = display.width        # get width of display
displayHeight = display.height      # get height of display
image = Image.new('1', (displayWidth, displayHeight))   # create graphics library image buffer
draw = ImageDraw.Draw(image)                            # create drawing object
font = ImageFont.truetype("DejaVuSans.ttf", 20)         # load and set default font

#draw.text((0,0), "Hello,\nRaspberry Pi!", font=font, fill=255)

display.image(image)  # set display buffer with image buffer
display.display()  # write display buffer to physical display

tGraph = graph2D(originX=0,originY=29,width=79,height=30,minValue=0,maxValue=100,c=1,bars=True)
bGraph = graph2D(originX=0,originY=62,width=79,height=30,minValue=0,maxValue=100,c=1,bars=True)

for i in range(100):
    tGraph.updateGraph2D(tGraph,i)
    draw.line(tGraph.coords, 1, 1)
    print(tGraph.coords)
    display.image(image)
    display.display()

#while True:
    #tempAM = round(thermometer.get_amb_temp(), 2)
    #display.fill(0)
    #display.hline(0,30,127,1)
    #display.hline(0,63,127,1)
    #tempIR = round(thermometer.get_obj_temp(), 1)
    #tempStr = (str(tempIR))
    #display.bigtext(tempStr,x=0,y=3,c=1)
    #display.temptext(tempStr, key=0, lbl="Exhaust")
    #display.updateGraph2D(tGraph, tempIR)
    #tempIR = round(thermometer.get_obj_temp(), 1) + 65
    #tempStr = (str(tempIR))
    #display.temptext(tempStr, key=1, lbl="Manifold")
    #display.updateGraph2D(botGraph, tempIR)
    #display.show()
    #display.text(tempStr,x=0,y=32,c=1)
    
    
    
