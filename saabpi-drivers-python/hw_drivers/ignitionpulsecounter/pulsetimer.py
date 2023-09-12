#!/usr/bin/env python

# low_high.py
# 2015-11-05
# Public Domain

import time
import pigpio

RX=12

INTERVAL=1000000
start_tick = None
last_tick = None

low_ticks = 0
high_ticks = 0

def cbf(gpio, level, tick):
   global start_tick, last_tick, low_ticks, high_ticks
   if start_tick is not None:
      ticks = pigpio.tickDiff(last_tick, tick)
      last_tick = tick
      if level == 0: # Falling edge.
         high_ticks = high_ticks + ticks
      else: # Rising edge.
         low_ticks = low_ticks + ticks
      interval = pigpio.tickDiff(start_tick, tick)
      if interval >= INTERVAL:
         print("ratio = {:.3f}".format(float(low_ticks)/float(interval)))
         print("lt={} ht={} int={}".format(low_ticks, high_ticks, interval))
         start_tick = tick
         last_tick = tick
         low_ticks = 0
         high_ticks = 0
   else:
      start_tick = tick
      last_tick = tick

pi = pigpio.pi() # Connect to local Pi.

pi.set_mode(RX, pigpio.INPUT)

cb = pi.callback(RX, pigpio.EITHER_EDGE, cbf)

time.sleep(60)

cb.cancel() # Cancel callback.

pi.stop() # Disconnect from local Pi.