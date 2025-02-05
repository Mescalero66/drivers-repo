#
# MIT License
#
# Copyright (c) 2023 Henrik Roslund
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""!
@brief  I2C cascade module library class
"""

import machine
from utime import sleep_ms


class I2C_CHT8305_SEN0546:
    #
    # CHT8305/SEN0546
    # Decimal address:  64  | Hexa address:  0x40
    #
    CHT8305_Address = 0x40
    I2C_Delay_time = 20
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

    def __init__(self, ID, SCL, SDA):
        self.i2c = machine.I2C(
            id=ID, scl=machine.Pin(SCL), sda=machine.Pin(SDA), freq=100000
        )
        #print("Scanning i2c bus for Temp Sensors")
        #devices = self.i2c.scan()
        #if len(devices) == 0:
        #    print("No i2c device !")
        #for device in devices:
        #    print("Decimal address: ", device, " | Hexa address: ", hex(device))

    def get_CHT8305_CONFIG(self):
        ReadBuf_CHT8305_Config_Reg = bytes(self.wLength)
        com_CHT8305_Config_Reg = bytearray(2)
        com_CHT8305_Config_Reg[0] = 0x10
        com_CHT8305_Config_Reg[1] = 0x00
        # i2c.writeto_mem(CHT8305_Address, REG_CONFIG, com_CHT8305_Config_Reg)
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Config_Reg = self.i2c.readfrom(self.CHT8305_Address, 2)
        print(
            "ReadBuf_CHT8305_Config_Reg Status: ",
            bin(ReadBuf_CHT8305_Config_Reg[0]),
            bin(ReadBuf_CHT8305_Config_Reg[1]),
        )

    def set_CHT8305_CONFIG_DEFAULT(self):
        ReadBuf_CHT8305_Config_Reg = bytes(self.wLength)
        com_CHT8305_Config_Reg = bytearray(2)
        com_CHT8305_Config_Reg[0] = 0x10
        com_CHT8305_Config_Reg[1] = 0x00
        self.i2c.writeto_mem(
            self.CHT8305_Address, self.REG_CONFIG, com_CHT8305_Config_Reg
        )
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Config_Reg = self.i2c.readfrom(self.CHT8305_Address, 2)
        print(
            "ReadBuf_CHT8305_Config_Reg Default: ",
            bin(ReadBuf_CHT8305_Config_Reg[0]),
            bin(ReadBuf_CHT8305_Config_Reg[1]),
        )

    def set_CHT8305_CONFIG_HEATER_ON(self):
        ReadBuf_CHT8305_Config_Reg = bytes(self.wLength)
        com_CHT8305_Config_Reg = bytearray(2)
        com_CHT8305_Config_Reg[0] = 0x30
        com_CHT8305_Config_Reg[1] = 0x00
        self.i2c.writeto_mem(
            self.CHT8305_Address, self.REG_CONFIG, com_CHT8305_Config_Reg
        )
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Config_Reg = self.i2c.readfrom(self.CHT8305_Address, 2)
        print(
            "ReadBuf_CHT8305_Config_Reg HEATER ON: ",
            bin(ReadBuf_CHT8305_Config_Reg[0]),
            bin(ReadBuf_CHT8305_Config_Reg[1]),
        )

    def get_CHT8305_MANUFACTURE_ID(self):
        ReadBuf_CHT8305_Manufacture_ID_Reg = bytes(self.wLength)
        com_CHT8305_Manufacture_ID_Reg = bytearray(2)
        self.i2c.writeto_mem(
            self.CHT8305_Address,
            self.REG_MANUFACTURE_ID,
            com_CHT8305_Manufacture_ID_Reg,
        )
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Manufacture_ID_Reg = self.i2c.readfrom(self.CHT8305_Address, 2)
        # print("ReadBuf_CHT8305_Manufacture_ID_Reg: ", ReadBuf_CHT8305_Manufacture_ID_Reg)
        print(
            "ReadBuf_CHT8305_Manufacture_ID_Reg: ",
            hex(ReadBuf_CHT8305_Manufacture_ID_Reg[0]),
            hex(ReadBuf_CHT8305_Manufacture_ID_Reg[1]),
        )

    def get_CHT8305_VERSION_ID(self):
        ReadBuf_CHT8305_Version_ID_Reg = bytes(self.wLength)
        com_CHT8305_Version_ID_Reg = bytearray(2)
        self.i2c.writeto_mem(
            self.CHT8305_Address, self.REG_VERSION_ID, com_CHT8305_Version_ID_Reg
        )
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Version_ID_Reg = self.i2c.readfrom(self.CHT8305_Address, 2)
        print(
            "ReadBuf_CHT8305_Version_ID_Reg: ",
            hex(ReadBuf_CHT8305_Version_ID_Reg[0]),
            hex(ReadBuf_CHT8305_Version_ID_Reg[1]),
        )

    def get_CHT8305_TEMPERATURE_HUMIDITY(self):
        ReadBuf_CHT8305_Temp_Reg = bytes(self.wLength)
        ReadBuf_CHT8305_Hum_Reg = bytes(self.wLength)
        com_CHT8305_T_Reg = bytearray(4)
        com_CHT8305_H_Reg = bytearray(4)
        com_CHT8305_T_Reg[0] = self.REG_TEMPERATURE
        com_CHT8305_H_Reg[0] = self.REG_HUMIDITY
        self.i2c.writeto_mem(
            self.CHT8305_Address, self.REG_TEMPERATURE, com_CHT8305_T_Reg
        )
        sleep_ms(self.I2C_Delay_time)
        ReadBuf_CHT8305_Temp_Reg = self.i2c.readfrom(self.CHT8305_Address, 4)
        # print("ReadBuf_CHT8305_Temp_Reg: ", ReadBuf_CHT8305_Temp_Reg)
        # print("ReadBuf_CHT8305_Temp_Reg[0]: ", hex(ReadBuf_CHT8305_Temp_Reg[0]), " | ",ReadBuf_CHT8305_Temp_Reg[0])
        # print("ReadBuf_CHT8305_Temp_Reg[1]: ", hex(ReadBuf_CHT8305_Temp_Reg[1]), "| ", ReadBuf_CHT8305_Temp_Reg[1])
        # print("ReadBuf_CHT8305_Temp_Reg[2]: ", hex(ReadBuf_CHT8305_Temp_Reg[2]), "| ", ReadBuf_CHT8305_Temp_Reg[2])
        # print("ReadBuf_CHT8305_Temp_Reg[3]: ", hex(ReadBuf_CHT8305_Temp_Reg[3]), "| ", ReadBuf_CHT8305_Temp_Reg[3])
        Temperature_raw = ReadBuf_CHT8305_Temp_Reg[0] << 8 | ReadBuf_CHT8305_Temp_Reg[1]
        Temperature = (Temperature_raw * 165 / 65535) - 40
        # print("Temperature: ", Temperature)
        Humidity_prep = ReadBuf_CHT8305_Temp_Reg[2] << 8 | ReadBuf_CHT8305_Temp_Reg[3]
        Humidity = (Humidity_prep / 65535) * 100
        # print("Humidity: ", Humidity)
        return Temperature, Humidity

    def req_CHT8305_TEMPERATURE_HUMIDITY(self):
        com_CHT8305_T_Reg = bytearray(4)
        com_CHT8305_H_Reg = bytearray(4)
        com_CHT8305_T_Reg[0] = self.REG_TEMPERATURE
        com_CHT8305_H_Reg[0] = self.REG_HUMIDITY
        self.i2c.writeto_mem(
            self.CHT8305_Address, self.REG_TEMPERATURE, com_CHT8305_T_Reg
        )

    def read_CHT8305_TEMPERATURE_HUMIDITY(self):
        ReadBuf_CHT8305_Temp_Reg = bytes(self.wLength)
        ReadBuf_CHT8305_Hum_Reg = bytes(self.wLength)
        ReadBuf_CHT8305_Temp_Reg = self.i2c.readfrom(self.CHT8305_Address, 4)
        Temperature_raw = ReadBuf_CHT8305_Temp_Reg[0] << 8 | ReadBuf_CHT8305_Temp_Reg[1]
        Temperature = (Temperature_raw * 165 / 65535) - 40
        Humidity_prep = ReadBuf_CHT8305_Temp_Reg[2] << 8 | ReadBuf_CHT8305_Temp_Reg[3]
        Humidity = (Humidity_prep / 65535) * 100
        return Temperature, Humidity