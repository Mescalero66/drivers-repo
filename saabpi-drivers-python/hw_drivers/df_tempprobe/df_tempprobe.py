# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.0 - Released 20231209
# 
# Python Driver for:
# DFRobot SEN0546 I2C Temperature & Humidity Sensor (Sensylink CHT8305C Chip)
# <https://wiki.dfrobot.com/SKU_SEN0546_I2C_Temperature_and_Humidity_Sensor_Stainless_Steel_Shell>
#
# Yet another DFRobot component with no fucking information about it, and no fucking code examples on GitHub anywhere

import smbus2
from time import sleep

class tempprobe:
    #
    # CHT8305 / SEN0546
    # Decimal address:  64  | Hexa address:  0x40
    #
    CHT8305_Address = 0x40              # temp sensor's I2C address
    I2C_Delay_time = 0.1               # wait time between requesting temp and reading temp from sensor

    # Registers fixed values

    REG_TEMPERATURE = 0x00              
    REG_HUMIDITY = 0x01
    REG_CONFIG = 0x02
    REG_ALERT_SETUP = 0x03
    REG_MANUFACTURE_ID = 0xFE
    REG_VERSION_ID = 0xFF

    BIT_T_RES = 2
    BIT_H_RES = 0
    BIT_BATTERY_OK = 3
    BIT_ACQ_MODE = 4
    BIT_HEATER = 5
    BIT_RST = 7
    T_RES_14 = 0
    T_RES_11 = 1
    H_RES_14 = 0
    H_RES_11 = 1
    H_RES_8 = 2

    wLength = 0
	
    def __init__(self, ID):
        self.i2c = smbus2.SMBus(1)      # create I2C object for the temp probe

    def get_Temp(self):                                         # define function get_temp
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_TEMPERATURE,0x80)
            # to I2C device (0x40), at the TEMP Register, write the 7-bit I2C address and WRITE flag (together 1000000, or 0x80))
        sleep(self.I2C_Delay_time)                              # wait for sensor to measure
        rTBinary = self.i2c.read_byte(self.CHT8305_Address)     # read the result out of the device (binary byte)
        rTBitShift = rTBinary << 8                              # bitshift the binary to get a number
        rTCalc = rTBitShift * 165 / 65535 - 40                  # do the required maths to it
        return rTCalc                                           # send it back
    
    def req_Temp(self):                                         # define function req_temp
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_TEMPERATURE,0x80)
            # to I2C device (0x40), at the TEMP Register, write the 7-bit I2C address and WRITE flag (together 1000000, or 0x80))
        #sleep(self.I2C_Delay_time)                              # wait for sensor to measure

    def read_Temp(self):
        rTBinary = self.i2c.read_byte(self.CHT8305_Address)     # read the result out of the device (binary byte)
        rTBitShift = rTBinary << 8                              # bitshift the binary to get a number
        rTCalc = rTBitShift * 165 / 65535 - 40                  # do the required maths to it
        return rTCalc                                           # send it back

    def get_Humi(self):                                         # define function get_humi
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_HUMIDITY,0x80)
            # to I2C device (0x40), at the HUMI Register, write the 7-bit I2C address and WRITE flag (together 1000000, or 0x80))
        sleep(self.I2C_Delay_time)                              # wait for sensor to measure
        rHBinary = self.i2c.read_byte(self.CHT8305_Address)     # read the result out of the device (binary byte)
        rHBitShift = rHBinary << 8                              # bitshift the binary to get a number
        rHCalc = rHBitShift * 100 / 65535                       # do the required maths to it
        return rHCalc                                           # send it back
    
    def req_Humi(self):                                         # define function req_humi
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_HUMIDITY,0x80)
            # to I2C device (0x40), at the HUMI Register, write the 7-bit I2C address and WRITE flag (together 1000000, or 0x80))
        #sleep(self.I2C_Delay_time)                              # wait for sensor to measure
    
    def read_Humi(self):                                        # define function read_humi
        rHBinary = self.i2c.read_byte(self.CHT8305_Address)     # read the result out of the device (binary byte)
        rHBitShift = rHBinary << 8                              # bitshift the binary to get a number
        rHCalc = rHBitShift * 100 / 65535                       # do the required maths to it
        return rHCalc                                           # send it back