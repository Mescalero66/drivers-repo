#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#
# compatibility for ports which do not have inet_ntop available
# from https://github.com/micropython/micropython/issues/8877#issuecomment-1178674681

try:
    from socket import inet_ntop
except ImportError:
    import socket

    def inet_ntop(type: int, packed_ip: bytes) -> str:
        if type == socket.AF_INET:
            return ".".join(map(str, packed_ip))
        elif type == socket.AF_INET6:
            iterator = zip(*[iter(packed_ip)] * 2)
            ipv6_addr = []
            for high, low in iterator:
                ipv6_addr.append(f"{high << 8 | low:04x}")

            return ":".join(ipv6_addr)
        raise ValueError("Invalid address type")
