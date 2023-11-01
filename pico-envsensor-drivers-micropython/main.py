import time
import machine
from machine import Pin, I2C, SoftI2C
import network
from umodbus.tcp import ModbusTCP
from ahtx0 import *
from mlx90614 import *
import DFRobot_I2C_Multiplexer
import I2C_CHT8305_SEN0546


I2CMultiAddr = 0x70  # I2C Multiplexer addr

I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(0, I2CMultiAddr, 9, 8)
for Port in range(0, 8):  # Scan I2C devices on each port
    print("Port:%s" % Port)
    addr = I2CMulti.scan(Port)
    if len(addr):
        print("i2c addr:%s" % addr)


nic = network.WIZNET5K()
nic.active(True)
nic.ifconfig("dhcp")
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
    }
}

# use the defined values of each register type provided by register_definitions
client.setup_registers(registers=register_definitions)

sensors = []
for i in range(4):
    I2CMulti.selectPort(i)
    sensors.append(I2C_CHT8305_SEN0546.I2C_CHT8305_SEN0546(0, 9, 8))


lastReadTime = time.time()
while True:
    try:
        result = client.process()
        now = time.time()
        if (now - lastReadTime) > 2:
            for i in range(4):
                I2CMulti.selectPort(i)
                Temperature, Humidity = sensors[i].get_CHT8305_TEMPERATURE_HUMIDITY()
                client.set_hreg(address=10 + (i * 2), value=int(Temperature * 10))
                client.set_hreg(address=11 + (i * 2), value=int(Humidity * 10))
            lastReadTime = now

        time.sleep_ms(100)

    except KeyboardInterrupt:
        print("KeyboardInterrupt, stopping TCP client...")
        break
    except Exception as e:
        print("Exception during execution: {}".format(e))
