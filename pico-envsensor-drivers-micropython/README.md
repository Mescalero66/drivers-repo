# Powertec Environment  Sensor

Repository for the environment sensor system in PowerCache

See PTwiki:
<http://power-tec.com.au/ptwiki/2hdv/8rdp/08/75>

## Installing on the RaspberryPi pico

1. Boot the Pico as a disk device. (on windows)
   1. Connect the Pico via USB cable to the host machine.
   2. The device will appear as a folder on the host machine
   3. If it doesn't appear, then push and hold the bootsel button, then push the run button.
   4. Copy the micropython image into the pico folder.
       1. This is located at: \\\\powertec-nas\PTES-Software\Release\Micropython
       2. Should be called something like: W5500_EVB_PICO-20230426-v1.20.0.uf2
   5. The device will now reboot on its own
2. Now that micropython is installed, it will connect to this project when it is loaded into VSCode
3. Connect the network port on the Pico to a network switch via ethernet cable. Make sure the network connection light is on the socket on the Pico
3. Install the modbus library
   1. Right-click on the install.py file in the project explorer and choose the "Run current file on Pico" option
   2. This will install the modbus library required by the environment sensor.
4. Install the project onto the Pico
   1. Right click in the empty area below the file list in the project explorer pane. Select the "Upload project to pico" option
5. Make sure the network configuration is correct in the network_address.txt file.
   1. First line is the static IP
   2. Seconds line in the network mask
   3. Third line is the network gateway
   4. Fourth line is the DNS server address
6. Once the network configuration is correct, right-click in the text editor and select "Upload current file to Pico"

## Modbus
The modbus configuration of this device is as follows:
1. Network port: 502
2. The data addresses start at 10 and are as follows:

| Address | Data |
| --- | --- |
| 10 | Temperature 1 |
| 11 | Humidity 1 |
| 12 | Temperature 2 |
| 13 | Humidity 2 |
| 14 | Temperature 3 |
| 15 | Humidity 3 |
| 16 | Temperature 4 |
| 17 | Humidity 4 |
| 18 | Temperature 5 |
| 19 | Humidity 5 |
| 20 | Temperature 6 |
| 21 | Humidity 6 |
| 22 | Temperature 7 |
| 23 | Humidity 7 |
| 24 | Temperature 8 |
| 25 | Humidity 8 |





