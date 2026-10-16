# DFRobot SEN0435 High Accuracy Temperature Sensor (Microchip MCP9808)

Asynchronous (`asyncio`) MicroPython driver for the Raspberry Pi Pico, ESP32-C3 and ESP32-S3.

Page: <https://wiki.dfrobot.com/sen0435/>

Datasheet: Microchip MCP9808, DS20005095B (May 2018)

- Digital temperature sensor, ±0.25 °C typical, ±0.5 °C max from -20 °C to 100 °C (±1 °C max from -40 °C to +125 °C)
- Selectable resolution: 0.5 / 0.25 / 0.125 / 0.0625 °C, converting in 30 / 65 / 130 / 250 ms
- Programmable upper, lower and critical limits, with hysteresis, driving an open-drain Alert (ALT) output
- Shutdown mode at 0.1 µA. Supply 2.7–5.5 V, 200 µA while converting
- I2C up to 400 kHz, address `0x18`–`0x1F`. The DFRobot board pulls A0–A2 high, so its default is **`0x1F`**

## Wiring

| SEN0435 board | Raspberry Pi Pico | ESP32-C3 / ESP32-S3 |
|---|---|---|
| VCC | 3V3(OUT) (pin 36) | 3V3 |
| GND | GND (pin 38) | GND |
| SDA | GP4 (pin 6) | GPIO 8 |
| SCL | GP5 (pin 7) | GPIO 9 |
| ALT (optional) | e.g. GP6 (pin 9) | e.g. GPIO 10 |

ESP32 boards have no fixed I2C pins, so GPIO 8/9 are just common defaults. Change `SDA` / `SCL` / `ALERT` in `mcp9808_test.py` to match your board. Power the board from 3.3 V, because the chip runs directly from VCC and its I2C lines follow it.

The address is `0x18 + 4·A2 + 2·A1 + A0`. A0–A2 are pulled high on the board, so leaving them open gives `0x1F`. Tie a pin to GND to clear its bit (A0 to GND gives `0x1E`; all three give `0x18`). Up to eight boards can share a bus.

## Files

- `mcp9808.py`: `MCP9808` class and `Measurement` namedtuple (`temperature`, `above_critical`, `above_upper`, `below_lower`).
- `mcp9808_test.py`: demo that scans the bus, reads the IDs and settings, sweeps the resolutions, streams readings, takes a single shot from shutdown, then sets up the alert output while a heartbeat task keeps running. It picks Pico or ESP32 pins from `sys.platform`.

## Usage

Copy both files to the board (e.g. `mpremote cp mcp9808.py mcp9808_test.py :`), then run `mpremote run mcp9808_test.py`. Rename the demo to `main.py` if it should run at boot.

```python
import asyncio
from machine import I2C, Pin
from mcp9808 import MCP9808

async def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    async with MCP9808(i2c) as mcp:             # 0x1F; checks the ID, starts converting; shuts down on exit
        print(await mcp.read_temperature())
        while True:
            m = await mcp.wait_measurement()    # returns a new reading every conversion (~0.3 s at 0.0625 °C)
            print(m.temperature)

asyncio.run(main())
```

Every method is a coroutine named after the datasheet register or feature (`get_…` / `set_…`). Conversion times are awaited with `asyncio.sleep_ms`, and a lock stops tasks from interleaving register accesses.

| Group | Methods |
|---|---|
| Measurement | `read_temperature`, `read_measurement`, `wait_measurement`, `measure_single_shot`, `conversion_ms`, `get/set_resolution` |
| Power | `shutdown`, `wake_up`, `reset` |
| Alert | `get/set_upper_limit`, `get/set_lower_limit`, `get/set_critical_limit`, `get/set_hysteresis`, `configure_alert`, `get_alert_status`, `wait_alert`, `clear_interrupt`, `lock_limits` |
| ID / raw | `get_manufacturer_id`, `get_device_id`, `get_config` |

## Notes

- The API matches the [CPython version](../Temp-MCP9808-python/) except in three places. MicroPython has no async generators, so `measurements()` becomes `wait_measurement()`, which returns one reading per call. `conversion_time()` (seconds) becomes `conversion_ms()`. The constructor also takes an optional `alert_pin`.
- With `alert_pin=Pin(n)`, `wait_alert()` sleeps until the ALT pin interrupt fires (the driver enables the internal pull-up). Without it, `wait_alert()` polls the Alert Stat bit. Either way, enable the alert with `configure_alert()` first. In interrupt mode the interrupt is cleared after each alert.
- `configure_alert()` selects comparator mode (asserted while a limit is exceeded, for thermostat use) or interrupt mode (asserted at each limit crossing until `clear_interrupt()`), the polarity, and critical-only alerts. Above TCRIT the output always behaves as a comparator. Hysteresis applies only as the temperature falls.
- The `Measurement` flags compare the temperature with the limit registers whether or not the alert is enabled. All limits are 0 °C at power-up, so at room temperature `above_critical` and `above_upper` read `True` until you set them.
- `lock_limits()` can only be undone by a power cycle. While locked, writes to the limits, hysteresis and alert settings are ignored, and so is `shutdown()`. The driver reads each write back and raises `RuntimeError` if the chip ignored it.
- There is no EEPROM or reset command. Settings stay until power-off, and `reset()` writes the power-on defaults back.
- For battery use, call `measure_single_shot()` every so often. It wakes the sensor, waits one conversion, reads, and shuts it down again.
- Exiting `async with` shuts the sensor down. If the Alert output should keep working after your program ends (e.g. as a hardware thermostat), call `wake_up()` yourself instead.
