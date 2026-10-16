# Texas Instruments ADS1115 16-bit 4-channel ADC

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Datasheet: <https://www.ti.com/product/ADS1115> (SBAS444E, December 2024)

- 16-bit delta-sigma ADC: 4 single-ended or 2 differential inputs, through a MUX and programmable gain amplifier
- Full-scale range ±6.144 / 4.096 / 2.048 / 1.024 / 0.512 / 0.256 V, 8–860 samples per second
- I2C address `0x48`–`0x4B` (set by the ADDR pin), up to 400 kHz
- Supply 2.0–5.5 V, 150 µA converting, 0.5 µA powered down
- ALERT/RDY pin: conversion-ready pulse or threshold comparator
- **Needs external pull-up resistors on SDA and SCL** (see [Pull-up resistors](#pull-up-resistors-required))

## Wiring

| ADS1115 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VDD | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6), **plus pull-up to 3.3 V** | GPIO 8, **plus pull-up to 3.3 V** |
| SCL | GP5 (pin 7), **plus pull-up to 3.3 V** | GPIO 9, **plus pull-up to 3.3 V** |
| ALERT/RDY (optional) | any GPIO, e.g. GP6 | any GPIO |
| A0–A3 | signals, 0 V to VDD | |

| ADDR connected to | GND | VDD | SDA | SCL |
|---|---|---|---|---|
| I2C address | `0x48` | `0x49` | `0x4A` | `0x4B` |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` / `RDY_PIN` in `adc_ads1115_test.py` to match your board.

### Pull-up resistors (required)

SDA and SCL are open-drain, so the bus needs one pull-up resistor on each line to 3.3 V. TI recommends 1–10 kΩ (§9.1.1). The internal pull-ups of the Pico and ESP32 are about 50 kΩ, too weak to rely on.

- Many breakout boards (Adafruit 1085, most blue "ADS1115 module" boards) already have 10 kΩ pull-ups. Check yours before adding more. A bare chip always needs them.
- Pull up to **3.3 V**, not 5 V, even if the ADS1115 runs from 5 V, so the Pico and ESP32 pins only ever see 3.3 V.
- One set of pull-ups per bus is enough, even with four ADS1115s.
- ALERT/RDY is open-drain too. The driver enables the GPIO's internal pull-up, which is enough for that pin.

## Files

- `adc_ads1115.py`: `ADS1115` class, plus the `GAINS` and `RATES` tables.
- `adc_ads1115_test.py`: demo that finds the chip, reads all four channels at once from separate tasks, does a differential read, sweeps the gain, times each data rate, then runs continuous mode while a heartbeat task keeps running.

## Usage

Copy both files to the board (e.g. `mpremote cp adc_ads1115.py adc_ads1115_test.py :`), then run `mpremote run adc_ads1115_test.py`.

```python
import asyncio
from machine import I2C, Pin
from adc_ads1115 import ADS1115

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with ADS1115(i2c, gain=4.096, rate=128) as adc:   # powers down on exit
        print(await adc.read_voltage(0))        # AIN0 vs GND
        print(await adc.read_voltage(0, 1))     # AIN0 - AIN1

asyncio.run(main())
```

| Group | Methods |
|---|---|
| Single shot | `read`, `read_voltage` |
| Continuous | `start_continuous`, `read_latest`, `wait_conversion` |
| Comparator | `start_comparator`, `wait_alert` |
| Power / reset | `power_down`, `general_call_reset` |
| Conversion | `raw_to_v`, `v_to_raw`, attributes `gain` (±V) and `rate` (SPS) |

## Notes

- **Input limits:** never apply more than VDD + 0.3 V or less than GND − 0.3 V to any input, whatever the range. ±6.144 V and ±4.096 V only set the scaling, so at VDD = 3.3 V the most you can measure is 3.3 V. Single-ended reads use codes 0 to +32767, and can read slightly negative near 0 V because of offset.
- `read()` waits one conversion time (1/DR, 1.2 ms to 125 ms) with `asyncio.sleep_ms`, then checks the OS bit, so the bus is free for other devices while the ADC converts. A lock serialises tasks, so concurrent reads of different channels are safe.
- Slower rates have less noise: at ±2.048 V, peak-to-peak noise is 62.5 µV (1 LSB) up to 128 SPS and 119 µV at 860 SPS (Table 6-1).
- Changing `gain` or `rate` takes effect on the next `read()`, `start_continuous()` or `start_comparator()`. Comparator thresholds are stored as codes, so call `start_comparator()` again after changing `gain`.
- With `rdy_pin`, `wait_conversion()` / `wait_alert()` sleep on a pin interrupt (`asyncio.ThreadSafeFlag`) and use no I2C until data is ready. Only one task at a time can wait on the pin. Without it, `wait_conversion()` sleeps one conversion time.
- A latched alert stays asserted until the conversion register is read. `wait_alert()` does that read.
- `general_call_reset()` resets every device on the bus that responds to the I2C general call, not just the ADS1115.
- Add a 0.1 µF capacitor between VDD and GND close to the chip (most breakout boards have one).
