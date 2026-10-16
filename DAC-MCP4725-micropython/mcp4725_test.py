# Demo / test for the MCP4725 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# Watch VOUT with a multimeter, wire an LED + 330 Ohm resistor from VOUT to GND to see the sine wave "breathe",
# or wire VOUT to an ADC pin (ADC_PIN) so the board measures its own output.
# A background "heartbeat" task keeps ticking while the DAC works, showing that the driver never blocks the event loop.

import math
import sys
import time
from machine import ADC, I2C, Pin
from mcp4725 import MCP4725

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# Pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9
ADC_PIN = None                  # GPIO wired to VOUT for loopback (e.g. 26 on a Pico), or None

VREF = 3.3                      # the board's VDD, which is also the DAC reference
STEP_DELAY_MS = 2000            # time to hold each voltage step, long enough to read a multimeter
WAVE_HZ = 0.5                   # sine-wave frequency, slow enough to follow on an LED
WAVE_SECONDS = 10               # length of the sine-wave demo
WRITE_EEPROM = False            # True stores mid-scale (the factory default) as the power-up value

PD_NAMES = {0: "on", 1: "off, 1k", 2: "off, 100k", 3: "off, 500k"}


def show(dac, label, s):
    print("{:<13} DAC: {:4d} = {:.3f} V ({:<9}) | EEPROM: {:4d} ({}) | ready: {}".format(
        label, s.code, dac.code_to_volts(s.code), PD_NAMES[s.power_down],
        s.eeprom_code, PD_NAMES[s.eeprom_power_down], s.ready))


def measure(adc):
    """Volts on the loopback pin. ESP32 has calibrated read_uv(), rp2 does not."""
    if sys.platform == "rp2":
        return adc.read_u16() * 3.3 / 65535
    return adc.read_uv() / 1_000_000


async def heartbeat():
    """Ticks once a second to show the loop stays responsive while the DAC is busy."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("  ...tick", n)


async def sine_wave(dac, hz, seconds):
    """Write a sine wave, with the phase taken from the clock so loop delays don't change the frequency."""
    start = time.ticks_ms()
    n = 0
    while True:
        t = time.ticks_diff(time.ticks_ms(), start) / 1000
        if t >= seconds:
            return n
        await dac.fast_write(round((1 + math.sin(2 * math.pi * hz * t)) / 2 * dac.MAX_CODE))
        n += 1
        await asyncio.sleep_ms(5)               # about 200 updates per second


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    if MCP4725.ADDRESS not in found:
        print("MCP4725 not found at 0x62, check wiring (0x63 if A0 is tied to VDD).")
        return

    adc = None
    if ADC_PIN is not None:
        adc = ADC(Pin(ADC_PIN)) if sys.platform == "rp2" else ADC(Pin(ADC_PIN), atten=ADC.ATTN_11DB)

    async with MCP4725(i2c, vref=VREF) as dac:
        show(dac, "At start", await dac.read())

        ticker = asyncio.create_task(heartbeat())

        # Voltage steps: the top step clamps to code 4095 = VREF * 4095/4096
        print("\nVoltage steps ({} s each)".format(STEP_DELAY_MS // 1000))
        for volts in (0, VREF / 4, VREF / 2, 3 * VREF / 4, VREF):
            code = await dac.set_voltage(volts)
            line = "Set {:.3f} V   code {:4d}, read back {:.3f} V".format(volts, code, await dac.get_voltage())
            if adc:
                await asyncio.sleep_ms(10)
                line += ", measured {:.3f} V".format(measure(adc))
            print(line)
            await asyncio.sleep_ms(STEP_DELAY_MS)

        print("\nSine wave ({} Hz for {} s)".format(WAVE_HZ, WAVE_SECONDS))
        n = await sine_wave(dac, WAVE_HZ, WAVE_SECONDS)
        print("{} updates, {:.0f} per second".format(n, n / WAVE_SECONDS))

        # Power-down: VOUT drops to 0 V through each resistor, then comes back at mid-scale
        print("\nPower-down modes ({} s each)".format(STEP_DELAY_MS // 1000))
        await dac.set_voltage(VREF / 2)
        for mode in (dac.PD_1K, dac.PD_100K, dac.PD_500K):
            await dac.power_down(mode)
            show(dac, "Powered down", await dac.read())
            await asyncio.sleep_ms(STEP_DELAY_MS)
        await dac.power_up()
        show(dac, "Powered up", await dac.read())

        if WRITE_EEPROM:
            print("\nEEPROM write (25-50 ms)")
            await dac.set_code(2048, persist=True)
            show(dac, "Stored", await dac.read())

        await dac.set_code(0)
        ticker.cancel()
    print("\nDone, output left at 0 V.")


asyncio.run(main())
