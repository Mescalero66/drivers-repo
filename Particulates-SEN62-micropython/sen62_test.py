# Demo / test for the SEN62 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import sys
from machine import I2C, Pin
from sen62 import SEN62

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
# SDA and SCL each need an external pull-up resistor (4.7–10 kΩ) to 3.3 V, see README.md
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

SAMPLES = 10                    # readings to take (one per second)
TEMP_OFFSET = 0.0               # C added to the temperature output (slot 0), e.g. -1.5 if the enclosure runs warm
RUN_FAN_CLEANING = False        # fan at full speed for 10 s
RUN_SHT_HEATER = False          # 1 s heater pulse, then 20 s to settle before measuring


def f(v):
    return "   n/a" if v is None else "{:6.1f}".format(v)


def show(n, m, nc):
    print("#{:<3} PM1.0 {} | PM2.5 {} | PM4.0 {} | PM10 {} ug/m3 | RH {} % | T {} C".format(
        n, f(m.pm1_0), f(m.pm2_5), f(m.pm4_0), f(m.pm10_0), f(m.humidity), f(m.temperature)))
    print("     PM0.5 {} | PM1.0 {} | PM2.5 {} | PM4.0 {} | PM10 {} #/cm3".format(
        f(nc.nc0_5), f(nc.nc1_0), f(nc.nc2_5), f(nc.nc4_0), f(nc.nc10_0)))


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("  ...tick", n)


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=100_000)    # SEN62 max is 100 kHz
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    if SEN62.ADDRESS not in found:
        print("SEN62 not found at 0x6B, check wiring and pull-ups.")
        return

    ticker = asyncio.create_task(heartbeat())

    async with SEN62(i2c) as sen:                   # stop + reset takes 2.6 s
        # Identification
        print("Product name  :", await sen.get_product_name())
        print("Product type  :", await sen.get_product_type())
        print("Serial number :", await sen.get_serial_number())
        print("Firmware      : {}.{}".format(*await sen.get_version()))
        print("Device status :", await sen.read_device_status())

        # Idle-mode maintenance
        if RUN_FAN_CLEANING:
            print("\nFan cleaning (10 s)")
            await sen.start_fan_cleaning()

        if RUN_SHT_HEATER:
            print("\nSHT heater (1 s), then 20 s to settle")
            await sen.activate_sht_heater()
            rh, t = await sen.get_sht_heater_measurements()
            print("After heating : RH {} % | T {} C".format(f(rh), f(t)))
            await asyncio.sleep(20)

        await sen.set_temperature_offset_parameters(TEMP_OFFSET)

        # Continuous mode: first reading after ~1.1 s, PM values settle after ~30 s
        print("\nContinuous measurement ({} samples)".format(SAMPLES))
        await sen.start_continuous_measurement()
        for n in range(1, SAMPLES + 1):
            m = await sen.wait_measurement()
            show(n, m, await sen.read_number_concentration_values())

        rh, t = await sen.read_measured_raw_values()
        print("\nUncompensated : RH {} % | T {} C".format(f(rh), f(t)))
        print("Device status :", await sen.read_device_status())

    ticker.cancel()
    print("\nDone, sensor left idle.")


asyncio.run(main())
