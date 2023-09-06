# The MIT License (MIT)
# 
# Test Code for Python Driver for:
# DFRobot DFR0576 I2C Multiplexer <https://wiki.dfrobot.com/Gravity__Digital_1-to-8_I2C_Multiplexer_SKU_DFR0576>
#
# Shout out to the DFRobot GitHub <https://github.com/DFRobot/DFRobot_I2C_Multiplexer/blob/main/raspberrypi/DFRobot_I2C_Multiplexer.py>

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from df_multiplexer import DFRobot_I2C_Multiplexer

I2CMultiAddr = 0x70       #I2C Multiplexer addr

I2CMulti = DFRobot_I2C_Multiplexer(I2CMultiAddr)
for Port in range(0,8):   #Scan i2C devices of each port
  print("Port:%s" %Port)
  addr = I2CMulti.scan(Port)
  if(len(addr)):
    print("i2c addr:%s" %addr)