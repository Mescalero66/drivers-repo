# BH1750 Ambient Light Sensor (ROHM BH1750FVI)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Page: <https://www.adafruit.com/product/4681> (also sold as the GY-302 module)

Datasheet: ROHM BH1750FVI Technical Note, Rev.D (2011.11)

- Digital lux meter with a spectral response close to the human eye, range 1–65535 lx (about 0.11–100000 lx using MTreg)
- I2C address `0x23` (ADDR low, default) or `0x5C` (ADDR high), up to 400 kHz
- Resolution modes: H (1 lx), H2 (0.5 lx), both 120 ms typ / 180 ms max, and L (4 lx), 16 ms typ / 24 ms max
- Continuous or one-time measurement. In one-time mode the sensor powers itself down afterwards (0.01 µA).
- No ID register and no data-ready flag, so the driver works out when results are ready from the conversion times

## Wiring (Raspberry Pi)

| BH1750 board | Pi pin |
|---|---|
| VIN / VCC | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |
| ADDR | leave open or GND for `0x23`, 3.3 V for `0x5C` |

Or use a STEMMA QT / Qwiic cable on the Adafruit board. Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `23` (or `5c`).

## Files

- `bh1750.py`: `BH1750` class.
- `bh1750_test.py`: demo that finds the sensor at either address, takes one-time readings in each resolution, sweeps MTreg, then streams continuous readings while a second task reads the same sensor and a heartbeat task checks that the event loop never blocks.

## Usage

```bash
pip install smbus2
python3 bh1750_test.py
```

```python
import asyncio
from bh1750 import BH1750

async def main():
    async with BH1750() as bh:                      # bus 1, 0x23; powers on, sets MTreg 69; powers down on exit
        print(await bh.measure(BH1750.RES_HIGH2))   # one-time reading, 0.5 lx resolution
        await bh.start_continuous()                 # H mode, waits for the first result
        async for lux in bh.measurements():         # yields each new reading
            print(lux)

asyncio.run(main())
```

| Group | Methods |
|---|---|
| Measurement | `measure`, `start_continuous`, `read_lux`, `wait_lux`, `measurements` |
| Power | `power_on`, `power_down`, `reset`, `close` |
| Sensitivity | `set_mtreg`, `lux_per_count`, `measurement_time`, `transmittance` (constructor argument / attribute) |

Resolutions are `BH1750.RES_HIGH` (default), `RES_HIGH2` and `RES_LOW`.

## Notes

- The API matches the [MicroPython version](../Lux-BH1750-micropython/), plus the `measurements()` async generator (MicroPython has no async generators). `measurement_time()` returns seconds here instead of `measurement_time_ms()`.
- Conversion: lx = count / 1.2 × (69 / MTreg), halved in H2 mode (p11). The 1.2 is typical: individual parts range from 0.96 to 1.44, so adjust `BH1750.ACCURACY` if you calibrate against a reference meter.
- `set_mtreg(31…254)` trades range for resolution. 254 gives 0.11 lx/count in H2 but takes up to 663 ms and tops out around 7400 lx. 31 reaches about 120000 lx (raw) with 81 ms conversions. The datasheet gives the MTreg formula for the H modes only. Like most libraries, this driver also applies it in L mode.
- Behind a cover, pass `transmittance=0.5` (for example) to cancel the cover's loss. Raise MTreg as well if you also want back the resolution the cover costs.
- Adafruit's CircuitPython names differ: their `Resolution.HIGH` is H2 here, `MID` is H, and `LOW` is L.
- The chip has no registers, so the driver uses raw `i2c_rdwr` writes and reads. The usual `read_word_data`-style SMBus calls send a register byte first, which the BH1750 would treat as an opcode.
- The Pi's I2C bus runs at 100 kHz by default, which is fine. Add `dtparam=i2c_arm_baudrate=400000` to `/boot/firmware/config.txt` for 400 kHz.
- A lock makes each command + wait + read sequence atomic, so several tasks can share one sensor. The `smbus2` transfers themselves block, but each takes well under 1 ms. All the conversion waits are non-blocking.
