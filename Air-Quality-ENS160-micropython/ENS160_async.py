# Asynchronous MicroPython driver for:
# DFRobot SEN0537 Fermion ENS160 Air Quality Sensor (ScioSense ENS160)
# <https://wiki.dfrobot.com/sen0537/docs/20389>
#
# Based on ENS160.py in this folder (credit to JustDr00py <https://github.com/JustDr00py/ens160-aht21>)
# and the ScioSense ENS160 datasheet v1.3 (2023-03-29). Section numbers in comments refer to it.

try:
    import asyncio
except ImportError:                                 # older firmware
    import uasyncio as asyncio
from collections import namedtuple
import time

# aqi: UBA index 1-5, tvoc in ppb, eco2 in ppm
Reading = namedtuple("Reading", ("aqi", "tvoc", "eco2"))
# DEVICE_STATUS bits (§16.2.7). validity is 0-3, see ENS160.VALIDITY
Status = namedtuple("Status", ("running", "error", "validity", "new_data", "new_gpr"))


class ENS160:
    ADDRESS = 0x53                                  # ADDR pin high (DFRobot default), 0x52 with ADDR low (§14.1.1)
    PART_ID = 0x0160

    # Registers (§16.1, Table 16)
    REG_PART_ID         = 0x00
    REG_OPMODE          = 0x10
    REG_COMMAND         = 0x12
    REG_TEMP_IN         = 0x13                      # followed by RH_IN at 0x15
    REG_DEVICE_STATUS   = 0x20
    REG_DATA_AQI        = 0x21                      # followed by DATA_TVOC 0x22 and DATA_ECO2 0x24
    REG_DATA_T          = 0x30
    REG_DATA_RH         = 0x32
    REG_GPR_READ        = 0x48

    # Operating modes (§16.2.2)
    MODE_DEEP_SLEEP     = 0x00
    MODE_IDLE           = 0x01
    MODE_STANDARD       = 0x02
    MODE_RESET          = 0xF0

    # Commands, only actioned in IDLE mode (§16.2.4)
    CMD_NOP             = 0x00
    CMD_GET_APPVER      = 0x0E
    CMD_CLRGPR          = 0xCC

    VALIDITY = ("Normal operation", "Warm-up", "Initial start-up", "Invalid output")    # §11, Table 10

    def __init__(self, i2c, address=ADDRESS):
        """i2c: a machine.I2C (or SoftI2C) object, max 1 MHz."""
        self.i2c = i2c
        self.address = address
        self._lock = asyncio.Lock()                 # keeps multi-step sequences (e.g. firmware version) atomic

    # ---- Context manager: check the chip and start sensing, then stop on exit ----

    async def __aenter__(self):
        await self.begin()
        return self

    async def __aexit__(self, *exc):
        await self.set_mode(self.MODE_IDLE)         # stop gas sensing (§15)

    # ---- Low-level I2C helpers (call with the lock held) ----

    def _read(self, reg, length):
        return self.i2c.readfrom_mem(self.address, reg, length)

    def _write(self, reg, data):
        self.i2c.writeto_mem(self.address, reg, bytes(data))

    @staticmethod
    def _u16(data, i=0):
        return data[i] | (data[i + 1] << 8)         # registers are little endian (§16.1)

    # ---- Setup and operating mode (§15, §16.2.1-2) ----

    async def begin(self):
        """Check the part ID, then start STANDARD gas sensing. Raises OSError on a wrong ID."""
        part_id = await self.get_id()
        if part_id != self.PART_ID:
            raise OSError("ENS160: unexpected PART_ID 0x{:04X} (expected 0x{:04X})".format(part_id, self.PART_ID))
        await self.set_mode(self.MODE_STANDARD)

    async def get_id(self):
        async with self._lock:
            return self._u16(self._read(self.REG_PART_ID, 2))

    async def set_mode(self, mode):
        async with self._lock:
            self._write(self.REG_OPMODE, (mode,))
            await asyncio.sleep_ms(10)

    async def get_mode(self):
        async with self._lock:
            return self._read(self.REG_OPMODE, 1)[0]

    async def reset(self):
        """Software reset, leaving the sensor in IDLE mode."""
        await self.set_mode(self.MODE_RESET)
        await self.set_mode(self.MODE_IDLE)

    async def get_firmware_version(self):
        """Returns 'major.minor.release' (§16.2.4.1). Commands only run in IDLE, so this briefly
        leaves the current mode. Going back to STANDARD restarts the 3 minute warm-up."""
        async with self._lock:
            mode = self._read(self.REG_OPMODE, 1)[0]
            self._write(self.REG_OPMODE, (self.MODE_IDLE,))
            await asyncio.sleep_ms(10)
            self._write(self.REG_COMMAND, (self.CMD_NOP,))
            self._write(self.REG_COMMAND, (self.CMD_CLRGPR,))
            await asyncio.sleep_ms(10)
            self._write(self.REG_COMMAND, (self.CMD_GET_APPVER,))
            await asyncio.sleep_ms(10)
            data = self._read(self.REG_GPR_READ, 8)
            if mode != self.MODE_IDLE:
                self._write(self.REG_OPMODE, (mode,))
                await asyncio.sleep_ms(10)
        return "{}.{}.{}".format(data[4], data[5], data[6])

    # ---- Status and measurements (§16.2.7-10) ----

    async def get_status(self):
        async with self._lock:
            s = self._read(self.REG_DEVICE_STATUS, 1)[0]
        return Status(bool(s & 0x80), bool(s & 0x40), (s >> 2) & 0x03, bool(s & 0x02), bool(s & 0x01))

    async def get_data(self):
        """AQI, TVOC and eCO2 in one 5-byte read, so all three come from the same sample."""
        async with self._lock:
            d = self._read(self.REG_DATA_AQI, 5)
        return Reading(d[0] & 0x07, self._u16(d, 1), self._u16(d, 3))

    async def wait_data(self, poll_ms=100, timeout_ms=5000):
        """Wait for a new sample (NEWDAT bit, about once a second in STANDARD mode), then return it."""
        start = time.ticks_ms()
        while not (await self.get_status()).new_data:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                raise OSError("ENS160: no new data within {} ms".format(timeout_ms))
            await asyncio.sleep_ms(poll_ms)
        return await self.get_data()

    # ---- Temperature / humidity compensation (§8.2, §16.2.5-6, §16.2.12-13) ----

    async def set_compensation(self, temp_c, humidity):
        """Write ambient temperature (°C) and relative humidity (%) from an external sensor.
        One auto-increment write to TEMP_IN and RH_IN, LSB before MSB as the datasheet requires."""
        t = round((temp_c + 273.15) * 64)
        rh = round(min(max(humidity, 0), 100) * 512)
        async with self._lock:
            self._write(self.REG_TEMP_IN, (t & 0xFF, t >> 8, rh & 0xFF, rh >> 8))

    async def get_temperature(self):
        """Temperature (°C) the ENS160 is using in its calculations."""
        async with self._lock:
            raw = self._u16(self._read(self.REG_DATA_T, 2))
        return raw / 64 - 273.15

    async def get_humidity(self):
        """Relative humidity (%) the ENS160 is using in its calculations."""
        async with self._lock:
            raw = self._u16(self._read(self.REG_DATA_RH, 2))
        return raw / 512

    # ---- Text ratings (no I/O) ----

    @staticmethod
    def interpret_eco2_level(eco2):
        # §5.2, Table 5
        if eco2 > 1500:
            return "Bad - Heavily contaminated indoor air / Ventilation required"
        elif eco2 > 1000:
            return "Poor - Contaminated indoor air / Ventilation recommended"
        elif eco2 > 800:
            return "Fair - Optional ventilation"
        elif eco2 > 600:
            return "Good - Average"
        elif eco2 >= 400:
            return "Excellent - Target level"
        else:
            return "Unknown"

    @staticmethod
    def interpret_tvoc_level(tvoc):
        # UBA TVOC levels (§5.3, Table 6), converted from ppm to ppb
        if tvoc < 65:
            return "Excellent"
        elif tvoc < 220:
            return "Good"
        elif tvoc < 650:
            return "Moderate"
        elif tvoc < 2200:
            return "Poor"
        else:
            return "Unhealthy"
