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
    i2c = I2C(0, scl=Pin(5), sda=Pin(4))
    display = HT16K33LED(i2c)
    display.set_brightness(15)

    def clear(disp_obj):
        for i in range(0,8):
            disp_obj.set_number(0, i, False)
   
    display.set_string("HiHoney", "r")
    time.sleep(PAUSE)
    display.set_string("Caitlin", "l")
    time.sleep(PAUSE)
    display.set_string("Nhung", "r")
    time.sleep(PAUSE)
    display.set_string("Charlie", "l")
    time.sleep(PAUSE)
    display.set_string("buttcrak", "l")
    time.sleep(PAUSE)

    i = 0
    j = 0 
    while i < 8:
        while j < 8:
            display.clear()
            display.set_character("*", j)
            j = j + 1
            display.draw()
            time.sleep(0.2)
        j = j - 1
        while j > 0:
            display.clear()
            display.set_character("o", j)
            j = j - 1
            display.draw()
            time.sleep(0.2)
        j = 0
        i = i + 1
        time.sleep(PAUSE)
       
    
    display.set_string("1234567", "r")
    time.sleep(PAUSE)
    display.set_string("12345", "r")
    time.sleep(PAUSE)
    display.set_string("123", "r")
    time.sleep(PAUSE)
    display.set_string("12", "r")
    time.sleep(PAUSE)
    display.set_string("123", "l")
    time.sleep(PAUSE)
    display.set_string("12345", "l")
    time.sleep(PAUSE)
    display.set_string("1234568", "l")
    time.sleep(PAUSE)

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