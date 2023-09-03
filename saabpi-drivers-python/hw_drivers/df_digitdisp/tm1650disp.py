# The MIT License (MIT)
# 
# Python Driver for:
# DFRobot DFR0645-R DFR0645-G <https://wiki.dfrobot.com/4-Digital%20LED%20Segment%20Display%20Module%20%20SKU:%20DFR0645-G_DFR0645-R>
# 
# Credit to stonatm <https://github.com/stonatm/tm1650_micropython>
# Credit to CarlWilliamsBristol <https://github.com/CarlWilliamsBristol/pxt-tm1650display>

import time
import math
import RPi.GPIO as GPIO

characterBytes = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 0x06, 0x0E, 0x38, 0x54, 0x74, 0x73, 0x67, 0x50, 0x78, 0x1C, 0x40, 0x63, 0x00]
digitAddress = [0x68, 0x6A, 0x6C, 0x6E]
pulseWidth = 120
halfPulseWidth = 60

class tm1650Display(object):
    displayDigitsRaw = [0, 0, 0, 0]
    def __init__(self, clockPin, dataPin):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(clockPin, GPIO.OUT)
        self._clockPin = clockPin
        GPIO.setup(dataPin, GPIO.OUT)
        self._dataPin = dataPin
        time.sleep(5)
 
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
            self.sendPair(self.digitAddress[i], 0)
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
        charIndex2 = self.charToIndex(c)
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
        for index in range(0, di, 1):
            c = outc[index]
            if (dp[index] == 0):
                self.showChar(index, c)
            else:
                self.showCharWithPoint(index, c)

    def showInteger(self, n):
        outc2 = [32, 32, 32, 32]
        i = 3
        absn = 0

        if (n > 9999) or (n < -999):
            self.showString("Err")
        else:
            absn = math.abs(n)
            if absn == 0:
                outc2[3] = 0x30
            else:
                while absn != 0:
                    outc2[i] = absn % 10 + 0x30
                    absn = math.floor(absn / 10)
                    i -= 1
                if n < 0:
                    outc2[i] = 0x2D
            for i in range(0, 4, 1):
                self.showChar(i, outc2[i])
    
    def showHex(self, n):
        j = 3
        if (n > 0xFFF) or (n < -32768):
            self.showString("Err")
        else:
            for j in range(0, 3, 1):
                self.displayDigitsRaw[j] = 0
            self.displayDigitsRaw[3] = characterBytes[0]
            if (n < 0):
                n = 0x10000 + n
            for j in range(3, 0, -1):
                self.displayDigitsRaw[j] = characterBytes[n & 15]
                n >>= 4
            for j in range(0, 4, 1):
                self.sendPair(self.digitAddress[j], self.displayDigitsRaw[j])
    
    def showDecimal(self, n):
        s = ""
        targetlen = 4
        if (n > 9999) or (math.abs(n) < 0.001) or (n < -999):
            self.showString("Err")
        else:
            s = n.toString()
            if (s.includes(".")):
                targetlen = 5
            while s.length < targetlen:
                s = " " + s
            self.showString(s)
    
    def toggleDP(self, pos):
        self.displayDigitsRaw[pos] ^= 128
        self.sendPair(self.digitAddress[pos], self.displayDigitsRaw[pos])

    def digitRaw(self, pos):
        return self.displayDigitsRaw[pos & 3]
    
    def digitChar(self, pos):
        raw = self.displayDigitsRaw[pos & 3]
        c = 0
        found = 0
        i = 0
        if (raw == 0):
            c = 32
        while (i < 30) and (found == 0):
            if (characterBytes[i] == raw):
                    found = 1
                    if (i < 10):
                        c = 0x30 + i
                    else:
                        if (i < 20):
                            c = 55 + i
                        else:
                            c = 77
                            if (i > 20):
                                c = c + (i - 19)
                                if (i > 25):
                                    c = c + 1
                                    if (i == 28):
                                        c = 0x2d
                                    elif (i == 29):
                                        c = 0x2a
                                    elif (i == 128):
                                        c = 0x2e
            else:
                i += 1
        return c

    #######################
    #
    # from the original code, the following appear to set values as hard coded, not sure why
    # 
    #   private clockPin: DigitalPin = DigitalPin.P1
    #   private dataPin: DigitalPin = DigitalPin.P0
    # 
    # I'VE MOVED THE FOLLOWING TWO TO THE TOP
    #
    #   private pulseWidth: number = 120
    #   private halfPulseWidth: number = 60
    #
    ########################

    def charToIndex(self, c):
        charCode = 30
        if (c < 30):
            charCode = c
        else:
            if (c > 0x2F) and (c < 0x3A):
                charCode = c - 0x30
            else:
                if (c > 0x40):
                    c &= 0xDF # uppercase
                elif (c > 0x40) and (c < 0x4B):
                    charCode = c - 0x37
                else:
                    if (c == 0x4C):
                        charCode = 20
                    elif (c > 0x4E) and (c <= 0x52):
                        charCode = 21 + (c - 0x4E)
                    elif (c == 0x54):
                        charCode = 26
                    elif (c == 0x55):
                        charCode = 27
                    elif (c == 0x2D):
                        charCode = 28
                    elif (c == 0x2A):
                        charCode = 29
        return charCode

    def sendPair(self, byte1, byte2):
        self.sendStart()
        self.sendByte(byte1)
        self.sendByte(byte2)
        self.goIdle()

    def sendStart(self):
        GPIO.output(self._dataPin, 0)
        time.sleep((pulseWidth / 1000000)) #adjust from microseconds back to seconds
        GPIO.output(self._clockPin, 0)

    def goIdle(self):
        GPIO.output(self._clockPin, 1)
        time.sleep((pulseWidth / 1000000)) #adjust from microseconds back to seconds
        GPIO.output(self._dataPin, 1)
        time.sleep((pulseWidth / 1000000))

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
            time.sleep((halfPulseWidth / 1000000))
            if ((byte & bitMask) == 0):
                GPIO.output(self._dataPin, 0)
            else:
                GPIO.output(self._dataPin, 1)
            time.sleep((halfPulseWidth / 1000000))
            GPIO.output(self._clockPin, 1)
            time.sleep((pulseWidth / 1000000))
            GPIO.output(self._clockPin, 0)
            print(bitMask)
            bitMask >>= 1
        
        # Clock is now low and we want the ACK bit so this time read SDA
        ackBit = GPIO.input(self._dataPin)              # Put Data Pin in Read Mode
        time.sleep((pulseWidth / 1000000))
        # Wait one more clock
        GPIO.output(self._clockPin, 1)
        time.sleep((pulseWidth / 1000000))
        ackBit = GPIO.input(self._dataPin)              # Read the actual ACK bit from display
        print(ackBit)
        GPIO.output(self._clockPin, 0)
        # Display takes about half a pulse width to release SDA
        # GPIO.setup(self._dataPin, pull_up_down=GPIO.PUD_UP)
        while (0 == ackBit):
            ackBit = GPIO.input(self._dataPin)
        GPIO.output(self._dataPin, 0)
        time.sleep((halfPulseWidth / 1000000))
        # end of function, maybe it works?

        ###################################
        #
        # not sure what the below 4 lines do
        #
        ###################################

        instanceNames = []
        instaceCount = 0
        # instances = tm1650Display.__class__[]
        currentInstanceIndex = 0


        

