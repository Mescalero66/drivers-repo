# coding: utf-_
import RPi.GPIO as GPIO
import time

lasttime=0
 
def callback_up(channel):
    global lasttime
    if lasttime==0:
        lasttime=time.time()
    else:
        now = time.time()
        gap=now-lasttime
        gap_mill = gap * 10000000
        RPM = round(30000000 / gap_mill, 1)
        print(RPM)
        lasttime=now
    
 
GPIO.setmode(GPIO.BCM)
PIR = 12
GPIO.setup(PIR, GPIO.IN)
try:
    GPIO.add_event_detect(PIR, GPIO.RISING, callback=callback_up)
    while 1:
        time.sleep(10)
except KeyboardInterrupt:
   print("fin")