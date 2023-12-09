# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.0 - Released 20231209
#
# Saabpi Project 2023
#
# Display RPM Test

import time
from hw_drivers.df_digitdisp.tm1650disp import dfDisp
from hw_drivers.ignitionpulsecounter.read_RPM import reader
import RPi.GPIO as GPIO
import pigpio

# connect to display's clockPin & dataPin
d1SDA = 16
d1SCL = 17
displayID = 1

disp1 = dfDisp(displayID, d1SCL, d1SDA)
disp1.display_on(0)

# specify GPIO Digital Pin of incoming Pulse signal
RPM_GPIO = 6
RUN_TIME = 600.0
SAMPLE_TIME = 0.01

pi = pigpio.pi()

p = reader(pi, RPM_GPIO)

start = time.time()
while (time.time() - start) < RUN_TIME:
      time.sleep(SAMPLE_TIME)
      RPM = p.RPM()     
      print("RPM={}".format(int(RPM)))
      disp1.show_string(format(int(RPM)))

p.cancel()
pi.stop()
disp1.display_clear()

disp1.show_string("5aab")


