import time
import machine
from machine import Pin, I2C, SoftI2C, SPI
import random
import network
from umodbus.tcp import ModbusTCP
import DFRobot_I2C_Multiplexer
import I2C_CHT8305_SEN0546
import ENS160

time.sleep(2)

I2CMultiAddr = 0x70  # I2C Multiplexer address

ip_address = "192.168.1.237"
network_mask = "255.255.255.0"
gateway_address = "192.168.1.1"
dns_server = "8.8.8.8"

try:
    f = open("network_address.txt", "r")
    ip_address = f.readline().rstrip("\r\n")
    network_mask = f.readline().rstrip("\r\n")
    gateway_address = f.readline().rstrip("\r\n")
    dns_server = f.readline().rstrip("\r\n")
    f.close()
except OSError:  # open failed
    # handle the file open case
    f.close()
    print(
        "failed loading network config from network_address.txt file. Using default config"
    )

print("PowerTec Enviro Sensor")
print("[I2C] v20250613-1047")
print("-----")
print("Network Config from File: (",ip_address,"-",network_mask,"-",gateway_address,"-",dns_server,")")
print("-----")

time.sleep(3)

connectingNIC = 0

# set up the Ethernet Hardware
try:
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
        if connectingNIC > 9:
            machine.reset()
        print("Getting IP.....")
    print('Device Network Address: ', nic.ifconfig())
except Exception as e:
    print("Exception during creation of NIC object: {}".format(e))

# set up the blinking LED
led = machine.Pin(25, machine.Pin.OUT)

# pico temp sensor pin
adcpin = 4
internal_sensor = machine.ADC(adcpin)

# start the beat
heartbeat = 0

def blink():
    led.high()
    time.sleep_ms(100)
    led.low()

def my_reg_get_cb(reg_type, address, val):
    blink()

def getPicoInternalTemp():
    try:
        adc_value = internal_sensor.read_u16()
        volt = (3.3/65535) * adc_value
        temperature = 27 - (volt - 0.706)/0.001721
        return int(round(temperature, 1) * 10)
    except Exception as e:
        print("Failed to get Pico internal temp", " : {}".format(e))
        pass

def resetIPviaModbus():
    Trigger = int(client.get_hreg(69))
    if Trigger == 1:
        setDiagRegister(57, 991)
        time.sleep(2)
        IP1 = int(client.get_hreg(61))
        IP2 = int(client.get_hreg(62))
        IP3 = int(client.get_hreg(63))
        IP4 = int(client.get_hreg(64))
        GW1 = int(client.get_hreg(65))
        GW2 = int(client.get_hreg(66))
        GW3 = int(client.get_hreg(67))
        GW4 = int(client.get_hreg(68))
        newIP = str(IP1) + "." + str(IP2) + "." + str(IP3) + "." + str(IP4)
        newGW = str(GW1) + "." + str(GW2) + "." + str(GW3) + "." + str(GW4)
        setDiagRegister(57, 992)
        time.sleep(2)
        f = open("network_address.txt", "r")
        ip_address = f.readline().rstrip("\r\n")
        network_mask = f.readline().rstrip("\r\n")
        gateway_address = f.readline().rstrip("\r\n")
        dns_server = f.readline().rstrip("\r\n")
        f.close()
        #print("read existing file")
        newNC = str(newIP) + "\n" + str(network_mask) + "\n" + str(newGW) + "\n" + str(dns_server) + "\n"
        try:
            f = open("network_address.txt", "w")
            f.write(newNC)
            f.close()
            setDiagRegister(57, 995)
            time.sleep(2)
        except OSError:
                print("Error: couldn't write a thing - device could be bricked now")
                setDiagRegister(57, 996)
                time.sleep(5)
        print("Network Config Updated from Modbus")
        setDiagRegister(57, 999)
        time.sleep(10)
        machine.reset()

def resetNoTemps():
    Reg11 = int(client.get_hreg(11))
    Reg12 = int(client.get_hreg(12))
    Reg13 = int(client.get_hreg(13))
    if (Reg11 + Reg12 + Reg13) == 0:
        client.set_hreg(address=10, value=int(666))   # register blank after ten minutes? that's a reset
        time.sleep(5)
        machine.reset()

def setHeartbeatRegister(heartbeat):
    try:
        heartbeat = heartbeat + random.randint(1,9)
        client.set_hreg(address=52, value=int(heartbeat))
        client.process()
        if heartbeat > 50:
            heartbeat = 0
        blink()
        return heartbeat
    except Exception as e:
        print("Failed to update Heartbeat Register", " : {}".format(e))
        pass

