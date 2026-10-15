# Demo / test for the asynchronous ENS160 driver on a Raspberry Pi Pico, ESP32-C3 or ESP32-S3.
# A sampler and a monitor task share the sensor while a heartbeat task counts event-loop ticks,
# showing that the driver never blocks the loop.

import sys
from machine import I2C, Pin
from ENS160_async import ENS160

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# I2C pins per board (edit to suit your wiring)
if sys.platform == "rp2":                           # Raspberry Pi Pico: I2C1 on GP2 (SDA) / GP3 (SCL)
    I2C_ID, SDA, SCL = 1, 2, 3
else:                                               # ESP32-C3 / ESP32-S3: GPIO8 (SDA) / GPIO9 (SCL)
    I2C_ID, SDA, SCL = 0, 8, 9

# Ambient conditions used for compensation. In a real deployment these would
# come from a separate temperature/humidity sensor.
AMBIENT_TEMP_C = 22.0
AMBIENT_HUMIDITY = 50.0

SAMPLES = 10                    # new sample about once a second in STANDARD mode
MONITOR_INTERVAL_S = 3
HEARTBEAT_MS = 100

ticks = 0


async def heartbeat():
    global ticks
    while True:
        await asyncio.sleep_ms(HEARTBEAT_MS)
        ticks += 1


async def monitor(ens):
    """Reads status and compensation values while the sampler runs, sharing the bus via the driver's lock."""
    while True:
        s = await ens.get_status()
        t = await ens.get_temperature()
        rh = await ens.get_humidity()
        print("    monitor: {} | error: {} | compensation {:.2f} C, {:.1f} %".format(ENS160.VALIDITY[s.validity], s.error, t, rh))
        await asyncio.sleep(MONITOR_INTERVAL_S)


async def sampler(ens):
    for n in range(1, SAMPLES + 1):
        r = await ens.wait_data()
        print("{:>2} AQI: {}  eCO2: {:5d} ppm ({})  TVOC: {:5d} ppb ({})".format(
            n, r.aqi, r.eco2, ens.interpret_eco2_level(r.eco2), r.tvoc, ens.interpret_tvoc_level(r.tvoc)))


async def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA), scl=Pin(SCL), freq=100_000)
    found = i2c.scan()
    print("I2C devices found:", [hex(a) for a in found])
    if ENS160.ADDRESS not in found:
        print("ENS160 not found at 0x{:02X}, check wiring.".format(ENS160.ADDRESS))
        return

    async with ENS160(i2c) as ens:                  # checks PART_ID, starts STANDARD mode
        print("Part ID  : 0x{:04X}".format(await ens.get_id()))
        print("Firmware :", await ens.get_firmware_version())
        print("Mode     : 0x{:02X}".format(await ens.get_mode()))
        await ens.set_compensation(AMBIENT_TEMP_C, AMBIENT_HUMIDITY)
        print("Compensation set: {:.1f} C, {:.1f} %".format(AMBIENT_TEMP_C, AMBIENT_HUMIDITY))
        print("-----")

        ticker = asyncio.create_task(heartbeat())
        watcher = asyncio.create_task(monitor(ens))
        await sampler(ens)
        watcher.cancel()
        ticker.cancel()

    print("-----")
    print("Heartbeat ticked {} times (every {} ms) during {} samples, so the loop was never blocked.".format(ticks, HEARTBEAT_MS, SAMPLES))
    print("Done, sensor left in IDLE mode.")


asyncio.run(main())
