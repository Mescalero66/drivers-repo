# Demo / test for the async HT16K33LED driver (DFRobot DFR0646) on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the display works, showing that the driver never blocks the event loop.

import sys
from machine import I2C, Pin
from HT16K33LED_async import HT16K33LED

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL = 0, 4, 5
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

PAUSE_MS = 2000                 # time to hold each screen


async def heartbeat():
    """Ticks once a second to show the loop stays responsive while the display is busy."""
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("  ...tick", n)


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    if HT16K33LED.ADDRESS not in found:
        print("HT16K33A not found at 0x70, check wiring.")
        return

    async with HT16K33LED(i2c) as display:          # initialises with a blank display
        ticker = asyncio.create_task(heartbeat())

        # All segments and decimal points on, then read the display RAM back to check the bus
        print("Segment test and RAM read-back")
        await display.set_string("8.8.8.8.8.8.8.8.")
        ram = await display.read_ram()
        print("RAM read-back:", "PASS" if ram == bytes(display.buffer) else "FAIL " + " ".join("%02X" % b for b in ram))
        await asyncio.sleep_ms(PAUSE_MS)

        print("Alignment")
        for text, align in (("HELLO", "l"), ("HELLO", "r"), ("3.14159", "r"), ("-12.5°C", "r")):
            print("  {:<12} {}".format(repr(text), align))
            await display.set_string(text, align)
            await asyncio.sleep_ms(PAUSE_MS)

        print("Brightness sweep")
        await display.set_string("bright")
        for level in list(range(16)) + list(range(14, -1, -1)) + [15]:
            await display.set_brightness(level)
            await asyncio.sleep_ms(80)

        print("Blink rates")
        for rate in (2, 1, 0.5, 0):
            await display.set_string("blink {}".format(rate))
            await display.set_blink_rate(rate)
            await asyncio.sleep_ms(PAUSE_MS)

        print("Rotation")
        await display.set_string("UP 123", "l")
        await asyncio.sleep_ms(PAUSE_MS)
        display.rotate()
        await display.draw()
        await asyncio.sleep_ms(PAUSE_MS)
        display.rotate()

        print("Counter")
        for n in range(0, 10001, 37):
            await display.set_string("{:.2f}".format(n / 100), "r")
            await asyncio.sleep_ms(10)

        print("Scroll")
        await display.scroll("HT16K33A Async driver")

        print("Standby and wake (display keeps its buffer)")
        await display.set_string("SLEEP", "r")
        await asyncio.sleep_ms(PAUSE_MS)
        await display.power_off()
        await asyncio.sleep_ms(PAUSE_MS)
        await display.power_on()
        await asyncio.sleep_ms(PAUSE_MS)

        ticker.cancel()
    print("\nDone, display in standby.")


asyncio.run(main())
