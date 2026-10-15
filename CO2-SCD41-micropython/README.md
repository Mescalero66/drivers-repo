# Adafruit SCD-41 CO2, Temperature & Humidity Sensor (Sensirion SCD41)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://www.adafruit.com/product/5190>

Datasheet: <https://sensirion.com/products/catalog/SCD41> (v1.7, April 2025)

- Photoacoustic NDIR CO2 sensor, with built-in temperature & humidity sensor
- CO2 range 400–5000 ppm, accuracy ±(50 ppm + 2.5%) between 400 and 1000 ppm
- I2C address `0x62` (fixed), standard and fast mode (≤ 400 kHz)
- Supply 2.4–5.5 V (the Adafruit board has a regulator and level shifting, so 3.3 V or 5 V both work)
- Periodic (5 s), low-power periodic (~30 s) and single-shot measurement modes
- Peak current up to 205 mA at 3.3 V while measuring, so power it from a supply that can deliver that, not a weak GPIO-powered rail

## Wiring

| SCD-41 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VIN | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6) | GPIO 8 |
| SCL | GP5 (pin 7) | GPIO 9 |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` in `scd41_test.py` to match your board. For example, the Adafruit QT Py ESP32-C3's STEMMA QT port uses SDA 5 / SCL 6.

## Files

- `scd41.py`: `SCD41` class and `Measurement` namedtuple (`co2`, `temperature`, `humidity`).
- `scd41_test.py`: demo that scans the bus, reads the ID and config, then takes periodic and single-shot readings while a heartbeat task keeps running. It picks Pico or ESP32 pins from `sys.platform`.

## Usage

Copy both files to the board (e.g. `mpremote cp scd41.py scd41_test.py :`), then run `mpremote run scd41_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from scd41 import SCD41

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    async with SCD41(i2c) as scd:               # wakes the sensor, stops it, reloads settings
        await scd.start_periodic_measurement()
        while True:
            m = await scd.wait_measurement()    # returns each new reading (every 5 s)
            print(m.co2, m.temperature, m.humidity)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet command (`get_…` / `set_…`). Command execution times are awaited with `asyncio.sleep_ms`, and a lock stops tasks from sending commands to the sensor at the same time.

| Group | Methods |
|---|---|
| Measurement | `start_periodic_measurement`, `start_low_power_periodic_measurement`, `stop_periodic_measurement`, `get_data_ready_status`, `read_measurement`, `wait_measurement`, `measure_single_shot`, `measure_single_shot_rht_only`, `power_down`, `wake_up` |
| Compensation | `get/set_temperature_offset`, `get/set_sensor_altitude`, `get/set_ambient_pressure` |
| Calibration | `perform_forced_recalibration`, `get/set_automatic_self_calibration_enabled`, `get/set_automatic_self_calibration_target` |
| Advanced | `persist_settings`, `get_serial_number`, `perform_self_test`, `perform_factory_reset`, `reinit`, `get_sensor_variant` |

## Notes

- The API matches the [CPython version](../CO2-SCD41-python/) except for one method. MicroPython has no async generators, so `measurements()` becomes `wait_measurement()`, which returns one reading per call.
- While periodic measurement is running, the sensor only accepts `read_measurement`, `get_data_ready_status`, `stop_periodic_measurement` and `get/set_ambient_pressure`. Call `stop_periodic_measurement()` before changing other settings.
- Settings are kept in RAM only. Call `persist_settings()` to save them, but sparingly, because the EEPROM is rated for about 2000 writes.
- Set the temperature offset (default 4 °C) after mounting the sensor in its final enclosure. The offset changes the RH/T readings only, not CO2.
- Automatic self-calibration (ASC, on by default) assumes the sensor sees fresh air (~400 ppm) at least once a week.
- For battery use, take a `measure_single_shot()` every few minutes and call `power_down()` / `wake_up()` in between (§3.11).
- `read_measurement()` raises `OSError` if no new data is ready. Use `wait_measurement()` or check `get_data_ready_status()` first.
