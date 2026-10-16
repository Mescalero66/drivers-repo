# Demo / test for the BMP280 driver on a Raspberry Pi (I2C bus 1).
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import asyncio
import time

from smbus2 import SMBus

from bmp280 import BMP280

I2C_BUS = 1
SEA_LEVEL_HPA = 1013.25         # local QNH for absolute altitude (from a weather service); 1013.25 = standard atmosphere
NORMAL_SAMPLES = 30             # normal-mode readings (about 10 per second with the "handheld_low_power" preset)

# Oversampling settings from Table 4: name, pressure, temperature
SWEEP = (("Ultra low pwr", 1, 1), ("Low power", 2, 1), ("Standard", 4, 1),
         ("High res", 8, 1), ("Ultra high", 16, 2))


def find_address(bus):
    """Probe 0x76 (SDO low, generic boards) then 0x77 (SDO high) for the BMP280 / BME280 chip ID."""
    with SMBus(bus) as smb:
        for address in (0x76, 0x77):
            try:
                if smb.read_byte_data(address, BMP280.ID) in BMP280.CHIP_IDS:
                    return address
            except OSError:
                pass
    return None


def show(label, m):
    t = "  --  " if m.temperature is None else f"{m.temperature:6.2f}"
    if m.pressure is None:
        print(f"{label:<14} T: {t} °C | P:    (skipped)")
    else:
        alt = BMP280.altitude(m.pressure, SEA_LEVEL_HPA * 100)
        print(f"{label:<14} T: {t} °C | P: {m.pressure / 100:7.2f} hPa | Alt: {alt:7.1f} m")


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
        print(f"BMP280 not found at 0x76 / 0x77 on I2C bus {I2C_BUS}, check wiring (i2cdetect -y {I2C_BUS}).")
        return

    async with BMP280(I2C_BUS, address) as bmp:    # resets, checks the chip ID, reads the calibration
        # Identification and settings after init()
        chip = await bmp.get_chip_id()
        p, t = await bmp.get_oversampling()
        print(f"Address       : 0x{address:02X}")
        print(f"Chip ID       : 0x{chip:02X} ({BMP280.CHIP_IDS[chip]})")
        print(f"Oversampling  : P x{p} / T x{t}")
        print(f"IIR filter    : {await bmp.get_filter()}")
        print(f"Standby       : {await bmp.get_standby()} ms")

        ticker = asyncio.create_task(heartbeat())

        # Forced mode: one measurement per call, then back to sleep. More oversampling takes longer.
        print("\nForced mode, oversampling sweep (Table 4)")
        for name, osrs_p, osrs_t in SWEEP:
            await bmp.set_oversampling(osrs_p, osrs_t)
            start = time.monotonic()
            m = await bmp.measure_single_shot()
            show(name, m)
            print(f"{'':<14} x{osrs_p} / x{osrs_t}, took {(time.monotonic() - start) * 1000:.0f} ms "
                  f"(max {bmp.measurement_time() * 1000:.1f} ms)")

        # Pressure skipped: the sensor works as a thermometer only (and measures faster)
        await bmp.set_oversampling(0, 1)
        show("Temp only", await bmp.measure_single_shot())

        # Normal mode: the sensor measures continuously; the IIR filter smooths out short disturbances
        await bmp.apply_preset("handheld_low_power")
        print(f"\nNormal mode, 'handheld_low_power' preset: P x16 / T x2, IIR {await bmp.get_filter()}, "
              f"standby {await bmp.get_standby()} ms, ~{bmp.output_data_rate():.1f} Hz")
        print("(raise or lower the sensor to see the height change)")
        ref = None
        n = 0
        async for m in bmp.measurements():
            n += 1
            alt = BMP280.altitude(m.pressure)
            if ref is None:
                ref = alt
            print(f"Normal {n:<7d} T: {m.temperature:6.2f} °C | P: {m.pressure:9.2f} Pa | dh: {alt - ref:+6.2f} m")
            if n >= NORMAL_SAMPLES:
                break

        ticker.cancel()
    print("\nDone, sensor left in sleep mode.")


if __name__ == "__main__":
    asyncio.run(main())
