# PowerTec Environment Sensor System

Repository for the PowerTec Environment Sensor System

## Installing on the RaspberryPi pico

See PTwiki:
<http://power-tec.com.au/ptwiki/2hdv/8rdp/08/75/start>

## Modbus
The modbus configuration of this device is as follows:
1. Network port: 502
2. The data addresses start at 10 and are as follows:

^ Address ^ Data ^ Address ^ Data ^ Address ^ Data ^
^ 10 | Temperature 1 (°C) ^ 20 | Temperature 6  (°C) ^ 30 | |
^ 11 | Humidity 1 (%) ^ 21 | Humidity 6 (%) ^ 31 | |
^ 12 | Temperature 2 (°C) ^ 22 |  ^ 32 | AQ Sensor 1 C02 (ppm) |
^ 13 | Humidity 2 (%) ^ 23 | ^ 33 | AQ Sensor 1 TVOC (ppb) |
^ 14 | Temperature 3 (°C) ^ 24 |  ^ 34 | AQ Sensor 1 Air Quality Index |
^ 15 | Humidity 3 (%) ^ 25 |  ^ 35 | AQ Sensor 2 C02 (ppm)  |
^ 16 | Temperature 4 (°C) ^ 26 |  ^ 36 | AQ Sensor 2 TVOC (ppb) |
^ 17 | Humidity 4 (%) ^ 27 |  ^ 37 | AQ Sensor 2 Air Quality Index |
^ 18 | Temperature 5 (°C) ^ 28 |  ^ 38 | |
^ 19 | Humidity 5 (%) ^ 29 |  ^ 39 | |