def setDiagRegister(diagnostic_reg, status_code):
    try:
        client.set_hreg(address=int(diagnostic_reg), value=int(status_code))
        client.process()
    except Exception as e:
        print("Failed to update Diagnostic Register", " : {}".format(e))
        pass

local_ip = nic.ifconfig()[0]
tcp_port = 502  # port to listen for requests/providing data

print("Setting up Modbus.....")

time.sleep(1)

client = ModbusTCP()

# check whether client has been bound to an IP and a port
if not client.get_bound_status():
    print("Binding client to ", local_ip, ":", tcp_port)
    try:
        client.bind(local_ip=local_ip, local_port=tcp_port)
    except OSError as e:
        print("Error in Modbus binding. System will restart.")
        time.sleep(1)
        machine.reset()

time.sleep(1)

register_definitions = {
    "HREGS": {
        ## Temp Sensor Values
        "TEMPERATURE_1": {"register": 10, "len": 1, "val": 0, "on_get_cb": my_reg_get_cb,},
        "HUMIDITY_1": { "register": 11, "len": 1, "val": 0,},
        "TEMPERATURE_2": { "register": 12, "len": 1, "val": 0,},
        "HUMIDITY_2": { "register": 13, "len": 1, "val": 0,},
        "TEMPERATURE_3": { "register": 14, "len": 1, "val": 0,},
        "HUMIDITY_3": { "register": 15, "len": 1, "val": 0,},
        "TEMPERATURE_4": { "register": 16, "len": 1, "val": 0,},
        "HUMIDITY_4": { "register": 17, "len": 1, "val": 0,},
        "TEMPERATURE_5": { "register": 18, "len": 1, "val": 0,},
        "HUMIDITY_5": { "register": 19, "len": 1, "val": 0,},
        "TEMPERATURE_6": { "register": 20, "len": 1, "val": 0,},
        "HUMIDITY_6": { "register": 21, "len": 1, "val": 0,},
        "TEMPERATURE_7": { "register": 22, "len": 1, "val": 0,},
        "HUMIDITY_7": { "register": 23, "len": 1, "val": 0,},
        "TEMPERATURE_8": { "register": 24, "len": 1, "val": 0,},
        "HUMIDITY_8": { "register": 25, "len": 1, "val": 0,},
        ## Air Quality Sensor Values
        "AVERAGE_AQI": { "register": 29, "len": 1, "val": 0,},
        "AQS1_ECO2": { "register": 30, "len": 1, "val": 0,},
        "AQS1_TVOC": { "register": 31, "len": 1, "val": 0,},
        "AQS2_ECO2": { "register": 32, "len": 1, "val": 0,},
        "AQS2_TVOC": { "register": 33, "len": 1, "val": 0,},
        "AQS3_ECO2": { "register": 34, "len": 1, "val": 0,},
        "AQS3_TVOC": { "register": 35, "len": 1, "val": 0,},
        "AQS4_ECO2": { "register": 36, "len": 1, "val": 0,},
        "AQS4_TVOC": { "register": 37, "len": 1, "val": 0,},
        "AQS5_ECO2": { "register": 38, "len": 1, "val": 0,},
        "AQS5_TVOC": { "register": 39, "len": 1, "val": 0,},
        "AQS6_ECO2": { "register": 40, "len": 1, "val": 0,},
        "AQS6_TVOC": { "register": 41, "len": 1, "val": 0,},
        "AQS7_ECO2": { "register": 42, "len": 1, "val": 0,},
        "AQS7_TVOC": { "register": 43, "len": 1, "val": 0,},
        "AQS8_ECO2": { "register": 44, "len": 1, "val": 0,},
        "AQS8_TVOC": { "register": 45, "len": 1, "val": 0,},
        ## Meta
        "HEARTBEAT": {"register": 52, "len": 1, "val": 0,},
        "TEMP_PICO": {"register": 53, "len": 1, "val": 0,},
        ## Diagnostics
        "SYS_STATUS": {"register": 54, "len": 1, "val": 91,},
        "SENSORS_ONLINE_TH": {"register": 55, "len": 1, "val": 0,},
        "SENSORS_ONLINE_AQ": {"register": 56, "len": 1, "val": 0,},
        "IP_RESET_STATUS": {"register": 57, "len": 1, "val": 0,},
        "BIG_EXCEPTIONS": {"register": 58, "len": 1, "val": 0,},
        "TEMP_PROBE_RESETS": {"register": 59, "len": 1, "val": 0,},
        ## IP Address
        "IP1": {"register": 61, "len": 1, "val": 0, "range": "[0, 256]"},
        "IP2": {"register": 62, "len": 1, "val": 0, "range": "[0, 256]"},
        "IP3": {"register": 63, "len": 1, "val": 0, "range": "[0, 256]"},
        "IP4": {"register": 64, "len": 1, "val": 0, "range": "[0, 256]"},
        ## Default Gateway
        "GW1": {"register": 65, "len": 1, "val": 0, "range": "[0, 256]"},
        "GW2": {"register": 66, "len": 1, "val": 0, "range": "[0, 256]"},
        "GW3": {"register": 67, "len": 1, "val": 0, "range": "[0, 256]"},
        "GW4": {"register": 68, "len": 1, "val": 0, "range": "[0, 256]"},
        ## Reset Trigger
        "IP_TRIGGER": {"register": 69, "len": 1, "val": 0, "range": "[0, 10]"}
    }
}

