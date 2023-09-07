# The MIT License (MIT)
# 
# Python Driver for:
# DFRobot SEN0546 I2C Temperature & Humidity Sensor (Sensylink CHT8305C Chip)
# <https://wiki.dfrobot.com/SKU_SEN0546_I2C_Temperature_and_Humidity_Sensor_Stainless_Steel_Shell>
#
# Yet another DFRobot component with no fucking information about it, and no fucking code examples on GitHub anywhere

import smbus2
from time import sleep

class df_tempprobe:
    #
    # CHT8305 / SEN0546
    # Decimal address:  64  | Hexa address:  0x40
    #
    CHT8305_Address = 0x40
    I2C_Delay_time = 0.02

    # Registers

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
        self.i2c = smbus2.SMBus(1)

    def get_Temp(self):
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_TEMPERATURE,0x80)
        sleep(self.I2C_Delay_time)
        rTBinary = self.i2c.read_byte(self.CHT8305_Address)
        rTBitShift = rTBinary << 8
        rTCalc = rTBitShift * 165 / 65535 - 40
        return rTCalc

    def get_Humi(self):
        self.i2c.write_byte_data(self.CHT8305_Address,self.REG_HUMIDITY,0x80)
        sleep(self.I2C_Delay_time)
        rHBinary = self.i2c.read_byte(self.CHT8305_Address)
        rHBitShift = rHBinary << 8
        rHCalc = rHBitShift * 100 / 65535
        return rHCalc