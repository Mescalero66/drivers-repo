from machine import I2C, Pin
import ENS160
import time
import ubinascii

# Initialize I2C interface (adjust pins and frequency as needed)
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=100000)

# Initialize the ENS160 sensor
sensor_ens160 = ENS160.ENS160(1,3,2)

# Offset for temperature adjustment (in Celsius)
temperature_offset = -10.0  # Adjust this value as needed

# Sleeptime ms
sleeptime = 60000

# Main loop to read and send sensor data
while True:
    aqi, tvoc, eco2, temp, rh, eco2_rating, tvoc_rating = sensor_ens160.read_air_quality()
    
    # Create payload
    #payload = bytearray()
    #payload.append(aqi)
    #payload.extend(tvoc.to_bytes(2, 'big'))
    #payload.extend(eco2.to_bytes(2, 'big'))

    # Print sensor data
    print(f"AQI: {aqi}")
    print(f"TVOC: {tvoc} ppb")
    print(f"TVOC Rating: {tvoc_rating}")
    print(f"eCO2: {eco2} ppm")
    print(f"eCO2 Rating: {eco2_rating}")
