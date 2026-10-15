# DFRobot SEN0537 Fermion ENS160 Air Quality Sensor (ScioSense ENS160)

MicroPython drivers (blocking and `asyncio`) for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://wiki.dfrobot.com/sen0537/docs/20389>

Datasheet: ScioSense ENS160 v1.3 (2023-03-29)

- Metal-oxide gas sensor that reports AQI (UBA 1–5), TVOC (0–65,000 ppb) and eCO2 (400–65,000 ppm), all calculated on the chip
- I2C address `0x53` (DFRobot default, ADDR high) or `0x52` (ADDR low), up to 1 MHz
- New sample about once a second in STANDARD mode
- Warm-up takes 3 minutes after each power-on or mode change. The first hour of a new sensor's life is the "initial start-up" phase.
- Feed it ambient temperature and humidity from another sensor for better accuracy

## Files

- `ENS160.py`: blocking `ENS160` class. Based on [JustDr00py/ens160-aht21](https://github.com/JustDr00py/ens160-aht21).
- `main.py`: demo for `ENS160.py` (Pico, I2C1 on GP2/GP3).
- `ENS160_async.py`: asynchronous `ENS160` class, plus `Reading` and `Status` namedtuples.
- `test_async.py`: demo for `ENS160_async.py`. It picks Pico or ESP32 pins from `sys.platform`.

## Usage (async)

Copy the files to the board (`mpremote cp ENS160_async.py test_async.py :`), then run `mpremote run test_async.py`.

```python
import asyncio
from machine import I2C, Pin
from ENS160_async import ENS160

async def main():
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100_000)
    async with ENS160(i2c) as ens:              # checks PART_ID and starts STANDARD mode; leaves IDLE on exit
        await ens.set_compensation(22.0, 50.0)  # °C, %RH
        while True:
            r = await ens.wait_data()           # waits for each new sample
            print(r.aqi, r.tvoc, r.eco2)

asyncio.run(main())
```

| Group | Methods |
|---|---|
| Setup | `begin`, `get_id`, `set_mode` / `get_mode`, `reset`, `get_firmware_version` |
| Measurement | `get_status`, `get_data`, `wait_data` |
| Compensation | `set_compensation`, `get_temperature`, `get_humidity` |
| Ratings | `interpret_eco2_level`, `interpret_tvoc_level` (static) |

## Notes

- `get_data()` reads AQI, TVOC and eCO2 in one transaction, so all three come from the same sample.
- `get_firmware_version()` has to switch to IDLE, so calling it in STANDARD mode restarts the 3-minute warm-up.
- Check `get_status().validity` (`ENS160.VALIDITY` has the text) before trusting readings. `get_status().error` reports the chip's error flag.
- In the async driver, a lock makes sure only one task talks to the sensor at a time, so several tasks can share one sensor.
