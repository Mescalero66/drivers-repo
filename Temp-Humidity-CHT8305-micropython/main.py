import time
import CHT8305

# I2C wiring on the Raspberry Pi Pico
I2C_CHANNEL = 1
I2C_CLOCK = 3   # GP3 -> SCL
I2C_DATA = 2    # GP2 -> SDA

READ_INTERVAL_S = 5
ENABLE_HEATER = False   # set True to demonstrate the on-chip heater

print("CHT8305 Temperature & Humidity Sensor Demo")
print("-----")

# set up the sensor
sensor = CHT8305.I2C_CHT8305_SEN0546(I2C_CHANNEL, I2C_CLOCK, I2C_DATA)

found = sensor.i2c.scan()
print("I2C devices found: ", [hex(a) for a in found])
if sensor.CHT8305_Address not in found:
    print("CHT8305 not found at address", hex(sensor.CHT8305_Address), "- check wiring.")
    raise SystemExit

# device information
sensor.get_CHT8305_MANUFACTURE_ID()
sensor.get_CHT8305_VERSION_ID()

# configuration
sensor.set_CHT8305_CONFIG_DEFAULT()
if ENABLE_HEATER:
    sensor.set_CHT8305_CONFIG_HEATER_ON()
sensor.get_CHT8305_CONFIG()
print("-----")

# single blocking read
Temperature, Humidity = sensor.get_CHT8305_TEMPERATURE_HUMIDITY()
if Temperature is not None:
    print(f"Initial reading  Temp: {Temperature:.1f}°C   Humi: {Humidity:.1f}%")
print("-----")

# continuous reading using the split request / read pattern
while True:
    try:
        sensor.req_CHT8305_TEMPERATURE_HUMIDITY()
        time.sleep_ms(200)   # allow the conversion to complete
        Temperature, Humidity = sensor.read_CHT8305_TEMPERATURE_HUMIDITY()
        if Temperature is None:
            raise OSError("no data returned")
        print(f"Temp: {Temperature:.1f}°C   Humi: {Humidity:.1f}%")
    except Exception as e:
        print("Failed reading from CHT8305 : {}".format(e))
        try:
            sensor.send_CHT8305_SOFT_RESET()
        except Exception:
            pass
    time.sleep(READ_INTERVAL_S)
