# Async demo for ENS160_AHT21.py: a sensor task and an LED heartbeat share the event loop.
# Raspberry Pi Pico, I2C1 on GP2 (SDA) / GP3 (SCL).
import asyncio
from machine import I2C, Pin
from ENS160_AHT21 import ENS160_AHT21, ENS160

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100_000)
board = ENS160_AHT21(i2c)


async def sensor():
    board.begin()
    print("ENS160 at 0x{:02X}, firmware {}".format(board.ens160.address, board.ens160.firmware_version()))
    while True:
        await board.ens160.wait_data_async()                # pace the loop on new ENS160 samples
        r = await board.read_async()                        # AHT21 conversion runs while other tasks run
        print("AQI {} | TVOC {:5d} ppb | eCO2 {:5d} ppm | PCB {:4.1f}°C {:4.1f}%RH | {}".format(
            r.aqi, r.tvoc, r.eco2, r.pcb_temp, r.pcb_humi, ENS160.VALIDITY[r.validity]))


async def heartbeat():
    led = Pin("LED", Pin.OUT)
    while True:
        led.toggle()
        await asyncio.sleep_ms(500)


async def main():
    asyncio.create_task(heartbeat())
    await sensor()


asyncio.run(main())
