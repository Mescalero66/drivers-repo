from HT16K33LED import HT16K33LED
import utime as time
from machine import I2C, Pin

"""
MicroPython driver for 8-digit 7-segment LED displays using the HT16K33 controller.
"""

POS = [0, 2, 4, 6, 8, 10, 12, 14]
DELAY = 0.01
PAUSE = 3

if __name__ == '__main__':
    i2c = I2C(0, scl=Pin(1), sda=Pin(0))
    display = HT16K33LED(i2c)
    display.set_brightness(15)

    def clear(disp_obj):
        for i in range(0,8):
            disp_obj.set_number(0, i, False)
   
    display.set_character(" ", 0)
    display.set_character("*", 1)
    display.set_character("-", 2)
    display.set_character("°", 3)
    display.draw()
    time.sleep(PAUSE)
    
    i = 0
    while i < 8:
        display.clear()
        display.set_character(" ", i)
        i = i + 1
        display.draw()
        time.sleep(PAUSE / 2)
       
    
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