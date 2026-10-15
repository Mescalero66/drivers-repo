# Adafruit SCD-41 CO2, Temperature & Humidity Sensor (Sensirion SCD41)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Page: <https://www.adafruit.com/product/5190>

Datasheet: <https://sensirion.com/products/catalog/SCD41> (v1.7, April 2025)

- Photoacoustic NDIR CO2 sensor, with built-in temperature & humidity sensor
- CO2 range 400–5000 ppm, accuracy ±(50 ppm + 2.5%) between 400 and 1000 ppm
- I2C address `0x62` (fixed), standard and fast mode (≤ 400 kHz)
- Supply 2.4–5.5 V (the Adafruit board has a regulator and level shifting, so 3.3 V or 5 V both work)
- Periodic (5 s), low-power periodic (~30 s) and single-shot measurement modes

## Wiring (Raspberry Pi)

| SCD-41 board | Pi pin |
|---|---|
| VIN | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |

Or use a STEMMA QT / Qwiic cable. Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `62`.

## Files

- `scd41.py`: `SCD41` class and `Measurement` dataclass (`co2`, `temperature`, `humidity`).
- `scd41_test.py`: demo that reads the ID and config, then takes periodic and single-shot readings while a heartbeat task keeps running.

## Usage

```bash
pip install smbus2
python3 scd41_test.py
```

```python
import asyncio
from scd41 import SCD41

async def main():
    async with SCD41() as scd:              # wakes the sensor, stops it, reloads settings
        await scd.start_periodic_measurement()
        async for m in scd.measurements():  # yields each new reading (every 5 s)
            print(m.co2, m.temperature, m.humidity)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet command (`get_…` / `set_…`). Command execution times are awaited with `asyncio.sleep`, and a lock stops tasks from sending commands to the sensor at the same time.

| Group | Methods |
|---|---|
| Measurement | `start_periodic_measurement`, `start_low_power_periodic_measurement`, `stop_periodic_measurement`, `get_data_ready_status`, `read_measurement`, `measurements`, `measure_single_shot`, `measure_single_shot_rht_only`, `power_down`, `wake_up` |
| Compensation | `get/set_temperature_offset`, `get/set_sensor_altitude`, `get/set_ambient_pressure` |
| Calibration | `perform_forced_recalibration`, `get/set_automatic_self_calibration_enabled`, `get/set_automatic_self_calibration_target` |
| Advanced | `persist_settings`, `get_serial_number`, `perform_self_test`, `perform_factory_reset`, `reinit`, `get_sensor_variant` |

## Notes

- While periodic measurement is running, the sensor only accepts `read_measurement`, `get_data_ready_status`, `stop_periodic_measurement` and `get/set_ambient_pressure`. Call `stop_periodic_measurement()` before changing other settings.
- Settings are kept in RAM only. Call `persist_settings()` to save them, but sparingly, because the EEPROM is rated for about 2000 writes.
- Set the temperature offset (default 4 °C) after mounting the sensor in its final enclosure. The offset changes the RH/T readings only, not CO2.
- Automatic self-calibration (ASC, on by default) assumes the sensor sees fresh air (~400 ppm) at least once a week.
- `read_measurement()` raises `OSError` if no new data is ready. Use `measurements()` or check `get_data_ready_status()` first.
- The I2C transfers themselves are blocking `smbus2` calls, but each takes only about 1 ms. All the long waits (up to 10 s) are non-blocking.
