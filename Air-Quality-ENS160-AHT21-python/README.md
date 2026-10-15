# ENS160 + AHT21 air quality and climate board

Python driver for a Raspberry Pi and the common blue combo board that puts a ScioSense ENS160 air-quality sensor and an ASAIR (Aosong) AHT21 temperature/humidity sensor on one I2C bus. The ENS160 does the air-quality sensing. The AHT21 only measures temperature and humidity at the ENS160 so the ENS160 can compensate for them.

Ported from [Air-Quality-ENS160-AHT21-micropython](../Air-Quality-ENS160-AHT21-micropython/), with the same classes and methods. Written from the datasheets:

- ScioSense ENS160 datasheet v1.3 (2023-03-29). Comments cite it as "ENS §".
- ASAIR AHT21 datasheet v1.0 (May 2021). Comments cite it as "AHT §".

## The board

| Pin | Use |
|---|---|
| VIN | 3.3–5 V supply. The board makes the ENS160's 1.8 V itself |
| 3V3 | 3.3 V |
| GND | Ground |
| SCL, SDA | I2C, shared by both sensors |
| ADD | ENS160 address select: high gives `0x53`, low gives `0x52` |
| CS | ENS160 interface select. Leave it high: pulling it low switches the ENS160 to SPI until the next power cycle (ENS §14) |
| INT | ENS160 interrupt output (optional, see `configure_interrupt`) |

| | ENS160 | AHT21 |
|---|---|---|
| I2C address | `0x53` / `0x52` | `0x38` (fixed) |
| Max clock | 1 MHz | **400 kHz**, so this is the limit for the bus |
| Ready after power-on | Immediately. Readings are reliable after a 3 min warm-up, or 1 h the first time a new sensor is powered | 100 ms |
| Protocol | Little-endian registers with auto-increment | Commands, then a 7-byte read with CRC-8 |

## Wiring to the Raspberry Pi

| Board | Pi header pin |
|---|---|
| VIN | 1 (3.3 V) |
| GND | 6 (GND) |
| SDA | 3 (GPIO2, SDA1) |
| SCL | 5 (GPIO3, SCL1) |
| ADD, CS, INT | Not connected |

Power the board from the Pi's **3.3 V**, not 5 V. The Pi's GPIO pins are 3.3 V only. If the board's SDA/SCL pull-up resistors go to VIN, 5 V on VIN would put 5 V on the Pi's pins.

## Setup

1. Turn on I2C: `sudo raspi-config` → Interface Options → I2C. Or add `dtparam=i2c_arm=on` to `/boot/firmware/config.txt` (`/boot/config.txt` on Bullseye and earlier) and reboot.
2. Install `smbus2`: `sudo apt install python3-smbus2`, or `pip install smbus2` inside a virtual environment.
3. Check both chips are on the bus: `i2cdetect -y 1` should show `38` and `53` (or `52`).
4. Your user needs to be in the `i2c` group (the default `pi`/first user is).

The Pi's I2C runs at 100 kHz by default, which suits both chips. To change it, add `dtparam=i2c_arm_baudrate=<Hz>` to `config.txt`. Don't go above 400000, the AHT21's limit.

## Files

- `ens160_aht21.py`: driver with the `I2C` bus wrapper, the `AHT21`, `ENS160` and combined `ENS160_AHT21` classes, plus the `Reading`, `AirQuality` and `Status` namedtuples.
- `ens160_aht21_test.py`: blocking demo. Prints a reading every 2 seconds until Ctrl+C.
- `ens160_aht21_test_async.py`: `asyncio` demo, with a heartbeat task to show the loop doesn't block.

## Usage

```python
from ens160_aht21 import I2C, ENS160_AHT21

with I2C(1) as i2c:                             # /dev/i2c-1, closed on exit
    board = ENS160_AHT21(i2c)                   # finds the ENS160 at 0x53 or 0x52
    board.begin()                               # checks both chips, starts gas sensing
    r = board.read()                            # AHT21 -> ENS160 compensation -> air quality
    print(r.aqi, r.tvoc, r.eco2, r.validity, r.pcb_temp, r.pcb_humi)
```

