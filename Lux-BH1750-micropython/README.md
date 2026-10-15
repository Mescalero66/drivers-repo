# BH1750 Ambient Light Sensor (ROHM BH1750FVI)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://www.adafruit.com/product/4681> (also sold as the GY-302 module)

Datasheet: ROHM BH1750FVI Technical Note, Rev.D (2011.11)

- Digital lux meter with a spectral response close to the human eye, range 1–65535 lx (about 0.11–100000 lx using MTreg)
- I2C address `0x23` (ADDR low, default) or `0x5C` (ADDR high), up to 400 kHz
- Resolution modes: H (1 lx), H2 (0.5 lx), both 120 ms typ / 180 ms max, and L (4 lx), 16 ms typ / 24 ms max
- Continuous or one-time measurement. In one-time mode the sensor powers itself down afterwards (0.01 µA).
- No ID register and no data-ready flag, so the driver works out when results are ready from the conversion times

## Wiring

| BH1750 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VIN / VCC | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6) | GPIO 8 |
| SCL | GP5 (pin 7) | GPIO 9 |
| ADDR | leave open or GND for `0x23` | |

Change `SDA` / `SCL` in `bh1750_test.py` to match your board.

## Files

- `bh1750.py`: `BH1750` class.
- `bh1750_test.py`: demo that takes one-time readings in each resolution, sweeps MTreg, then streams continuous readings while a second task reads the same sensor and a heartbeat task checks that the event loop never blocks. It picks Pico or ESP32 pins from `sys.platform`, and finds the sensor at either address.

## Usage

Copy both files to the board (`mpremote cp bh1750.py bh1750_test.py :`), then run `mpremote run bh1750_test.py`.

```python
import asyncio
from machine import I2C, Pin
from bh1750 import BH1750

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with BH1750(i2c) as bh:                   # powers on, sets MTreg 69; powers down on exit
        print(await bh.measure(BH1750.RES_HIGH2))   # one-time reading, 0.5 lx resolution
        await bh.start_continuous()                 # H mode, waits for the first result
        while True:
            print(await bh.wait_lux())              # returns each new reading

asyncio.run(main())
```

| Group | Methods |
|---|---|
| Measurement | `measure`, `start_continuous`, `read_lux`, `wait_lux` |
| Power | `power_on`, `power_down`, `reset` |
| Sensitivity | `set_mtreg`, `lux_per_count`, `measurement_time_ms`, `transmittance` (constructor argument / attribute) |

Resolutions are `BH1750.RES_HIGH` (default), `RES_HIGH2` and `RES_LOW`.

## Notes

- Conversion: lx = count / 1.2 × (69 / MTreg), halved in H2 mode (p11). The 1.2 is typical: individual parts range from 0.96 to 1.44, so adjust `BH1750.ACCURACY` if you calibrate against a reference meter.
- `set_mtreg(31…254)` trades range for resolution. 254 gives 0.11 lx/count in H2 but takes up to 663 ms and tops out around 7400 lx. 31 reaches about 120000 lx (raw) with 81 ms conversions. The datasheet gives the MTreg formula for the H modes only. Like most libraries, this driver also applies it in L mode.
- Behind a cover, pass `transmittance=0.5` (for example) to cancel the cover's loss. Raise MTreg as well if you also want back the resolution the cover costs.
- Adafruit's CircuitPython names differ: their `Resolution.HIGH` is H2 here, `MID` is H, and `LOW` is L.
- `wait_lux()` has no data-ready flag to poll, so it waits one worst-case conversion time after the previous read. That guarantees a new sample.
- A lock makes each command + wait + read sequence atomic, so several tasks can share one sensor. `measure()` holds the lock for the whole conversion, because any other command would abort it.
