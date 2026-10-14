import time, machine
import ENS160

# I2C bus wiring on the Raspberry Pi Pico
I2C_ID = 1
I2C_SCL = 3  # GP3
I2C_SDA = 2  # GP2

# Ambient conditions used for compensation. In a real deployment these would
# come from a separate temperature/humidity sensor.
AMBIENT_TEMP_C = 22.0
AMBIENT_HUMIDITY = 50.0

READ_INTERVAL_S = 2

led = machine.Pin(25, machine.Pin.OUT)

VALIDITY_FLAGS = {
    0: "Normal operation",
    1: "Warm-up phase",
    2: "Initial start-up phase",
    3: "Invalid output",
}

def blink():
    led.high()
    time.sleep_ms(100)
    led.low()

def validity(status):
    return VALIDITY_FLAGS[(status >> 2) & 0x03]

def calibrate(sensor, temp_celsius, humidity):
    temp_value = int((temp_celsius + 273.15) * 64)
    humi_value = int(humidity * 512)
    sensor.calibrate_Temperature(temp_value & 0xFF, (temp_value >> 8) & 0xFF)
    sensor.calibrate_Humidity(humi_value & 0xFF, (humi_value >> 8) & 0xFF)
    print(f"Compensation set: {temp_celsius:.1f}°C (0x{temp_value:04X}), {humidity:.1f}% (0x{humi_value:04X})")

print("ENS160 Air Quality Sensor Demo")
print("-----")

try:
    sensor = ENS160.ENS160(I2C_ID, I2C_SCL, I2C_SDA)
except Exception as e:
    print("Failed to initialise ENS160: {}".format(e))
    raise

print(f"Device ID: 0x{sensor.get_id():04X}")
print(f"Status:    0x{sensor.get_status():02X} ({validity(sensor.get_status())})")
calibrate(sensor, AMBIENT_TEMP_C, AMBIENT_HUMIDITY)
print("-----")

while True:
    try:
        status = sensor.get_status()
        aqi = sensor.get_aqi()
        eco2, tvoc = sensor.get_air_quality()
        print(f"AQI: {aqi}   eCO2: {eco2}ppm ({sensor.interpret_eco2_level(eco2)})   TVOC: {tvoc}ppb ({sensor.interpret_tvoc_level(tvoc)})   [{validity(status)}]")
        blink()
    except Exception as e:
        print("Failed reading from ENS160: {}".format(e))
    time.sleep(READ_INTERVAL_S)
