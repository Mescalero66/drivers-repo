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

I2CMultiAddr = 0x70     #I2C Multiplexer addr
port = 0                #The I2C device is connected to port 0

i2cDevAddr = 24         #I2C device addr
reg = 0                 #I2C register addr

buf = [111,107]         #The information will be sent 
nbytes = 3              #The length of received data

#Create an I2C Multiplexer object, the address of I2C Multiplexer is 0X70
I2CMulti = DFRobot_I2C_Multiplexer(I2CMultiAddr)  

#Write buf to the Reg register of the I2C device on port 0
# I2CMulti.writeto_mem(port,i2cDevAddr,reg,buf)

#Read message of 3 bytes length from the Reg register of the I2C device on Port 0.
#data = I2CMulti.readfrom_mem(port,i2cDevAddr,reg,nbytes)
#print(data)