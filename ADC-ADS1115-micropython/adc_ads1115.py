# Asynchronous MicroPython driver for the Texas Instruments ADS1115 16-bit, 4-channel I2C ADC.
#
# Targets: Raspberry Pi Pico (rp2), ESP32-C3, ESP32-S3.
# Based on the TI ADS111x datasheet SBAS444E (December 2024). Section numbers in comments refer to it.
#
# Derived from robert-hh/ads1x15 <https://github.com/robert-hh/ads1x15>:
# The MIT License (MIT)
# Copyright (c) 2016 Radomir Dopieralski (@deshipu), 2017 Robert Hammelrath (@robert-hh)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

try:
    import asyncio
except ImportError:                                 # older firmware
    import uasyncio as asyncio
from machine import Pin
from micropython import const

# Register pointers (§8.1.1)
_CONVERSION     = const(0)
_CONFIG         = const(1)
_LO_THRESH      = const(2)
_HI_THRESH      = const(3)

# Config register bits (§8.1.3, Table 8-3)
_OS             = const(0x8000)                     # write 1: start single shot; read 1: idle
_MODE_SINGLE    = const(0x0100)                     # 0 = continuous
_COMP_WINDOW    = const(0x0010)
_COMP_ACT_HIGH  = const(0x0008)
_COMP_LATCH     = const(0x0004)
_COMP_OFF       = const(0x0003)                     # COMP_QUE = 11: comparator off, ALERT/RDY high-Z

# MUX[2:0]: (positive input, negative input) -> code. None = GND (single-ended).
_MUX = {(0, 1): 0, (0, 3): 1, (1, 3): 2, (2, 3): 3, (0, None): 4, (1, None): 5, (2, None): 6, (3, None): 7}
_QUEUE = {1: 0, 2: 1, 4: 2}                         # COMP_QUE: conversions beyond threshold before alert

GAINS = (6.144, 4.096, 2.048, 1.024, 0.512, 0.256)  # PGA[2:0] full-scale range, ±V (Table 7-1)
RATES = (8, 16, 32, 64, 128, 250, 475, 860)         # DR[2:0] samples per second


