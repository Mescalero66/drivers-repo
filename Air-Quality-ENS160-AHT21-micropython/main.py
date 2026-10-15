# Demo for ENS160_AHT21.py: a Raspberry Pi Pico reading an ENS160 + AHT21 board on I2C1 (GP2 SDA, GP3 SCL).
from machine import I2C, Pin
import time
from ENS160_AHT21 import ENS160_AHT21, ENS160

READ_INTERVAL_S = 2

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100_000)     # <= 400 kHz for the AHT21
print("I2C devices:", [hex(a) for a in i2c.scan()])

board = ENS160_AHT21(i2c)
board.begin()
print("ENS160 at 0x{:02X}, firmware {}".format(board.ens160.address, board.ens160.firmware_version()))
print("-----")

while True:
    try:
        r = board.read()
        print("AQI {} ({}) | TVOC {:5d} ppb | eCO2 {:5d} ppm ({}) | PCB {:4.1f}°C {:4.1f}%RH | {}".format(
            r.aqi, ENS160.AQI_RATING[r.aqi] if 1 <= r.aqi <= 5 else "?",
            r.tvoc, r.eco2, ENS160.eco2_rating(r.eco2),
            r.pcb_temp, r.pcb_humi, ENS160.VALIDITY[r.validity]))
    except OSError as e:
        print("Read failed:", e)
    time.sleep(READ_INTERVAL_S)
