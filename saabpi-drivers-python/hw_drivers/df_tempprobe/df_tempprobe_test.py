# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>

import time
from df_tempprobe import tempprobe

probe1 = tempprobe(1)                       # create tempprobe object
#probe1.i2c.open(1)
i = 0

while i < 30:
    rTCalc = round(probe1.get_Temp(), 1)    # call get_temp function, put rounded result in rTCalc     
    rHCalc = round(probe1.get_Humi(), 1)    # call get_humi function, put rounded result in rHCalc
    print("Temp: ", rTCalc)
    print("Humidity: ", rHCalc)
    i += 1                                  
    time.sleep(2)                           # about 2 seconds is the quickest you can set this before you there's no real change between refreshes

