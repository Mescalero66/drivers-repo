# Demo / test for the SCD41 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import sys
from machine import I2C, Pin
from scd41 import SCD41

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

PERIODIC_SAMPLES = 3            # periodic readings to take (one every 5 s)
RUN_SELF_TEST = False           # self test takes 10 s


def show(label, m):
    print("{:<12} CO2: {:5d} ppm | Temp: {:5.1f} C | RH: {:5.1f} %".format(label, m.co2, m.temperature, m.humidity))


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("  ...tick", n)


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=100_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    if SCD41.ADDRESS not in found:
        print("SCD41 not found at 0x62, check wiring.")
        return

    async with SCD41(i2c) as scd:
        # Identification
        print("Serial number : 0x{:012X}".format(await scd.get_serial_number()))
        print("Sensor variant:", await scd.get_sensor_variant())

        # Current configuration (read-only, nothing is written to EEPROM)
        print("Temp offset   : {:.2f} C".format(await scd.get_temperature_offset()))
        print("Altitude      :", await scd.get_sensor_altitude(), "m")
        print("ASC enabled   :", await scd.get_automatic_self_calibration_enabled())
        print("ASC target    :", await scd.get_automatic_self_calibration_target(), "ppm")

        ticker = asyncio.create_task(heartbeat())

        # Periodic mode: first reading arrives about 5 s after starting
        print("\nPeriodic mode ({} samples)".format(PERIODIC_SAMPLES))
        await scd.start_periodic_measurement()
        for n in range(1, PERIODIC_SAMPLES + 1):
            show("Periodic {}".format(n), await scd.wait_measurement())
        await scd.stop_periodic_measurement()

        # Single-shot mode (SCD41/SCD43 only)
        print("\nSingle shot (5 s)")
        show("Single", await scd.measure_single_shot())
        show("RH/T only", await scd.measure_single_shot_rht_only())

        if RUN_SELF_TEST:
            print("\nSelf test (10 s)")
            print("Self test:", "PASS" if await scd.perform_self_test() else "FAIL")

        ticker.cancel()
    print("\nDone, sensor left idle.")


asyncio.run(main())
