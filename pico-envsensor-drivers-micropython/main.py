import time
import machine
from machine import Pin, I2C, SoftI2C
import network
from umodbus.tcp import ModbusTCP
import DFRobot_I2C_Multiplexer
import I2C_CHT8305_SEN0546


I2CMultiAddr = 0x70  # I2C Multiplexer addr


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
    print("Network config: ")
    print(ip_address)
    print(network_mask)
    print(gateway_address)
    print(dns_server)
except OSError:  # open failed
    # handle the file open case
    print(
        "failed loading network config from network_address.txt file. Using default config"
    )

nic = network.WIZNET5K()
nic.active(True)
nic.ifconfig((ip_address, network_mask, gateway_address, dns_server))
nic.isconnected()


led = machine.Pin(25, machine.Pin.OUT)


def blink():
    led.high()
    time.sleep_ms(100)
    led.low()
    time.sleep_ms(100)


def my_reg_get_cb(reg_type, address, val):
    blink()


# network connections shall be made here, check the MicroPython port specific
# documentation for connecting to or creating a network

# TCP Client/Slave setup
# set IP address of this MicroPython device explicitly
# local_ip = '192.168.4.1'  # IP address
# or get it from the system after a connection to the network has been made
# it is not the task of this lib to provide a detailed explanation for this


local_ip = nic.ifconfig()[0]
tcp_port = 502  # port to listen for requests/providing data

print("Setting up Modbus")

client = ModbusTCP()

# check whether client has been bound to an IP and a port
if not client.get_bound_status():
    print("Binding client to ", local_ip, ":", tcp_port)
    client.bind(local_ip=local_ip, local_port=tcp_port)

register_definitions = {
    "HREGS": {
        "TEMPERATURE_1": {
            "register": 10,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_1": {
            "register": 11,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_2": {
            "register": 12,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_2": {
            "register": 13,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_3": {
            "register": 14,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_3": {
            "register": 15,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_4": {
            "register": 16,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_4": {
            "register": 17,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_5": {
            "register": 18,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_5": {
            "register": 19,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_6": {
            "register": 20,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_6": {
            "register": 21,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_7": {
            "register": 22,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_7": {
            "register": 23,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "TEMPERATURE_8": {
            "register": 24,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
        "HUMIDITY_8": {
            "register": 25,
            "len": 1,
            "val": 0,
            "on_get_cb": my_reg_get_cb,
        },
    }
}

channel = 1
clock_pin = 3
data_pin = 2

# use the defined values of each register type provided by register_definitions
client.setup_registers(registers=register_definitions)

print("Registering sensors")
I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(
    channel, I2CMultiAddr, clock_pin, data_pin
)
for Port in range(0, 8):  # Scan I2C devices on each port
    try:
        print("Port:%s" % Port)
        addr = I2CMulti.scan(Port)
        if len(addr):
            print("i2c addr:%s" % addr)
    except OSError as ex:
        print("Failed scanning sensor on channel ", Port, " : {}".format(ex))

sensors = []
for i in range(8):
    try:
        I2CMulti.selectPort(i)
        sensors.append(
            I2C_CHT8305_SEN0546.I2C_CHT8305_SEN0546(channel, clock_pin, data_pin)
        )
    except OSError as ex:
        print("Failed registering sensor on channel ", i, " : {}".format(ex))


print("Starting main loop")
lastReadTime = time.time()
while True:
    try:
        result = client.process()
        now = time.time()
        if (now - lastReadTime) > 2:
            for i in range(8):
                try:
                    I2CMulti.selectPort(i)
                    Temperature, Humidity = sensors[
                        i
                    ].get_CHT8305_TEMPERATURE_HUMIDITY()
                    client.set_hreg(address=10 + (i * 2), value=int(Temperature * 10))
                    client.set_hreg(address=11 + (i * 2), value=int(Humidity * 10))
                except Exception as e:
                    print("Failed reading sensor on channel ", i, " : {}".format(e))
                except OSError as ex:
                    print("Failed reading sensor on channel ", i, " : {}".format(ex))
            lastReadTime = now

        time.sleep_ms(100)

    except KeyboardInterrupt:
        print("KeyboardInterrupt, stopping TCP client...")
        break
    except Exception as e:
        print("Exception during execution: {}".format(e))
