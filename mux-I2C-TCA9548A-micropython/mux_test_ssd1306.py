# import time, sys, framebuf, Pin, I2C
from mux import I2CMultiplex
from ssd1306 import SSD1306_I2C

I2CMultiAddr = 0x70

pix_res_x  = 128 # SSD1306 horizontal resolution
pix_res_y = 64   # SSD1306 vertical resolution

OLEDAddr = 0x3C
OLEDCount = 8
OLEDs = []   

# Create multiplexer object
mux = I2CMultiplex(I2CMultiAddr, I2Cbus=1, scl_pin=15, sda_pin=14)
# Use mux.i2c as the shared I2C bus for OLEDs

# define OLEDs
for i in range(OLEDCount):
    mux.select_port(i)
    OLEDs.append(SSD1306_I2C(pix_res_x, pix_res_y, mux.i2c))

for i in range(OLEDCount):
    mux.select_port(i)
    OLEDs[i].fill(0)
    text = f"OLED # {i}"
    OLEDs[i].banner_text_inverted(text)
    date = f"2{i}/12"
    OLEDs[i].date_text(date)
    year = "2025"
    OLEDs[i].year_text(year)
    OLEDs[i].show()

for i in range(OLEDCount):
    mux.select_port(i)
    OLEDs[i].fill(0)
    text = "Wednesday"
    OLEDs[i].banner_text(text)
    date = f"1{i}/11"
    OLEDs[i].date_text(date)
    year = "2025"
    OLEDs[i].year_text(year)
    OLEDs[i].show()

