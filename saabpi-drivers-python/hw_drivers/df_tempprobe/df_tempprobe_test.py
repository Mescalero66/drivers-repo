import time
import smbus2
import df_tempprobe_j
import RPi.GPIO as GPIO


open(1)
i2c = smbus2.SMBus(1)

time.sleep(1)
i2c = df_tempprobe_j.testRead()
print(df_tempprobe_j.testRead)

i2c = df_tempprobe_j.get_CHT8305_TEMPERATURE_HUMIDITY()
