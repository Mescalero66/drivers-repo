# DFRobot SEN0546 I2C Temperature & Humidity Sensor, Stainless Steel Shell (Sensylink CHT8305C)

Python drivers for Raspberry Pi, using `smbus2`: a blocking one and an asynchronous (`asyncio`) one.

Page: <https://www.dfrobot.com/product-2600.html>

Wiki: <https://wiki.dfrobot.com/SKU_SEN0546_I2C_Temperature_and_Humidity_Sensor_Stainless_Steel_Shell>

Datasheet: Sensylink CHT8305C, Rev 2.2 (Jul 2020) <https://dfimg.dfrobot.com/nobody/wiki/4c8e1057e1c118e5c72f8ff6147575db.pdf>

- Temperature -40 – 125 °C, ±0.5 °C max from 0 to 50 °C. Humidity 0 – 100 %RH, ±3 %RH max at 50 %RH (±5 %RH max from 20 to 80 %RH)
- 14-bit readings (0.02 °C / 0.02 %RH). A temperature + humidity conversion takes about 11 ms, then the sensor drops back to standby (0.05 µA)
- Programmable temperature and humidity high limits, with alert status bits. The ALERT pin isn't wired out on the probe
- On-chip heater (about 7 mA) for driving off condensation
- Supply 2.5–5.5 V. I2C up to 400 kHz at `0x40` (the chip's AD0 pin isn't wired out, so the address is fixed)
- 304 stainless steel housing, 1.5 m cable, built-in 4.7 kΩ pull-ups and 100 nF capacitor

> **Probe version:** since 10/7/2025 DFRobot ship the SEN0546 with a newer CHT832X chip. These drivers are for the **CHT8305**, which has a **white** SCL wire. The CHT832X version has a green SCL wire and needs a different driver.

## Wiring (Raspberry Pi)

| Probe wire | Pi pin |
|---|---|
| Red, VCC | 3.3 V (pin 1) |
| Black, GND | GND (pin 6) |
| White, SCL | GPIO 3 / SCL (pin 5) |
| Yellow, SDA | GPIO 2 / SDA (pin 3) |

Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `40`.

![Probe Pinout](https://dfimg.dfrobot.com/nobody/wiki/83f1a068a3f9e142fad7e93c5229d248.png)

## Files

- `cht8305_async.py`: asynchronous `CHT8305` class, with `Measurement` (`temperature`, `humidity`) and `AlertStatus` (`pending`, `humidity`, `temperature`) dataclasses.
- `cht8305_async_test.py`: demo that reads the IDs and settings, takes single and lower-resolution readings, streams readings, sets alert limits and (optionally) runs the heater, while a heartbeat task keeps running.
- `df_tempprobe.py`: original blocking `tempprobe` class from the Saabpi project: `get_Temp` / `get_Humi`, or split `req_…` / `read_…`.
- `df_tempprobe_test.py`: prints temperature and humidity every 2 seconds.

## Usage

```bash
pip install smbus2
python3 cht8305_async_test.py
```

```python
import asyncio
from cht8305_async import CHT8305

async def main():
    async with CHT8305() as cht:                    # bus 1, 0x40; checks the ID; heater off on exit
        m = await cht.read_measurement()            # one T + RH conversion
        print(m.temperature, m.humidity)
        async for m in cht.measurements(2.0):       # a reading every 2 s
            print(m.temperature, m.humidity)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). The conversion wait uses `asyncio.sleep`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `read_measurement`, `read_temperature`, `read_humidity`, `measurements` |
| Configuration | `get/set_resolution`, `get/set_heater`, `get_supply_low`, `soft_reset`, `get_config`, `close` |
| Alert | `get/set_alert_limits`, `get/set_alert_mode`, `get_alert_status` |
| ID | `get_manufacturer_id` (0x5959), `get_version_id` (0x8305) |

The blocking driver is used like this:

```python
from df_tempprobe import tempprobe
probe = tempprobe(1)                    # I2C bus 1
print(probe.get_Temp(), probe.get_Humi())
```

## Notes

- Writing the register pointer `0x00` (or `0x01`) starts a conversion. The sensor then NACKs reads until it has finished. The async driver waits 12 ms and then retries every 2 ms. It leaves clock stretching off, because the Raspberry Pi's I2C hardware handles stretched clocks badly.
- Take no more than one reading per second. More often than that, self-heating raises the temperature reading (datasheet §2). Every 2 s or slower is plenty.
- The alert limits keep only the top 9 bits of temperature (0.32 °C steps) and the top 7 bits of humidity (0.78 %RH steps), rounded down. The flags update after each measurement. `set_alert_mode()` chooses whether temperature, humidity, either or both trigger an alert.
- Settings are lost at power-off. `soft_reset()` restores the defaults: 14-bit, heater off, limits 59.9 °C / 79.7 %RH.
- The heater makes readings warmer and drier while it runs. Exiting `async with` always turns it off.
- `df_tempprobe.py` v1.2 fixes two bugs against the datasheet. It used to read only the high byte of each result, which gave 0.64 °C / 0.39 %RH steps that always read low. It also sent an extra `0x80` byte when starting a conversion; `0x80` is the datasheet's 8-bit form of the address, not data.
