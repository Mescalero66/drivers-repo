# Demo / test for the SEN62 driver on a Raspberry Pi (I2C bus 1).
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import asyncio
from sen62 import SEN62

SAMPLES = 10                    # readings to take (one per second)
TEMP_OFFSET = 0.0               # °C added to the temperature output (slot 0), e.g. -1.5 if the enclosure runs warm
RUN_FAN_CLEANING = False        # fan at full speed for 10 s
RUN_SHT_HEATER = False          # 1 s heater pulse, then 20 s to settle before measuring


def f(v):
    return "   n/a" if v is None else f"{v:6.1f}"


def show(n, m, nc):
    print(f"#{n:<3} PM1.0 {f(m.pm1_0)} | PM2.5 {f(m.pm2_5)} | PM4.0 {f(m.pm4_0)} | PM10 {f(m.pm10_0)} µg/m³"
          f" | RH {f(m.humidity)} % | T {f(m.temperature)} °C")
    print(f"     PM0.5 {f(nc.nc0_5)} | PM1.0 {f(nc.nc1_0)} | PM2.5 {f(nc.nc2_5)} | PM4.0 {f(nc.nc4_0)}"
          f" | PM10 {f(nc.nc10_0)} #/cm³")


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print(f"  ...tick {n}")


async def main():
    ticker = asyncio.create_task(heartbeat())

    async with SEN62(bus=1) as sen:                 # stop + reset takes 2.6 s
        # Identification
        print(f"Product name  : {await sen.get_product_name()}")
        print(f"Product type  : {await sen.get_product_type()}")
        print(f"Serial number : {await sen.get_serial_number()}")
        major, minor = await sen.get_version()
        print(f"Firmware      : {major}.{minor}")
        print(f"Device status : {await sen.read_device_status()}")

        # Idle-mode maintenance
        if RUN_FAN_CLEANING:
            print("\nFan cleaning (10 s)")
            await sen.start_fan_cleaning()

        if RUN_SHT_HEATER:
            print("\nSHT heater (1 s), then 20 s to settle")
            await sen.activate_sht_heater()
            rh, t = await sen.get_sht_heater_measurements()
            print(f"After heating : RH {f(rh)} % | T {f(t)} °C")
            await asyncio.sleep(20)

        await sen.set_temperature_offset_parameters(TEMP_OFFSET)

        # Continuous mode: first reading after ~1.1 s, PM values settle after ~30 s
        print(f"\nContinuous measurement ({SAMPLES} samples)")
        await sen.start_continuous_measurement()
        n = 0
        async for m in sen.measurements():
            n += 1
            show(n, m, await sen.read_number_concentration_values())
            if n >= SAMPLES:
                break

        rh, t = await sen.read_measured_raw_values()
        print(f"\nUncompensated : RH {f(rh)} % | T {f(t)} °C")
        print(f"Device status : {await sen.read_device_status()}")

    ticker.cancel()
    print("\nDone, sensor left idle.")


if __name__ == "__main__":
    asyncio.run(main())
