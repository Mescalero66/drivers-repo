# Pico Environment Sensor [I2C]
Originally for the PowerTec Environment Sensor device.

## Installing on the RaspberryPi pico
See PTwiki:
<https://power-tec.com.au/ptwiki/1sdv/field_devices/pt_envsensor>

## Modbus Registers
The Modbus configuration of this device is as follows:
 - Network Port: 502
 
 - Temperature values are in °C x 10 (i.e. 21.5°C will be returned as 215)
 - eCO2 values are in ppm
 - TVOC values are in ppb
 
 - The data registers start at `10` and are as follows:

| Addr | Description | Addr | Description | Addr | Description | Addr | Description |
| :---: | --- | :---: | --- | :---: | --- | :---: | --- |
| `10` | Temp 01 | `20` | Temp 06  | `30` | AQS1 eCO2 | `40` | AQS6 eCO2 |
| `11` | Humi 01 | `21` | Humi 06 | `31` | AQS1 TVOC | `41` | AQS6 TVOC |
| `12` | Temp 02 | `22` | Temp 07  | `32` | AQS2 eCO2 | `42` | AQS7 eCO2 |
| `13` | Humi 02 | `23` | Humi 07 | `33` | AQS2 TVOC | `43` | AQS7 TVOC |
| `14` | Temp 03 | `24` | Temp 08  | `34` | AQS3 eCO2 | `44` | AQS8 eCO2 |
| `15` | Humi 03 | `25` | Humi 08 | `35` | AQS3 TVOC | `45` | AQS8 TVOC |
| `16` | Temp 04 | 26 |  | `36` | AQS4 eCO2 | 46 |  |
| `17` | Humi 04 | 27 |  | `37` | AQS4 TVOC | 47 |  |
| `18` | Temp 05 | 28 |  | `38` | AQS5 eCO2 | 48 |  |
| `19` | Humi 05 | 28 |  | `39` | AQS5 TVOC | 49 |  |

## Network Configuration
IP addresses can be set by editing the **network_config.py** file before copying the project to the Pico.

Default network configuration addresses are:
 - ip_address = '192.168.1.23'
 - subnet_mask = '255.255.255.0'
 - default_gateway = '192.168.1.1'
 - dns = '8.8.8.8'

## Refer to this repo for async/non-blocking modbus components
https://github.com/brainelectronics/micropython-modbus/blob/2f4e4eb691847e5242a5c33be6bad77782a4357a/examples/
