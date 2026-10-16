# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# v1.2 - checked against the Sensylink CHT8305C datasheet Rev 2.2 (Jul 2020): reads both data bytes,
#        sends only the register pointer to trigger a conversion, honours the bus number
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
    CHT8305_Address = 0x40              # temp sensor's 7-bit I2C address (the datasheet's "0x80" is the 8-bit form)
    I2C_Delay_time = 0.1               # wait time between requesting temp and reading temp from sensor (needs > 20 ms)

    # Registers fixed values

    REG_TEMPERATURE = 0x00
    REG_HUMIDITY = 0x01
    REG_CONFIG = 0x02
    REG_ALERT_SETUP = 0x03
    REG_MANUFACTURE_ID = 0xFE
    REG_VERSION_ID = 0xFF

    # Config register bit positions, counted within the MSB (config bits 15-8)
    BIT_T_RES = 2                       # 1 = 11-bit, 0 = 14-bit temperature
    BIT_H_RES = 0                       # 2 bits: 00 = 14-bit, 01 = 11-bit, 10 = 8-bit humidity
    BIT_VCC_LOW = 3                     # VCCS, read-only: 1 = supply below 2.8 V
    BIT_ACQ_MODE = 4                    # 1 = measure T then RH (default), 0 = T or RH only
    BIT_HEATER = 5
    BIT_CLKSTR = 6                      # clock stretching while converting (default off)
    BIT_RST = 7
    T_RES_14 = 0
    T_RES_11 = 1
    H_RES_14 = 0
    H_RES_11 = 1
    H_RES_8 = 2

    def __init__(self, ID):
        self.i2c = smbus2.SMBus(ID)     # create I2C object for the temp probe, on I2C bus ID (1 on a Raspberry Pi)

    def close(self):
        self.i2c.close()

    def _trigger(self, reg):
        # writing the register pointer 0x00 / 0x01 starts a conversion (datasheet 1.4.2).
        # The I2C hardware sends the address byte itself, so only the pointer is written.
        self.i2c.write_byte(self.CHT8305_Address, reg)

    def _read_word(self):
        # both data bytes must be read together, MSB first (datasheet 1.1.1). The sensor NACKs until the conversion is done.
        msg = smbus2.i2c_msg.read(self.CHT8305_Address, 2)
        self.i2c.i2c_rdwr(msg)
        msb, lsb = list(msg)
        return msb << 8 | lsb

    def get_Temp(self):                                         # define function get_temp
        self._trigger(self.REG_TEMPERATURE)                     # start a measurement
        sleep(self.I2C_Delay_time)                              # wait for sensor to measure
        return self.read_Temp()                                 # read and convert it

    def req_Temp(self):                                         # define function req_temp
        self._trigger(self.REG_TEMPERATURE)                     # start a measurement, read it later with read_Temp()

    def read_Temp(self):
        rTRaw = self._read_word()                               # read the 16-bit result out of the device
        rTCalc = rTRaw * 165 / 65535 - 40                       # datasheet formula (1)
        return rTCalc                                           # send it back

    def get_Humi(self):                                         # define function get_humi
        self._trigger(self.REG_HUMIDITY)                        # start a measurement
        sleep(self.I2C_Delay_time)                              # wait for sensor to measure
        return self.read_Humi()                                 # read and convert it

    def req_Humi(self):                                         # define function req_humi
        self._trigger(self.REG_HUMIDITY)                        # start a measurement, read it later with read_Humi()

    def read_Humi(self):                                        # define function read_humi
        rHRaw = self._read_word()                               # read the 16-bit result out of the device
        rHCalc = rHRaw * 100 / 65535                            # datasheet formula (2)
        return rHCalc                                           # send it back