class ADS1115:
    ADDRESSES = (0x48, 0x49, 0x4A, 0x4B)            # ADDR pin to GND / VDD / SDA / SCL (Table 7-2)

    def __init__(self, i2c, address=0x48, gain=4.096, rate=128, rdy_pin=None):
        """i2c: machine.I2C (up to 400 kHz). gain: full-scale range in ±V (one of GAINS). rate: SPS (one of RATES).
        rdy_pin: optional machine.Pin wired to ALERT/RDY, for wait_conversion() / wait_alert() without polling."""
        self.i2c = i2c
        self.address = address
        self.gain = gain                            # takes effect on the next read / start_*()
        self.rate = rate
        self._config(0, 1, 0)                       # validate gain and rate now
        self._buf = bytearray(2)
        self._lock = asyncio.Lock()                 # one I2C sequence at a time
        self._pin = rdy_pin
        self._flag = None
        if rdy_pin is not None:
            self._flag = asyncio.ThreadSafeFlag()
            rdy_pin.init(Pin.IN, Pin.PULL_UP)       # open-drain output (§4)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.power_down()

    # ---- Low-level helpers ----

    def _write(self, reg, value):
        self._buf[0] = (value >> 8) & 0xFF          # masking also encodes negative thresholds
        self._buf[1] = value & 0xFF
        self.i2c.writeto_mem(self.address, reg, self._buf)

    def _read(self, reg):
        self.i2c.readfrom_mem_into(self.address, reg, self._buf)
        return self._buf[0] << 8 | self._buf[1]

    def _read_signed(self):
        v = self._read(_CONVERSION)
        return v - 0x10000 if v & 0x8000 else v     # two's complement (§7.5.4)

    def _config(self, ch, ch2, mode, comp=_COMP_OFF):
        if (ch, ch2) not in _MUX:
            raise ValueError("invalid input pair")
        if self.gain not in GAINS or self.rate not in RATES:
            raise ValueError("gain must be one of GAINS and rate one of RATES")
        return _MUX[(ch, ch2)] << 12 | GAINS.index(self.gain) << 9 | mode | RATES.index(self.rate) << 5 | comp

    def _conversion_ms(self):
        return 1100 // self.rate + 1                # 1 / DR, plus 10 % oscillator tolerance (§5.5, §7.3.6)

    def _arm(self, rising):
        """Route ALERT/RDY edges to the ThreadSafeFlag."""
        if self._pin is not None:
            self._pin.irq(lambda p: self._flag.set(), Pin.IRQ_RISING if rising else Pin.IRQ_FALLING)

    def raw_to_v(self, raw):
        return raw * self.gain / 32768              # LSB = FSR / 2^16 (Equation 4)

    def v_to_raw(self, volts):
        return max(-32768, min(32767, round(volts * 32768 / self.gain)))

    # ---- Single-shot (§7.4.2.1) ----

    async def read(self, channel=0, channel2=None):
        """One conversion of channel vs GND, or channel - channel2 (pairs 0-1, 0-3, 1-3, 2-3). Returns the raw code.
        Stops any continuous or comparator mode."""
        async with self._lock:
            self._write(_CONFIG, _OS | self._config(channel, channel2, _MODE_SINGLE))
            await asyncio.sleep_ms(self._conversion_ms())
            for _ in range(10):                     # usually done on the first check
                if self._read(_CONFIG) & _OS:
                    return self._read_signed()
                await asyncio.sleep_ms(1)
        raise OSError("ADS1115 conversion timed out")

    async def read_voltage(self, channel=0, channel2=None):
        return self.raw_to_v(await self.read(channel, channel2))

    # ---- Continuous conversion (§7.4.2.2, §7.3.8) ----

    async def start_continuous(self, channel=0, channel2=None):
        """Convert continuously at self.rate, with a ~8 µs active-low pulse on ALERT/RDY after each conversion."""
        async with self._lock:
            self._write(_LO_THRESH, 0x0000)         # Lo MSB = 0, Hi MSB = 1 selects conversion-ready mode
            self._write(_HI_THRESH, 0x8000)
            self._write(_CONFIG, self._config(channel, channel2, 0, comp=0))
        self._arm(rising=False)

    async def read_latest(self):
        """Most recent continuous-mode result (raw code). Also clears a latched alert."""
        async with self._lock:
            return self._read_signed()

    async def wait_conversion(self):
        """Wait for the next continuous-mode result and return it (raw code). Uses rdy_pin if given, otherwise
        sleeps one conversion time. Only one task at a time may wait on rdy_pin."""
        if self._flag is None:
            await asyncio.sleep_ms(self._conversion_ms())
        else:
            self._flag.clear()
            await self._flag.wait()
        return await self.read_latest()

    # ---- Comparator (§7.3.7) ----

    async def start_comparator(self, low, high, channel=0, channel2=None, window=False, latched=False,
                               queue=1, active_high=False):
        """Convert continuously and drive ALERT/RDY when the input passes the thresholds (in volts, at the current gain).
        Traditional mode: asserts above `high`, releases below `low`. Window mode: asserts outside low..high.
        queue: 1, 2 or 4 conversions beyond threshold before asserting. Call again after changing gain."""
        if queue not in _QUEUE or high <= low:
            raise ValueError("queue must be 1, 2 or 4, and high > low")
        comp = (_QUEUE[queue] | (_COMP_WINDOW if window else 0) | (_COMP_LATCH if latched else 0)
                | (_COMP_ACT_HIGH if active_high else 0))
        async with self._lock:
            self._write(_LO_THRESH, self.v_to_raw(low))
            self._write(_HI_THRESH, self.v_to_raw(high))
            self._write(_CONFIG, self._config(channel, channel2, 0, comp))
        self._arm(rising=active_high)

    async def wait_alert(self):
        """Wait until ALERT/RDY asserts (needs rdy_pin), then return the triggering result (raw code)."""
        if self._flag is None:
            raise RuntimeError("wait_alert() needs rdy_pin")
        self._flag.clear()
        await self._flag.wait()
        return await self.read_latest()

    # ---- Power / reset (§7.4) ----

    async def power_down(self):
        """Single-shot mode with the comparator off: the chip idles at ~0.5 µA until the next read()."""
        async with self._lock:
            self._write(_CONFIG, self._config(0, 1, _MODE_SINGLE))
        if self._pin is not None:
            self._pin.irq(None)

    async def general_call_reset(self):
        """I2C general-call reset (§7.5.1.2): registers back to defaults. Resets every device on the bus that
        responds to general call, not just this one."""
        async with self._lock:
            self.i2c.writeto(0x00, b"\x06")
            await asyncio.sleep_ms(1)
