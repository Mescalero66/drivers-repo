# The MIT License (MIT)
# 
# Python Driver for:
# DFRobot SEN0546 I2C Temperature & Humidity Sensor <https://wiki.dfrobot.com/SKU_SEN0546_I2C_Temperature_and_Humidity_Sensor_Stainless_Steel_Shell>
#
# Shout out to Loztal <https://github.com/Loztal/CHT8305_SEN0546>

from smbus2 import SMBus
from time import sleep
import RPi.GPIO as GPIO

i2c=SMBus(1)

###########################
# CHT8305/SEN0546
# Decimal address:  64  | Hexa address:  0x40
###########################

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

def get_CHT8305_CONFIG ():
    ReadBuf_CHT8305_Config_Reg = bytes(wLength)
    com_CHT8305_Config_Reg = bytearray(2)
    com_CHT8305_Config_Reg[0] = 0x10
    com_CHT8305_Config_Reg[1] = 0x00
    #i2c.write_i2c_block_data(CHT8305_Address, REG_CONFIG, com_CHT8305_Config_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Config_Reg = i2c.read_i2c_block_data(CHT8305_Address, 2)
    print("ReadBuf_CHT8305_Config_Reg Status: ",bin(ReadBuf_CHT8305_Config_Reg[0]),bin(ReadBuf_CHT8305_Config_Reg[1]))
    
def set_CHT8305_CONFIG_DEFAULT ():
    ReadBuf_CHT8305_Config_Reg = bytes(wLength)
    com_CHT8305_Config_Reg = bytearray(2)
    com_CHT8305_Config_Reg[0] = 0x10
    com_CHT8305_Config_Reg[1] = 0x00
    i2c.write_i2c_block_data(CHT8305_Address, REG_CONFIG, com_CHT8305_Config_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Config_Reg = i2c.read_i2c_block_data(CHT8305_Address, 2)
    print("ReadBuf_CHT8305_Config_Reg Default: ",bin(ReadBuf_CHT8305_Config_Reg[0]),bin(ReadBuf_CHT8305_Config_Reg[1]))
    
def set_CHT8305_CONFIG_HEATER_ON ():
    ReadBuf_CHT8305_Config_Reg = bytes(wLength)
    com_CHT8305_Config_Reg = bytearray(2)
    com_CHT8305_Config_Reg[0] = 0x30
    com_CHT8305_Config_Reg[1] = 0x00
    i2c.write_i2c_block_data(CHT8305_Address, REG_CONFIG, com_CHT8305_Config_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Config_Reg = i2c.read_i2c_block_data(CHT8305_Address, 2)
    print("ReadBuf_CHT8305_Config_Reg HEATER ON: ",bin(ReadBuf_CHT8305_Config_Reg[0]),bin(ReadBuf_CHT8305_Config_Reg[1]))

def get_CHT8305_MANUFACTURE_ID ():
    ReadBuf_CHT8305_Manufacture_ID_Reg = bytes(wLength)
    com_CHT8305_Manufacture_ID_Reg = bytearray(2)
    i2c.write_i2c_block_data(CHT8305_Address, REG_MANUFACTURE_ID, com_CHT8305_Manufacture_ID_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Manufacture_ID_Reg = i2c.read_i2c_block_data(CHT8305_Address, 2)
    #print("ReadBuf_CHT8305_Manufacture_ID_Reg: ", ReadBuf_CHT8305_Manufacture_ID_Reg)
    print("ReadBuf_CHT8305_Manufacture_ID_Reg: ", hex(ReadBuf_CHT8305_Manufacture_ID_Reg[0]), hex(ReadBuf_CHT8305_Manufacture_ID_Reg[1]))

def get_CHT8305_VERSION_ID ():
    ReadBuf_CHT8305_Version_ID_Reg = bytes(wLength)
    com_CHT8305_Version_ID_Reg = bytearray(2)
    i2c.write_i2c_block_data(CHT8305_Address, REG_VERSION_ID, com_CHT8305_Version_ID_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Version_ID_Reg = i2c.read_i2c_block_data(CHT8305_Address, 2)
    print("ReadBuf_CHT8305_Version_ID_Reg: ", hex(ReadBuf_CHT8305_Version_ID_Reg[0]), hex(ReadBuf_CHT8305_Version_ID_Reg[1]))
    
def get_CHT8305_TEMPERATURE_HUMIDITY ():
    ReadBuf_CHT8305_Temp_Reg = bytes(wLength)
    ReadBuf_CHT8305_Hum_Reg = bytes(wLength)
    com_CHT8305_T_Reg = bytearray(4)
    com_CHT8305_H_Reg = bytearray(4)
    com_CHT8305_T_Reg[0]=REG_TEMPERATURE
    com_CHT8305_H_Reg[0]=REG_HUMIDITY
    i2c.write_i2c_block_data(CHT8305_Address, REG_TEMPERATURE, com_CHT8305_T_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Temp_Reg = i2c.read_i2c_block_data(CHT8305_Address, 4)
    #print("ReadBuf_CHT8305_Temp_Reg: ", ReadBuf_CHT8305_Temp_Reg)
    #print("ReadBuf_CHT8305_Temp_Reg[0]: ", hex(ReadBuf_CHT8305_Temp_Reg[0]), " | ",ReadBuf_CHT8305_Temp_Reg[0])
    #print("ReadBuf_CHT8305_Temp_Reg[1]: ", hex(ReadBuf_CHT8305_Temp_Reg[1]), "| ", ReadBuf_CHT8305_Temp_Reg[1])
    #print("ReadBuf_CHT8305_Temp_Reg[2]: ", hex(ReadBuf_CHT8305_Temp_Reg[2]), "| ", ReadBuf_CHT8305_Temp_Reg[2])
    #print("ReadBuf_CHT8305_Temp_Reg[3]: ", hex(ReadBuf_CHT8305_Temp_Reg[3]), "| ", ReadBuf_CHT8305_Temp_Reg[3])
    Temperature_raw = ReadBuf_CHT8305_Temp_Reg[0] << 8 | ReadBuf_CHT8305_Temp_Reg[1]
    Temperature = (Temperature_raw *165/65535)-40
    print("Temperature: ", Temperature)
    Humidity_prep = ReadBuf_CHT8305_Temp_Reg[2] << 8 | ReadBuf_CHT8305_Temp_Reg[3]
    Humidity = (Humidity_prep /65535)*100
    print("Humidity: ", Humidity)

def get_CHT8305_HUMIDITY ():
    ReadBuf_CHT8305_Hum_Reg = bytes(wLength)
    com_CHT8305_H_Reg = bytearray(4)
    com_CHT8305_H_Reg[0]=REG_HUMIDITY
    i2c.write_i2c_block_data(CHT8305_Address, REG_HUMIDITY, com_CHT8305_H_Reg)
    sleep(I2C_Delay_time)
    ReadBuf_CHT8305_Hum_Reg = i2c.read_i2c_block_data(CHT8305_Address, 4)
    Humidity_prep = ReadBuf_CHT8305_Hum_Reg[0] << 8 | ReadBuf_CHT8305_Hum_Reg[1]
    Humidity = (Humidity_prep /65535)*100
    print("Humidity: ", Humidity)