import network
import mip

nic = network.WIZNET5K()
nic.active(True)
nic.ifconfig("dhcp")
nic.isconnected()
mip.install("github:brainelectronics/micropython-modbus")
