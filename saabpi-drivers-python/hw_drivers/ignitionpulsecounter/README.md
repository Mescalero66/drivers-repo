# Ignition Pulse Reader for Saab 900 Turbo (1986-1990)

#### MIT License - Copyright (c) 2023 Mescalero - <https://github.com/Mescalero66/saabpi>

## Saab 900 Official Service Manual (1986-87)
### Chapter 3 - Electrical System

**_Page 340-7_**
> If on 1986 and 1987 models, all electrical checks are as specified but the car still does not start, check the **ignition pulse amplifier** on the main fuse relay panel. See Fig. 12. 

> This relay-like amplifier is designed to "amplify" the tachometer signal for more reliable control of electronic components affected by the ignition system (LH fuel injection, fuel pump control, etc.).

>![Fig12](https://github.com/Mescalero66/saabpi/blob/main/hw_drivers/ignitionpulsecounter/refdocs/saab900_ch3-pg340.7-fig12.png?raw=true)
>_Figure 12_


**_Page 340-10_**
> While operating the starter, there should be an oscillating voltage (pulses between 0 and 8 volts (DC), average of 2.8 volts).


### Chapter 3.1 - Electrical System, Instruments

**_Page 340-3_**

>**Ignition pulse amplifier**

>The ignition system is equipped with an ignitionp ulse amplifier (not included on cars without tachometer), to provide more reliable control of the electronic components affected by the ignition (the APC and LH systems), and to reduce the radio interference.

> The ignition pulse amplifier is located in the electrical distribution box, in position D.

> The wiring diagram for the ignition pulse amplifier can be found in the Service Manual, Group 3:2.

**_Page 340-17_**

>**Timing Service Instrument**

>The timing service instrument (TSI) can be connected to the ignition service socket, located at the fuse box, and, via a pulse sensor, to the HT lead for NO.1 cylinder. The instrument includes a tachometer, a dwell-angle meter, a stroboscopic lamp , a switch for the starter motor and, in the latest version, an ignition-timing meter with a graduated dial.

## Saab 900 Official Service Manual (1988-1990)

### Chapter 3.2 - Electrical System, System Diagrams, Operation and Fault Tracing

**_Page 73_**

>**LH2.4 T16 Lambda (1989 model) (AU-market) Fuel System Operation**

>On the basis of the data stored in the control unit and the incoming information from various sensors, the control unit calculates and controls the opening times of the electrically operated fuel injection valves (206). **The control unit receives information onglne speed by sensing the pulses from the ignition system.**

**_Page 85_**

>**T16 Lambda (1989 model) Ignition System (with tachometer) Operation**

>This breakerless ignition system is equipped with a Hall sensor.

>When ignition switch 20 is in the start or drive position, ignition coil 5 and amplifier 146 will be energised (+15).

>The amplifier receives ignition pulses (via a 3-core shielded cable) from the Hall sensor in ignition distibutor 6.

>The pulses are amplified and adapted in amplifier 146. A high-tension pulse is generated in the secondary winding each time a pulse breaks the primary cirrcuit of the ignition coil.

>The hlgh-tenslon pulse is then supplied to the corresponding spark piug via the distributor.

>Tachometer 110 is supplied across fuse 7. The control pulses required for displaying the engine speed are supplied from the ignition amplifier.

>**Timing Service Instrument (TSI)** socket 73 is intended for a special ignition service instrument and has the following terminals:

>       1. Positive supply direct from battery 1

>       2. Earth

>       3. Solenoid (terminal 50) on starter motor 4

>       4. Positive supply (+15) from the ignition switch when the latter is in the start or drive position

>       5. **Ignition pulses from ignition system amplifier 146**

>       6. Not used

![TSIpinout](https://github.com/Mescalero66/saabpi/blob/main/hw_drivers/ignitionpulsecounter/refdocs/saab900_TSIsocket73_pinout.jpg?raw=true)
_Timing Service Instrument (TSI) Socket 73 Pinout_


## Ignition Pulse Counter - Hardware
_Credit to **DarkCupid** for the original experiment many many years ago - see <https://www.youtube.com/watch?v=BnltsAlthNA>_

_**Insert Circuit Diagram**_


## read this stuff

<http://abyz.me.uk/rpi/pigpio/python.html>
