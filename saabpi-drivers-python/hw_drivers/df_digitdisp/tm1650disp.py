# The MIT License (MIT)
# 
# Python Driver for:
# DFRobot DFR0645-R DFR0645-G <https://wiki.dfrobot.com/4-Digital%20LED%20Segment%20Display%20Module%20%20SKU:%20DFR0645-G_DFR0645-R>
# 
# Credit to stonatm <https://github.com/stonatm/tm1650_micropython>
# Credit to CarlWilliamsBristol <https://github.com/CarlWilliamsBristol/pxt-tm1650display>

import time
import math
from RPi.GPIO import GPIO, SoftI2C

#
# const characterBytes: number[] = [
#       0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F,  /* 0 - 9 */
#        0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 0x06, 0x0E,  /* A - J */
#        0x38, 0x54, 0x74, 0x73, 0x67, 0x50, 0x78, 0x1C, 0x40, 0x63,  /* LnoPQrtu-* (degree) */
#        0x00]
#    const digitAddress: number[] = [0x68, 0x6A, 0x6C, 0x6E]

class tm1650Display(object):
    def __init__(self, clockPin, dataPin):
        self._clockPin = GPIO(clockPin, direction=GPIO.OUT)
        self._dataPin = GPIO(dataPin, direction=GPIO.OUT)
    
    digitAddress = ["0x68", "0x6A", "0x6C", "0x6E"]

    displayDigitsRaw = [0, 0, 0, 0]

    def setSpeed(self, baud):
        clockLength = 120
        clockLength = 1000000 / baud
        if(clockLength >= 4):
            self.pulseWidth = math.floor(clockLength / 2)
            self.halfPulseWidth = math.floor(clockLength /4)
        else:
            self.pulseWidth = 2
            self.halfPulseWidth = 1

    def displayOn(self, brightness):
        self.goIdle()
        brightness &= 7
        brightness <<= 4
        brightness |= 1
        self.sendPair(0x48, brightness)

    def displayOff(self):
        self.sendPair(0x48, 0)

    def displayClear(self):
        for i in range(0, 4, 1):
            self.sendPair(self.digitAddress(i), 0)
            self.displayDigitsRaw[i] = 0
    
    def showSegments(self, pos, pattern):
        pos &= 3
        self.displayDigitsRaw[pos] = pattern
        self.sendPair(self.digitAddress[pos], self.displayDigitsRaw[pos])
    
    def showChar(self, pos, c):
        charIndex = 30
        pos &= 3
        charIndex = self.CharToIndex(c)
        if (c == 0x2E):
            self.displayDigitsRaw[pos] |= 128
        else:
            self.displayDigitsRaw[pos] = characterBytes[charIndex]
        self.sendPair(self.digitAddress[pos], self.displayDigitsRaw[pos])

    def showCharWithPoint(self, pos, c):
        charIndex2 = 30
        pos &= 3
        CharIndex2 = self.charToIndex(c)
        self.displayDigitsRaw[pos] = characterBytes[charIndex2] | 128
        self.sendPair(self.digitAddress[pos], self.displayDigitsRaw[pos])

    def showString(self, s):
        outc = []
        dp = [0, 0, 0, 0]
        c = 0
        index = 0
        di = 0
        
        for index in range(0, (s.len), 1):
            for di in range(0, 4, 1):
                c = s.charCodeAt(index)
                if (c == 0x2E):
                    if (di == 0):
                        outc[di] = 32
                        dp[di] = 1
                        di += 1
                    else:
                        if (dp[di - 1] == 0):
                            dp[di - 1] = 1
                        else:
                            dp[di] = 1
                            di += 1
                            outc[di] = 32
                else:
                    outc[di] = c
                    di += 1
        for index in range(0, di, 1);
            c = outc[index]
            if (dp[index] == 0):
                self.showChar(index, c)
            else:
                self.showCharWithPoint(index, c)
    
    ## you are up to
    #
    # def showInteger
    #
    # <https://github.com/CarlWilliamsBristol/pxt-tm1650display/blob/master/tm1650display.ts>
    #
    # it's 2:20am FFS
    







    def sendPair(self, byte1, byte2):
        self.sendStart()
        self.sendByte(byte1)
        self.sendByte(byte2)
        self.goIdle()

    def sendStart(self):
        GPIO.output(self._dataPin, 0)
        time.sleep((self.pulseWidth / 1000000)) #adjust from microseconds back to seconds
        GPIO.output(self._clockPin, 0)

    def goIdle(self):
        GPIO.output(self._clockPin, 1)
        time.sleep((self.pulseWidth / 1000000)) #adjust from microseconds back to seconds
        GPIO.output(self._dataPin, 0)
        time.sleep((self.pulseWidth / 1000000))

    #    
    # Function sendByte
    #       
    # The idle state has both clock (SCL) and data (SDA) HIGH.
    # In this function, SCL will start and end LOW, SDA unknown
    # Data are clocked out MSB first. 
    # 8 bits are clocked out, latched by the display on the falling edge of SCL. 
    # A final ninth clock is sent to allow the display to send an ACK bit.

    def sendByte(self, byte):
        bitMask = 128
        ackBit = 0
        while bitMask != 0:
            time.sleep((self.halfPulseWidth / 1000000))
            if ((byte & bitMask) == 0):
                GPIO.output(self._dataPin, 0)
            else:
                GPIO.output(self._dataPin, 1)
            time.sleep((self.halfPulseWidth / 1000000))
            GPIO.output(self._clockPin, 1)
            time.sleep((self.pulseWidth / 1000000))
            GPIO.output(self._clockPin, 0)
            bitMask >> 1
        
        # Clock is now low and we want the ACK bit so this time read SDA
        ackBit = GPIO.input(self._dataPin)              # Put Data Pin in Read Mode
        time.sleep((self.pulseWidth / 1000000))
        # Wait one more clock
        GPIO.output(self._clockPin, 1)
        time.sleep((self.pulseWidth / 1000000))
        ackBit = GPIO.input(self._dataPin)              # Read the actual ACK bit from display
        GPIO.output(self._clockPin, 0)
        # Display takes about half a pulse width to release SDA
        GPIO.setup(self._dataPin, pull_up_down=GPIO.PUD_UP)
        while (0 == ackBit):
            ackBit = GPIO.input(self._dataPin)
        GPIO.output(self._dataPin, 0)
        time.sleep((self.halfPulseWidth / 1000000))
        # end of function, maybe it works?

        

