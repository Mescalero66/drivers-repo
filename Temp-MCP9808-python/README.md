# DFRobot SEN0435 High Accuracy Temperature Sensor (Microchip MCP9808)

Asynchronous (`asyncio`) Python driver for Raspberry Pi, using `smbus2`.

Page: <https://wiki.dfrobot.com/sen0435/>

Datasheet: Microchip MCP9808, DS20005095B (May 2018)

- Digital temperature sensor, ±0.25 °C typical, ±0.5 °C max from -20 °C to 100 °C (±1 °C max from -40 °C to +125 °C)
- Selectable resolution: 0.5 / 0.25 / 0.125 / 0.0625 °C, converting in 30 / 65 / 130 / 250 ms
- Programmable upper, lower and critical limits, with hysteresis, driving an open-drain Alert (ALT) output
- Shutdown mode at 0.1 µA. Supply 2.7–5.5 V, 200 µA while converting
- I2C up to 400 kHz, address `0x18`–`0x1F`. The DFRobot board pulls A0–A2 high, so its default is **`0x1F`**

## Wiring (Raspberry Pi)

| SEN0435 board | Pi pin |
|---|---|
| VCC | 3.3 V (pin 1) |
| GND | GND (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |
| ALT | optional, any GPIO (open-drain, needs a pull-up) |
| A0 / A1 / A2 | leave open for `0x1F`, or tie to GND to clear that bit |

Power the board from 3.3 V. The chip runs directly from VCC, so 5 V would put 5 V logic on the I2C lines. Enable I2C with `sudo raspi-config` and check that `i2cdetect -y 1` shows `1f`.

The address is `0x18 + 4·A2 + 2·A1 + A0`. For example, A0 tied to GND gives `0x1E`, and all three tied to GND give `0x18`. Up to eight boards can share a bus.

## Files

- `mcp9808.py`: `MCP9808` class and `Measurement` dataclass (`temperature`, `above_critical`, `above_upper`, `below_lower`).
- `mcp9808_test.py`: demo that finds the sensor at any address, reads the IDs and settings, sweeps the resolutions, streams readings, takes a single shot from shutdown, then sets up the alert output while a heartbeat task keeps running.

## Usage

```bash
pip install smbus2
python3 mcp9808_test.py
```

```python
import asyncio
from mcp9808 import MCP9808

async def main():
    async with MCP9808() as mcp:            # bus 1, 0x1F; checks the ID, starts converting; shuts down on exit
        print(await mcp.read_temperature())
        async for m in mcp.measurements():  # yields a new reading every conversion (~0.3 s at 0.0625 °C)
            print(m.temperature)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). Conversion times are awaited with `asyncio.sleep`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `read_temperature`, `read_measurement`, `measurements`, `measure_single_shot`, `conversion_time`, `get/set_resolution` |
| Power | `shutdown`, `wake_up`, `reset`, `close` |
| Alert | `get/set_upper_limit`, `get/set_lower_limit`, `get/set_critical_limit`, `get/set_hysteresis`, `configure_alert`, `get_alert_status`, `wait_alert`, `clear_interrupt`, `lock_limits` |
| ID / raw | `get_manufacturer_id`, `get_device_id`, `get_config` |

## Notes

- `configure_alert()` selects comparator mode (asserted while a limit is exceeded, for thermostat use) or interrupt mode (asserted at each limit crossing until `clear_interrupt()`), the polarity, and critical-only alerts. Above TCRIT the output always behaves as a comparator. Hysteresis applies only as the temperature falls.
- `wait_alert()` polls the Alert Stat bit, so ALT doesn't need to be wired. The alert must be enabled with `configure_alert()` first. In interrupt mode it clears the interrupt after each alert.
- The `Measurement` flags compare the temperature with the limit registers whether or not the alert is enabled. All limits are 0 °C at power-up, so at room temperature `above_critical` and `above_upper` read `True` until you set them.
- `lock_limits()` can only be undone by a power cycle. While locked, writes to the limits, hysteresis and alert settings are ignored, and so is `shutdown()`. The driver reads each write back and raises `RuntimeError` if the chip ignored it.
- There is no EEPROM or reset command. Settings stay until power-off, and `reset()` writes the power-on defaults back.
- Exiting `async with` shuts the sensor down. If the Alert output should keep working after your program ends, call `wake_up()` and `close()` yourself instead.
- The I2C transfers are blocking `smbus2` calls, but each takes well under 1 ms. All conversion waits are non-blocking.
