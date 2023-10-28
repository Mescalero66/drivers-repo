# MIT License
# Copyright (c) 2023 Mescalero
# <https://github.com/Mescalero66/saabpi>
# 
# Python Driver for:
# PiicoDev OLED SSD1306 Display
# <https://core-electronics.com.au/piicodev-oled-display-module-128x64-ssd1306.html>
#
# Shout outs to: 
# <https://github.com/CoreElectronics/CE-PiicoDev-PyPI/tree/main>
# <https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py>
# <https://github.com/fizban99/microbit_ssd1306/blob/master/ssd1306_text.py>
# <https://github.com/adafruit/Adafruit_Python_SSD1306/blob/master/Adafruit_SSD1306/SSD1306.py>

_SET_CONTRAST = 0x81
_SET_ENTIRE_ON = 0xA4
_SET_NORM_INV = 0xA6
_SET_DISP = 0xAE
_SET_MEM_ADDR = 0x20
_SET_COL_ADDR = 0x21
_SET_PAGE_ADDR = 0x22
_SET_DISP_START_LINE = 0x40
_SET_SEG_REMAP = 0xA0
_SET_MUX_RATIO = 0xA8
_SET_IREF_SELECT = 0xAD
_SET_COM_OUT_DIR = 0xC0
_SET_DISP_OFFSET = 0xD3
_SET_COM_PIN_CFG = 0xDA
_SET_DISP_CLK_DIV = 0xD5
_SET_PRECHARGE = 0xD9
_SET_VCOM_DESEL = 0xDB
_SET_CHARGE_PUMP = 0x8D
ID = 0
WIDTH = 128
HEIGHT = 64
i2c_err_str = 'Cannnot communicate with module at address 0x{:02X}, check wiring'
compat_ind = 1

from smbus2 import SMBus, i2c_msg
from math import cos,sin,radians
from struct import pack_into
from time import sleep

compat_str = '\nit is bwoken!\n'

