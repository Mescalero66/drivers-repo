# Demo / test for the BH1750 driver on a Raspberry Pi (I2C bus 1).
# Takes one-time readings in each resolution, sweeps MTreg, then streams continuous readings while a
# monitor task shares the sensor. A heartbeat task records the longest gap between its ticks: a driver
# that blocked the event loop during a conversion would push that gap up to the measurement time.

import asyncio
import time

from smbus2 import SMBus, i2c_msg

from bh1750 import BH1750

I2C_BUS = 1
CONTINUOUS_SAMPLES = 10
MONITOR_INTERVAL = 0.5          # s
HEARTBEAT = 0.02                # s

RES_NAMES = {BH1750.RES_LOW: "L  (4 lx)", BH1750.RES_HIGH: "H  (1 lx)", BH1750.RES_HIGH2: "H2 (0.5 lx)"}

max_gap = 0.0


def find_address(bus):
    """The BH1750 has no ID register, so probe both addresses with a harmless POWER_ON."""
    with SMBus(bus) as smb:
        for address in (BH1750.ADDRESS, BH1750.ADDRESS_ALT):
            try:
                smb.i2c_rdwr(i2c_msg.write(address, [BH1750.POWER_ON]))
                return address
            except OSError:
                pass
    return None


async def heartbeat():
    global max_gap
    last = time.monotonic()
    while True:
        await asyncio.sleep(HEARTBEAT)
        now = time.monotonic()
        max_gap = max(max_gap, now - last)
        last = now


async def monitor(bh):
    """Reads the latest value alongside the sampler, sharing the bus via the driver's lock."""
    while True:
        await asyncio.sleep(MONITOR_INTERVAL)
        print(f"    monitor: {await bh.read_lux():.2f} lx")


async def main():
    address = find_address(I2C_BUS)
    if address is None:
        print(f"BH1750 not found at 0x23 or 0x5C on I2C bus {I2C_BUS}, check wiring (i2cdetect -y {I2C_BUS}).")
        return

    async with BH1750(I2C_BUS, address) as bh:      # powers on, sets MTreg to 69; powers down on exit
        print(f"BH1750 at 0x{address:02X}")

        # One-time mode: the sensor powers itself down after each reading
        print(f"\nOne-time measurements (MTreg {bh.mtreg})")
        for res in (BH1750.RES_LOW, BH1750.RES_HIGH, BH1750.RES_HIGH2):
            start = time.monotonic()
            lux = await bh.measure(res)
            took = (time.monotonic() - start) * 1000
            print(f"  {RES_NAMES[res]:<12} {lux:9.2f} lx  ({bh.lux_per_count(res):.3f} lx/count, took {took:.0f} ms)")

        # MTreg trades range for resolution: the reading should stay about the same, the step size changes
        print("\nMTreg sweep (H2 one-time)")
        for mt in (BH1750.MTREG_MIN, BH1750.MTREG_DEFAULT, BH1750.MTREG_MAX):
            await bh.set_mtreg(mt)
            lux = await bh.measure(BH1750.RES_HIGH2)
            print(f"  MTreg {mt:3d}: {lux:9.2f} lx  ({bh.lux_per_count():.3f} lx/count, "
                  f"up to {bh.measurement_time() * 1000:.0f} ms, max {65535 * bh.lux_per_count():.0f} lx)")
        await bh.set_mtreg(BH1750.MTREG_DEFAULT)

        # Continuous mode with a second task reading the same sensor
        print(f"\nContinuous H mode ({CONTINUOUS_SAMPLES} samples)")
        await bh.start_continuous(BH1750.RES_HIGH)
        ticker = asyncio.create_task(heartbeat())
        watcher = asyncio.create_task(monitor(bh))
        n = 0
        async for lux in bh.measurements():
            n += 1
            print(f"{n:>2} {lux:9.2f} lx")
            if n >= CONTINUOUS_SAMPLES:
                break
        watcher.cancel()
        ticker.cancel()

    print("-----")
    print(f"Longest heartbeat gap: {max_gap * 1000:.0f} ms (every {HEARTBEAT * 1000:.0f} ms requested; "
          f"a blocking driver would show ~{bh.measurement_time() * 1000:.0f} ms).")
    print("Done, sensor powered down.")


if __name__ == "__main__":
    asyncio.run(main())
