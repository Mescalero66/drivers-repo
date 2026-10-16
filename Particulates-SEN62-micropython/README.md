# Sensirion SEN62 Particulate Matter, Temperature & Humidity Sensor (SEN62-SIN-T)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://sensirion.com/products/catalog/SEN62>

Datasheet: SEN6x Datasheet v1.0 (October 2026), which covers the whole SEN6x family

- Laser-scattering PM sensor with a fan, plus compensated temperature & humidity (SHT4x inside)
- PM1.0 / PM2.5 / PM4.0 / PM10 mass concentration (0–1000 µg/m³ specified) and PM0.5–PM10 number concentration
- PM2.5 precision ±(5 µg/m³ + 5 %) up to 100 µg/m³. Temperature ±0.45 °C, RH ±4.5 %RH typical
- I2C address `0x6B` (fixed), **standard mode only (≤ 100 kHz)**, no clock stretching (the sensor NACKs while busy)
- Supply 3.15–3.6 V, about 75 mA while measuring (130 mA peaks, 190 mA max), so the Pico's 3V3(OUT) and ESP32 boards' 3V3 pins can power it. SDA/SCL are 5 V tolerant
- New reading every second. PM values are stable about 30 s after starting
- **Needs external pull-up resistors on SDA and SCL** (see [Pull-up resistors](#pull-up-resistors-required))

## Wiring

The sensor has a 6-pin 1.25 mm connector (mating plug JST GHR-06V-S). Keep the cable short: under 10 cm is recommended, 50 cm is the maximum.

| SEN62 pin | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| 1 VDD | 3V3(OUT) (pin 36) | 3V3 |
| 2 GND | GND (pin 38) | GND |
| 3 SDA | GP4 (pin 6), **plus 10 kΩ pull-up to 3.3 V** | GPIO 8, **plus 10 kΩ pull-up to 3.3 V** |
| 4 SCL | GP5 (pin 7), **plus 10 kΩ pull-up to 3.3 V** | GPIO 9, **plus 10 kΩ pull-up to 3.3 V** |
| 5 GND, 6 VDD | leave unconnected (joined to pins 2 and 1 inside) | |

### Pull-up resistors (required)

The Pico and ESP32 boards need **external pull-up resistors** on both I2C lines. Without them, the bus may not work at all, or `i2c.scan()` may find the sensor while reads fail with `OSError` or CRC errors.

```
3.3 V ──┬──────┬
       10k    10k
        │      │
SDA ────┴──────┼──── SEN62 pin 3
SCL ───────────┴──── SEN62 pin 4
```

- SDA and SCL are open-drain, and the SEN62 has no pull-ups of its own (datasheet §3.1, example value 10 kΩ).
- The internal pull-ups that `machine.I2C` enables on the Pico and ESP32 are about 50 kΩ, too weak to rely on, especially over the sensor's cable.
- Pull up to **3.3 V**, not 5 V, so the Pico and ESP32 pins only ever see 3.3 V.
- Any value from 4.7 kΩ to 10 kΩ works. Use the lower end with a longer cable.
- If another board on the same bus already has pull-ups (for example an Adafruit STEMMA QT breakout), you don't need to add a second set.

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` in `sen62_test.py` to match your board.

## Files

- `sen62.py`: `SEN62` class, plus `Measurement`, `NumberConcentration` and `DeviceStatus` namedtuples.
- `sen62_test.py`: demo that scans the bus, reads the product info, firmware version and status, then takes 10 readings (mass and number concentrations, RH, T) while a heartbeat task keeps running. It picks Pico or ESP32 pins from `sys.platform`. Flags at the top turn on fan cleaning and the SHT heater.

## Usage

Copy both files to the board (e.g. `mpremote cp sen62.py sen62_test.py :`), then run `mpremote run sen62_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from sen62 import SEN62

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    async with SEN62(i2c) as sen:               # stops any running measurement and resets the sensor
        await sen.start_continuous_measurement()
        while True:
            m = await sen.wait_measurement()    # returns each new reading (every second)
            print(m.pm2_5, m.pm10_0, m.humidity, m.temperature)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet command. Command execution times (20 ms to 1.4 s) are awaited with `asyncio.sleep_ms`, and a lock stops tasks from sending commands to the sensor at the same time.

| Group | Methods |
|---|---|
| Measurement | `start_continuous_measurement`, `stop_measurement`, `get_data_ready`, `read_measured_values`, `wait_measurement`, `read_measured_raw_values`, `read_number_concentration_values` |
| Temperature compensation | `set_temperature_offset_parameters`, `set_temperature_acceleration_parameters` |
| Device info / status | `get_product_type`, `get_product_name`, `get_serial_number`, `get_version`, `read_device_status`, `read_and_clear_device_status` |
| Maintenance | `device_reset`, `start_fan_cleaning`, `activate_sht_heater`, `get_sht_heater_measurements` |

## Notes

- The API matches the [CPython version](../Particulates-SEN62-python/) except for one method. MicroPython has no async generators, so `measurements()` becomes `wait_measurement()`, which returns one reading per call.
- Values the sensor reports as unknown are returned as `None` (sent as 0xFFFF / 0x7FFF). This happens, for example, before the first reading after a start.
- In measurement mode the sensor accepts only reads, status, device info and `set_temperature_offset_parameters`. Reset, fan cleaning, the SHT heater and acceleration parameters need idle mode, so call `stop_measurement()` (1.4 s) first.
- All settings are volatile and are lost on reset or power-off, so reapply temperature offsets at startup.
- The PM, RH&T and fan error flags are sticky. Clear them with `read_and_clear_device_status()`. The fan-speed warning clears itself.
- `start_fan_cleaning()` runs the fan at full speed and returns after 10 s. After `activate_sht_heater()`, wait 20 s before measuring. `get_sht_heater_measurements()` needs firmware 6.0 or later.
- Only the SEN62 commands are included. The rest of the SEN6x family uses the same protocol, but each variant has its own *Read Measured Values* command (datasheet Table 27).
