# Adafruit MCP4725 12-Bit DAC (Microchip MCP4725)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://www.adafruit.com/product/935>

Datasheet: <https://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf> (DS22039D, June 2009)

- Single-channel 12-bit voltage-output DAC with a buffered rail-to-rail output: VOUT = VDD × code / 4096
- VDD is both the supply (2.7–5.5 V) and the reference, so output accuracy depends on how clean the supply is
- I2C address `0x62` on the Adafruit board, or `0x63` with A0 tied to VDD. Standard, fast and high-speed (3.4 MHz) mode
- On-board EEPROM stores the power-up code and power-down mode (factory default: mid-scale, output on)
- 6 µs settling time. The output sags with loads under about 3.5 kΩ (Figure 2-15)
- Power-down modes pull VOUT to GND through 1 kΩ, 100 kΩ or 500 kΩ and draw about 60 nA

## Wiring

| MCP4725 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VDD | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6) | GPIO 8 |
| SCL | GP5 (pin 7) | GPIO 9 |
| A0 | leave open for `0x62`, or VDD for `0x63` | same |
| VOUT | optional loopback: GP26 / ADC0 (pin 31) | optional loopback: any ADC1 pin |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` in `mcp4725_test.py` to match your board. For example, the Adafruit QT Py ESP32-C3's STEMMA QT port uses SDA 5 / SCL 6.

## Files

- `mcp4725.py`: `MCP4725` class and `Status` namedtuple (`ready`, `por`, `power_down`, `code`, `eeprom_power_down`, `eeprom_code`).
- `mcp4725_test.py`: demo that scans the bus, reads the status, steps through five voltages, plays a sine wave, cycles the power-down modes, then leaves the output at 0 V. A heartbeat task keeps running throughout. It picks Pico or ESP32 pins from `sys.platform`. Set `ADC_PIN` to the pin wired to VOUT, and the demo also measures each voltage step.

## Usage

Copy both files to the board (e.g. `mpremote cp mcp4725.py mcp4725_test.py :`), then run `mpremote run mcp4725_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from mcp4725 import MCP4725

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with MCP4725(i2c, vref=3.3) as dac:       # checks that the DAC answers
        await dac.set_voltage(1.25)                 # returns the code written (1552)
        await dac.set_code(4095)                    # full scale
        await dac.set_voltage(2.0, persist=True)    # also becomes the power-up value
        print(await dac.read())

asyncio.run(main())
```

Every method is a coroutine apart from the `volts_to_code` / `code_to_volts` conversions. The EEPROM write time is awaited with `asyncio.sleep_ms`, and a lock stops tasks from writing to the DAC at the same time.

| Group | Methods |
|---|---|
| Output | `set_code`, `set_voltage`, `get_code`, `get_voltage`, `fast_write`, `write_dac_and_eeprom`, `volts_to_code`, `code_to_volts` |
| Status | `read` |
| Power | `power_down`, `power_up` |
| General call (bus-wide) | `general_call_reset`, `general_call_wake_up` |

## Notes

- The API matches the [CPython version](../DAC-MCP4725-python/).
- Power the board from 3.3 V. The board's I2C pull-ups go to VDD, so powering it from 5 V would pull SDA/SCL above 3.3 V. Set `vref` to match the VDD you use.
- The default address `0x62` is the same as the SCD41's. To use both on one bus, tie the DAC's A0 to VDD and pass `address=0x63`. Some other MCP4725 boards use `0x60` / `0x61`.
- `set_code` / `set_voltage` use the 2-byte fast write and switch the output on. `persist=True` sends the 3-byte DAC + EEPROM write and waits for RDY/BSY (25–50 ms). The chip ignores writes until the EEPROM write finishes, and the lock is held until then.
- The EEPROM is rated for 1 million writes. That is plenty for set points, but don't use `persist=True` inside a waveform loop.
- The general call commands go to address `0x00`, so every device on the bus that supports them responds. `general_call_reset()` reloads every MCP4725 from its EEPROM and also resets an ADS1115, for example. Use `power_down()` / `power_up()` to control just one DAC.
- If VDD rises slower than 1 V/ms, the DAC may not load its EEPROM at power-up. The datasheet recommends a `general_call_reset()` after power-up (§5.4.2).
- Loopback readings are approximate. The Pico's ADC has a few LSB of error and is referenced to its own 3.3 V rail. ESP32 ADCs saturate below 3.3 V (about 2.5 V on the C3, about 3.1 V on the S3), so the top steps read low.