class framebuf:
    class FrameBuffer():
            # Framebuffer manipulation, used by Microbit and Linux
        def _set_pos(self, col=0, page=0):
            self.write_cmd(0xb0 | page)  # page number
            # take upper and lower value of col * 2
            c1, c2 = col * 2 & 0x0F, col >> 3
            self.write_cmd(0x00 | c1)  # lower start column address
            self.write_cmd(0x10 | c2)  # upper start column address
            
        def fill(self, c=0):
            for i in range(0, 1024):
                if c > 0:
                    self.buffer[i] = 0xFF
                else:
                    self.buffer[i] = 0x00
                    
        def pixel(self, x, y, color):
            x = x & (WIDTH - 1)
            y = y & (HEIGHT - 1)
            page, shift_page = divmod(y, 8)
            ind = x + page * 128
            b = self.buffer[ind] | (1 << shift_page) if color else self.buffer[ind] & ~ (1 << shift_page)
            pack_into(">B", self.buffer, ind, b)
            self._set_pos(x, page)

        def line(self, x1, y1, x2, y2, c):
            # bresenham
            steep = abs(y2-y1) > abs(x2-x1)
            
            if steep:
                # Swap x/y
                tmp = x1
                x1 = y1
                y1 = tmp
                
                tmp = y2
                y2 = x2
                x2 = tmp
            
            if x1 > x2:
                # Swap start/end
                tmp = x1
                x1 = x2
                x2 = tmp
                tmp = y1
                y1 = y2
                y2 = tmp
            
            dx = x2 - x1;
            dy = abs(y2-y1)
            
            err = dx/2
            
            if(y1 < y2):
                ystep = 1
            else:
                ystep = -1
                
            while x1 <= x2:
                if steep:
                    self.pixel(y1, x1, c)
                else:
                    self.pixel(x1, y1, c)
                err -= dy
                if err < 0:
                    y1 += ystep
                    err += dx
                x1 += 1        
    
        def hline(self, x, y, l, c):
            self.line(x, y, x + l, y, c)
            
        def vline(self, x, y, h, c):
            self.line(x, y, x, y + h, c)
            
        def rect(self, x, y, w, h, c):
            self.hline(x, y, w, c)
            self.hline(x, y+h, w, c)
            self.vline(x, y, h, c)
            self.vline(x+w, y, h, c)
                    
        def fill_rect(self, x, y, w, h, c):
            for i in range(y, y + h):
                self.hline(x, i, w, c)
                
        def text(self, text, x, y, c=1):
            fontFile = open("/home/pi/saabpi/hw_drivers/pd_oleddisp/fonts/font-pet-me-128.dat", "rb")
            font = bytearray(fontFile.read())
            for text_index in range(0, len(text)):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,7):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coordinate = x + col + text_index * 8
                            y_coordinate = y+i
                            if x_coordinate < WIDTH and y_coordinate < HEIGHT:
                                self.pixel(x_coordinate, y_coordinate, c)

        def bigtext(self, text, x, y, c=1):
            fontFile = open("/home/pi/saabpi/hw_drivers/pd_oleddisp/fonts/font-pet-me-128.dat", "rb")
            font = bytearray(fontFile.read())
            for text_index in range(0, len(text)):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = x + (col*2) + (text_index * 14)
                            y_coordinate = y+(i*3)
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,3):
                                    self.pixel(x_coord, y_coordinate - iY, c)
                                    self.pixel(x_coord - 1, y_coordinate - iY, c)
                                    # the font size can't be changed, they said!
                                    # ha!
        
        def temptext(self, text, lbl, key=0, x=83, y=3, c=1):
            # key = 0 for TOP ROW, 1 for BOTTOM ROW
            if key == 0:
                self.text(lbl,0,0,1)
                self.text("c",120,22,1)
                y = 10
            else:
                self.text(lbl,0,33,1)
                self.text("c",120,55,1)
                y = 43      
            fontFile = open("/home/pi/saabpi/hw_drivers/pd_oleddisp/fonts/font-pet-me-128.dat", "rb")
            font = bytearray(fontFile.read())
            for text_index in range(0, len(text)-2):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = x + (col*2) + (text_index * 15)
                            y_coordinate = y+(i*3)
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,3):
                                    self.pixel(x_coord, y_coordinate - iY, c)
                                    self.pixel(x_coord - 1, y_coordinate - iY, c)
            for text_index in range(len(text)-2, len(text)):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = (x-3) + col + (text_index * 8) + ((len(text)-2) * 8)
                            y_coordinate = y+(i*2) - 1
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,2):
                                    self.pixel(x_coord, y_coordinate - iY, c)

        def temptext_altA(self, text, lbl, key=0, x=83, y=3, c=1):
            # key = 0 for TOP ROW, 1 for BOTTOM ROW
            if key == 0:
                self.text(lbl,0,0,1)
                self.text("c",120,16,1)
                y = 3
            else:
                self.text(lbl,0,33,1)
                self.text("c",120,49,1)
                y = 36      
            fontFile = open("/home/pi/saabpi/hw_drivers/pd_oleddisp/fonts/font-pet-me-128.dat", "rb")
            font = bytearray(fontFile.read())
            for text_index in range(0, len(text)-2):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = x + (col*2) + (text_index * 15)
                            y_coordinate = y+(i*3)
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,3):
                                    self.pixel(x_coord, y_coordinate - iY, c)
                                    self.pixel(x_coord - 1, y_coordinate - iY, c)
            for text_index in range(len(text)-2, len(text)):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = (x-3) + col + (text_index * 8) + ((len(text)-2) * 8)
                            y_coordinate = y+(i*2) - 1
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,2):
                                    self.pixel(x_coord, y_coordinate - iY, c)
        
        def temptext_altB(self, text, lbl, key=0, x=83, y=3, c=1):
            # key = 0 for TOP ROW, 1 for BOTTOM ROW
            if key == 0:
                self.text(lbl,(128-(len(lbl)*8)),0,1)
                self.text("c",120,22,1)
                y = 10
            else:
                self.text(lbl,(128-(len(lbl)*8)),33,1)
                self.text("c",120,55,1)
                y = 43      
            fontFile = open("/home/pi/saabpi/hw_drivers/pd_oleddisp/fonts/font-pet-me-128.dat", "rb")
            font = bytearray(fontFile.read())
            for text_index in range(0, len(text)-2):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = x + (col*2) + (text_index * 15)
                            y_coordinate = y+(i*3)
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,3):
                                    self.pixel(x_coord, y_coordinate - iY, c)
                                    self.pixel(x_coord - 1, y_coordinate - iY, c)
            for text_index in range(len(text)-2, len(text)):
                for col in range(8):
                    fontDataPixelValues = font[(ord(text[text_index])-32)*8 + col]
                    for i in range(0,8):
                        if fontDataPixelValues & 1 << i != 0:
                            x_coord = (x-3) + col + (text_index * 8) + ((len(text)-2) * 8)
                            y_coordinate = y+(i*2) - 1
                            if x_coord < WIDTH and y_coordinate < HEIGHT:
                                for iY in range(0,2):
                                    self.pixel(x_coord, y_coordinate - iY, c)
    