# use the defined values of each register type provided by register_definitions
client.setup_registers(registers=register_definitions)

setDiagRegister(54, 92)

# define I2C pins
channel = 1
clock_pin = 3
data_pin = 2

print("Registering Sensors.....")

time.sleep(3) # attempt to resolve the device not properly starting up and getting hung up

setDiagRegister(54, 94)

try:
    I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(channel, I2CMultiAddr, clock_pin, data_pin)
    time.sleep_ms(500)
    I2CMulti.selectPort(0)
    setDiagRegister(54, 95)
except Exception as e:
    print("Failed to initialise I2C multiplexer", " : {}".format(e))
    time.sleep(2)
    machine.reset()

THsensors = []
AQsensors = []

THsensorsFP = 0 # First Port
THsensorsCt = 0 # Count
THsensorsLP = 0 # Last Port
AQsensorsFP = 0 # First Port
AQsensorsCt = 0 # Count
AQsensorsLP = 0 # Last Port

setDiagRegister(54, 96)

for Port in range(0, 8):  # Scan I2C devices on each port
    try:
        addr = I2CMulti.scan(Port)
        if len(addr):
            if 64 in addr:
                THsensors.append(I2C_CHT8305_SEN0546.I2C_CHT8305_SEN0546(channel, clock_pin, data_pin))
                print("Registered Temp Sensor on Port: ", Port)
                THsensorsCt += 1
                THsensorsLP = Port + 1
                AQsensors.append(Port)
                setDiagRegister(55, THsensorsCt)
            elif 83 in addr:
                AQsensors.append(ENS160.ENS160(channel, clock_pin, data_pin))
                print("Registered AQ Sensor on Port: ", Port)
                AQsensorsCt += 1
                AQsensorsLP = Port + 1
                THsensors.append(Port)
                setDiagRegister(56, AQsensorsCt)
        else:
            THsensors.append(Port)
            AQsensors.append(Port)
            print("No Device Found on Port: ", Port)
        setDiagRegister(54, 98)
    except Exception as e:
        print("Failed scanning sensor device on channel ", Port, " : {}".format(e))
        pass

THsensorsFP = THsensorsLP - THsensorsCt
#print("TH First: ", THsensorsFP, " - TH Ct: ", THsensorsCt, " - TH Last: ", THsensorsLP -1)
AQsensorsFP = AQsensorsLP - AQsensorsCt
#print("AQ First: ", AQsensorsFP, " - AQ Ct: ", AQsensorsCt, " - AQ Last: ", AQsensorsLP -1)

print("Starting Main Loop.....")
setDiagRegister(54, 99)
lastReadTime = time.time()
calibrateTime = time.time()
resetTime = time.time()
bigExceptions = 0
softSensorResets = 0
AQI_rating = 1

