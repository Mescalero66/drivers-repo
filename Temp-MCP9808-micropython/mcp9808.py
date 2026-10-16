# Asynchronous MicroPython driver for:
# DFRobot SEN0435 Fermion: MCP9808 High Accuracy I2C Temperature Sensor (Microchip MCP9808)
# <https://wiki.dfrobot.com/sen0435/>
#
# Targets: Raspberry Pi Pico (rp2), ESP32-C3, ESP32-S3.
# Based on the Microchip MCP9808 datasheet DS20005095B (May 2018). Section numbers in comments refer to it.

try:
    import asyncio
except ImportError:                                 # older firmware
    import uasyncio as asyncio
from collections import namedtuple
from machine import Pin

# temperature in °C; flags TA ≥ TCRIT, TA > TUPPER, TA < TLOWER (set whatever the alert configuration, §5.1.3)
Measurement = namedtuple("Measurement", ("temperature", "above_critical", "above_upper", "below_lower"))


class MCP9808:
    ADDRESS = 0x1F                                  # DFRobot board: A2 A1 A0 pulled high. Range 0x18–0x1F (§4.1.4)

    # Register pointers (§5.1, Register 5-1)
    CONFIG                  = 0x01
    T_UPPER                 = 0x02
    T_LOWER                 = 0x03
    T_CRIT                  = 0x04
    T_A                     = 0x05
    MANUFACTURER_ID         = 0x06
    DEVICE_ID               = 0x07
    RESOLUTION              = 0x08

    # CONFIG bits (§5.1.1, Register 5-2)
    HYST_SHIFT              = 9                     # bits 10–9
    SHDN                    = 0x0100
    CRIT_LOCK               = 0x0080
    WIN_LOCK                = 0x0040
    INT_CLEAR               = 0x0020
    ALERT_STAT              = 0x0010                # read-only
    ALERT_CNT               = 0x0008                # alert output enabled
    ALERT_SEL               = 0x0004                # TCRIT only
    ALERT_POL               = 0x0002                # active-high
    ALERT_MOD               = 0x0001                # interrupt mode
    _CHECK = 0x07CF                                 # bits that read back as written (not INT_CLEAR / ALERT_STAT)

    MANUFACTURER = 0x0054
    DEVICE = 0x04

    HYSTERESIS = (0.0, 1.5, 3.0, 6.0)               # °C, THYST codes 00–11
    RESOLUTIONS = (0.5, 0.25, 0.125, 0.0625)        # °C, resolution codes 00–11 (Register 5-7)
    CONVERSION_MS = (30, 65, 130, 250)              # typical tCONV per resolution (Table 5-2)

    def __init__(self, i2c, address=ADDRESS, alert_pin=None):
        """i2c: a machine.I2C (or SoftI2C) object, max 400 kHz.
        alert_pin: optional machine.Pin wired to ALT, so wait_alert() sleeps until the pin interrupt instead of polling."""
        self.i2c = i2c
        self.address = address
        self._buf = bytearray(2)
        self._lock = asyncio.Lock()                 # one register sequence at a time
        self._res = 3                               # power-up default, re-read in __aenter__
        self._pin = alert_pin
        self._flag = None
        self._active = 0                            # Alert pin level when asserted
        if alert_pin is not None:
            self._flag = asyncio.ThreadSafeFlag()
            alert_pin.init(Pin.IN, Pin.PULL_UP)     # open-drain output (§3.3)

    # ---- Context manager: check the ID, start converting; shut down on exit ----

    async def __aenter__(self):
        if await self.get_manufacturer_id() != self.MANUFACTURER or (await self.get_device_id())[0] != self.DEVICE:
            raise RuntimeError("no MCP9808 at 0x%02X" % self.address)
        await self.get_resolution()
        await self.wake_up()
        return self

    async def __aexit__(self, *exc):
        if self._pin is not None:
            self._pin.irq(None)
        try:
            await self.shutdown()                   # 0.1 µA
        except RuntimeError:
            pass                                    # locked: SHDN can't be set until a power cycle

    # ---- Low-level I2C helpers (§4.1, Figures 5-2 to 5-8) ----

    def _read(self, reg, n=2):
        """Write the register pointer, repeated START, read n bytes MSB first."""
        if n == 2:
            self.i2c.readfrom_mem_into(self.address, reg, self._buf)
            return self._buf[0] << 8 | self._buf[1]
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _write(self, reg, value, n=2):
        if n == 2:
            self._buf[0] = value >> 8 & 0xFF
            self._buf[1] = value & 0xFF
            self.i2c.writeto_mem(self.address, reg, self._buf)
        else:
            self.i2c.writeto_mem(self.address, reg, bytes((value & 0xFF,)))

    async def _get(self, reg, n=2):
        async with self._lock:
            return self._read(reg, n)

    async def _set_checked(self, reg, value, mask=0xFFFF):
        """Write a register and read it back. Locked registers ignore writes, so a mismatch raises."""
        async with self._lock:
            self._write(reg, value)
            got = self._read(reg)
        if (got ^ value) & mask:
            raise RuntimeError("MCP9808 ignored write to register 0x%02X (locked until power cycle?)" % reg)

    async def _update_config(self, clear=0, set_=0):
        """Read-modify-write CONFIG, then check the change took effect."""
        async with self._lock:
            cfg = self._read(self.CONFIG) & ~(self.INT_CLEAR | self.ALERT_STAT)
            new = (cfg & ~clear) | set_
            self._write(self.CONFIG, new)
            got = self._read(self.CONFIG)
        if (got ^ new) & self._CHECK:
            raise RuntimeError("MCP9808 ignored CONFIG write (locked until power cycle?)")

    @staticmethod
    def _to_celsius(raw):
        """13-bit two's complement, 1/16 °C per LSB (§5.1.3.1). Also used for the limit registers."""
        raw &= 0x1FFF
        return (raw - 0x2000 if raw & 0x1000 else raw) / 16

    @staticmethod
    def _from_celsius(celsius):
        """Limit registers: 11-bit two's complement in bits 12–2, 0.25 °C per LSB (§5.1.2)."""
        if not -256 <= celsius <= 255.75:
            raise ValueError("MCP9808 limit out of range -256 – 255.75 C")
        return (round(celsius * 4) << 2) & 0x1FFC

    def conversion_ms(self):
        """Milliseconds per conversion at the current resolution, with a 25 % margin (the datasheet gives typical values only)."""
        return self.CONVERSION_MS[self._res] * 5 // 4

    # ---- Temperature (§5.1.3) ----

    async def read_measurement(self):
        """Latest temperature plus the TA vs TCRIT / TUPPER / TLOWER flags. The register updates every tCONV."""
        raw = await self._get(self.T_A)
        return Measurement(self._to_celsius(raw), bool(raw & 0x8000), bool(raw & 0x4000), bool(raw & 0x2000))

    async def read_temperature(self):
        return (await self.read_measurement()).temperature

    async def wait_measurement(self):
        """Wait one conversion time, then return the new measurement."""
        await asyncio.sleep_ms(self.conversion_ms())
        return await self.read_measurement()

    async def measure_single_shot(self):
        """Wake, wait one conversion, read, shut down again: about 0.1 µA between readings (§5.2.1)."""
        await self.wake_up()
        m = await self.read_measurement()
        await self.shutdown()
        return m

    # ---- Power (§5.2.1) ----

    async def shutdown(self):
        """Stop converting. Registers stay readable and writable; TA keeps the last value. Not allowed while locked."""
        await self._update_config(set_=self.SHDN)

    async def wake_up(self):
        """Return to continuous conversion, then wait until TA holds a fresh value."""
        await self._update_config(clear=self.SHDN)
        await asyncio.sleep_ms(self.conversion_ms())

    # ---- Resolution (§5.1.6, §5.2.4) ----

    async def get_resolution(self):
        """°C per LSB: 0.5, 0.25, 0.125 or 0.0625."""
        self._res = await self._get(self.RESOLUTION, n=1) & 0x03
        return self.RESOLUTIONS[self._res]

    async def set_resolution(self, step):
        """0.5 (30 ms), 0.25 (65 ms), 0.125 (130 ms) or 0.0625 °C (250 ms, power-up default)."""
        if step not in self.RESOLUTIONS:
            raise ValueError("MCP9808 resolution must be one of %s" % (self.RESOLUTIONS,))
        code = self.RESOLUTIONS.index(step)
        async with self._lock:
            self._write(self.RESOLUTION, code, n=1)
        self._res = code

    # ---- Alert limits (§5.1.2) ----

    async def get_upper_limit(self):
        return self._to_celsius(await self._get(self.T_UPPER))

    async def set_upper_limit(self, celsius):
        await self._set_checked(self.T_UPPER, self._from_celsius(celsius))

    async def get_lower_limit(self):
        return self._to_celsius(await self._get(self.T_LOWER))

    async def set_lower_limit(self, celsius):
        await self._set_checked(self.T_LOWER, self._from_celsius(celsius))

    async def get_critical_limit(self):
        return self._to_celsius(await self._get(self.T_CRIT))

    async def set_critical_limit(self, celsius):
        await self._set_checked(self.T_CRIT, self._from_celsius(celsius))

    # ---- Configuration and alert output (§5.1.1, §5.2.2, §5.2.3) ----

    async def get_config(self):
        """Raw 16-bit CONFIG register."""
        return await self._get(self.CONFIG)

    async def get_hysteresis(self):
        return self.HYSTERESIS[(await self.get_config()) >> self.HYST_SHIFT & 0x03]

    async def set_hysteresis(self, celsius):
        """0, 1.5, 3 or 6 °C, applied to all three limits as the temperature falls."""
        if celsius not in self.HYSTERESIS:
            raise ValueError("MCP9808 hysteresis must be one of %s" % (self.HYSTERESIS,))
        await self._update_config(clear=0x03 << self.HYST_SHIFT, set_=self.HYSTERESIS.index(celsius) << self.HYST_SHIFT)

    async def configure_alert(self, enabled=True, interrupt=False, active_high=False, critical_only=False):
        """Set up the open-drain Alert (ALT) pin.
        interrupt=False: comparator mode, asserted while a limit is exceeded (thermostat use).
        interrupt=True: asserted at each limit crossing until clear_interrupt().
        critical_only=True: alert only when TA ≥ TCRIT (always comparator mode)."""
        if interrupt and critical_only:
            raise ValueError("MCP9808 interrupt mode can't be used with critical_only")
        bits = ((self.ALERT_CNT if enabled else 0) | (self.ALERT_SEL if critical_only else 0)
                | (self.ALERT_POL if active_high else 0) | (self.ALERT_MOD if interrupt else 0))
        await self._update_config(clear=0x000F, set_=bits)
        if self._pin is not None:
            self._active = 1 if active_high else 0
            if enabled:
                self._pin.irq(lambda p: self._flag.set(), Pin.IRQ_RISING if active_high else Pin.IRQ_FALLING)
            else:
                self._pin.irq(None)

    async def get_alert_status(self):
        """True while the Alert output is asserted."""
        return bool(await self.get_config() & self.ALERT_STAT)

    async def clear_interrupt(self):
        """Release the Alert output in interrupt mode (not possible in shutdown)."""
        await self._update_config(set_=self.INT_CLEAR)

    async def wait_alert(self, poll_ms=100):
        """Wait until the alert is asserted, then return the measurement that caused it. Uses alert_pin if given,
        otherwise polls the Alert Stat bit. In interrupt mode the interrupt is cleared afterwards, so the next call
        waits for the next crossing. Only one task at a time may wait on alert_pin."""
        if self._flag is None:
            while not await self.get_alert_status():
                await asyncio.sleep_ms(poll_ms)
        else:
            self._flag.clear()
            if self._pin.value() != self._active:   # already asserted (comparator mode): no edge will come
                await self._flag.wait()
        m = await self.read_measurement()
        cfg = await self.get_config()
        if cfg & self.ALERT_MOD and not cfg & self.ALERT_SEL:
            await self.clear_interrupt()
        return m

    async def lock_limits(self, critical=True, window=True):
        """Lock TCRIT and/or TUPPER/TLOWER and the alert settings against writes. Only a power cycle unlocks them."""
        await self._update_config(set_=(self.CRIT_LOCK if critical else 0) | (self.WIN_LOCK if window else 0))

    async def reset(self):
        """Write the power-on defaults (§5.3, Table 5-3). The chip has no reset command, so this fails if locked."""
        await self._set_checked(self.CONFIG, 0x0000, self._CHECK)
        if self._pin is not None:
            self._pin.irq(None)
        for reg in (self.T_UPPER, self.T_LOWER, self.T_CRIT):
            await self._set_checked(reg, 0x0000)
        await self.set_resolution(0.0625)

    # ---- Identification (§5.1.4, §5.1.5) ----

    async def get_manufacturer_id(self):
        """0x0054 for Microchip."""
        return await self._get(self.MANUFACTURER_ID)

    async def get_device_id(self):
        """(device ID, revision). The MCP9808 device ID is 0x04."""
        word = await self._get(self.DEVICE_ID)
        return word >> 8, word & 0xFF
