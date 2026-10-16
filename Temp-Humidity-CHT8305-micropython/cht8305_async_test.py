# Demo / test for the asyncio CHT8305 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import sys
from machine import I2C, Pin
from cht8305_async import CHT8305

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

SAMPLES = 5                     # readings, one every SAMPLE_INTERVAL s
SAMPLE_INTERVAL = 2             # s (datasheet: no more than one per second, to avoid self-heating)
HEATER_SECONDS = 0              # set to e.g. 10 to watch the heater warm the probe


def show(label, m):
    print("{:<12} Temp: {:6.2f} C | RH: {:5.1f} %".format(label, m.temperature, m.humidity))


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
    candidates = [a for a in CHT8305.ADDRESSES if a in found]
    if not candidates:
        print("CHT8305 not found at 0x40/0x44/0x48/0x4C, check wiring.")
        return
    address = candidates[0]

    async with CHT8305(i2c, address) as cht:        # checks the ID; turns the heater off on exit
        await cht.soft_reset()                      # start from the power-on defaults

        # Identification and settings
        print("CHT8305 at 0x{:02X}".format(address))
        print("Manufacturer  : 0x{:04X}".format(await cht.get_manufacturer_id()))
        print("Version       : 0x{:04X}".format(await cht.get_version_id()))
        print("Config        : 0x{:04X}".format(await cht.get_config()))
        t_bits, h_bits = await cht.get_resolution()
        print("Resolution    : T {}-bit, RH {}-bit".format(t_bits, h_bits))
        print("Supply < 2.8 V:", await cht.get_supply_low())
        t_lim, h_lim = await cht.get_alert_limits()
        print("Alert limits  : {:.1f} C / {:.1f} %RH".format(t_lim, h_lim))

        ticker = asyncio.create_task(heartbeat())

        # Single conversions
        print("\nSingle conversions")
        show("T + RH", await cht.read_measurement())
        print("{:<12} Temp: {:6.2f} C".format("T only", await cht.read_temperature()))
        print("{:<12} RH: {:5.1f} %".format("RH only", await cht.read_humidity()))

        # Lower resolution: coarser steps
        await cht.set_resolution(11, 8)
        show("11 / 8-bit", await cht.read_measurement())
        await cht.set_resolution(14, 14)

        # Periodic readings
        print("\nPeriodic ({} samples, every {} s)".format(SAMPLES, SAMPLE_INTERVAL))
        for n in range(1, SAMPLES + 1):
            show("Sample {}".format(n), await cht.read_measurement())
            await asyncio.sleep(SAMPLE_INTERVAL)

        # Alert high limits, checked after each measurement
        m = await cht.read_measurement()
        await cht.set_alert_mode(CHT8305.ALERT_EITHER)
        await cht.set_alert_limits(m.temperature - 1, min(100, m.humidity + 10))
        t_lim, h_lim = await cht.get_alert_limits()
        await cht.read_measurement()
        print("\nAlert limits {:.2f} C / {:.1f} %RH (temperature already over): {}".format(
            t_lim, h_lim, await cht.get_alert_status()))
        await cht.set_alert_limits(m.temperature + 5, min(100, m.humidity + 10))
        t_lim, h_lim = await cht.get_alert_limits()
        await cht.read_measurement()
        print("Alert limits {:.2f} C / {:.1f} %RH (both under): {}".format(t_lim, h_lim, await cht.get_alert_status()))

        # Heater
        if HEATER_SECONDS:
            print("\nHeater on for {} s".format(HEATER_SECONDS))
            await cht.set_heater(True)
            for _ in range(HEATER_SECONDS // 2):
                await asyncio.sleep(2)
                show("Heater", await cht.read_measurement())
            await cht.set_heater(False)

        await cht.soft_reset()                      # limits and settings back to defaults
        ticker.cancel()
    print("\nDone.")


asyncio.run(main())
