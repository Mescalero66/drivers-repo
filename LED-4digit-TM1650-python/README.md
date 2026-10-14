# DF Robot Gravity 4-Digit LED Segment Display (DFR0645-R -G)

Page: <https://www.dfrobot.com/product-1967.html>

Wiki: <https://wiki.dfrobot.com/4-Digital%20LED%20Segment%20Display%20Module%20%20SKU:%20DFR0645-G_DFR0645-R>

- Voltage: 5VDC (confirmed 3V3 also works)
- Interface: I2C
    - **not I2C** despite false advertising from DFRobot
    - it uses a very annoying non-addressable digital I/O, and you can only send commands via some hybrid of binary data and pulse width modulation.

## REGARDING BRIGHTNESS
- The reds are brighter than the greens.
- For rough brightness equivalents:
  - Green: MAX=0 MIN=2
  - Red: MAX=5 MIN=1

## TM1650 SIGNAL SEQUENCING

![TM1650 SIGNAL](https://github.com/carlwilliamsbristol/pxt-tm1650display/raw/master/bit_sequence.png)

## absolutely key to getting it to work

<https://github.com/CarlWilliamsBristol/pxt-tm1650display>

## TM1650 Datasheet

https://bafnadevices.com/wp-content/uploads/2024/04/TM1650_V2.2_EN.pdf

**shout out to the above CarlWilliamsBristol!**
it would have been absolutely impossible to get this to work without their very detailed explanation. 
I've blatantly stolen the critical part here:

  _A very brief overview of the communication protocol, for the curious:_

  _It's "like" I2C. You have a clock line controlled by the host, and a biderectional data line. For this extension, the facility to read back from the display is effectively un-used. ACK bits sent back during display updates are read but discarded and there are no methods included (at the moment) to support the keyboard reading aspect of the chip._

  _Clock and data lines start both set high (idle state)._

  _In general, the data line must not change while the clock line is high, and data are clocked into the display when the clock line goes from high to low, so the general line sequence for a bit is, from a position where the clock is low, set data, take clock high, take clock low again, move on to the next bit. Bytes are sent starting with the most significant bit (MSB first)._

  _The beginning of a transaction is signaled with a "start" sequence, which is distinguished by violating the rule about not changing the data line while the clock is high. A high-to-low transition on the data line while the clock line is high represents "start". At the end of a transaction, taking data from low to high while clock is high signifies "stop". Every complete transation comprises "start", then two bytes, then "stop". Each byte includes an extra clock pulse for an ACK bit that is signalled on the data line by the TM1650._

  _In more detail: after the start signal, eight bits are clocked out in big-endian order (most significant first) and then a further ninth clock in effect acknowledges an ACK bit from the display, signalled on SDA, which can be read by the host during the ninth clock period. (Note: According to the data sheet, after the falling edge of the 8th clock, the TM1650 drives SDA low if the transaction was successful. It appears, on examination with an oscilloscope, to release the line again roughly half a clock period after the falling edge of the ninth clock, and it appears to need some additional breathing space - with the host keeping clock low - in which to process the byte just received.) A second group of eight bits are sent, and a second ACK bit obtained. After the two bytes are sent, the host sends a stop sequence which involves taking the clock high, then taking data high, in that order. The communication lines are then back in the "idle" state._

  _The two bytes are basically an address/data pair. They are either referred to as "command 1, command 2" or as "address, data" in the datasheet, depending on the first byte. Turning the display on is achieved by sending 0x48 as "command 1" and a "display on" code as "command 2". Writing segment data to the display involves sending one of four addresses - one for each digit - followed by a byte that represents a bit pattern that maps onto the segments._

  _Serial data timing defaults to a data rate of about 8000kbps. Port pin numbers and data rate are configurable. It doesn't need to be very fast because updating the entire display only takes 8 bytes of serial traffic. As you increase the speed, the "baud rate" is increasingly inaccurate, because of overheads with the bit-banged approach._

## read this stuff maybe
<https://www.dfrobot.com/forum/topic/319680>
<https://github.com/DFRobot/DFRobot_LedDisplayModule> (useless)

