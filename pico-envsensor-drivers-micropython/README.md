# PowerTec Environment Sensor System [I2C]

Repository for the PowerTec Environment Sensor System

## Installing on the RaspberryPi pico

See PTwiki:
<https://power-tec.com.au/ptwiki/1sdv/field_devices/pt_envsensor>

## Modbus
The modbus configuration of this device is as follows:
1. Network port: 502
2. The data addresses start at 10 and are as follows:

| Addr | Description | Addr | Description | Addr | Description |
| :---: | --- | :---: | --- | :---: | --- |
| `10` | Temperature 1 (°C) | `20` | Temperature 6 (°C) | 30 |  |
| `11` | Humidity 1 (%) | `21` | Humidity 6 (%) | 31 |  |
| `12` | Temperature 2 (°C) | 22 |  | `32` | AQS 1 C02 (ppm) |
| `13` | Humidity 2 (%) | 23 |  | `33` | AQS 1 TVOC (ppb) |
| `14` | Temperature 3 (°C) | 24 |  | `34` | AQS 1 Air Quality Index |
| `15` | Humidity 3 (%) | 25 |  | `35` | AQS2 C02 (ppm) |
| `16`| Temperature 4 (°C) | 26 |  | `36` | AQS2 TVOC (ppb) |
| `17` | Humidity 4 (%) | 27 |  | `37` | AQS2 Air Quality Index |
| `18` | Temperature 5 (°C) | 28 |  | 38 |  |
| `19` | Humidity 5 (%) | 29 |  | 39 |  |

### Diagnostic Registers
| Addr | Description | Values |
| :---: | --- | --- |
| `54` |  |  |
| `55` |  |  |
| `56` |  |  |
| `57` |  |  |
| `58` | Count of Big Exceptions | **0 < 11** <br> A running count of the number of Big Exceptions that have occurred in the Main Loop. If the count reaches 10, the system will reboot. |
| `59` |  |  |

## Resetting the IP via Modbus
1. Every 600 seconds, the device checks if the Reset Trigger (Register 49) is value **1**.
2. If the Reset Trigger is **1**, a new IP and Gateway address is constructed from registers 41 to 44, and 45 to 48, respectively.
3. The network_address.txt file is then **OVERWRITTEN** with the new information, and the system is rebooted.

**Be careful doing this, because typos may result in the device to be inaccessble from the network!**

 Addr | Desc | Addr | Desc |
| --- | --- | --- | --- |
| `41` | IP Oct #1 | `45` | Gateway Oct #1 |
| `42` | IP Oct #2 | `46` | Gateway Oct #2 |
| `43` | IP Oct #3 | `47` | Gateway Oct #3 |
| `44` | IP Oct #4 | `48` | Gateway Oct #4 |
| - | - | `49` | Reset Trigger |






