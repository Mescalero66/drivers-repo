import time, machine, network, asyncio
from machine import Pin, SPI
from umodbus.asynchronous.tcp import AsyncModbusTCP as ModbusTCP
import DFRobot_I2C_Multiplexer
import I2C_CHT8305_SEN0546
import ENS160
import network_config

I2CMux_addr = 0x70
I2CMux_channel = 1
I2CMux_clock = 3
I2CMux_data = 2
led = machine.Pin(25, machine.Pin.OUT)

def blink():
    led.high()
    time.sleep_ms(100)
    led.low()

def load_default_network_config():
    global ip_address, network_mask, gateway_address, dns_server
    ip_address = "192.168.1.123"
    network_mask = "255.255.255.0"
    gateway_address = "192.168.1.1"
    dns_server = "8.8.8.8"

try:
    ip_address = network_config.ip_address
    network_mask = network_config.subnet_mask
    gateway_address = network_config.default_gateway
    dns_server = network_config.dns
except OSError:
    print("failed loading network config from network_address.txt file. Using default config")
    load_default_network_config()

print("PowerTec Enviro Sensor")
print("[I2C] v20260105-2114")
print("-----")
print("Network Config: (",ip_address,"-",network_mask,"-",gateway_address,"-",dns_server,")")
print("-----")

# set up the Ethernet Hardware
try:
    connectingNIC = 0
    spi=SPI(0,2_000_000, mosi=Pin(19),miso=Pin(16),sck=Pin(18))
    try:
        nic = network.WIZNET5K(spi,Pin(17),Pin(20),Pin(21)) #spi,cs,reset,int
    except:
        print("NIC object already exists.")
        pass
    nic.active(True)
    nic.ifconfig((ip_address, network_mask, gateway_address, dns_server))
    while not nic.isconnected():
        connectingNIC += 1
        time.sleep(2)
        if connectingNIC > 5:
            print("Failed to configure network. Device will reboot.")
            machine.reset()
        print("Getting IP.....")
    print('Device Network Address: ', nic.ifconfig())
except Exception as e:
    print("Exception during creation of NIC object: {}".format(e))

# set up modbus
print("Setting up Modbus.....")
local_ip = nic.ifconfig()[0]
tcp_port = 502  # port to listen for requests/providing modbus data
register_definitions = {
    "HREGS": {
        "TEMP_1": { "register": 10, "len": 1, "val": 0},
        "HUMI_1": { "register": 11, "len": 1, "val": 0},
        "TEMP_2": { "register": 12, "len": 1, "val": 0},
        "HUMI_2": { "register": 13, "len": 1, "val": 0},
        "TEMP_3": { "register": 14, "len": 1, "val": 0},
        "HUMI_3": { "register": 15, "len": 1, "val": 0},
        "TEMP_4": { "register": 16, "len": 1, "val": 0},
        "HUMI_4": { "register": 17, "len": 1, "val": 0},
        "TEMP_5": { "register": 18, "len": 1, "val": 0},
        "HUMI_5": { "register": 19, "len": 1, "val": 0},
        "TEMP_6": { "register": 20, "len": 1, "val": 0},
        "HUMI_6": { "register": 21, "len": 1, "val": 0},
        "TEMP_7": { "register": 22, "len": 1, "val": 0},
        "HUMI_7": { "register": 23, "len": 1, "val": 0},
        "TEMP_8": { "register": 24, "len": 1, "val": 0},
        "HUMI_8": { "register": 25, "len": 1, "val": 0},
        "AQS1_ECO2": { "register": 30, "len": 1, "val": 0},
        "AQS1_TVOC": { "register": 31, "len": 1, "val": 0},
        "AQS2_ECO2": { "register": 32, "len": 1, "val": 0},
        "AQS2_TVOC": { "register": 33, "len": 1, "val": 0},
        "AQS3_ECO2": { "register": 34, "len": 1, "val": 0},
        "AQS3_TVOC": { "register": 35, "len": 1, "val": 0},
        "AQS4_ECO2": { "register": 36, "len": 1, "val": 0},
        "AQS4_TVOC": { "register": 37, "len": 1, "val": 0},
        "AQS5_ECO2": { "register": 38, "len": 1, "val": 0},
        "AQS5_TVOC": { "register": 39, "len": 1, "val": 0},
        "AQS6_ECO2": { "register": 40, "len": 1, "val": 0},
        "AQS6_TVOC": { "register": 41, "len": 1, "val": 0},
        "AQS7_ECO2": { "register": 42, "len": 1, "val": 0},
        "AQS7_TVOC": { "register": 43, "len": 1, "val": 0},
        "AQS8_ECO2": { "register": 44, "len": 1, "val": 0},
        "AQS8_TVOC": { "register": 45, "len": 1, "val": 0}
    }
}

