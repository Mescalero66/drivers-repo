# Asynchronous Python driver for:
# Adafruit MCP4725 Breakout Board - 12-Bit DAC with I2C Interface (Microchip MCP4725)
# <https://www.adafruit.com/product/935>
#
# Based on the Microchip MCP4725 datasheet DS22039D (June 2009). Section numbers in comments refer to it.

import asyncio
from dataclasses import dataclass

from smbus2 import SMBus, i2c_msg


@dataclass
class Status:
    ready: bool             # RDY/BSY: False while an EEPROM write is in progress
    por: bool               # power-on-reset bit
    power_down: int         # DAC register power-down mode (PD_…)
    code: int               # DAC register code, 0–4095
    eeprom_power_down: int  # power-down mode loaded at power-up
    eeprom_code: int        # code loaded at power-up


class MCP4725:
    ADDRESS = 0x62                                  # Adafruit board: 0x62, or 0x63 with A0 tied to VDD (§7.2)
    GENERAL_CALL = 0x00                             # reaches every device on the bus (§7.3)

    # Write command types: C2 C1 C0 in the top bits of the first data byte (§6.1, Table 6-2)
    FAST_WRITE              = 0x00                  # C2 C1 = 0 0, DAC register only
    WRITE_DAC_EEPROM        = 0x60                  # C2 C1 C0 = 0 1 1, DAC register and EEPROM

    # General call commands, sent as the second byte (§7.3)
    GC_RESET                = 0x06
    GC_WAKE_UP              = 0x09

    # Power-down modes, PD1 PD0 (§5.5, Table 5-2)
    PD_NORMAL               = 0                     # output on
    PD_1K                   = 1                     # output off, 1 kΩ to GND
    PD_100K                 = 2                     # output off, 100 kΩ to GND
    PD_500K                 = 3                     # output off, 500 kΩ to GND

    MAX_CODE = 4095

    def __init__(self, bus=1, address=ADDRESS, vref=3.3):
        """vref: the board's VDD supply, which is also the DAC reference (§5.3)."""
        self.address = address
        self.vref = vref
        self._bus = SMBus(bus)
        self._lock = asyncio.Lock()                 # writes are ignored during an EEPROM write (§5.6)

    # ---- Context manager: check the DAC answers, leave the output as it is on exit ----

    async def __aenter__(self):
        await self.read()                           # raises OSError if the DAC does not ACK
        return self

    async def __aexit__(self, *exc):
        self.close()

    def close(self):
        self._bus.close()

    # ---- Low-level I2C helpers ----

    @classmethod
    def _check(cls, code, power_down):
        if not 0 <= code <= cls.MAX_CODE:
            raise ValueError(f"MCP4725 code {code} out of range 0–{cls.MAX_CODE}")
        if not 0 <= power_down <= 3:
            raise ValueError(f"MCP4725 power-down mode {power_down} out of range 0–3")

    def _write(self, data, address=None):
        self._bus.i2c_rdwr(i2c_msg.write(self.address if address is None else address, data))

    def _fast_write(self, code, power_down):
        """0 0 PD1 PD0 D11–D8 | D7–D0 (§6.1.1, Figure 6-1)."""
        self._write([power_down << 4 | code >> 8, code & 0xFF])

    def _read_status(self):
        """5-byte read (§6.2, Figure 6-3):
        RDY POR x x x PD1 PD0 x | D11–D4 | D3–D0 x x x x | x PD1 PD0 x D11–D8 | D7–D0 (EEPROM)."""
        msg = i2c_msg.read(self.address, 5)
        self._bus.i2c_rdwr(msg)
        b = list(msg)
        return Status(
            ready=bool(b[0] & 0x80),
            por=bool(b[0] & 0x40),
            power_down=(b[0] >> 1) & 0x03,
            code=b[1] << 4 | b[2] >> 4,
            eeprom_power_down=(b[3] >> 5) & 0x03,
            eeprom_code=(b[3] & 0x0F) << 8 | b[4],
        )

    # ---- Read (§6.2) ----

    async def read(self):
        """Read the DAC register, EEPROM contents and EEPROM write status."""
        async with self._lock:
            return self._read_status()

    async def get_code(self):
        return (await self.read()).code

    async def get_voltage(self):
        return self.code_to_volts(await self.get_code())

    # ---- Write (§6.1) ----

    async def fast_write(self, code, power_down=PD_NORMAL):
        """Update the DAC register only, in a 2-byte write. VOUT changes at the final ACK (§6.1.1)."""
        self._check(code, power_down)
        async with self._lock:
            self._fast_write(code, power_down)

    async def write_dac_and_eeprom(self, code, power_down=PD_NORMAL):
        """Update the DAC register and also store code and mode as the power-up value (§6.1.3).
        Waits for the EEPROM write to finish (25 ms typical, 50 ms max). Rated for 1 million writes."""
        self._check(code, power_down)
        async with self._lock:
            self._write([self.WRITE_DAC_EEPROM | power_down << 1, code >> 4, (code & 0x0F) << 4])
            await asyncio.sleep(0.025)
            for _ in range(15):                     # poll RDY/BSY for up to another 75 ms
                if self._read_status().ready:
                    return
                await asyncio.sleep(0.005)
        raise RuntimeError("MCP4725 EEPROM write did not finish")

    async def set_code(self, code, persist=False):
        """Set the output code (0–4095) and switch the output on. persist=True also stores it in EEPROM."""
        if persist:
            await self.write_dac_and_eeprom(code)
        else:
            await self.fast_write(code)

    async def set_voltage(self, volts, persist=False):
        """Set VOUT in volts, clamped to 0 – vref × 4095/4096. Returns the code written."""
        code = self.volts_to_code(volts)
        await self.set_code(code, persist)
        return code

    def volts_to_code(self, volts):
        return min(max(round(volts * 4096 / self.vref), 0), self.MAX_CODE)

    def code_to_volts(self, code):
        return code * self.vref / 4096              # VOUT = VREF × Dn / 4096 (§5.1, Equation 5-1)

    # ---- Power-down (§5.5) ----

    async def power_down(self, mode=PD_500K):
        """Switch the output off and pull VOUT to GND through 1 kΩ, 100 kΩ or 500 kΩ. The code is kept."""
        if mode not in (self.PD_1K, self.PD_100K, self.PD_500K):
            raise ValueError(f"MCP4725 power-down mode must be 1, 2 or 3, not {mode}")
        async with self._lock:
            self._fast_write(self._read_status().code, mode)

    async def power_up(self):
        """Switch the output back on at its previous code (settles in < 10 µs)."""
        async with self._lock:
            self._fast_write(self._read_status().code, self.PD_NORMAL)

    # ---- General call (§7.3), bus-wide ----

    async def general_call_reset(self):
        """Reload the DAC register from EEPROM, as at power-up (§7.3.1).
        Every device on the bus that supports general call resets too (an ADS1115, for example)."""
        async with self._lock:
            self._write([self.GC_RESET], self.GENERAL_CALL)
            await asyncio.sleep(0.001)

    async def general_call_wake_up(self):
        """Clear the power-down bits of every MCP4725 on the bus. EEPROM is not changed (§7.3.2)."""
        async with self._lock:
            self._write([self.GC_WAKE_UP], self.GENERAL_CALL)
