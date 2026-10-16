# Demo / test for the BMP280 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import sys
import time
from machine import I2C, Pin
from bmp280 import BMP280

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

SEA_LEVEL_HPA = 1013.25         # local QNH for absolute altitude (from a weather service); 1013.25 = standard atmosphere
NORMAL_SAMPLES = 30             # normal-mode readings (about 10 per second with the "handheld_low_power" preset)

# Oversampling settings from Table 4: name, pressure, temperature
SWEEP = (("Ultra low pwr", 1, 1), ("Low power", 2, 1), ("Standard", 4, 1),
         ("High res", 8, 1), ("Ultra high", 16, 2))


def show(label, m):
    t = "  --  " if m.temperature is None else "{:6.2f}".format(m.temperature)
    if m.pressure is None:
        print("{:<14} T: {} C | P:    (skipped)".format(label, t))
    else:
        alt = BMP280.altitude(m.pressure, SEA_LEVEL_HPA * 100)
        print("{:<14} T: {} C | P: {:7.2f} hPa | Alt: {:7.1f} m".format(label, t, m.pressure / 100, alt))


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("  ...tick", n)


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    address = None
    for a in (0x76, 0x77):                          # 0x76: SDO low (generic boards), 0x77: SDO high
        if a in found:
            address = a
            break
    if address is None:
        print("BMP280 not found at 0x76 / 0x77, check wiring.")
        return

    async with BMP280(i2c, address) as bmp:        # resets, checks the chip ID, reads the calibration
        # Identification and settings after init()
        chip = await bmp.get_chip_id()
        p, t = await bmp.get_oversampling()
        print("Address       : 0x{:02X}".format(address))
        print("Chip ID       : 0x{:02X} ({})".format(chip, BMP280.CHIP_IDS[chip]))
        print("Oversampling  : P x{} / T x{}".format(p, t))
        print("IIR filter    :", await bmp.get_filter())
        print("Standby       :", await bmp.get_standby(), "ms")

        ticker = asyncio.create_task(heartbeat())

        # Forced mode: one measurement per call, then back to sleep. More oversampling takes longer.
        print("\nForced mode, oversampling sweep (Table 4)")
        for name, osrs_p, osrs_t in SWEEP:
            await bmp.set_oversampling(osrs_p, osrs_t)
            start = time.ticks_ms()
            m = await bmp.measure_single_shot()
            show(name, m)
            print("{:<14} x{} / x{}, took {} ms (max {:.1f} ms)".format(
                "", osrs_p, osrs_t, time.ticks_diff(time.ticks_ms(), start), bmp.measurement_ms()))

        # Pressure skipped: the sensor works as a thermometer only (and measures faster)
        await bmp.set_oversampling(0, 1)
        show("Temp only", await bmp.measure_single_shot())

        # Normal mode: the sensor measures continuously; the IIR filter smooths out short disturbances
        await bmp.apply_preset("handheld_low_power")
        print("\nNormal mode, 'handheld_low_power' preset: P x16 / T x2, IIR {}, standby {} ms, ~{:.1f} Hz".format(
            await bmp.get_filter(), await bmp.get_standby(), bmp.output_data_rate()))
        print("(raise or lower the sensor to see the height change)")
        ref = None
        for n in range(1, NORMAL_SAMPLES + 1):
            m = await bmp.wait_measurement()
            alt = BMP280.altitude(m.pressure)
            if ref is None:
                ref = alt
            print("Normal {:<7d} T: {:6.2f} C | P: {:9.2f} Pa | dh: {:+6.2f} m".format(
                n, m.temperature, m.pressure, alt - ref))

        ticker.cancel()
    print("\nDone, sensor left in sleep mode.")


asyncio.run(main())
