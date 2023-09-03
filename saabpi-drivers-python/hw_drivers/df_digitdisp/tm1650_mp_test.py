import smbus
from tm1650_mp import TM1650

channel = 1
bus = smbus.SMBus(channel)

disp = TM1650(2, 3)

disp.display_on()

for i in range(10000):
  disp.display_integer(i)

disp.display_clear()
disp.display_off()