# Demo for ens160_aht21.py: a Raspberry Pi reading an ENS160 + AHT21 board on I2C bus 1 (GPIO2 SDA, GPIO3 SCL).
import time
from ens160_aht21 import I2C, ENS160_AHT21, ENS160

I2C_BUS = 1
READ_INTERVAL_S = 2

with I2C(I2C_BUS) as i2c:
    board = ENS160_AHT21(i2c)
    board.begin()
    print(f"ENS160 at 0x{board.ens160.address:02X}, firmware {board.ens160.firmware_version()}")
    print("-----")

    try:
        while True:
            try:
                r = board.read()
                aqi_text = ENS160.AQI_RATING[r.aqi] if 1 <= r.aqi <= 5 else "?"
                print(f"AQI {r.aqi} ({aqi_text}) | TVOC {r.tvoc:5d} ppb | "
                      f"eCO2 {r.eco2:5d} ppm ({ENS160.eco2_rating(r.eco2)}) | "
                      f"PCB {r.pcb_temp:4.1f}°C {r.pcb_humi:4.1f}%RH | {ENS160.VALIDITY[r.validity]}")
            except OSError as e:
                print("Read failed:", e)
            time.sleep(READ_INTERVAL_S)
    except KeyboardInterrupt:
        print()
