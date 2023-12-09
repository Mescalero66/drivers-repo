# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.0 - Released 20231209
# 
# Python Driver for:
# Seeed Grove LED Bar 104030002 <https://www.seeedstudio.com/Grove-LED-Bar.html>
# 
# Credit to zolgear <https://github.com/zolgear/grove.py>


import time
from grove.gpio import GPIO

__all__ = ['GroveLedBar']

class GroveLedBar(object):
    '''
    Class for Grove - LED Bar

    Args:
        pin(int): number of digital pin the led bar connected.
        reverse: sets the led bar direction for level values. default False.
    '''
    def __init__(self, pin, reverse=False):
        self._dio = GPIO(pin, direction=GPIO.OUT)
        self._clk = GPIO(pin + 1, direction=GPIO.OUT)
        self._reverse = reverse
        self._clk_data = 0

    def __del__(self):
        self.level(0)
        self._dio.write(0)
        self._clk.write(0)

    @property
    def reverse(self):
        '''
        led bar direction for level values.
        '''
        return self._reverse
    
    @reverse.setter
    def reverse(self, value: bool):
        if type(value) is not bool:
            raise TypeError('reverse must be bool')
        self._reverse = value

    def level(self, value, brightness=255):
        '''
        select a level to light the led bar.
        value: number of level, 0 - 10.
        brightness:
            8-bit grayscale mode: 0 - 127 (128 - 255)
        '''
        # print('level:{0:2} ['.format(value), end='')
        self._begin()
        for i in range(9,-1,-1) if self._reverse else range(10):
            self._write16(brightness if value > i else 0)
            # print('{0}:{1:3}'.format(i, brightness if value > i else 0), end=', ')
        self._end()
        # print(']')

    def bits(self, val, brightness=255):
        val &= 0x3FF
        self._begin()
        for i in range(9,-1,-1) if self._reverse else range(10):
            self._write16(brightness if (val >> i) & 1 else 0)
        self._end()

    def bytes(self, buf):
        self._begin()
        for i in range(9,-1,-1) if self._reverse else range(10):
            self._write16(buf[i])
        self._end()

    def _begin(self):
        self._write16(0)    # 8-bit grayscale mode

    def _end(self):
        '''
        fill to 208-bit shift register
        '''
        self._write16(0)
        self._write16(0)
        self._latch()


    def _send_clock(self):
        self._clk_data = abs(self._clk_data - 1)
        self._clk.write(self._clk_data)

    def _write16(self, data):
        for i in range(15, -1, -1):
            self._dio.write((data >> i) & 1)
            self._send_clock()

    def _latch(self):
        '''
        Internal-latch control cycle
        '''
        self._dio.write(0)
        self._send_clock()  # keeping DCKI level
        time.sleep(.00022)  # Tstart: >220us

        for i in range(4):  # Send 4 DI pulses
            self._dio.write(1)
            time.sleep(.00000007)    # twH: >70ns
            self._dio.write(0)
            time.sleep(.00000023)    # twL: >230ns

        time.sleep(.0000002)    # Tstop: >200ns (not supported cascade)


Grove = GroveLedBar


def main():
    from grove.helper import SlotHelper
    sh = SlotHelper(SlotHelper.GPIO)
    pin = sh.argv2pin()

    ledbar = GroveLedBar(pin)

    while True:
        for i in range(0, 11):
            ledbar.level(i)
            time.sleep(.5)
        
        ledbar.reverse = not ledbar.reverse
        time.sleep(1)


if __name__ == '__main__':
    main()
   
