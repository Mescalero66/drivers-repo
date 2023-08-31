from my9221 import MY9221
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

GPIO.setup(29, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)

ledbar = MY9221(29, 31, reverse=False)

ledbar.level(8, 255)