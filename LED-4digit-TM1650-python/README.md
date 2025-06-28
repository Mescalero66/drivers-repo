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

**shout out to the above CarlWilliamsBristol!**
it would have been absolutely impossible to get this to work without their very detailed explanation.

## read this stuff maybe
<https://www.dfrobot.com/forum/topic/319680>
<https://github.com/DFRobot/DFRobot_LedDisplayModule> (useless)

