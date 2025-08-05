from machine import Pin, UART
import time

# Set up UART connection to GPS module
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Main loop
while True:
    # Check if data is available from GPS
    if uart.any():
        # Read the available data
        gps_reading = uart.read().decode('utf-8')
        
        print(gps_reading)