#time.sleep(2) # attempt to resolve the device not properly starting up and getting hung up

# set up i2c mux
print("Registering Sensors.....")
try:
    I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(I2CMux_channel, I2CMux_addr, I2CMux_clock, I2CMux_data)
    time.sleep_ms(500)
    I2CMulti.selectPort(0)
except Exception as e:
    print("Failed to initialise I2C multiplexer", " : {}".format(e))
    time.sleep(1)
    machine.reset()

THsensors = []
AQsensors = []

THsensorsFP = 0 # First Port
THsensorsCt = 0 # Count
THsensorsLP = 0 # Last Port
AQsensorsFP = 0 # First Port
AQsensorsCt = 0 # Count
AQsensorsLP = 0 # Last Port

# scan the mux for devices
for Port in range(0, 8):  # Scan I2C devices on each port
    try:
        addr = I2CMulti.scan(Port)
        if len(addr):
            if 64 in addr:
                THsensors.append(I2C_CHT8305_SEN0546.I2C_CHT8305_SEN0546(I2CMux_channel, I2CMux_clock, I2CMux_data))
                print("Registered Temp Sensor on Port: ", Port)
                THsensorsCt += 1
                THsensorsLP = Port + 1
                AQsensors.append(Port)
            elif 83 in addr:
                AQsensors.append(ENS160.ENS160(I2CMux_channel, I2CMux_clock, I2CMux_data))
                print("Registered AQ Sensor on Port: ", Port)
                AQsensorsCt += 1
                AQsensorsLP = Port + 1
                THsensors.append(Port)
        else:
            THsensors.append(Port)
            AQsensors.append(Port)
            print("No Device Found on Port: ", Port)
    except Exception as e:
        print("Failed scanning sensor device on channel ", Port, " : {}".format(e))
        pass

THsensorsFP = THsensorsLP - THsensorsCt
AQsensorsFP = AQsensorsLP - AQsensorsCt

async def start_modbus_tcp_server(host_ip, host_port, max_connections, reg_definitions):
    global modbus_client
    modbus_client = ModbusTCP()
    if not modbus_client.get_bound_status():
        await modbus_client.bind(local_ip=host_ip, local_port=host_port, max_connections=max_connections)
        modbus_client.setup_registers(registers=reg_definitions)
    print('Serving as Modbus TCP client on {}:{}'.format(local_ip, tcp_port))
    await modbus_client.serve_forever()

async def poll_temp_sensors():
    global modbus_client
    while True:
        try:
            await asyncio.sleep(1)
            for i in range(THsensorsFP, THsensorsLP):
                try:
                    I2CMulti.selectPort(i)
                    THsensors[i].req_CHT8305_TEMPERATURE_HUMIDITY()
                except Exception as e:
                    print("Failed requesting from Temp Sensor on Port ", i, " : {}".format(e))
                    pass
            await asyncio.sleep_ms(200)    
            for i in range(THsensorsFP, THsensorsLP):
                try:
                    I2CMulti.selectPort(i)
                    Temperature, Humidity = THsensors[i].read_CHT8305_TEMPERATURE_HUMIDITY()
                    modbus_client.set_hreg(address=10 + (i * 2), value=int(Temperature * 10))
                    modbus_client.set_hreg(address=11 + (i * 2), value=int(Humidity * 10))
                    print(f"#{i}  Temp: {Temperature:.1f}°C   Humi: {Humidity:.1f}%")
                except Exception as e:
                    print("Failed reading from Temp Sensor on Port ", i, " : {}".format(e))
                    try:
                        THsensors[i].send_CHT8305_SOFT_RESET()
                    except Exception as e:
                        pass
                    pass
            await asyncio.sleep(4)
        except Exception as e:
            print("Big Exception during execution of main loop: {}".format(e))
            bigExceptions += 1
            if bigExceptions > 9:
                time.sleep(2)
                machine.reset()
            pass

