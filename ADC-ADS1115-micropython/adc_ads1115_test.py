# Demo / test for the ADS1115 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the ADC works, showing that the driver never blocks the event loop.

import sys
import time
from machine import I2C, Pin
from adc_ads1115 import ADS1115, GAINS

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# Pins per board (edit to suit your wiring). SDA and SCL need pull-up resistors, see README.md
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9
RDY_PIN = None                  # GPIO wired to ALERT/RDY (e.g. 6), or None to time conversions instead


async def heartbeat():
    """Ticks every 250 ms to show the loop stays responsive during conversions."""
    n = 0
    while True:
        await asyncio.sleep_ms(250)
        n += 1
        print("  ...tick", n)


async def timed(adc, rate):
    adc.rate = rate
    t0 = time.ticks_ms()
    v = await adc.read_voltage(0)
    return v, time.ticks_diff(time.ticks_ms(), t0)


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
    found = [a for a in i2c.scan() if a in ADS1115.ADDRESSES]
    print("ADS1115 found at:", [hex(a) for a in found])
    if not found:
        print("No ADS1115 at 0x48-0x4B, check wiring and pull-ups.")
        return

    rdy = Pin(RDY_PIN) if RDY_PIN is not None else None
    ticker = asyncio.create_task(heartbeat())

    async with ADS1115(i2c, found[0], gain=4.096, rate=128, rdy_pin=rdy) as adc:
        # Four tasks share the chip; the lock runs their conversions one after another
        volts = await asyncio.gather(*[adc.read_voltage(ch) for ch in range(4)])
        print("\nSingle-ended (+-4.096 V):", " | ".join("AIN{} {:.4f} V".format(i, v) for i, v in enumerate(volts)))
        print("Differential AIN0-AIN1  : {:.4f} V".format(await adc.read_voltage(0, 1)))

        # Gain sweep on AIN0: smaller ranges give finer steps but clip at +-full scale
        print("\nGain sweep on AIN0")
        for g in GAINS:
            adc.gain = g
            raw = await adc.read(0)
            print("  +-{:5.3f} V: raw {:6d} = {:.5f} V".format(g, raw, adc.raw_to_v(raw)))
        adc.gain = 4.096

        # Data rate: one conversion takes 1/DR
        print("\nData rate on AIN0")
        for rate in (8, 128, 860):
            v, ms = await timed(adc, rate)
            print("  {:3d} SPS: {:.4f} V in {} ms".format(rate, v, ms))

        # Continuous mode at 8 SPS for 1 s
        adc.rate = 8
        print("\nContinuous AIN0 at 8 SPS ({})".format("RDY pin" if rdy else "timed"))
        await adc.start_continuous(0)
        for n in range(8):
            print("  #{} {:.4f} V".format(n + 1, adc.raw_to_v(await adc.wait_conversion())))

    ticker.cancel()
    print("\nDone, ADC powered down.")


asyncio.run(main())
