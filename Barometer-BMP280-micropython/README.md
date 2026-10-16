# Generic BMP280 Barometric Pressure Sensor Breakout (Bosch BMP280)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Board: generic 6-pin "GY-BMP280" breakout (VCC, GND, SCL, SDA, CSB, SDO)

Datasheet: Bosch Sensortec BMP280, BST-BMP280-DS001-26, rev 1.26 (October 2021)

- Absolute barometric pressure 300–1100 hPa (about +9000 to -500 m), plus temperature -40 to +85 °C
- Relative accuracy ±0.12 hPa (±1 m), absolute ±1 hPa; resolution 0.16 Pa and 0.01 °C
- Oversampling ×1–×16 per measurement, built-in IIR filter, sleep / forced / normal power modes, 2.7 µA at 1 Hz
- I2C address **`0x76`** (SDO low) or `0x77` (SDO high), up to 3.4 MHz; SPI is not used by this driver
- Chip supply 1.71–3.6 V (4.25 V absolute maximum)

## Wiring

| BMP280 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VCC | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SCL | GP5 (pin 7) | GPIO 9 |
| SDA | GP4 (pin 6) | GPIO 8 |
| CSB | not connected (pulled up on the board: selects I2C) | not connected |
| SDO | not connected (`0x76`), or 3V3 for `0x77` | not connected |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` in `bmp280_test.py` to match your board.

Power the board from **3.3 V**. The common purple 6-pin board has no regulator, so 5 V goes straight to the chip. The board has pull-ups on SDA/SCL and pulls CSB high, which selects I2C. If CSB is ever low at power-up, the chip locks into SPI until the next power cycle (§5.1). The board pulls SDO low, so the default address is `0x76`. Adafruit's board defaults to `0x77`. Tie SDO to 3V3 to run two sensors on one bus.

## Files

- `bmp280.py`: `BMP280` class and `Measurement` namedtuple (`temperature` in °C, `pressure` in Pa).
- `bmp280_test.py`: demo that scans the bus, reads the chip ID and settings, then:
  - takes forced-mode readings at each oversampling setting, and a temperature-only reading;
  - streams normal-mode readings with the height change from the first reading;
  - keeps a heartbeat task running throughout.
  
  It picks Pico or ESP32 pins from `sys.platform`.

## Usage

Copy both files to the board (e.g. `mpremote cp bmp280.py bmp280_test.py :`), then run `mpremote run bmp280_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from bmp280 import BMP280

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with BMP280(i2c) as bmp:              # 0x76; resets, checks the chip ID, reads calibration; sleeps on exit
        m = await bmp.measure_single_shot()     # forced mode, x16 / x2 oversampling: 43 ms
        print(m.temperature, m.pressure, BMP280.altitude(m.pressure))
        await bmp.apply_preset("handheld_low_power")   # normal mode, IIR 4, 10 Hz
        while True:
            m = await bmp.wait_measurement()    # returns each new sample
            print(m.pressure)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). Measurement times are awaited with `asyncio.sleep_ms`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `measure_single_shot`, `read_measurement`, `wait_measurement`, `measurement_ms`, `output_data_rate` |
| Settings | `get/set_mode`, `get/set_oversampling`, `get/set_filter`, `get/set_standby`, `apply_preset` |
| Device | `init`, `reset`, `get_chip_id`, `get_status` |
| Altitude (static) | `BMP280.altitude(pressure, sea_level=101325)`, `BMP280.sea_level_pressure(pressure, altitude)` |

## Notes

- The API matches the [Python version](../Barometer-BMP280-python/) except in two places. MicroPython has no async generators, so `measurements()` becomes `wait_measurement()`, which returns one reading per call. `measurement_time()` (seconds) becomes `measurement_ms()`.
- Compensation uses Bosch's 64-bit integer formulas (§3.11.3). MicroPython integers grow as needed, so the result is exact. The floating-point formula would lose accuracy, because Pico and ESP32 floats are single precision.
- `PRESETS` holds the six use cases from Table 7: `handheld_low_power`, `handheld_dynamic`, `weather`, `elevator`, `drop`, `indoor_navigation`. `apply_preset()` starts normal mode for all of them except `weather`. That one stays asleep so you can call `measure_single_shot()` once a minute.
- Oversampling is ×0 (skipped) to ×16. A skipped value comes back as `None`. Pressure also needs the temperature result, so skipping temperature makes both `None`. After `init()` the sensor uses ×16 / ×2 (ultra high resolution). After `reset()` both are skipped until you set them.
- Changing the filter or standby time in normal mode works. The chip may ignore `config` writes in normal mode (§4.3.5), so the driver briefly drops to sleep for the write. Writing the filter also resets it.
- `wait_measurement()` paces itself to the output data rate (Table 14). It re-reads if the sample hasn't changed yet, because the standby timer is only accurate to ±5 % (±25 % max).
- For altitude, pass your local QNH (sea-level pressure from a weather report, in Pa) to `altitude()`. Height differences between readings are accurate to about ±1 m without it. The `pressure` value in Pa can go straight into the SCD41's `set_ambient_pressure()`.
- The temperature is the chip's own temperature, used for compensation. It reads a little above ambient because of self-heating from the PCB (Table 2, note 3).
- Keep strong light off the vent hole, because it can shift the readings (§7.6). Boards sold as BMP280 sometimes carry a BME280 (chip ID `0x60`). The driver accepts it and reads its temperature and pressure (not humidity).
