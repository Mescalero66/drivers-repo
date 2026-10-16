# Sensirion SEN62 Particulate Matter, Temperature & Humidity Sensor (SEN62-SIN-T)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Page: <https://sensirion.com/products/catalog/SEN62>

Datasheet: SEN6x Datasheet v1.0 (October 2026), which covers the whole SEN6x family

- Laser-scattering PM sensor with a fan, plus compensated temperature & humidity (SHT4x inside)
- PM1.0 / PM2.5 / PM4.0 / PM10 mass concentration (0–1000 µg/m³ specified) and PM0.5–PM10 number concentration
- PM2.5 precision ±(5 µg/m³ + 5 %) up to 100 µg/m³. Temperature ±0.45 °C, RH ±4.5 %RH typical
- I2C address `0x6B` (fixed), **standard mode only (≤ 100 kHz)**, no clock stretching (the sensor NACKs while busy)
- Supply 3.15–3.6 V, about 75 mA while measuring (130 mA peaks). SDA/SCL are 5 V tolerant
- New reading every second. PM values are stable about 30 s after starting

## Wiring (Raspberry Pi)

The sensor has a 6-pin 1.25 mm connector (mating plug JST GHR-06V-S). Keep the cable short: under 10 cm is recommended, 50 cm is the maximum.

| SEN62 pin | Pi pin |
|---|---|
| 1 VDD | 3.3 V (pin 1) |
| 2 GND | GND (pin 6) |
| 3 SDA | GPIO 2 / SDA (pin 3) |
| 4 SCL | GPIO 3 / SCL (pin 5) |
| 5 GND, 6 VDD | leave unconnected (they are joined to pins 2 and 1 inside the sensor) |

The Pi's bus 1 already has pull-ups, and its default speed is 100 kHz. Don't raise `i2c_arm_baudrate`. Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `6b`.

## Files

- `sen62.py`: `SEN62` class, plus `Measurement`, `NumberConcentration` and `DeviceStatus` dataclasses.
- `sen62_test.py`: demo that reads the product info, firmware version and status, then takes 10 readings (mass and number concentrations, RH, T) while a heartbeat task keeps running. Flags at the top turn on fan cleaning and the SHT heater.

## Usage

```bash
pip install smbus2
python3 sen62_test.py
```

```python
import asyncio
from sen62 import SEN62

async def main():
    async with SEN62() as sen:                  # stops any running measurement and resets the sensor
        await sen.start_continuous_measurement()
        async for m in sen.measurements():      # yields each new reading (every second)
            print(m.pm2_5, m.pm10_0, m.humidity, m.temperature)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet command. Command execution times (20 ms to 1.4 s) are awaited with `asyncio.sleep`, and a lock stops tasks from sending commands to the sensor at the same time.

| Group | Methods |
|---|---|
| Measurement | `start_continuous_measurement`, `stop_measurement`, `get_data_ready`, `read_measured_values`, `measurements`, `read_measured_raw_values`, `read_number_concentration_values` |
| Temperature compensation | `set_temperature_offset_parameters`, `set_temperature_acceleration_parameters` |
| Device info / status | `get_product_type`, `get_product_name`, `get_serial_number`, `get_version`, `read_device_status`, `read_and_clear_device_status` |
| Maintenance | `device_reset`, `start_fan_cleaning`, `activate_sht_heater`, `get_sht_heater_measurements` |

## Notes

- Values the sensor reports as unknown are returned as `None` (sent as 0xFFFF / 0x7FFF). This happens, for example, before the first reading after a start.
- In measurement mode the sensor accepts only reads, status, device info and `set_temperature_offset_parameters`. Reset, fan cleaning, the SHT heater and acceleration parameters need idle mode, so call `stop_measurement()` (1.4 s) first.
- All settings are volatile and are lost on reset or power-off, so reapply temperature offsets at startup. If the sensor is mounted near something warm, use offset slots 1–4 for heat sources that switch on and off.
- The PM, RH&T and fan error flags are sticky. Clear them with `read_and_clear_device_status()`. The fan-speed warning clears itself.
- `start_fan_cleaning()` runs the fan at full speed and returns after 10 s. After `activate_sht_heater()`, wait 20 s before measuring. `get_sht_heater_measurements()` needs firmware 6.0 or later.
- Only the SEN62 commands are included. The rest of the SEN6x family uses the same protocol, but each variant has its own *Read Measured Values* command (datasheet Table 27).
- The I2C transfers are blocking `smbus2` calls, but the longest (a 48-byte string) takes about 5 ms. All the long waits are non-blocking.
