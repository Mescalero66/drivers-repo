# Generic BMP280 Barometric Pressure Sensor Breakout (Bosch BMP280)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Board: generic 6-pin "GY-BMP280" breakout (VCC, GND, SCL, SDA, CSB, SDO)

Datasheet: Bosch Sensortec BMP280, BST-BMP280-DS001-26, rev 1.26 (October 2021)

- Absolute barometric pressure 300–1100 hPa (about +9000 to -500 m), plus temperature -40 to +85 °C
- Relative accuracy ±0.12 hPa (±1 m), absolute ±1 hPa; resolution 0.16 Pa and 0.01 °C
- Oversampling ×1–×16 per measurement, built-in IIR filter, sleep / forced / normal power modes, 2.7 µA at 1 Hz
- I2C address **`0x76`** (SDO low) or `0x77` (SDO high), up to 3.4 MHz; SPI is not used by this driver
- Chip supply 1.71–3.6 V (4.25 V absolute maximum)

## Wiring (Raspberry Pi)

| BMP280 board | Pi pin |
|---|---|
| VCC | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |
| CSB | not connected (pulled up on the board: selects I2C) |
| SDO | not connected (`0x76`), or 3.3 V for `0x77` |

Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `76`.

Power the board from **3.3 V**. The common purple 6-pin board has no regulator, so 5 V goes straight to the chip. The board pulls SDO low, so the default address is `0x76`. Adafruit's board defaults to `0x77`. Tie SDO to 3.3 V to run two sensors on one bus. If CSB is ever low at power-up, the chip locks into SPI until the next power cycle (§5.1).

## Files

- `bmp280.py`: `BMP280` class and `Measurement` dataclass (`temperature` in °C, `pressure` in Pa).
- `bmp280_test.py`: demo that finds the sensor at either address, reads the chip ID and settings, then:
  - takes forced-mode readings at each oversampling setting, and a temperature-only reading;
  - streams normal-mode readings with the height change from the first reading;
  - keeps a heartbeat task running throughout.

## Usage

```bash
pip install smbus2
python3 bmp280_test.py
```

```python
import asyncio
from bmp280 import BMP280

async def main():
    async with BMP280(bus=1) as bmp:            # 0x76; resets, checks the chip ID, reads calibration; sleeps on exit
        m = await bmp.measure_single_shot()     # forced mode, x16 / x2 oversampling: 43 ms
        print(m.temperature, m.pressure, BMP280.altitude(m.pressure))
        await bmp.apply_preset("handheld_low_power")   # normal mode, IIR 4, 10 Hz
        async for m in bmp.measurements():      # yields each new sample
            print(m.pressure)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). Measurement times are awaited with `asyncio.sleep`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `measure_single_shot`, `read_measurement`, `measurements`, `measurement_time`, `output_data_rate` |
| Settings | `get/set_mode`, `get/set_oversampling`, `get/set_filter`, `get/set_standby`, `apply_preset` |
| Device | `init`, `reset`, `get_chip_id`, `get_status` |
| Altitude (static) | `BMP280.altitude(pressure, sea_level=101325)`, `BMP280.sea_level_pressure(pressure, altitude)` |

## Notes

- `PRESETS` holds the six use cases from Table 7: `handheld_low_power`, `handheld_dynamic`, `weather`, `elevator`, `drop`, `indoor_navigation`. `apply_preset()` starts normal mode for all of them except `weather`. That one stays asleep so you can call `measure_single_shot()` once a minute.
- Oversampling is ×0 (skipped) to ×16. A skipped value comes back as `None`. Pressure also needs the temperature result, so skipping temperature makes both `None`. After `init()` the sensor uses ×16 / ×2 (ultra high resolution). After `reset()` both are skipped until you set them.
- Changing the filter or standby time in normal mode works. The chip may ignore `config` writes in normal mode (§4.3.5), so the driver briefly drops to sleep for the write. Writing the filter also resets it.
- `measurements()` paces itself to the output data rate (Table 14). It re-reads if the sample hasn't changed yet, because the standby timer is only accurate to ±5 % (±25 % max).
- Compensation uses Bosch's 64-bit integer formulas (§3.11.3), the same code as the MicroPython driver. Both platforms therefore give identical results.
- For altitude, pass your local QNH (sea-level pressure from a weather report, in Pa) to `altitude()`. Height differences between readings are accurate to about ±1 m without it. The `pressure` value in Pa can go straight into the SCD41's `set_ambient_pressure()`.
- The temperature is the chip's own temperature, used for compensation. It reads a little above ambient because of self-heating from the PCB (Table 2, note 3).
- Boards sold as BMP280 sometimes carry a BME280 (chip ID `0x60`). The driver accepts it and reads its temperature and pressure (not humidity).
- The I2C transfers themselves are blocking `smbus2` calls, but each takes well under 1 ms. All the waits (up to 43 ms per measurement, and up to 4 s between normal-mode samples) are non-blocking.
