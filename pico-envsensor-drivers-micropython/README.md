# PowerTec Environment Sensor System [I2C]

Repository for the PowerTec Environment Sensor System

## Installing on the RaspberryPi pico

See PTwiki:
<https://power-tec.com.au/ptwiki/1sdv/field_devices/pt_envsensor>

## Modbus Registers
The Modbus configuration of this device is as follows:
 - Network Port: 502

 - The Device Heartbeat (Register 52) with a value **>= 0 < 59** indicates that the system is operating normally in the main loop.
 
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
| `19` | Humi 05 | `29` | Average AQI | `39` | AQS5 TVOC | 49 |  |
| | | | | | | 50 |  |
| | | | | | | 51 |  |
| | | | | | | `52` | **Device Heartbeat** |
| | | | | | | `53` | Pico Internal Temp |

## Modbus Status & Settings Registers

### Diagnostic Registers
| Addr | Description | Values |
| :---: | --- | --- |
| `54` | System Status | **START UP:** <br> **91** = System starting up. <br> **92** = Setting up I2C bus. <br> **94** = Setting up I2C multiplexer device. <br> **95** = Multiplexer device online. <br> **96** = Scanning for temperature sensors. <br> **98** = Temperature sensor(s) online. <br> **99** = Entering the Main Loop. **100** = System Operating in Main Loop. <br> <br> **ERROR CODES:** <br> **111** = Serious exception in main loop. System will continue. <br> **112** = Multiple serious exceptions in main loop.System will restart in 5 seconds. <br> **113** = .... <br> **114** = .... <br> **115** = .... **119** = Main Loop has ended somehow. System will restart. |
| `55` | Temp & Humidity Sensors Online | **0 < 9** <br> Number of I2C Temperature + Humidity sensors detected at startup. |
| `56` | Air Quality Sensors Online | **0 < 8** <br> Number of I2C Air Quality sensors detected at startup. |
| `57` | IP Address Reset Status | **991** = IP reset triggered, reading new details. <br> **992** = Writing IP and Gateway to network_address.txt <br> **995** = New details written to network_address.txt. <br> **996** = **ERROR** when writing new IP and Gateway to file. <br> **999** = Network Configuration Updated. System will restart in 10 seconds. |
| `58` | Main Loop Exceptions | Number of serious exceptions in the main loop. System will restart if ten exceptions occur. |
| `59` | Temp Sensor Soft Resets | Number of temp sensor soft resets, sent after a failed temp sensor reading. System will not reset. |

## Resetting the IP via Modbus
1. Every 600 seconds, the device checks if the Reset Trigger (Register 69) is value **1**.
2. If the Reset Trigger is **1**, a new IP and gateway address is constructed from registers 61 to 64, and 65 to 68, respectively.
3. The network_address.txt file is then **OVERWRITTEN** with the new information, and the system is rebooted.

**Be careful doing this, because typos may result in the device to be inaccessble from the network!**

 Addr | Desc | Addr | Desc |
| --- | --- | --- | --- |
| `61` | IP Oct #1 | `65` | Gateway Oct #1 |
| `62` | IP Oct #2 | `66` | Gateway Oct #2 |
| `63` | IP Oct #3 | `67` | Gateway Oct #3 |
| `64` | IP Oct #4 | `68` | Gateway Oct #4 |
| - | - | `69` | Reset Trigger |






