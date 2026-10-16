# Demo / test for the asyncio CHT8305 driver on a Raspberry Pi (I2C bus 1).
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import asyncio

from smbus2 import SMBus, i2c_msg

from cht8305_async import CHT8305

I2C_BUS = 1
SAMPLES = 5                     # readings, one every SAMPLE_INTERVAL s
SAMPLE_INTERVAL = 2.0           # s (datasheet: no more than one per second, to avoid self-heating)
HEATER_SECONDS = 0              # set to e.g. 10 to watch the heater warm the probe


def find_address(bus):
    """Probe 0x40, 0x44, 0x48, 0x4C for the CHT8305 manufacturer ID (0x5959)."""
    with SMBus(bus) as smb:
        for address in CHT8305.ADDRESSES:
            try:
                smb.i2c_rdwr(i2c_msg.write(address, [CHT8305.MANUFACTURER_ID]))
                rd = i2c_msg.read(address, 2)
                smb.i2c_rdwr(rd)
                if bytes(rd) == b"\x59\x59":
                    return address
            except OSError:
                pass
    return None


def show(label, m):
    print(f"{label:<12} Temp: {m.temperature:6.2f} °C | RH: {m.humidity:5.1f} %")


async def heartbeat():
    """Ticks once a second to show the loop stays responsive during sensor waits."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print(f"  ...tick {n}")


async def main():
    address = find_address(I2C_BUS)
    if address is None:
        print(f"CHT8305 not found on I2C bus {I2C_BUS}, check wiring (i2cdetect -y {I2C_BUS}).")
        return

    async with CHT8305(I2C_BUS, address) as cht:    # checks the ID; turns the heater off on exit
        await cht.soft_reset()                      # start from the power-on defaults

        # Identification and settings
        print(f"CHT8305 at 0x{address:02X}")
        print(f"Manufacturer  : 0x{await cht.get_manufacturer_id():04X}")
        print(f"Version       : 0x{await cht.get_version_id():04X}")
        print(f"Config        : 0x{await cht.get_config():04X}")
        t_bits, h_bits = await cht.get_resolution()
        print(f"Resolution    : T {t_bits}-bit, RH {h_bits}-bit")
        print(f"Supply < 2.8 V: {await cht.get_supply_low()}")
        t_lim, h_lim = await cht.get_alert_limits()
        print(f"Alert limits  : {t_lim:.1f} °C / {h_lim:.1f} %RH")

        ticker = asyncio.create_task(heartbeat())

        # Single conversions
        print("\nSingle conversions")
        show("T + RH", await cht.read_measurement())
        print(f"{'T only':<12} Temp: {await cht.read_temperature():6.2f} °C")
        print(f"{'RH only':<12} RH: {await cht.read_humidity():5.1f} %")

        # Lower resolution: coarser steps
        await cht.set_resolution(11, 8)
        show("11 / 8-bit", await cht.read_measurement())
        await cht.set_resolution(14, 14)

        # Periodic readings
        print(f"\nPeriodic ({SAMPLES} samples, every {SAMPLE_INTERVAL} s)")
        n = 0
        async for m in cht.measurements(SAMPLE_INTERVAL):
            n += 1
            show(f"Sample {n}", m)
            if n >= SAMPLES:
                break

        # Alert high limits, checked after each measurement
        m = await cht.read_measurement()
        await cht.set_alert_mode(CHT8305.ALERT_EITHER)
        await cht.set_alert_limits(m.temperature - 1, min(100, m.humidity + 10))
        t_lim, h_lim = await cht.get_alert_limits()
        await cht.read_measurement()
        print(f"\nAlert limits {t_lim:.2f} °C / {h_lim:.1f} %RH (temperature already over): {await cht.get_alert_status()}")
        await cht.set_alert_limits(m.temperature + 5, min(100, m.humidity + 10))
        t_lim, h_lim = await cht.get_alert_limits()
        await cht.read_measurement()
        print(f"Alert limits {t_lim:.2f} °C / {h_lim:.1f} %RH (both under): {await cht.get_alert_status()}")

        # Heater
        if HEATER_SECONDS:
            print(f"\nHeater on for {HEATER_SECONDS} s")
            await cht.set_heater(True)
            for _ in range(HEATER_SECONDS // 2):
                await asyncio.sleep(2)
                show("Heater", await cht.read_measurement())
            await cht.set_heater(False)

        await cht.soft_reset()                      # limits and settings back to defaults
        ticker.cancel()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
