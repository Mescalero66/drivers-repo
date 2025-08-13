import time
from mux import I2CMultiplex

I2CMultiAddr = 0x70  # I2C Multiplexer address

# Create multiplexer object
I2CMulti = I2CMultiplex(I2CMultiAddr, I2Cbus=1, scl_pin=15, sda_pin=14)

for port in range(8):  # Scan I2C devices on each port
    print("Port:", port)
    addr_list = I2CMulti.scan(port)
    if addr_list:
        # Show addresses in hex
        print("I2C addresses:", [hex(a) for a in addr_list])
    else:
        print("No devices found")
    time.sleep(0.1)
