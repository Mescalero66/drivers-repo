from machine import Pin, UART
import time
import parseGPS

# Set up UART connection to GPS module
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Create a GPS reader object
GPS_obj = parseGPS.GPSReader(uart)

# Main loop
while True:
    # Get the GPS data, this will also try and read any new information form the GPS
    gps_data = GPS_obj.get_data()
    
    # Print the GPS data
    print(gps_data.has_fix, "[", gps_data.satellites, "]", gps_data.latitude, gps_data.longitude, gps_data.time)
    
    # Small delay
    time.sleep(2)