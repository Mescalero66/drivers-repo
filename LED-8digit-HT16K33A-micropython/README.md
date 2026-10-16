# DFRobot DFR0646 8-Digit 7-Segment LED Display (Holtek HT16K33A)

MicroPython drivers for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3: an asynchronous (`asyncio`) driver and the original blocking one.

Datasheet: Holtek HT16K33A, *RAM Mapping 16×8 LED Controller Driver with Keyscan*, v1.11 (June 2026), from <https://www.holtek.com>

- 8 digits with decimal points, multiplexed by the HT16K33A: one COM line per digit, segments a–g and the decimal point on ROW0–7
- I2C address `0x70` (`1110 A2 A1 A0`, so up to `0x77` where the address pins are available), standard and fast mode (≤ 400 kHz)
- 16 brightness steps (PWM duty 1/16–16/16), blinking at 2, 1 or 0.5 Hz, standby at about 1 µA
- The HT16K33A is specified for a 4.5–5.5 V supply

## Wiring

| DFR0646 | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VCC | VBUS 5 V (pin 40), see warning below | 5V, see warning below |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6) | GPIO 8 |
| SCL | GP5 (pin 7) | GPIO 9 |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` in `HT16K33LED_async_test.py` to match your board.

> **Warning: check the board's I2C pull-ups before powering VCC from 5 V.**
> The HT16K33A is specified for VDD = 4.5–5.5 V, which is why the table above uses 5 V. A 3.3 V supply is out of the chip's spec.
> 5 V is only safe if the DFR0646's SDA/SCL pull-ups do **not** go to VCC. If they do, they put 5 V on the Pico's or ESP32's I2C pins, which are 3.3 V-only.
> The datasheet also requires an SDA/SCL logic high of at least 0.7 × VDD (3.5 V at 5 V), which is above the 3.3 V these boards drive. Without a level shifter it may work, but it is out of spec.
> Check the DFRobot wiki or schematic for the DFR0646's pull-ups and any level shifting before wiring.

## Files

- `HT16K33LED_async.py`: asynchronous `HT16K33LED` class. It initialises in the datasheet order, clearing display memory before turning the display on. It also handles brightness, blinking, standby/wake, left/right-aligned strings with decimal points, scrolling, 180° rotation, raw glyphs and display-memory read-back.
- `HT16K33LED_async_test.py`: demo of a segment test with memory read-back, text alignment, brightness, blink rates, rotation, a fast counter, scrolling and standby, while a heartbeat task keeps running. It picks Pico or ESP32 pins from `sys.platform`.
- `HT16K33LED.py`: the original blocking driver (`HT16K33` base class and `HT16K33LED`), based on code by Tony Smith ([@smittytone](https://github.com/smittytone)).
- `LED_8Digit.py`: demo for the blocking driver. `testing/LED_8Digit_orig.py`: the original demo.

## Usage

Copy the driver and the demo to the board (e.g. `mpremote cp HT16K33LED_async.py HT16K33LED_async_test.py :`), then run `mpremote run HT16K33LED_async_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from HT16K33LED_async import HT16K33LED

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with HT16K33LED(i2c) as display:          # initialises with a blank display, standby on exit
        await display.set_brightness(8)
        await display.set_string("-12.5°C", "r")    # each '.' lights the decimal point of the digit before it
        await asyncio.sleep(2)
        await display.scroll("Hello there")         # other tasks keep running between steps

asyncio.run(main())
```

Methods that talk to the chip are coroutines. A lock keeps multi-command sequences (start-up, standby, wake) together when several tasks share the display. Buffer methods are plain functions that return `self` for chaining. They change only the local buffer, so call `draw()` afterwards.

| Group | Methods |
|---|---|
| Setup and power | `begin`, `power_on`, `power_off`, `set_brightness`, `set_blink_rate` |
| Display memory | `draw`, `read_ram`, `set_string`, `scroll` |
| Buffer (no I/O) | `clear`, `rotate`, `set_glyph`, `set_character`, `set_number` |

## Notes

- Display memory holds random data at power-up, so both drivers write the buffer between switching the oscillator on and turning the display on (datasheet p.14). In standby the chip ignores every command except the system-setup command, so `draw()` has no effect after `power_off()`. `power_on()` re-sends the buffer.
- Text options: `set_string` truncates text longer than the display, and `scroll` shows all of it. A `.` joins the character before it, and a leading or doubled `.` gets a digit of its own. Unsupported characters raise `ValueError`. Letters are approximations on 7 segments (e.g. `s` = `5`, `z` = `2`, `x` = `h`), and `set_glyph` takes any raw segment pattern.
- `rotate()` turns the display 180° for upside-down mounting. The decimal points then light on the other side of each digit.
- The chip's key-scan inputs and INT pin are not supported, because the DFR0646 has no keys. `begin()` sets the ROW/INT pin to a row output explicitly instead of relying on the power-on default.
- Blocking driver: `power_on()` now writes the buffer before turning the display on, and `update()` now honours `rotate()` (it previously skipped the rotation).
