## credit to JustDr00py
##<https://github.com/JustDr00py/ens160-aht21>

from machine import I2C
import machine
import time

address = 0x53

class ENS160:
    def __init__(self, ID, SCL, SDA):
        self.i2c = machine.I2C(id=ID, scl=machine.Pin(SCL), sda=machine.Pin(SDA), freq=100000)
        self.address = address
        self.set_mode(0x02)
        time.sleep_ms(1000)

    def _read_register(self, reg, length):
        return self.i2c.readfrom_mem(self.address, reg, length)

    def _write_register(self, reg, data):
        self.i2c.writeto_mem(self.address, reg, data)

    def set_mode(self, mode):
        self._write_register(0x10, bytes([mode]))  # Operating Mode

    def get_id(self):
        data = self._read_register(0x00, 2)  # Device Identity (0x0160)
        return (data[1] << 8) | data[0]  # LSB first, then MSB

    def get_firmware_version(self):
        mode = self._read_register(0x10, 1)[0]  # save current Operating Mode
        self.set_mode(0x01)  # commands are only accepted in Idle mode
        self._write_register(0x12, bytes([0x00]))  # NOP
        self._write_register(0x12, bytes([0xCC]))  # CLRGPR - clear General Purpose Read registers
        time.sleep_ms(10)
        self._write_register(0x12, bytes([0x0E]))  # GET_APPVER
        time.sleep_ms(10)
        data = self._read_register(0x48, 8)  # General Purpose Read registers
        self.set_mode(mode)
        return f"{data[4]}.{data[5]}.{data[6]}"  # major.minor.release

    def get_status(self):
        data = self._read_register(0x20, 1)  # Operating Mode
        return data[0]
    
    def get_aqi(self):
        data = self._read_register(0x21, 1)  # Air Quality Index
        aqi_uba = data[0] & 0x07  # Extract the lower 3 bits
        return aqi_uba
    
    def get_tvoc(self):
        data = self._read_register(0x22, 2)  # TVOC Concentration (ppb)
        tvoc = (data[1] << 8) | data[0]  # LSB first, then MSB
        return tvoc

    def get_eco2(self):
        data = self._read_register(0x24, 2)  # Equivalent CO2 Concentration (ppm)
        eco2 = (data[1] << 8) | data[0]  # LSB first, then MSB
        return eco2

    def get_temperature(self):
        data = self._read_register(0x30, 2)  # Temperature used in calculations
        temp_raw = (data[1] << 8) | data[0]  # LSB first, then MSB
        temp_kelvin = temp_raw / 64.0
        temp_celsius = temp_kelvin - 273.15
        return temp_celsius

    def get_humidity(self):
        data = self._read_register(0x32, 2)  # Relative Humidity used in calculations
        rh_raw = (data[1] << 8) | data[0]  # LSB first, then MSB
        rh = rh_raw / 512.0  # RH% * 512
        return rh

    def interpret_eco2_level(self, eco2):
        if eco2 > 1500:
            return "Bad - Heavily contaminated indoor air / Ventilation required"
        elif eco2 > 1000:
            return "Poor - Contaminated indoor air / Ventilation recommended"
        elif eco2 > 800:
            return "Fair - Optional ventilation"
        elif eco2 > 600:
            return "Good - Average"
        elif eco2 >= 400:
            return "Excellent - Target level"
        else:
            return "Unknown"

    def interpret_tvoc_level(self, tvoc):
        if tvoc <= 50:
            return "Excellent"
        elif tvoc <= 100:
            return "Good"
        elif tvoc <= 150:
            return "Moderate"
        elif tvoc <= 200:
            return "Unhealthy"
        elif tvoc <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"

    def read_air_quality(self):
        aqi = self.get_aqi()
        tvoc = self.get_tvoc()
        eco2 = self.get_eco2()
        temp = self.get_temperature()
        rh = self.get_humidity()
        eco2_rating = self.interpret_eco2_level(eco2)
        tvoc_rating = self.interpret_tvoc_level(tvoc)
        return aqi, tvoc, eco2, temp, rh, eco2_rating, tvoc_rating
    
    def get_air_quality(self):
        eco2 = self.get_eco2()
        tvoc = self.get_tvoc()
        return eco2, tvoc
    
    def calibrate_Temperature(self, temp_lsb, temp_msb):
        self._write_register(0x13, bytes([temp_lsb]))
        self._write_register(0x14, bytes([temp_msb]))

    def calibrate_Humidity(self, humi_lsb, humi_msb):
        self._write_register(0x15, bytes([humi_lsb]))
        self._write_register(0x16, bytes([humi_msb]))