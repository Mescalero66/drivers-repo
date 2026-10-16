# DFRobot SEN0546 I2C Temperature & Humidity Sensor, Stainless Steel Shell (Sensylink CHT8305C)

MicroPython drivers for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3: a blocking one and an asynchronous (`asyncio`) one.

Page: <https://www.dfrobot.com/product-2600.html>

Wiki: <https://wiki.dfrobot.com/SKU_SEN0546_I2C_Temperature_and_Humidity_Sensor_Stainless_Steel_Shell>

Datasheet: Sensylink CHT8305C, Rev 2.2 (Jul 2020)

- Temperature -40 – 125 °C, ±0.5 °C max from 0 to 50 °C. Humidity 0 – 100 %RH, ±3 %RH max at 50 %RH (±5 %RH max from 20 to 80 %RH)
- 14-bit readings (0.02 °C / 0.02 %RH). A temperature + humidity conversion takes about 11 ms, then the sensor drops back to standby (0.05 µA)
- Programmable temperature and humidity high limits, with alert status bits. The ALERT pin isn't wired out on the probe
- On-chip heater (about 7 mA) for driving off condensation
- Supply 2.5–5.5 V. I2C up to 400 kHz at `0x40` (the chip's AD0 pin isn't wired out, so the address is fixed)
- 304 stainless steel housing, 1.5 m cable, built-in 4.7 kΩ pull-ups and 100 nF capacitor

> **Probe version:** since 10/7/2025 DFRobot ship the SEN0546 with a newer CHT832X chip. These drivers are for the **CHT8305**, which has a **white** SCL wire. The CHT832X version has a green SCL wire and needs a different driver.

## Wiring

| Probe wire | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| Red, VCC | 3V3(OUT) (pin 36) | 3V3 |
| Black, GND | GND (pin 38) | GND |
| Yellow, SDA | GP4 (pin 6) | GPIO 8 |
| White, SCL | GP5 (pin 7) | GPIO 9 |

These are the pins `cht8305_async_test.py` uses. ESP32 boards have no fixed I2C pins, so change `SDA` / `SCL` there to match your board. The older `main.py` demo uses I2C1 on GP2 (SDA) / GP3 (SCL).

## Files

- `cht8305_async.py`: asynchronous `CHT8305` class, with `Measurement` (`temperature`, `humidity`) and `AlertStatus` (`pending`, `humidity`, `temperature`) namedtuples.
- `cht8305_async_test.py`: demo that scans the bus, reads the IDs and settings, takes single and lower-resolution readings, takes periodic readings, sets alert limits and (optionally) runs the heater, while a heartbeat task keeps running. It picks Pico or ESP32 pins from `sys.platform`.
- `CHT8305.py`: original blocking `I2C_CHT8305_SEN0546` class: `get_…` reads (which also print), split `req_…` / `read_…` measurement, default config, heater on, soft reset, and IDs.
- `main.py`: blocking demo for `CHT8305.py` on the Pico.

## Usage

Copy the driver and its demo to the board (e.g. `mpremote cp cht8305_async.py cht8305_async_test.py :`), then run `mpremote run cht8305_async_test.py`.

```python
import asyncio
from machine import I2C, Pin
from cht8305_async import CHT8305

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    async with CHT8305(i2c) as cht:                 # 0x40; checks the ID; heater off on exit
        while True:
            m = await cht.read_measurement()        # one T + RH conversion
            print(m.temperature, m.humidity)
            await asyncio.sleep(2)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). The conversion wait uses `asyncio.sleep_ms`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `read_measurement`, `read_temperature`, `read_humidity` |
| Configuration | `get/set_resolution`, `get/set_heater`, `get_supply_low`, `soft_reset`, `get_config` |
| Alert | `get/set_alert_limits`, `get/set_alert_mode`, `get_alert_status` |
| ID | `get_manufacturer_id` (0x5959), `get_version_id` (0x8305) |

## Notes

- The API matches the [Python version](../Temp-Humidity-CHT8305-python/) except that MicroPython has no async generators, so there is no `measurements()`. Call `read_measurement()` in a loop instead. The constructor also takes a `machine.I2C` object, so the sensor can share a bus with other devices.
- Writing the register pointer `0x00` (or `0x01`) starts a conversion. The sensor then NACKs reads until it has finished. The async driver waits 12 ms and then retries every 2 ms, with clock stretching left off.
- Take no more than one reading per second. More often than that, self-heating raises the temperature reading (datasheet §2). Every 2 s or slower is plenty.
- The alert limits keep only the top 9 bits of temperature (0.32 °C steps) and the top 7 bits of humidity (0.78 %RH steps), rounded down. The flags update after each measurement. `set_alert_mode()` chooses whether temperature, humidity, either or both trigger an alert.
- Settings are lost at power-off. `soft_reset()` restores the defaults: 14-bit, heater off, limits 59.9 °C / 79.7 %RH.
- The heater makes readings warmer and drier while it runs. Exiting `async with` always turns it off.
- Fixes to `CHT8305.py`, checked against the datasheet:
  - `get_CHT8305_CONFIG()` now sets the register pointer before reading. Called after a measurement, it used to return temperature data.
  - The `get_…` methods also return their values.
  - `BIT_BATTERY_OK` is now `BIT_VCC_LOW`, because the bit is set when the supply is *below* 2.8 V.
