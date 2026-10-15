# Demo / test for the BH1750 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# Takes one-time readings in each resolution, sweeps MTreg, then streams continuous readings while a
# monitor task shares the sensor. A heartbeat task records the longest gap between its ticks: a driver
# that blocked the event loop during a conversion would push that gap up to the measurement time.

import sys
import time
from machine import I2C, Pin
from bh1750 import BH1750

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

CONTINUOUS_SAMPLES = 10
MONITOR_INTERVAL_MS = 500
HEARTBEAT_MS = 20

RES_NAMES = {BH1750.RES_LOW: "L  (4 lx)", BH1750.RES_HIGH: "H  (1 lx)", BH1750.RES_HIGH2: "H2 (0.5 lx)"}

max_gap_ms = 0


async def heartbeat():
    global max_gap_ms
    last = time.ticks_ms()
    while True:
        await asyncio.sleep_ms(HEARTBEAT_MS)
        now = time.ticks_ms()
        max_gap_ms = max(max_gap_ms, time.ticks_diff(now, last))
        last = now


async def monitor(bh):
    """Reads the latest value alongside the sampler, sharing the bus via the driver's lock."""
    while True:
        await asyncio.sleep_ms(MONITOR_INTERVAL_MS)
        print("    monitor: {:.2f} lx".format(await bh.read_lux()))


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    address = next((a for a in (BH1750.ADDRESS, BH1750.ADDRESS_ALT) if a in found), None)
    if address is None:
        print("BH1750 not found at 0x23 or 0x5C, check wiring.")
        return

    async with BH1750(i2c, address) as bh:          # powers on, sets MTreg to 69; powers down on exit
        print("BH1750 at 0x{:02X}".format(address))

        # One-time mode: the sensor powers itself down after each reading
        print("\nOne-time measurements (MTreg {})".format(bh.mtreg))
        for res in (BH1750.RES_LOW, BH1750.RES_HIGH, BH1750.RES_HIGH2):
            start = time.ticks_ms()
            lux = await bh.measure(res)
            print("  {:<12} {:9.2f} lx  ({:.3f} lx/count, took {} ms)".format(
                RES_NAMES[res], lux, bh.lux_per_count(res), time.ticks_diff(time.ticks_ms(), start)))

        # MTreg trades range for resolution: the reading should stay about the same, the step size changes
        print("\nMTreg sweep (H2 one-time)")
        for mt in (BH1750.MTREG_MIN, BH1750.MTREG_DEFAULT, BH1750.MTREG_MAX):
            await bh.set_mtreg(mt)
            lux = await bh.measure(BH1750.RES_HIGH2)
            print("  MTreg {:3d}: {:9.2f} lx  ({:.3f} lx/count, up to {} ms, max {:.0f} lx)".format(
                mt, lux, bh.lux_per_count(), bh.measurement_time_ms(), 65535 * bh.lux_per_count()))
        await bh.set_mtreg(BH1750.MTREG_DEFAULT)

        # Continuous mode with a second task reading the same sensor
        print("\nContinuous H mode ({} samples)".format(CONTINUOUS_SAMPLES))
        await bh.start_continuous(BH1750.RES_HIGH)
        ticker = asyncio.create_task(heartbeat())
        watcher = asyncio.create_task(monitor(bh))
        for n in range(1, CONTINUOUS_SAMPLES + 1):
            print("{:>2} {:9.2f} lx".format(n, await bh.wait_lux()))
        watcher.cancel()
        ticker.cancel()

    print("-----")
    print("Longest heartbeat gap: {} ms (every {} ms requested; a blocking driver would show ~{} ms).".format(
        max_gap_ms, HEARTBEAT_MS, bh.measurement_time_ms()))
    print("Done, sensor powered down.")


asyncio.run(main())
