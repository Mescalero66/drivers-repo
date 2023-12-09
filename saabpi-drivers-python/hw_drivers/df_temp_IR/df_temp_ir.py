# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.0 - Released 20231209
# 
# Python Driver for:
# DFRobot SEN0206 I2C Infrared Temperature Sensor (MLX90614) Chip
# <https://wiki.dfrobot.com/IR_Thermometer_Sensor_MLX90614_SKU__SEN0206>
#
# Shout outs to: 
# <https://github.com/CRImier/python-MLX90614>
# <https://github.com/sightsdev/PyMLX90614/>

import smbus2
from time import sleep

addr=0x5A

class MLX90614():

    # RAM offsets with 16-bit data, MSB first
    MLX90614_RAWIR1 = 0x04          # Raw data IR channel 1
    MLX90614_RAWIR2 = 0x05          # Raw data IR channel 2
    MLX90614_TA = 0x06              # Ambient temperature
    MLX90614_TOBJ1 = 0x07           # Object 1 temperature
    MLX90614_TOBJ2 = 0x08           # Object 2 temperature

    # EEPROM offsets with 16-bit data, MSB first
    MLX90614_TOMAX = 0x20           # Object temperature max register
    MLX90614_TOMIN = 0x21           # Object temperature min register
    MLX90614_PWMCTRL = 0x22         # PWM configuration register
    MLX90614_TARANGE = 0x23         # Ambient temperature register
    MLX90614_EMISS = 0x24           # Emissivity correction register
    MLX90614_CONFIG = 0x25          # Configuration register 
    MLX90614_ADDR = 0x2E            # Slave address register   
    MLX90614_ID1 = 0x3C             # 1 ID register (read-only)
    MLX90614_ID2 = 0x3D             # 2 ID register (read-only)
    MLX90614_ID3 = 0x3E             # 3 ID register (read-only)
    MLX90614_ID4 = 0x3F             # 3 ID register (read-only)

    comm_retries = 5
    comm_sleep_amount = 0.1

    def __init__(self, bus, addr=0x5A):
        self.bus = bus
        self.addr = addr
    
    def read_reg(self, register_addr):
        err = None
        for i in range(self.comm_retries):
            try:
                return self.bus.read_word_data(self.addr, register_addr)
            except IOError as e:
                err = e
                # sleeping to prevent problems with sensor when requesting data too quickly
                sleep(self.comm_sleep_amount)
        # By this time, we made a couple requests and the sensor didn't respond
        # (judging by the fact we haven't returned from this function yet)
        # So let's just re-raise the last IOError we got
        raise err

    def data_to_temp(self, reg):
        data = self.read_reg(reg)
        temp = (data * 0.02) - 273.15
        return temp

    def get_amb_temp(self):
        return self.data_to_temp(self.MLX90614_TA)

    def get_obj_temp(self):
        return self.data_to_temp(self.MLX90614_TOBJ1)
    
    def get_obj2_temp(self):
        return self.data_to_temp(self.MLX90614_TOBJ2)

if __name__ == "__main__":
    sensor = MLX90614()
    print(sensor.get_amb_temp())
    print(sensor.get_obj_temp())
    print(sensor.get_obj2_temp())