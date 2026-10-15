# Asynchronous MicroPython driver for:
# ROHM BH1750FVI ambient light sensor (Adafruit 4681, GY-302 and similar breakouts)
# <https://www.adafruit.com/product/4681>
#
# Targets: Raspberry Pi Pico (rp2), ESP32-C3, ESP32-S3.
# Based on the ROHM BH1750FVI datasheet Rev.D (2011.11) and Adafruit_CircuitPython_BH1750.
# Page numbers in comments refer to the datasheet.

try:
    import asyncio
except ImportError:                                 # older firmware
    import uasyncio as asyncio
import time


class BH1750:
    ADDRESS             = 0x23                      # ADDR pin low (p10)
    ADDRESS_ALT         = 0x5C                      # ADDR pin high

    # Instruction set (p5). The chip has no registers: each opcode is a 1-byte write ended by a STOP (p10)
    POWER_DOWN          = 0x00
    POWER_ON            = 0x01
    RESET               = 0x07                      # clears the data register only, ignored while powered down
    CONTINUOUS          = 0x10                      # | resolution
    ONE_TIME            = 0x20                      # | resolution, powers down after the measurement
    MTREG_HIGH          = 0x40                      # | MTreg[7:5]
    MTREG_LOW           = 0x60                      # | MTreg[4:0]

    # Resolution, the low bits of the measurement opcodes (p5, p12)
    RES_HIGH            = 0x00                      # H-Resolution Mode: 1 lx, 120 ms typ (ROHM's recommended mode)
    RES_HIGH2           = 0x01                      # H-Resolution Mode2: 0.5 lx, 120 ms typ
    RES_LOW             = 0x03                      # L-Resolution Mode: 4 lx, 16 ms typ

    # Measurement time register (p11). Sensitivity and conversion time both scale with MTreg / 69
    MTREG_MIN           = 31
    MTREG_DEFAULT       = 69
    MTREG_MAX           = 254

    ACCURACY            = 1.2                       # typical counts per lx (p2, spread 0.96-1.44)
    _MAX_TIME_H         = 180                       # worst-case conversion time in ms at MTreg 69 (p2)
    _MAX_TIME_L         = 24

    def __init__(self, i2c, address=ADDRESS, transmittance=1.0):
        """i2c: a machine.I2C (or SoftI2C) object, max 400 kHz.
        transmittance: fraction of light let through by a cover or optical window (0-1).
        Readings are divided by it to cancel the window's influence (p11)."""
        self.i2c = i2c
        self.address = address
        self.transmittance = transmittance
        self.mtreg = self.MTREG_DEFAULT
        self.resolution = self.RES_HIGH
        self.continuous = False
        self._next_ms = time.ticks_ms()             # when a sample newer than the last one read is guaranteed
        self._lock = asyncio.Lock()                 # keeps command + wait + read sequences atomic

    # ---- Context manager: power on with a known MTreg, power down on exit ----

    async def __aenter__(self):
        await self.power_on()
        await self.set_mtreg(self.mtreg)            # MTreg survives a host restart, so put it in a known state
        return self

    async def __aexit__(self, *exc):
        await self.power_down()

    # ---- Low-level I2C helpers (call with the lock held) ----

    def _cmd(self, opcode):
        self.i2c.writeto(self.address, bytes((opcode,)))

    def _read_raw(self):
        d = self.i2c.readfrom(self.address, 2)      # high byte first (p10)
        self._next_ms = time.ticks_add(time.ticks_ms(), self.measurement_time_ms())
        return d[0] << 8 | d[1]

    def _check_resolution(self, resolution):
        if resolution not in (self.RES_HIGH, self.RES_HIGH2, self.RES_LOW):
            raise ValueError("BH1750: unknown resolution {}".format(resolution))

    async def _start_continuous(self, resolution):
        self._cmd(self.CONTINUOUS | resolution)
        self.resolution = resolution
        self.continuous = True
        await asyncio.sleep_ms(self.measurement_time_ms(resolution))   # first result (p7, step 2)
        self._next_ms = time.ticks_ms()

    # ---- Scaling and timing (no I/O) ----

    def measurement_time_ms(self, resolution=None):
        """Worst-case conversion time in ms for a resolution (default: current) at the current MTreg."""
        if resolution is None:
            resolution = self.resolution
        base = self._MAX_TIME_L if resolution == self.RES_LOW else self._MAX_TIME_H
        return -(-base * self.mtreg // self.MTREG_DEFAULT)              # round up

    def lux_per_count(self, resolution=None):
        """lx per count (p11): 1 / 1.2 * (69 / MTreg), halved in H-Resolution Mode2, then window-corrected."""
        if resolution is None:
            resolution = self.resolution
        lpc = self.MTREG_DEFAULT / (self.ACCURACY * self.mtreg)
        if resolution == self.RES_HIGH2:
            lpc /= 2
        return lpc / self.transmittance

    # ---- Power and configuration (p4-5, p11) ----

    async def power_on(self):
        """Wake the sensor. It then waits for a measurement command (stops continuous mode)."""
        async with self._lock:
            self._cmd(self.POWER_ON)
            self.continuous = False

    async def power_down(self):
        """Low-power state, about 0.01 uA (p2)."""
        async with self._lock:
            self._cmd(self.POWER_DOWN)
            self.continuous = False

    async def reset(self):
        """Clear the data register to 0, leaving the sensor powered on and idle (p5)."""
        async with self._lock:
            self._cmd(self.POWER_ON)                # RESET is not accepted while powered down
            self._cmd(self.RESET)
            self.continuous = False

    async def set_mtreg(self, mtreg):
        """Measurement time register, 31-254 (default 69). Higher values give finer resolution (down to
        0.11 lx/count in H2) but longer conversions and a lower maximum. If continuous measurement is
        running it is restarted, so the next reading is taken with the new value."""
        if not self.MTREG_MIN <= mtreg <= self.MTREG_MAX:
            raise ValueError("BH1750: mtreg must be {}-{}".format(self.MTREG_MIN, self.MTREG_MAX))
        async with self._lock:
            self._cmd(self.MTREG_HIGH | (mtreg >> 5))
            self._cmd(self.MTREG_LOW | (mtreg & 0x1F))
            self.mtreg = mtreg
            if self.continuous:
                await self._start_continuous(self.resolution)

    # ---- Measurement (p5, p7) ----

    async def start_continuous(self, resolution=RES_HIGH):
        """Start continuous measurement and wait for the first result."""
        self._check_resolution(resolution)
        async with self._lock:
            await self._start_continuous(resolution)

    async def read_lux(self):
        """Latest result in lx. In continuous mode the sensor updates it every ~120 ms (H modes) or ~16 ms (L)."""
        async with self._lock:
            raw = self._read_raw()
            scale = self.lux_per_count()
        return raw * scale

    async def wait_lux(self):
        """Continuous mode: wait until a sample newer than the last one read is available, then return it in lx."""
        if not self.continuous:
            raise RuntimeError("BH1750: continuous measurement is not running")
        delay = time.ticks_diff(self._next_ms, time.ticks_ms())
        if delay > 0:
            await asyncio.sleep_ms(delay)
        return await self.read_lux()

    async def measure(self, resolution=RES_HIGH):
        """One-time measurement in lx. The sensor powers itself down afterwards, ending continuous mode."""
        self._check_resolution(resolution)
        async with self._lock:
            self._cmd(self.ONE_TIME | resolution)
            self.resolution = resolution
            self.continuous = False
            await asyncio.sleep_ms(self.measurement_time_ms(resolution))
            raw = self._read_raw()
            scale = self.lux_per_count(resolution)
        return raw * scale
