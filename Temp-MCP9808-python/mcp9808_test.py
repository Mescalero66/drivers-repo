# Demo / test for the MCP9808 driver on a Raspberry Pi (I2C bus 1).
# A background "heartbeat" task keeps ticking while the sensor works, showing that the driver never blocks the event loop.

import asyncio
import time

from smbus2 import SMBus, i2c_msg

from mcp9808 import MCP9808

I2C_BUS = 1
CONTINUOUS_SAMPLES = 8          # readings at 0.0625 °C (one every ~0.3 s)
ALERT_WAIT = 30                 # s to wait for you to warm the sensor with a finger (0 to skip)


def find_address(bus):
    """Probe 0x1F (DFRobot default) first, then 0x18–0x1E, for the MCP9808 manufacturer ID."""
    with SMBus(bus) as smb:
        for address in (0x1F, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E):
            try:
                rd = i2c_msg.read(address, 2)
                smb.i2c_rdwr(i2c_msg.write(address, [MCP9808.MANUFACTURER_ID]), rd)
                if bytes(rd) == b"\x00\x54":
                    return address
            except OSError:
                pass
    return None


def show(label, m):
    flags = "".join(f for f, on in ((" >CRIT", m.above_critical), (" >UPPER", m.above_upper),
                                    (" <LOWER", m.below_lower)) if on)
    print(f"{label:<12} {m.temperature:8.4f} °C{flags}")


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
        print(f"MCP9808 not found at 0x18–0x1F on I2C bus {I2C_BUS}, check wiring (i2cdetect -y {I2C_BUS}).")
        return

    async with MCP9808(I2C_BUS, address) as mcp:    # checks the ID and starts converting; shuts down on exit
        # Identification
        dev, rev = await mcp.get_device_id()
        print(f"MCP9808 at 0x{address:02X}")
        print(f"Manufacturer  : 0x{await mcp.get_manufacturer_id():04X}")
        print(f"Device / rev  : 0x{dev:02X} / 0x{rev:02X}")

        # Settings left from before (they survive until power-off), then back to the power-on defaults
        print(f"Config        : 0x{await mcp.get_config():04X}")
        print(f"Resolution    : {await mcp.get_resolution()} °C")
        print(f"Hysteresis    : {await mcp.get_hysteresis()} °C")
        print(f"Limits        : lower {await mcp.get_lower_limit()} / upper {await mcp.get_upper_limit()} / "
              f"critical {await mcp.get_critical_limit()} °C")
        await mcp.reset()

        ticker = asyncio.create_task(heartbeat())

        # Each resolution: finer steps take longer to convert
        print("\nResolution sweep")
        for step in MCP9808.RESOLUTIONS:
            await mcp.set_resolution(step)
            start = time.monotonic()
            await asyncio.sleep(mcp.conversion_time())
            t = await mcp.read_temperature()
            print(f"  {step:<6} °C: {t:8.4f} °C  (waited {(time.monotonic() - start) * 1000:.0f} ms)")

        # Continuous conversion at the finest resolution
        print(f"\nContinuous ({CONTINUOUS_SAMPLES} samples)")
        print("(all limits are 0 °C after reset(), so above 0 °C the >CRIT and >UPPER flags are set)")
        n = 0
        async for m in mcp.measurements():
            n += 1
            show(f"Sample {n}", m)
            if n >= CONTINUOUS_SAMPLES:
                break

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
        print(f"\nAlert: upper limit {await mcp.get_upper_limit()} °C (below the current temperature)")
        show("Alert", await asyncio.wait_for(mcp.wait_alert(), 2))

        await mcp.set_upper_limit(t + 2)            # releases once TA ≤ upper - hysteresis
        await asyncio.sleep(mcp.conversion_time())
        print(f"Alert: upper limit {await mcp.get_upper_limit()} °C, asserted: {await mcp.get_alert_status()}")
        if ALERT_WAIT:
            print(f"Warm the sensor by 2 °C (touch it), waiting up to {ALERT_WAIT} s...")
            try:
                show("Alert", await asyncio.wait_for(mcp.wait_alert(), ALERT_WAIT))
            except asyncio.TimeoutError:
                print("No alert (timed out).")

        await mcp.reset()                           # alert off, limits back to 0 °C
        ticker.cancel()
    print("\nDone, sensor shut down.")


if __name__ == "__main__":
    asyncio.run(main())
