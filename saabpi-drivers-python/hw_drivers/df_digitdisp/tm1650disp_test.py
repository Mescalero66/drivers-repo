
import time
from tm1650disp import tm1650Display
import RPi.GPIO as GPIO

# connect to clockPin & dataPin
clockPin = 27
dataPin = 17

# create object
disp1 = tm1650Display(clockPin, dataPin)
disp1.sendStart()

# turn on with brightness (high 0 to low 7)
disp1.displayOn(0)

# set communications speed (baud rate)
# disp1.setSpeed(100000)

# display number
disp1.showInteger(1234)
time.sleep(3)

# display decimal number
disp1.showDecimal(12.34)
time.sleep(3)

# display hex code
disp1.showHex(123)
time.sleep(3)

# display character at a given position (0 - 3)
disp1.showChar(0, "a")
time.sleep(1)
disp1.showChar(1, "b")
time.sleep(1)
disp1.showChar(2, "c")
time.sleep(1)
disp1.showChar(3, "d")
time.sleep(1)

# display a string
disp1.showString("Saab")
time.sleep(5)

# clear display
disp1.displayClear()

# display off
disp1.displayOff()