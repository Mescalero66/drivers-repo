from HT16K33LED import HT16K33LED
import utime as time
from machine import I2C, Pin

"""
MicroPython driver for 8-digit 7-segment LED displays using the HT16K33 controller.
Includes decimal points, extended charset, scrolling text, and justification.
"""

POS = [0, 2, 4, 6, 8, 10, 12, 14]
DELAY = 0.01
PAUSE = 3

CHARSET = [
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F,  # 0–9
    0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 0x06, 0x1E,  # A–J
    0x75, 0x38, 0x37, 0x54, 0x5C, 0x73, 0x67, 0x50, 0x6D, 0x78,  # K–T
    0x3E, 0x1C, 0x2A, 0x76, 0x6E, 0x5B,                          # U–Z
    0x00, 0x40, 0x63, 0x48, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00   # space, -, °, =, _
]

CHAR_LOOKUP = {
    0x20: 36,  # space
    0x2D: 37,  # dash
    0xB0: 38,  # degree °
    0x2A: 38,  # * = degree symbol
    0x3D: 39,  # equal =
    0x5F: 40   # underscore
}

if __name__ == '__main__':
    i2c = I2C(0, scl=Pin(1), sda=Pin(0))
    display = HT16K33LED(i2c)
    display.set_brightness(15)

    def clear(d):
        for i in range(0,8):
            d.set_number(0, i, False)

    sync_text = b"\x6D\x6E\x37\x39"
    runs = 2
    while True:
        # Write 'SYNC' to the LED using custom glyphs
        display.clear()
        for i in range(len(sync_text)):
            display.set_glyph(sync_text[i], i)
            display.set_glyph(sync_text[i], i + 4)
        display.draw()
        time.sleep(PAUSE)

        # Write 'SYNC' to the LED -- this time with decimal points
        for i in range(len(sync_text)):
            display.set_glyph(sync_text[i], i, True)
            display.set_glyph(sync_text[i], i + 4, True)
        display.draw()
        time.sleep(PAUSE)

        # Write 'BEEF' to the display using the charset characters
        display.set_character("B", 0).set_character("E", 1)
        display.set_character("E", 2).set_character("F", 3)
        display.set_character("B", 4).set_character("E", 5)
        display.set_character("E", 6).set_character("F", 7)
        display.draw()
        time.sleep(PAUSE)

        display.set_character(" ", 2).set_character(" ", 3)
        display.set_character(" ", 6).set_character(" ", 7)
        display.draw()
        time.sleep(PAUSE)

        # Show a countdown using the charset numbers
        # (also uses 'set_colon()')
        count = 0
        while True:
            # Convert 'count' into Binary-Coded Decimal (BCD)
            bcd = int(str(count), 16)

            # Display 'count' as decimal digits
            # Include a decimal point on digit 5
            display.set_number((bcd & 0xF0000000) >> 28, 0)
            display.set_number((bcd & 0x0F000000) >> 24, 1)
            display.set_number((bcd & 0x00F00000) >> 20, 2)
            display.set_number((bcd & 0x000F0000) >> 16, 3)
            display.set_number((bcd & 0x0000F000) >> 12, 4)
            display.set_number((bcd & 0x00000F00) >> 8, 5, True)
            display.set_number((bcd & 0x000000F0) >> 4, 6)
            display.set_number((bcd & 0x0000000F), 7)
            display.draw()

            count += 100
            if count >= 99999999: break

        # Pause for breath
        time.sleep(DELAY)

        # Flash the LED
        display.set_blink_rate(1)
        time.sleep(PAUSE)
        display.set_blink_rate(0)
        time.sleep(PAUSE)

        runs -= 1
        if runs < 1:
            break