async def poll_aq_sensors():
    global modbus_client
    while True:
        try:
            await asyncio.sleep(4)
            for i in range(AQsensorsFP, AQsensorsLP):
                try:
                    I2CMulti.selectPort(i)
                    eco2, tvoc = AQsensors[i].get_air_quality()
                    AQsensor_regindex = i - AQsensorsFP
                    modbus_client.set_hreg(address=30 + (AQsensor_regindex * 2), value=int(eco2))
                    modbus_client.set_hreg(address=31 + (AQsensor_regindex * 2), value=int(tvoc))
                    print(f"#{i}  eC02: {eco2}ppm   TVOC: {tvoc}ppb")
                except Exception as e:
                    print("Failed reading from AQ Sensor on Port ", i, " : {}".format(e))
                    pass
            await asyncio.sleep(1)
        except Exception as e:
            print("Big Exception during execution of AQ Sensor loop: {}".format(e))
            pass
    
async def calibrate_aq_sensors():
    global modbus_client
    while True:
        try:
            await asyncio.sleep((15 * 60))
            #await asyncio.sleep((10))
            try:
                temp_celsius = (modbus_client.get_hreg(10) / 10)
                temp_value = int((temp_celsius + 273.15) * 64)
                temp_lsb = temp_value & 0xFF
                temp_msb = (temp_value >> 8) & 0xFF
                humidity = (modbus_client.get_hreg(11) / 10)
                humi_value = int((humidity * 512))
                humi_lsb = humi_value & 0xFF
                humi_msb = (humi_value >> 8) & 0xFF
            except Exception as e:
                print("Failed to read modbus registers for AQ calibration "," : {}".format(e))
                pass
            for i in range(AQsensorsFP, AQsensorsLP):
                try:
                    I2CMulti.selectPort(i)
                    AQsensors[i].calibrate_Temperature(temp_lsb, temp_msb)
                    AQsensors[i].calibrate_Humidity(humi_lsb, humi_msb)
                    print(f"Calibrated AQ Sensor #{i}: {temp_celsius:.1f}°C (0x{temp_value:04X}), {humidity:.1f}% (0x{humi_value:04X})")
                except Exception as e:
                    print("Failed calibrating AQ Sensor on channel", i, ": {}".format(e))
                    pass
        except Exception as e:
            print("Failed to calibrate AQ sensors: {}".format(e))
            pass

async def main_loop():
    tasks = []
    result = None
    tasks.append(asyncio.create_task(start_modbus_tcp_server(host_ip=local_ip, host_port=tcp_port, max_connections=10, reg_definitions=register_definitions)))
    await asyncio.sleep(2)
    tasks.append(asyncio.create_task(poll_temp_sensors()))
    if AQsensorsCt > 0:
        tasks.append(asyncio.create_task(poll_aq_sensors()))
        tasks.append(asyncio.create_task(calibrate_aq_sensors()))  
    try:
        print("Starting main loop.....")
        result = await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        print("ONGOING TASKS LOOP CANCELLED")
    print(f"result: {result}")

try:
    asyncio.run(main_loop())
except asyncio.CancelledError:
    print('MAIN LOOP CANCELLED')
    asyncio.new_event_loop() 
finally:
    asyncio.new_event_loop()

time.sleep(3)
machine.reset()