class pd_OLED(framebuf.FrameBuffer):
    def init_display(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.pages = HEIGHT // 8
        self.buffer = bytearray(self.pages * WIDTH)
        for cmd in (
            _SET_DISP,  # display off
            _SET_MEM_ADDR, # address setting
            0x00,  # horizontal
            # resolution and layout
            _SET_DISP_START_LINE,  # start at line 0
            _SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            _SET_MUX_RATIO,
            HEIGHT - 1,
            _SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            _SET_DISP_OFFSET,
            0x00,
            _SET_COM_PIN_CFG,
            0x12,
            # timing and driving scheme
            _SET_DISP_CLK_DIV,
            0x80,
            _SET_PRECHARGE,
            0xF1,
            _SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            _SET_CONTRAST,
            0xFF,# maximum
            _SET_ENTIRE_ON,  # output follows RAM contents
            _SET_NORM_INV,  # not inverted
            _SET_IREF_SELECT,
            0x30,  # enable internal IREF during display on
            # charge pump
            _SET_CHARGE_PUMP,
            0x14,
            _SET_DISP | 0x01,  # display on
        ):  # on
            self.write_cmd(cmd)

    def poweroff(self):
        self.write_cmd(_SET_DISP)

    def poweron(self):
        self.write_cmd(_SET_DISP | 0x01)

    def setContrast(self, contrast):
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(_SET_NORM_INV | (invert & 1))

    def rotate(self, rotate):
        self.write_cmd(_SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self.write_cmd(_SET_SEG_REMAP | (rotate & 1))

    def show(self):
        x0 = 0
        x1 = WIDTH - 1
        self.write_cmd(_SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(_SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)
        
    def write_cmd(self, cmd):
        try:
            self.i2c.writeto_mem(self.addr, int.from_bytes(b'\x80','big'), bytes([cmd]))
            self.comms_err = False
        except:
            print(i2c_err_str.format(self.addr))
            self.comms_err = True
            
    def write_data(self, buf):
        try:
            self.write_list[1] = buf
            self.i2c.writeto_mem(self.addr, int.from_bytes(self.write_list[0],'big'), self.write_list[1])
            self.comms_err = False
        except:
            print(i2c_err_str.format(self.addr))
            self.comms_err = True
            
    def circ(self,x,y,r,t=1,c=1):
        for i in range(x-r,x+r+1):
            for j in range(y-r,y+r+1):
                if t==1:
                    if((i-x)**2 + (j-y)**2 < r**2):
                        self.pixel(i,j,1)
                else:
                    if((i-x)**2 + (j-y)**2 < r**2) and ((i-x)**2 + (j-y)**2 >= (r-r*t-1)**2):
                        self.pixel(i,j,c)
                   
    def arc(self,x,y,r,stAng,enAng,t=0,c=1):
        for i in range(r*(1-t)-1,r):
            for ta in range(stAng,enAng,1):
                X = int(i*cos(radians(ta))+ x)
                Y = int(i*sin(radians(ta))+ y)
                self.pixel(X,Y,c)
            
    def load_pbm(self, filename, c):
        with open(filename, 'rb') as f:
            line = f.readline()
            if line.startswith(b'P4') is False:
                print('Not a valid pbm P4 file')
                return
            line = f.readline()
            while line.startswith(b'#') is True:
                line = f.readline()
            data_piicodev = bytearray(f.read())
        for byte in range(WIDTH // 8 * HEIGHT):
            for bit in range(8):
                if data_piicodev[byte] & 1 << bit != 0:
                    x_coordinate = ((8-bit) + (byte * 8)) % WIDTH
                    y_coordinate = byte * 8 // WIDTH
                    if x_coordinate < WIDTH and y_coordinate < HEIGHT:
                        self.pixel(x_coordinate, y_coordinate, c)
                        
    class graph2D:
        def __init__(self, originX = 0, originY = HEIGHT-1, width = WIDTH, height = HEIGHT, minValue=0, maxValue=255, c = 1, bars = False):
            self.minValue = minValue
            self.maxValue = maxValue
            self.originX = originX
            self.originY = originY
            self.width = width
            self.height = height
            self.c = c
            self.m = (1-height)/(maxValue-minValue)
            self.offset = originY-self.m*minValue
            self.bars = bars
            self.data = []

    def updateGraph2D(self, graph, value):
        graph.data.insert(0,value)
        if len(graph.data) > graph.width:
            graph.data.pop()
        x = graph.originX+graph.width-1
        m = graph.c
        for value in graph.data:
            y = round(graph.m*value + graph.offset)
            if graph.bars == True:
                for idx in range(y, graph.originY+1):
                    if x >= graph.originX and x < graph.originX+graph.width and idx <= graph.originY and idx > graph.originY-graph.height:
                        self.pixel(x,idx, m)
            else:
                if x >= graph.originX and x < graph.originX+graph.width and y <= graph.originY and y > graph.originY-graph.height:
                    self.pixel(x,y, m)
            x -= 1

class pd_OLED_Linux(pd_OLED):
    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=0x3C):
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b'\x40', None]  # Co=0, D/C#=1
        self.init_display()
        self.fill(0)
        self.show()
                        
def create_pd_OLED(address=0x3C,bus=None, freq=None, sda=None, scl=None, asw=None):
    if asw == 0: _a = 0x3C
    elif asw == 1: _a = 0x3D
    else: _a = address # parse desired address from direct address input or asw switch position (0 or 1)
    try:
        if compat_ind >= 1:
            pass
        else:
            print(compat_str)
    except:
        print(compat_str)
    display = pd_OLED_Linux(addr=_a, freq=freq)
    return display

def create_unified_i2c(bus=None, freq=None, sda=None, scl=None, suppress_warnings=True):
    i2c = I2CUnifiedLinux(bus=bus, suppress_warnings=suppress_warnings)
    return i2c

class I2CBase:
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        raise NotImplementedError('writeto_mem')

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        raise NotImplementedError('readfrom_mem')

    def write8(self, addr, buf, stop=True):
        raise NotImplementedError('write')

    def read16(self, addr, nbytes, stop=True):
        raise NotImplementedError('read')

    def __init__(self, bus=None, freq=None, sda=None, scl=None):
        raise NotImplementedError('__init__')


class I2CUnifiedLinux(I2CBase):
    def __init__(self, bus=None, suppress_warnings=True):
        if suppress_warnings == False:
            with open('/boot/config.txt') as config_file:
                if 'dtparam=i2c_arm=on' in config_file.read():
                    pass
                else:
                    print('I2C is not enabled')
                config_file.close()
            with open('/boot/config.txt') as config_file:
                if 'dtparam=i2c_arm_baudrate=400000' in config_file.read():
                    pass
                else:
                    print('Slow baudrate detected')
                config_file.close()
        if bus is None:
            bus = 1
        self.i2c = SMBus(bus)

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        data = [None] * nbytes # initialise empty list
        self.smbus_i2c_read(addr, memaddr, data, nbytes, addrsize=addrsize)
        return data
    
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        self.smbus_i2c_write(addr, memaddr, buf, len(buf), addrsize=addrsize)
    
    def smbus_i2c_write(self, address, reg, data_p, length, addrsize=8):
        ret_val = 0
        data = []
        for index in range(length):
            data.append(data_p[index])
        if addrsize == 8:
            msg_w = i2c_msg.write(address, [reg] + data)
        elif addrsize == 16:
            msg_w = i2c_msg.write(address, [reg >> 8, reg & 0xff] + data)
        else:
            raise Exception('address must be 8 or 16 bits long only')
        self.i2c.i2c_rdwr(msg_w)
        return ret_val
        
    def smbus_i2c_read(self, address, reg, data_p, length, addrsize=8):
        ret_val = 0
        if addrsize == 8:
            msg_w = i2c_msg.write(address, [reg]) # warning this is set up for 16-bit addresses
        elif addrsize == 16:
            msg_w = i2c_msg.write(address, [reg >> 8, reg & 0xff]) # warning this is set up for 16-bit addresses
        else:
            raise Exception('address must be 8 or 16 bits long only')
        msg_r = i2c_msg.read(address, length)
        self.i2c.i2c_rdwr(msg_w, msg_r)
        if ret_val == 0:
            for index in range(length):
                data_p[index] = ord(msg_r.buf[index])
        return ret_val
    
    def write8(self, addr, reg, data):
        if reg is None:
            d = int.from_bytes(data, 'big')
            self.i2c.write_byte(addr, d)
        else:
            r = int.from_bytes(reg, 'big')
            d = int.from_bytes(data, 'big')
            self.i2c.write_byte_data(addr, r, d)
    
    def read16(self, addr, reg):
        regInt = int.from_bytes(reg, 'big')
        return self.i2c.read_word_data(addr, regInt).to_bytes(2, byteorder='little', signed=False)
