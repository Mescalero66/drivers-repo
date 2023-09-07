import time
from df_tempprobe import df_tempprobe

probe1 = df_tempprobe(1)
#probe1.i2c.open(1)
i = 0

while i < 30:
    rTCalc = probe1.get_Temp()
    rHCalc = probe1.get_Humi()
    rTCalc = round(rTCalc, 1)
    print("Temp: ", rTCalc)
    rHCalc = round(rHCalc, 1)
    print("Humidity: ", rHCalc)
    i += 1
    time.sleep(3) # about 3 seconds is the quickest you can set this before you start to no real change between refreshes

