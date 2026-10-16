# Asynchronous MicroPython driver for:
# DFRobot DFR0646 8-digit 7-segment LED display (Holtek HT16K33A LED controller)
#
# Targets: Raspberry Pi Pico (rp2), ESP32-C3, ESP32-S3.
# Based on the Holtek HT16K33A datasheet v1.11 (June 2026). Page numbers in comments refer to it.
# Character set and rotation from the blocking HT16K33LED.py (after Tony Smith, @smittytone).

try:
    import asyncio
except ImportError:                                 # older firmware
    import uasyncio as asyncio


class HT16K33LED:
    ADDRESS = 0x70                                  # 1110 A2 A1 A0: 0x70-0x77 (p.26)

    # Commands: top nibble selects the command, bottom nibble is its argument (Command Summary, p.28)
    DISPLAY_ADDRESS         = 0x00                  # | A3-A0, display RAM pointer
    SYSTEM_SETUP            = 0x20                  # | S: 0 standby, 1 oscillator on
    DISPLAY_SETUP           = 0x80                  # | B1 B0 << 1 | D: blink rate, display on
    ROW_INT_SETUP           = 0xA0                  # | act << 1 | row/int: 0 = pin is a row output
    DIMMING                 = 0xE0                  # | P3-P0: duty (P + 1)/16

    BLINK_RATES = (0, 2, 1, 0.5)                    # Hz, indexed by B1 B0 (p.13)

    # Segment bits: a=0 (top), clockwise b-f = 1-5, g=6 (middle), decimal point=7
    #
    #         0
    #         _
    #     5 |   | 1
    #         - <---- 6
    #     4 |   | 2
    #         _   . <-- 7
    #         3
    DOT = 0x80
    CHARSET = {
        '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
        '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
        'a': 0x77, 'b': 0x7C, 'c': 0x39, 'd': 0x5E, 'e': 0x79,
        'f': 0x71, 'g': 0x3D, 'h': 0x76, 'i': 0x06, 'j': 0x1E,
        'k': 0x75, 'l': 0x38, 'm': 0x37, 'n': 0x54, 'o': 0x5C,
        'p': 0x73, 'q': 0x67, 'r': 0x50, 's': 0x6D, 't': 0x78,
        'u': 0x3E, 'v': 0x1C, 'w': 0x2A, 'x': 0x76, 'y': 0x6E,
        'z': 0x5B, ' ': 0x00, '-': 0x40, '°': 0x63, '=': 0x48,
        '_': 0x08, '*': 0x63, '.': 0x80,
    }

    def __init__(self, i2c, address=ADDRESS, digits=8):
        """i2c: a machine.I2C (or SoftI2C) object, up to 400 kHz. digits: 1-8 digits fitted."""
        if not 0 < digits < 9:
            raise ValueError("HT16K33LED digits must be 1-8")
        self.i2c = i2c
        self.address = address
        self.max_digits = digits
        self.buffer = bytearray(16)                 # display RAM image: digit n at byte 2n (COMn, ROW0-7)
        self.is_rotated = False
        self.brightness = 15                        # 0-15 = 1/16-16/16 duty
        self.blink_rate = 0                         # Hz
        self._on = False
        self._lock = asyncio.Lock()                 # keeps multi-command sequences together

    # ---- Context manager: initialise and clear on entry, standby on exit ----

    async def __aenter__(self):
        await self.begin()
        return self

    async def __aexit__(self, *exc):
        await self.power_off()

    # ---- Low-level I2C helpers ----

    def _cmd(self, byte):
        self.i2c.writeto(self.address, bytes((byte,)))

    def _display_setup(self):
        self._cmd(self.DISPLAY_SETUP | self.BLINK_RATES.index(self.blink_rate) << 1 | self._on)

    def _frame(self):
        """The buffer as sent to the display, turned 180 degrees if rotated."""
        if not self.is_rotated:
            return self.buffer
        frame = bytearray(16)
        n = self.max_digits
        for i in range(n):
            g = self.buffer[(n - 1 - i) << 1]       # reverse digit order...
            frame[i << 1] = (g & 0xC0) | (g & 0x07) << 3 | (g & 0x38) >> 3   # ...and swap a-c with d-f
        return frame

    def _write_ram(self):
        """Page write from address 0x00; the pointer auto-increments over all 16 bytes (p.26)."""
        self.i2c.writeto_mem(self.address, self.DISPLAY_ADDRESS, self._frame())

    # ---- Setup and power (p.10-13, p.29) ----

    async def begin(self):
        """Initialise in the datasheet order (p.29). Display RAM is cleared before the display is
        turned on, because it holds random data after power-up (p.14)."""
        async with self._lock:
            await asyncio.sleep_ms(1)               # no I2C for 1 ms after power-on (p.10)
            self._cmd(self.SYSTEM_SETUP | 1)        # standby ignores everything else, so this goes first
            self._cmd(self.ROW_INT_SETUP)           # ROW/INT pin as a row output (POR default, set explicitly)
            self._cmd(self.DIMMING | self.brightness)
            self.clear()
            self._write_ram()
            self._on = True
            self._display_setup()

    async def power_on(self):
        """Leave standby and show the current buffer."""
        async with self._lock:
            self._cmd(self.SYSTEM_SETUP | 1)
            self._write_ram()
            self._on = True
            self._display_setup()

    async def power_off(self):
        """Display off, then standby (oscillator off, about 1 uA). The buffer is kept."""
        async with self._lock:
            self._on = False
            self._display_setup()
            self._cmd(self.SYSTEM_SETUP)

    async def set_brightness(self, brightness=15):
        """0 (1/16 duty, dim but not off) to 15 (16/16 duty, the power-on default) (p.16)."""
        if not 0 <= brightness <= 15:
            raise ValueError("HT16K33LED brightness must be 0-15")
        self.brightness = brightness
        async with self._lock:
            self._cmd(self.DIMMING | brightness)

    async def set_blink_rate(self, rate=0):
        """Blink the whole display at 0 (off), 2, 1 or 0.5 Hz. Does not turn the display on."""
        if rate not in self.BLINK_RATES:
            raise ValueError("HT16K33LED blink rate must be 0, 2, 1 or 0.5 Hz")
        self.blink_rate = rate
        async with self._lock:
            self._display_setup()

    # ---- Display RAM (p.14) ----

    async def draw(self):
        """Send the buffer to the display."""
        async with self._lock:
            self._write_ram()

    async def read_ram(self):
        """Read the 16 display RAM bytes back from the chip (page read, p.27)."""
        async with self._lock:
            return self.i2c.readfrom_mem(self.address, self.DISPLAY_ADDRESS, 16)

    # ---- Buffer editing: no I/O, call draw() to show the result ----

    def clear(self):
        for i in range(16):
            self.buffer[i] = 0
        return self

    def rotate(self):
        """Toggle 180 degree rotation, for a display mounted upside down. Applies at the next draw()."""
        self.is_rotated = not self.is_rotated
        return self

    def set_glyph(self, glyph, digit=0, has_dot=False):
        """Raw segment pattern (0x00-0xFF, bit 7 = decimal point) at a digit (0 = leftmost)."""
        if not 0 <= digit < self.max_digits:
            raise ValueError("HT16K33LED digit must be 0-%d" % (self.max_digits - 1))
        if not 0 <= glyph <= 0xFF:
            raise ValueError("HT16K33LED glyph must be 0x00-0xFF")
        self.buffer[digit << 1] = glyph | (self.DOT if has_dot else 0)
        return self

    def set_character(self, char, digit=0, has_dot=False):
        """One character from CHARSET (case-insensitive) at a digit."""
        glyph = self.CHARSET.get(char.lower())
        if glyph is None:
            raise ValueError("HT16K33LED has no glyph for %r" % char)
        return self.set_glyph(glyph, digit, has_dot)

    def set_number(self, number, digit=0, has_dot=False):
        """One decimal digit (0-9) at a digit."""
        if not 0 <= number <= 9:
            raise ValueError("HT16K33LED number must be 0-9")
        return self.set_character(str(number), digit, has_dot)

    def _glyphs(self, text):
        """Text to a list of glyphs. A '.' joins the character before it; a leading or second '.'
        takes a digit of its own."""
        glyphs = []
        for char in text:
            if char == "." and glyphs and not glyphs[-1] & self.DOT:
                glyphs[-1] |= self.DOT
            else:
                glyph = self.CHARSET.get(char.lower())
                if glyph is None:
                    raise ValueError("HT16K33LED has no glyph for %r" % char)
                glyphs.append(glyph)
        return glyphs

    async def set_string(self, string, alignment="l"):
        """Show text, left ("l") or right ("r") aligned, and draw it. Text longer than the display is
        cut off; use scroll() to show all of it."""
        if alignment not in ("l", "r"):
            raise ValueError("HT16K33LED alignment must be 'l' or 'r'")
        glyphs = self._glyphs(string)[:self.max_digits]
        pad = [0] * (self.max_digits - len(glyphs))
        glyphs = pad + glyphs if alignment == "r" else glyphs + pad
        for digit, glyph in enumerate(glyphs):
            self.buffer[digit << 1] = glyph
        await self.draw()

    async def scroll(self, text, delay_ms=300):
        """Scroll text right to left across the display, one digit every delay_ms, ending blank."""
        n = self.max_digits
        glyphs = [0] * n + self._glyphs(text) + [0] * n
        for start in range(len(glyphs) - n + 1):
            for digit in range(n):
                self.buffer[digit << 1] = glyphs[start + digit]
            await self.draw()
            await asyncio.sleep_ms(delay_ms)