Each `read()` measures temperature and humidity with the AHT21 and writes them to the ENS160's `TEMP_IN`/`RH_IN` for compensation (ENS §8.2). It then reads AQI, TVOC and eCO2 together in one transfer.
- `pcb_temp` (°C) and `pcb_humi` (%RH) are the AHT21 values sent to the ENS160. They describe the air on the board, warmed by the ENS160 heater, so they will read warmer and drier than the room.
- `board.ens160.compensation()` reads the values back from the ENS160 (`DATA_T`/`DATA_RH`) if you want to confirm they arrived.
- `read_async()` does the same as `read()`, but other tasks run during the AHT21's 80 ms conversion.

`I2C(bus)` takes a bus number or an already-open `smbus2.SMBus`. It provides the same `readfrom`, `writeto`, `readfrom_mem` and `writeto_mem` methods as MicroPython's `machine.I2C`, which is why the sensor classes match the MicroPython driver line for line.

The two sensor classes also work on their own:

| Class | Methods |
|---|---|
| `AHT21` | `begin`, `status`, `trigger` + `result` (split measurement), `measure`, `measure_async`, `crc8` |
| `ENS160` | `begin`, `part_id`, `set_mode` / `mode`, `reset`, `firmware_version`, `configure_interrupt`, `status`, `read`, `wait_data`, `wait_data_async`, `raw_resistance`, `set_compensation`, `compensation`, `eco2_rating` |

## Notes

- **Why every transfer uses `i2c_rdwr`.** The AHT21 has no registers. You write a 3-byte command and read back 7 bytes. SMBus block calls such as `read_i2c_block_data` always send a register byte first, which the AHT21 would misread. `i2c_rdwr` sends exactly the messages given, so the driver uses it for everything. ENS160 register reads become a register-address write, a repeated START, then the read (ENS §14.1.3).
- **Compensation uses the raw AHT21 values.** The ENS160's metal-oxide sensing films react to water vapour as well as to VOCs. The compensation tells its algorithm how much water vapour is present so it can remove that effect (ENS §8.2). What matters is the air at the ENS160 itself, and the AHT21, a few millimetres away and warmed by the same heater, measures exactly that. So the ENS160 always gets the raw AHT21 readings. It falls back to 25 °C / 50 %RH if it never gets any.
- **Measurement rate.** AHT §4.4 asks for no more than one measurement per second, so the AHT21 doesn't heat itself. `ENS160_AHT21.read()` only measures and updates the compensation once a second, however often it is called.
- **Validity.** Check `Reading.validity` before trusting readings: 0 normal, 1 warm-up, 2 initial start-up, 3 invalid (`ENS160.VALIDITY` has the text). Restarting the script restarts warm-up, because `begin()` writes STANDARD mode again. Leaving STANDARD mode does too, and that includes `firmware_version()`, because commands only run in IDLE.
- **One owner at a time.** The driver has no locking. Use the board from one thread, or one asyncio task, at a time.
- **Intermittent I/O errors.** Raspberry Pi 1–4 I2C hardware handles clock stretching poorly. If you see occasional `OSError`s, try a lower bus speed (e.g. `dtparam=i2c_arm_baudrate=50000`), and keep the wires short.
- **AHT21 "0x71".** AHT §7.4 says to "send 0x71" to get the status byte. `0x71` is just the read address byte, `(0x38 << 1) | 1`, so this is a plain 1-byte read, not a command.
- **AHT21 initialisation.** If status bits 3 and 4 aren't both set, AHT §7.4 says to initialise registers 0x1B, 0x1C and 0x1E, and refers to ASAIR's example code for how. `AHT21.begin()` follows that example code. Genuine parts normally report 0x18 and skip this step.
- **Datasheet errors.**
  - ENS160 Table 32 shows the `DATA_T` bytes the wrong way round (the register is little endian like the rest).
  - The `DATA_MISR` example code in ENS §16.2.14 has an operator-precedence bug and defines `misr_set()` twice. `ENS160.read(verify=True)` uses a corrected version. It is untested on hardware, because the datasheet is unclear about when the checksum resets.