while True:
    try:
        now = time.time()
        if (now - lastReadTime) > 3:
            for i in range(THsensorsFP, THsensorsLP):
                try:
                    I2CMulti.selectPort(i)
                    Temperature, Humidity = THsensors[i].get_CHT8305_TEMPERATURE_HUMIDITY()
                    client.set_hreg(address=10 + (i * 2), value=int(Temperature * 10))
                    client.set_hreg(address=11 + (i * 2), value=int(Humidity * 10))
                    print("Port: ", i, "Temp: ", Temperature, "Humi: ", Humidity)
                except Exception as e:
                    print("Failed reading Temp Sensor on Port ", i, " : {}".format(e))
                    try:
                        THsensors[i].send_CHT8305_SOFT_RESET()
                        print("Sending soft reset to Temp Sensor on Port: ", i)
                    except Exception as e:
                        print("Failed failed to soft reset Temp Sensor on Port ", i, " : {}".format(e))
                        pass
                    client.set_hreg(address=10 + (i * 2), value=int(0))
                    client.set_hreg(address=11 + (i * 2), value=int(0))
                    softSensorResets += 1
                    setDiagRegister(59, softSensorResets)
                    pass
            lastReadTime = now
            if AQsensorsCt != 0:
                for i in range(AQsensorsFP, AQsensorsLP):
                    try:
                        I2CMulti.selectPort(i)
                        aqi, tvoc, eco2, temp, rh, eco2_rating, tvoc_rating = AQsensors[i].read_air_quality()
                        #print(f"AQI: {aqi}")
                        #print(f"TVOC: {tvoc} ppb")
                        #print(f"TVOC Rating: {tvoc_rating}")
                        #print(f"eCO2: {eco2} ppm")
                        #print(f"Temperature (ENS160): {temp} °F")
                        #print(f"Humidity (ENS160): {rh} %")
                        #print(f"eCO2 Rating: {eco2_rating}")
                        AQsensor_regindex = i - AQsensorsFP
                        client.set_hreg(address=30 + (AQsensor_regindex * 2), value=int(eco2))
                        client.set_hreg(address=31 + (AQsensor_regindex * 2), value=int(tvoc))
                        print("Port: ", i, "eCO2: ", eco2, "TVOC: ", tvoc, "AQI: ", aqi)
                        AQI_rating += int(aqi)
                    except Exception as e:
                        print("Failed reading AQ Sensor on Port ", i, " : {}".format(e))
                        client.set_hreg(address=30 + (AQsensor_regindex * 2), value=int(0))
                        client.set_hreg(address=31 + (AQsensor_regindex * 2), value=int(0))
                        pass
                # calculate average of all AQI index ratings
                try:
                    AQI_rating = AQI_rating / AQsensorsCt
                    setDiagRegister(29, AQI_rating)
                    AQI_rating = 1
                except Exception as e:
                    print("Failed to push average AQI Index rating to register 29 ", " : {}".format(e))
                    pass
            
            # get Pico internal temp
            client.set_hreg(address=53, value=(getPicoInternalTemp()))
            
            #result = client.process()                      # disabled here to stop double processing in a loop - it's now only processed on heartbeat update or diag reg update
            
            # Heartbeat
            client.set_hreg(address=54, value=100)          # confirm we're in the main loop
            heartbeat = setHeartbeatRegister(heartbeat)     # Update Heartbeat & process client
        
        # calibrate AQ sensors to temperature every 15 mins
        if (now - calibrateTime) > 900:
            calibrateTime = now
            if AQsensorsCt != 0:
                try:
                    Temperature = int(client.get_hreg(10) / 10)
                    #print("Calibrating Temperature with: ", Temperature)
                    Humidity = int(client.get_hreg(11) / 10)
                    #print("Calibrating Humidity with: ", Humidity)
                except Exception as e:
                    print("Failed to read modbus registers for AQ calibration "," : {}".format(e))
                    pass
                for i in range(AQsensorsFP, AQsensorsLP):
                    try:
                        I2CMulti.selectPort(i)
                        AQsensors[i].calibrate_Temperature(Temperature)
                        AQsensors[i].calibrate_Humidity(Humidity)
                    except Exception as e:
                        print("Failed calibrating AQ Sensor on channel ", i, " : {}".format(e))
                        pass
        # check for IP address reset trigger every 10 mins
        if (now - resetTime) > 600:
            resetTime = now
            resetIPviaModbus()

        # take a breath before starting the loop again    
        time.sleep_ms(500)
    except KeyboardInterrupt:
        print("KeyboardInterrupt, stopping TCP client...")
        break
    except Exception as e:
        print("Big Exception during execution of main loop: {}".format(e))
        bigExceptions += 1
        setDiagRegister(54, 111)
        setDiagRegister(58, bigExceptions)
        time.sleep(2)
        if bigExceptions > 9:
            setDiagRegister(54, 112)
            time.sleep(2)
            machine.reset()
        pass

setDiagRegister(54, 119)
time.sleep(3)
machine.reset()
