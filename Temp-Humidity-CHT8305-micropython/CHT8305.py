# MicroPython driver for the DFRobot SEN0546 I2C Temperature & Humidity Sensor (Sensylink CHT8305C).
# Checked against the CHT8305C datasheet Rev 2.2 (Jul 2020). For an asyncio version see cht8305_async.py.

import machine
from utime import sleep_ms

class I2C_CHT8305_SEN0546:
    CHT8305_Address = 0x40      # 7-bit address, AD0 to GND (the datasheet's "0x80" is the 8-bit form)
    I2C_Delay_time = 50         # ms; a T + RH conversion takes about 11 ms (datasheet example waits 20 ms)

    # Registers
    REG_TEMPERATURE = 0x00
    REG_HUMIDITY = 0x01
    REG_CONFIG = 0x02
    REG_ALERT_SETUP = 0x03
    REG_MANUFACTURE_ID = 0xFE
    REG_VERSION_ID = 0xFF

    # Config register bit positions, counted within the MSB (config bits 15-8)
    BIT_T_RES = 2               # 1 = 11-bit, 0 = 14-bit temperature
    BIT_H_RES = 0               # 2 bits: 00 = 14-bit, 01 = 11-bit, 10 = 8-bit humidity
    BIT_VCC_LOW = 3             # VCCS, read-only: 1 = supply below 2.8 V
    BIT_ACQ_MODE = 4            # 1 = measure T then RH (default), 0 = T or RH only
    BIT_HEATER = 5
    BIT_CLKSTR = 6              # clock stretching while converting (default off)
    BIT_RESET = 7
    T_RES_14 = 0
    T_RES_11 = 1
    H_RES_14 = 0
    H_RES_11 = 1
    H_RES_8 = 2

    def __init__(self, ID, SCL, SDA):
        self.i2c = machine.I2C(id=ID, scl=machine.Pin(SCL), sda=machine.Pin(SDA), freq=100000)

    def _read_reg(self, reg):
        # set the register pointer, then read the 16-bit value MSB first (datasheet 1.5.2)
        self.i2c.writeto(self.CHT8305_Address, bytes([reg]))
        data = self.i2c.readfrom(self.CHT8305_Address, 2)
        return data[0] << 8 | data[1]

    def _write_config(self, value, label):
        self.i2c.writeto_mem(self.CHT8305_Address, self.REG_CONFIG, bytes([value >> 8, value & 0xFF]))
        sleep_ms(self.I2C_Delay_time)
        config = self._read_reg(self.REG_CONFIG)
        print(label, bin(config >> 8), bin(config & 0xFF))
        return config

    def get_CHT8305_CONFIG(self):
        config = self._read_reg(self.REG_CONFIG)
        print("ReadBuf_CHT8305_Config_Reg Status: ", bin(config >> 8), bin(config & 0xFF))
        return config

    def set_CHT8305_CONFIG_DEFAULT(self):
        # 0x1000: T then RH, 14-bit both, heater off, no clock stretching
        return self._write_config(0x1000, "ReadBuf_CHT8305_Config_Reg Default: ")

    def set_CHT8305_CONFIG_HEATER_ON(self):
        # 0x3000: default plus heater (bit 13, about 7 mA). Turn off with set_CHT8305_CONFIG_DEFAULT()
        return self._write_config(0x3000, "ReadBuf_CHT8305_Config_Reg HEATER ON: ")

    def send_CHT8305_SOFT_RESET(self):
        # bit 15 resets every register to its default; it reads back as 0 afterwards (datasheet 1.2)
        return self._write_config(0x8000, "SOFT RESET Sent to CHT8305: ")

    def get_CHT8305_MANUFACTURE_ID(self):
        mid = self._read_reg(self.REG_MANUFACTURE_ID)     # 0x5959
        print("ReadBuf_CHT8305_Manufacture_ID_Reg: ", hex(mid >> 8), hex(mid & 0xFF))
        return mid

    def get_CHT8305_VERSION_ID(self):
        vid = self._read_reg(self.REG_VERSION_ID)         # 0x8305
        print("ReadBuf_CHT8305_Version_ID_Reg: ", hex(vid >> 8), hex(vid & 0xFF))
        return vid

    def get_CHT8305_TEMPERATURE_HUMIDITY(self):
        self.req_CHT8305_TEMPERATURE_HUMIDITY()
        sleep_ms(self.I2C_Delay_time)
        return self.read_CHT8305_TEMPERATURE_HUMIDITY()

    def req_CHT8305_TEMPERATURE_HUMIDITY(self):
        # writing the pointer 0x00 starts a T + RH conversion (datasheet 1.4.2)
        try:
            self.i2c.writeto(self.CHT8305_Address, bytes([self.REG_TEMPERATURE]))
        except Exception as e:
            print("Error in req_CHT8305_TEMPERATURE_HUMIDITY function", " : {}".format(e))

    def read_CHT8305_TEMPERATURE_HUMIDITY(self):
        # 4 bytes: temperature MSB, LSB, humidity MSB, LSB. The sensor NACKs until the conversion is done.
        Temperature = None
        Humidity = None
        try:
            data = self.i2c.readfrom(self.CHT8305_Address, 4)
            temp_raw = (data[0] << 8) | data[1]
            Temperature = (temp_raw * 165 / 65535) - 40
            hum_raw = (data[2] << 8) | data[3]
            Humidity = (hum_raw / 65535) * 100
        except Exception as e:
            print("Error in read_CHT8305_TEMPERATURE_HUMIDITY function", " : {}".format(e))
        return Temperature, Humidity
