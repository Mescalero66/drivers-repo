# Demo / test for the SCD41 driver on a Raspberry Pi (I2C bus 1).
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import asyncio
from scd41 import SCD41

PERIODIC_SAMPLES = 3            # periodic readings to take (one every 5 s)
RUN_SELF_TEST = False           # self test takes 10 s


def show(label, m):
    print(f"{label:<12} CO2: {m.co2:5d} ppm | Temp: {m.temperature:5.1f} °C | RH: {m.humidity:5.1f} %")


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print(f"  ...tick {n}")


async def main():
    async with SCD41(bus=1) as scd:
        # Identification
        print(f"Serial number : 0x{await scd.get_serial_number():012X}")
        print(f"Sensor variant: {await scd.get_sensor_variant()}")

        # Current configuration (read-only, nothing is written to EEPROM)
        print(f"Temp offset   : {await scd.get_temperature_offset():.2f} °C")
        print(f"Altitude      : {await scd.get_sensor_altitude()} m")
        print(f"ASC enabled   : {await scd.get_automatic_self_calibration_enabled()}")
        print(f"ASC target    : {await scd.get_automatic_self_calibration_target()} ppm")

        ticker = asyncio.create_task(heartbeat())

        # Periodic mode: first reading arrives about 5 s after starting
        print(f"\nPeriodic mode ({PERIODIC_SAMPLES} samples)")
        await scd.start_periodic_measurement()
        n = 0
        async for m in scd.measurements():
            n += 1
            show(f"Periodic {n}", m)
            if n >= PERIODIC_SAMPLES:
                break
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


if __name__ == "__main__":
    asyncio.run(main())
