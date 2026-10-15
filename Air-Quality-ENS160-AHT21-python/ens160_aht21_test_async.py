# Async demo for ens160_aht21.py: a sensor task and a heartbeat task share the event loop.
# Raspberry Pi, I2C bus 1 (GPIO2 SDA, GPIO3 SCL).
import asyncio
import time
from ens160_aht21 import I2C, ENS160_AHT21, ENS160

I2C_BUS = 1


async def sensor(board):
    board.begin()
    print(f"ENS160 at 0x{board.ens160.address:02X}, firmware {board.ens160.firmware_version()}")
    while True:
        await board.ens160.wait_data_async()                # pace the loop on new ENS160 samples
        r = await board.read_async()                        # AHT21 conversion runs while other tasks run
        print(f"AQI {r.aqi} | TVOC {r.tvoc:5d} ppb | eCO2 {r.eco2:5d} ppm | "
              f"PCB {r.pcb_temp:4.1f}°C {r.pcb_humi:4.1f}%RH | {ENS160.VALIDITY[r.validity]}")


async def heartbeat():
    start = time.monotonic()
    while True:
        await asyncio.sleep(10)
        print(f"-- running {time.monotonic() - start:.0f} s")


async def main():
    with I2C(I2C_BUS) as i2c:
        board = ENS160_AHT21(i2c)
        hb = asyncio.create_task(heartbeat())
        try:
            await sensor(board)
        finally:
            hb.cancel()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print()
