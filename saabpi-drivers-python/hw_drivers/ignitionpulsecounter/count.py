# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224

import time
import pigpio 

GPIO=12
pi = pigpio.pi() # Connect to local Pi.
cb = pi.callback(GPIO)

for i in 1:
   print(cb.count)
   time.sleep(1.0)
   i += 1