# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224
# 
# Python Driver for:
# DFRobot DFR0645-R DFR0645-G <https://wiki.dfrobot.com/4-Digital%20LED%20Segment%20Display%20Module%20%20SKU:%20DFR0645-G_DFR0645-R>
# NOTE: THIS IS NOT AN I2C DEVICE 
#
# Shout out to CarlWilliamsBristol <https://github.com/CarlWilliamsBristol/pxt-tm1650display>

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

characterBytes = [
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F,
    0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 0x06, 0x0E,
    0x38, 0x54, 0x74, 0x73, 0x67, 0x50, 0x78, 0x1C, 0x40, 0x63,
    0x00
]
digitAddress = [0x68, 0x6A, 0x6C, 0x6E]
 
class dfDisp:
    def __init__(self, ID, clock=1, data=0):
        self.displayDigitsRaw = [0, 0, 0, 0]
        self.pulse_width = (120 / 10000000)
        self.half_pulse_width = (60 / 10000000)
        self.reconfigure(clock, data)

    def set_speed(self, baud=8333):
        clock_length = 120
        clock_length = 1000000 / baud
        if clock_length >= 4:
            self.pulse_width = int(clock_length / 2)
            self.half_pulse_width = int(clock_length / 4)
        else:
            self.pulse_width = 2
            self.half_pulse_width = 1

    def reconfigure(self, clock=1, data=0):
        self.clock_pin = clock
        self.data_pin = data
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.output(self.clock_pin, 0)
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.output(self.data_pin, 0)
        # GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.output(self.data_pin, 0)
        self.go_idle()

    def display_on(self, brightness=0):
        self.go_idle()
        brightness &= 7
        brightness <<= 4
        brightness |= 1
        self.send_pair(0x48, brightness)

    def display_off(self):
        self.send_pair(0x48, 0)

    def display_clear(self):
        for i in range(4):
            self.send_pair(digitAddress[i], 0)
            self.displayDigitsRaw[i] = 0

    def show_segments(self, pos=0, pattern=0):
        pos &= 3
        self.displayDigitsRaw[pos] = pattern
        self.send_pair(digitAddress[pos], self.displayDigitsRaw[pos])

    def show_char(self, pos=0, c=0):
        char_index = 30
        pos &= 3
        char_index = self.char_to_index(c)
        if c == 0x2E:
            self.displayDigitsRaw[pos] |= 128
        else:
            self.displayDigitsRaw[pos] = characterBytes[char_index]
        #print(digitAddress[pos])
        #print(self.displayDigitsRaw[pos])
        self.send_pair(digitAddress[pos], self.displayDigitsRaw[pos])

    def show_char_with_point(self, pos=0, c=0):
        char_index2 = 30
        pos &= 3
        char_index2 = self.char_to_index(c)
        self.displayDigitsRaw[pos] = characterBytes[char_index2] | 128
        self.send_pair(digitAddress[pos], self.displayDigitsRaw[pos])

    def show_string(self, s):
        outc = [0, 0, 0, 0]
        dp = [0, 0, 0, 0]
        c = 0
        index = 0
        di = 0

        # Ensure the string does not exceed the length of the display
        if len(s) > 5: # if you change this (and line below) to '5', you can send a 5 digit string if 1 digit is a decimal point - i.e. "21.5c"
            s = s[:5]  # Truncate the string if it's too long
        if len(s) < 4:
            s = " " + s

        for index in range(len(s)):
            c = ord(s[index])
            if c == 0x2E:
                if di == 0:
                    outc[di] = 32
                    dp[di] = 1
                    di += 1
                else:
                    if dp[di - 1] == 0:
                        dp[di - 1] = 1
                    else:
                        dp[di] = 1
                        di += 1
                        outc[di] = 32
            else:
                outc[di] = c
                di += 1
        for index in range(di):
            c = outc[index]
            if dp[index] == 0:
                self.show_char(index, c)
            else:
                self.show_char_with_point(index, c)

    def show_integer(self, n= int(0)):
        outc2 = [32, 32, 32, 32]
        i = 3
        absn = 0

        if (n > 9999) or (n < -999):
            self.show_string("Err ")
        else:
            absn = abs(n)
            if absn == 0:
                outc2[3] = 0x30
            else:
                while absn != 0:
                    outc2[i] = (absn % 10) + 0x30
                    absn = absn // 10
                    i -= 1
                if n < 0:
                    outc2[i] = 0x2D
            for i in range(4):
                # print(outc2[i])
                self.show_char(i, outc2[i])

    def show_hex(self, n=0):
        j = 3

        if (n > 0xFFFF) or (n < -32768):
            self.show_string("Err ")
        else:
            for j in range(3):
                self.displayDigitsRaw[j] = 0
            self.displayDigitsRaw[3] = characterBytes[0]
            if n < 0:
                n = 0x10000 + n
            for j in range(3, -1, -1):
                self.displayDigitsRaw[j] = characterBytes[n & 15]
                n >>= 4
            for j in range(4):
                self.send_pair(digitAddress[j], self.displayDigitsRaw[j])

    def show_decimal(self, n=0):
        s = ""
        target_len = 4

        if (n > 9999) or (abs(n) < 0.001) or (n < -999):
            self.show_string("Err ")
        else:
            s = str(n)
            if "." in s:
                target_len = 4 - (len(s) - s.index("."))
                if target_len > 4:
                    target_len = 4
                if target_len < 0:
                    target_len = 0
            else:
                s += "."
            for _ in range(target_len):
                s += "0"
            self.show_string(s)

    def go_idle(self):
        GPIO.output(self.clock_pin, 1)
        time.sleep(self.pulse_width)
        GPIO.output(self.data_pin, 1)
        time.sleep(self.pulse_width)
    
    def send_Start(self):
        GPIO.output(self.clock_pin, 1)
        time.sleep(self.pulse_width)
        GPIO.output(self.data_pin, 1)
        time.sleep(self.pulse_width)
        GPIO.output(self.data_pin, 0)
        time.sleep(self.pulse_width)
        GPIO.output(self.clock_pin, 0)

    def send_pair(self, d=0, v=0):
        self.send_Start()
        #print("d", d)
        self.send_byte(d)
        #print("v", v)
        self.send_byte(v)
        self.go_idle()

    def send_byte(self, data=0):
        bitMask = 128
        while bitMask != 0:
        # for _ in range(8):
        #   v = data & 1
        #   data >>= 1
        #   b <<= 1
        #   b |= v
        #   time.sleep(5)
            time.sleep(self.half_pulse_width)
            if (data & bitMask) == 0:
                GPIO.output(self.data_pin, 0)
            else:
                GPIO.output(self.data_pin, 1)
            time.sleep(self.half_pulse_width)
            GPIO.output(self.clock_pin, 1)
            time.sleep(self.pulse_width)
            GPIO.output(self.clock_pin, 0)
            bitMask >>= 1

        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(self.pulse_width)
        GPIO.output(self.clock_pin, 1)
        time.sleep(self.pulse_width)
        ackBit = GPIO.input(self.data_pin)
        GPIO.output(self.clock_pin, 0)
        GPIO.setup(self.data_pin, GPIO.OUT)
        GPIO.output(self.data_pin, 0)
        time.sleep(self.half_pulse_width)

    def char_to_index(self, c):
        char_code = 30
        if c < 30:
            char_code = c
        else:
            if 0x2F < c < 0x3A:
                char_code = c - 0x30
            else:
                if c > 0x40:
                    c &= 0xDF  # Uppercase
                if 0x40 < c < 0x4B:
                    char_code = c - 0x37
                else:
                    if c == 0x4C:
                        char_code = 20
                    if 0x4E <= c <= 0x52:
                        char_code = 21 + (c - 0x4E)
                    if c == 0x54:
                        char_code = 26
                    if c == 0x55:
                        char_code = 27
                    if c == 0x2D:
                        char_code = 28
                    if c == 0x2A:
                        char_code = 29
        return char_code
