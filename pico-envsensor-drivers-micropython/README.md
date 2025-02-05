# PowerTec Environment Sensor System

Repository for the PowerTec Environment Sensor System

## Installing on the RaspberryPi pico

See PTwiki:
<https://power-tec.com.au/ptwiki/1sdv/field_devices/pt_envsensor>

## Modbus
The modbus configuration of this device is as follows:
1. Network port: 502
2. The data addresses start at 10 and are as follows:

| Address | Data | Address | Data | Address | Data |
| --- | --- | --- | --- | --- | --- |
| 10 | Temperature 1 (°C) | 20 | Temperature 6 (°C) | 30 |  |
| 11 | Humidity 1 (%) | 21 | Humidity 6 (%) | 31 |  |
| 12 | Temperature 2 (°C) | 22 |  | 32 | AQS 1 C02 (ppm) |
| 13 | Humidity 2 (%) | 23 |  | 33 | AQS 1 TVOC (ppb) |
| 14 | Temperature 3 (°C) | 24 |  | 34 | AQS 1 Air Quality Index |
| 15 | Humidity 3 (%) | 25 |  | 35 | AQS2 C02 (ppm) |
| 16 | Temperature 4 (°C) | 26 |  | 36 | AQS2 TVOC (ppb) |
| 17 | Humidity 4 (%) | 27 |  | 37 | AQS2 Air Quality Index |
| 18 | Temperature 5 (°C) | 28 |  | 38 |  |
| 19 | Humidity 5 (%) | 29 |  | 39 |  |








