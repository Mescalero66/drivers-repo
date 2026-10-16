# Demo / test for the MCP4725 driver on a Raspberry Pi (I2C bus 1).
# Watch VOUT with a multimeter, or wire an LED + 330 Ω resistor from VOUT to GND to see the sine wave "breathe".
# A background "heartbeat" task keeps ticking while the DAC works, showing that the driver never blocks the event loop.

import asyncio
import math
import time

from mcp4725 import MCP4725

VREF = 3.3                      # the board's VDD, which is also the DAC reference
STEP_DELAY = 2.0                # seconds to hold each voltage step, long enough to read a multimeter
WAVE_HZ = 0.5                   # sine-wave frequency, slow enough to follow on an LED
WAVE_SECONDS = 10               # length of the sine-wave demo
WRITE_EEPROM = False            # True stores mid-scale (the factory default) as the power-up value

PD_NAMES = {0: "on", 1: "off, 1k", 2: "off, 100k", 3: "off, 500k"}


def show(dac, label, s):
    print(f"{label:<13} DAC: {s.code:4d} = {dac.code_to_volts(s.code):.3f} V ({PD_NAMES[s.power_down]:<9}) | "
          f"EEPROM: {s.eeprom_code:4d} ({PD_NAMES[s.eeprom_power_down]}) | ready: {s.ready}")


async def heartbeat():
    """Ticks once a second to show the loop stays responsive while the DAC is busy."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print(f"  ...tick {n}")


async def sine_wave(dac, hz, seconds):
    """Write a sine wave, with the phase taken from the clock so loop delays don't change the frequency."""
    start = time.monotonic()
    n = 0
    while (t := time.monotonic() - start) < seconds:
        await dac.fast_write(round((1 + math.sin(2 * math.pi * hz * t)) / 2 * dac.MAX_CODE))
        n += 1
        await asyncio.sleep(0.005)              # about 200 updates per second
    return n


async def main():
    async with MCP4725(bus=1, vref=VREF) as dac:
        show(dac, "At start", await dac.read())

        ticker = asyncio.create_task(heartbeat())

        # Voltage steps: the top step clamps to code 4095 = VREF × 4095/4096
        print(f"\nVoltage steps ({STEP_DELAY:.0f} s each)")
        for volts in (0, VREF / 4, VREF / 2, 3 * VREF / 4, VREF):
            code = await dac.set_voltage(volts)
            print(f"Set {volts:.3f} V   code {code:4d}, read back {await dac.get_voltage():.3f} V")
            await asyncio.sleep(STEP_DELAY)

        print(f"\nSine wave ({WAVE_HZ} Hz for {WAVE_SECONDS} s)")
        n = await sine_wave(dac, WAVE_HZ, WAVE_SECONDS)
        print(f"{n} updates, {n / WAVE_SECONDS:.0f} per second")

        # Power-down: VOUT drops to 0 V through each resistor, then comes back at mid-scale
        print(f"\nPower-down modes ({STEP_DELAY:.0f} s each)")
        await dac.set_voltage(VREF / 2)
        for mode in (dac.PD_1K, dac.PD_100K, dac.PD_500K):
            await dac.power_down(mode)
            show(dac, "Powered down", await dac.read())
            await asyncio.sleep(STEP_DELAY)
        await dac.power_up()
        show(dac, "Powered up", await dac.read())

        if WRITE_EEPROM:
            print("\nEEPROM write (25–50 ms)")
            await dac.set_code(2048, persist=True)
            show(dac, "Stored", await dac.read())

        await dac.set_code(0)
        ticker.cancel()
    print("\nDone, output left at 0 V.")


if __name__ == "__main__":
    asyncio.run(main())
