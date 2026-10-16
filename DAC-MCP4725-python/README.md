# Adafruit MCP4725 12-Bit DAC (Microchip MCP4725)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Page: <https://www.adafruit.com/product/935>

Datasheet: <https://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf> (DS22039D, June 2009)

- Single-channel 12-bit voltage-output DAC with a buffered rail-to-rail output: VOUT = VDD × code / 4096
- VDD is both the supply (2.7–5.5 V) and the reference, so output accuracy depends on how clean the supply is
- I2C address `0x62` on the Adafruit board, or `0x63` with A0 tied to VDD. Standard, fast and high-speed (3.4 MHz) mode
- On-board EEPROM stores the power-up code and power-down mode (factory default: mid-scale, output on)
- 6 µs settling time. The output sags with loads under about 3.5 kΩ (Figure 2-15)
- Power-down modes pull VOUT to GND through 1 kΩ, 100 kΩ or 500 kΩ and draw about 60 nA

## Wiring (Raspberry Pi)

| MCP4725 board | Pi pin |
|---|---|
| VDD | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |
| A0 | leave open for `0x62`, or VDD for `0x63` |
| VOUT | multimeter, or an LED + 330 Ω resistor to GND |

Or use a STEMMA QT / Qwiic cable. Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `62`.

## Files

- `mcp4725.py`: `MCP4725` class and `Status` dataclass (`ready`, `por`, `power_down`, `code`, `eeprom_power_down`, `eeprom_code`).
- `mcp4725_test.py`: demo that reads the status, steps through five voltages, plays a sine wave, cycles the power-down modes, then leaves the output at 0 V. A heartbeat task keeps running throughout.

## Usage

```bash
pip install smbus2
python3 mcp4725_test.py
```

```python
import asyncio
from mcp4725 import MCP4725

async def main():
    async with MCP4725(vref=3.3) as dac:            # checks that the DAC answers
        await dac.set_voltage(1.25)                 # returns the code written (1552)
        await dac.set_code(4095)                    # full scale
        await dac.set_voltage(2.0, persist=True)    # also becomes the power-up value
        print(await dac.read())

asyncio.run(main())
```

Every method is a coroutine apart from the `volts_to_code` / `code_to_volts` conversions. The EEPROM write time is awaited with `asyncio.sleep`, and a lock stops tasks from writing to the DAC at the same time.

| Group | Methods |
|---|---|
| Output | `set_code`, `set_voltage`, `get_code`, `get_voltage`, `fast_write`, `write_dac_and_eeprom`, `volts_to_code`, `code_to_volts` |
| Status | `read` |
| Power | `power_down`, `power_up` |
| General call (bus-wide) | `general_call_reset`, `general_call_wake_up` |

## Notes

- Power the board from the Pi's 3.3 V. The board's I2C pull-ups go to VDD, so powering it from 5 V would pull SDA/SCL above 3.3 V. Set `vref` to match the VDD you use.
- The default address `0x62` is the same as the SCD41's. To use both on one bus, tie the DAC's A0 to VDD and pass `address=0x63`. Some other MCP4725 boards use `0x60` / `0x61`.
- `set_code` / `set_voltage` use the 2-byte fast write and switch the output on. `persist=True` sends the 3-byte DAC + EEPROM write and waits for RDY/BSY (25–50 ms). The chip ignores writes until the EEPROM write finishes, and the lock is held until then.
- The EEPROM is rated for 1 million writes. That is plenty for set points, but don't use `persist=True` inside a waveform loop.
- The general call commands go to address `0x00`, so every device on the bus that supports them responds. `general_call_reset()` reloads every MCP4725 from its EEPROM and also resets an ADS1115, for example. Use `power_down()` / `power_up()` to control just one DAC.
- If VDD rises slower than 1 V/ms, the DAC may not load its EEPROM at power-up. The datasheet recommends a `general_call_reset()` after power-up (§5.4.2).
- Each `smbus2` write blocks for about 0.3 ms at 100 kHz. Waveforms reach a few hundred updates per second when paced with `asyncio.sleep`. For faster updates, raise the bus speed with `dtparam=i2c_arm_baudrate=400000` in `/boot/firmware/config.txt`.
