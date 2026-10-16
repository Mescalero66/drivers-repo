# Demo / test for the MCP9808 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import sys
import time
from machine import I2C, Pin
from mcp9808 import MCP9808

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring). ALERT: GPIO wired to ALT, or None to poll the Alert Stat bit instead.
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C0 on GP4 (SDA) / GP5 (SCL)
    I2C_ID, SDA, SCL, ALERT = 0, 4, 5, None         # e.g. ALERT = 6 for GP6
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL, ALERT = 0, 8, 9, None         # e.g. ALERT = 10 for GPIO10

CONTINUOUS_SAMPLES = 8          # readings at 0.0625 C (one every ~0.3 s)
ALERT_WAIT = 30                 # s to wait for you to warm the sensor with a finger (0 to skip)


def show(label, m):
    flags = "".join(f for f, on in ((" >CRIT", m.above_critical), (" >UPPER", m.above_upper),
                                    (" <LOWER", m.below_lower)) if on)
    print("{:<12} {:8.4f} C{}".format(label, m.temperature, flags))


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
    candidates = [a for a in found if 0x18 <= a <= 0x1F]
    if not candidates:
        print("MCP9808 not found at 0x18-0x1F, check wiring.")
        return
    address = MCP9808.ADDRESS if MCP9808.ADDRESS in candidates else candidates[0]
    alert_pin = Pin(ALERT) if ALERT is not None else None

    async with MCP9808(i2c, address, alert_pin) as mcp:     # checks the ID and starts converting; shuts down on exit
        # Identification
        dev, rev = await mcp.get_device_id()
        print("MCP9808 at 0x{:02X}".format(address))
        print("Manufacturer  : 0x{:04X}".format(await mcp.get_manufacturer_id()))
        print("Device / rev  : 0x{:02X} / 0x{:02X}".format(dev, rev))

        # Settings left from before (they survive until power-off), then back to the power-on defaults
        print("Config        : 0x{:04X}".format(await mcp.get_config()))
        print("Resolution    :", await mcp.get_resolution(), "C")
        print("Hysteresis    :", await mcp.get_hysteresis(), "C")
        print("Limits        : lower {} / upper {} / critical {} C".format(
            await mcp.get_lower_limit(), await mcp.get_upper_limit(), await mcp.get_critical_limit()))
        await mcp.reset()

        ticker = asyncio.create_task(heartbeat())

        # Each resolution: finer steps take longer to convert
        print("\nResolution sweep")
        for step in MCP9808.RESOLUTIONS:
            await mcp.set_resolution(step)
            start = time.ticks_ms()
            t = (await mcp.wait_measurement()).temperature
            print("  {:<6} C: {:8.4f} C  (waited {} ms)".format(step, t, time.ticks_diff(time.ticks_ms(), start)))

        # Continuous conversion at the finest resolution
        print("\nContinuous ({} samples)".format(CONTINUOUS_SAMPLES))
        print("(all limits are 0 C after reset(), so above 0 C the >CRIT and >UPPER flags are set)")
        for n in range(1, CONTINUOUS_SAMPLES + 1):
            show("Sample {}".format(n), await mcp.wait_measurement())

        # Low-power use: shut down between readings
        print("\nSingle shot from shutdown")
        show("Single", await mcp.measure_single_shot())
        await mcp.wake_up()

        # Alert output in comparator mode, with limits set around the current temperature
        t = await mcp.read_temperature()
        await mcp.set_hysteresis(1.5)
        await mcp.set_lower_limit(t - 10)
        await mcp.set_critical_limit(t + 5)
        await mcp.set_upper_limit(t - 1)            # already exceeded, so the alert asserts straight away
        await mcp.configure_alert(enabled=True)     # comparator mode, active-low
        print("\nAlert ({}): upper limit {} C (below the current temperature)".format(
            "ALT pin interrupt" if alert_pin else "polling Alert Stat", await mcp.get_upper_limit()))
        show("Alert", await asyncio.wait_for(mcp.wait_alert(), 2))

        await mcp.set_upper_limit(t + 2)            # releases once TA <= upper - hysteresis
        await asyncio.sleep_ms(mcp.conversion_ms())
        print("Alert: upper limit {} C, asserted: {}".format(await mcp.get_upper_limit(), await mcp.get_alert_status()))
        if ALERT_WAIT:
            print("Warm the sensor by 2 C (touch it), waiting up to {} s...".format(ALERT_WAIT))
            try:
                show("Alert", await asyncio.wait_for(mcp.wait_alert(), ALERT_WAIT))
            except asyncio.TimeoutError:
                print("No alert (timed out).")

        await mcp.reset()                           # alert off, limits back to 0 C
        ticker.cancel()
    print("\nDone, sensor shut down.")


asyncio.run(main())
