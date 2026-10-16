# drivers

Hardware drivers and test scripts for sensors, displays and I/O modules, collected into one repo.

Each folder holds one driver for one device on one platform, named `<Function>-<Bus>-<Chip>-<platform>`:

- **`-micropython`** folders target the **Raspberry Pi Pico**, and some also the ESP32 (MicroPython, using `machine.Pin` / `machine.I2C` / `machine.UART`).
- **`-python`** folders target a **Raspberry Pi** running Linux (CPython). Most came from the [Saabpi](https://github.com/Mescalero66/saabpi) project and use `smbus2`, `RPi.GPIO`, `pigpio` or Seeed's `grove.py`.

## Device index

### Displays

- **DFRobot DFR0645 4-digit 7-segment LED** (TM1650, 2-wire I2C-like, bit-banged)
  - [LED-4digit-TM1650-micropython](LED-4digit-TM1650-micropython/)
  - [LED-4digit-TM1650-python](LED-4digit-TM1650-python/)
- **DFRobot DFR0646 8-digit 7-segment LED** (HT16K33, I2C 0x70)
  - [LED-8digit-HT16K33A-micropython](LED-8digit-HT16K33A-micropython/)
- **Seeed Grove 4-digit display** (TM1637, 2-wire CLK/DIO)
  - [LED-4digit-TM1637-python](LED-4digit-TM1637-python/)
- **Seeed Grove LED Bar, 10 segment** (MY9221, 2-wire DIO/CLK)
  - [LED-Bar-MY9221-python](LED-Bar-MY9221-python/)
- **128x64 OLED** (SSD1306, I2C 0x3C / 0x3D or SPI)
  - [OLED-SSD1306-micropython](OLED-SSD1306-micropython/)
  - [OLED-SSD1306-python](OLED-SSD1306-python/)

### Sensors

- **Adafruit SCD-41 CO2, temperature & humidity sensor** (Sensirion SCD41, I2C 0x62)
  - [CO2-SCD41-micropython](CO2-SCD41-micropython/)
  - [CO2-SCD41-python](CO2-SCD41-python/)
- **Air quality: AQI, TVOC, eCO2** (ENS160, I2C 0x53)
  - [Air-Quality-ENS160-micropython](Air-Quality-ENS160-micropython/)
- **ENS160 + AHT21 air quality and climate board** (ENS160 I2C 0x53 / 0x52, AHT21 I2C 0x38)
  - [Air-Quality-ENS160-AHT21-micropython](Air-Quality-ENS160-AHT21-micropython/)
  - [Air-Quality-ENS160-AHT21-python](Air-Quality-ENS160-AHT21-python/)
- **BH1750 ambient light sensor** (ROHM BH1750FVI, I2C 0x23 / 0x5C)
  - [Lux-BH1750-micropython](Lux-BH1750-micropython/)
  - [Lux-BH1750-python](Lux-BH1750-python/)
- **DFRobot SEN0546 temperature & humidity probe** (CHT8305C, I2C 0x40)
  - [Temp-Humidity-CHT8305-micropython](Temp-Humidity-CHT8305-micropython/)
  - [Temp-Humidity-CHT8305-python](Temp-Humidity-CHT8305-python/)
- **DFRobot SEN0206 non-contact IR thermometer** (MLX90614, I2C 0x5A)
  - [Temp-Infrared-MLX90614-python](Temp-Infrared-MLX90614-python/)
- **Seeed Grove 3-axis digital compass v2** (BMM150, I2C 0x13)
  - [Compass-I2C-BMM150-python](Compass-I2C-BMM150-python/)
- **Sensirion SEN62 particulate matter, temperature & humidity sensor** (SEN62-SIN-T, I2C 0x6B)
  - [Particulates-SEN62-micropython](Particulates-SEN62-micropython/)
  - [Particulates-SEN62-python](Particulates-SEN62-python/)

### GPS

- **NEO-6M GPS module** (u-blox NEO-6M, UART 9600 baud)
  - [GPS-UART-Neo6M-micropython](GPS-UART-Neo6M-micropython/)
- **DFRobot TEL0138 USB GPS receiver** (u-blox UBX-G7020-KT, USB serial)
  - [GPS-USB-UBXG7020KT-python](GPS-USB-UBXG7020KT-python/)

### Bus / I/O

- **TI ADS1115 16-bit 4-channel ADC** (I2C 0x48–0x4B)
  - [ADC-ADS1115-micropython](ADC-ADS1115-micropython/)
- **DFRobot DFR0576 1-to-8 I2C multiplexer** (TCA9548A, I2C 0x70–0x77)
  - [mux-I2C-TCA9548A-micropython](mux-I2C-TCA9548A-micropython/)
  - [Mux-I2C-TCA9548A-python](Mux-I2C-TCA9548A-python/)
- **Saab 900 ignition pulse, engine RPM** (GPIO edge timing)
  - [Ignition-Pulse-Saab900-python](Ignition-Pulse-Saab900-python/)

## MicroPython drivers (Raspberry Pi Pico)

### [ADC-ADS1115-micropython](ADC-ADS1115-micropython/)
Texas Instruments ADS1115 16-bit, 4-channel ADC, for the Pico, ESP32-C3 and ESP32-S3. Checked against the TI datasheet; derived from [robert-hh/ads1x15](https://github.com/robert-hh/ads1x15).
- `adc_ads1115.py`: asynchronous (`asyncio`) `ADS1115` class. Single-shot single-ended and differential reads in raw codes or volts, gain and data rate by value, continuous mode, threshold comparator, and optional ALERT/RDY pin interrupts so tasks wait without polling. Power down and general-call reset.
- `adc_ads1115_test.py`: demo that reads all channels from concurrent tasks, sweeps gain, times each data rate and runs continuous mode while a heartbeat task keeps running.

### [Air-Quality-ENS160-micropython](Air-Quality-ENS160-micropython/)
ScioSense ENS160 digital air-quality sensor.
- `ENS160.py`: `ENS160` class. Reads AQI, TVOC (ppb), eCO2 (ppm), device ID, firmware version and status. Sets temperature/humidity compensation and gives text ratings for eCO2 and TVOC levels. Based on [JustDr00py/ens160-aht21](https://github.com/JustDr00py/ens160-aht21).
- `main.py`: demo that sets compensation values, then prints readings and validity status in a loop.
- `ENS160_async.py`: asynchronous (`asyncio`) `ENS160` class with the same features, plus `wait_data()` (waits for each new sample) and decoded status flags. Works on the Pico, ESP32-C3 and ESP32-S3.
- `test_async.py`: demo where a sampler task and a monitor task share the sensor while a heartbeat task shows the loop never blocks.

### [Air-Quality-ENS160-AHT21-micropython](Air-Quality-ENS160-AHT21-micropython/)
ENS160 + AHT21 combo board: a ScioSense ENS160 air-quality sensor and an ASAIR AHT21 temperature/humidity sensor on one I2C bus. Written from the datasheets.
- `ENS160_AHT21.py`: `AHT21`, `ENS160` and the combined `ENS160_AHT21` classes. Each `read()` measures temperature and humidity with the AHT21, feeds them to the ENS160 as compensation, then reads AQI, TVOC and eCO2. CRC-checked AHT21 reads, blocking and `asyncio` methods.
- `main.py`: blocking demo. `main_async.py`: `asyncio` demo with an LED heartbeat.

### [CO2-SCD41-micropython](CO2-SCD41-micropython/)
Adafruit SCD-41 CO2, temperature and humidity sensor (Sensirion SCD41), for the Pico, ESP32-C3 and ESP32-S3.
- `scd41.py`: asynchronous (`asyncio`) `SCD41` class. Periodic, low-power and single-shot measurements, temperature offset, altitude/pressure compensation, forced and automatic self-calibration, serial number, variant, self test, power down/wake up. All replies are CRC-checked.
- `scd41_test.py`: demo that reads the ID and config, then takes periodic and single-shot readings while a heartbeat task keeps running. It picks Pico or ESP32 pins automatically.

### [GPS-UART-Neo6M-micropython](GPS-UART-Neo6M-micropython/)
NEO-6M GPS module over UART.
- `parseGPS.py`: non-blocking NMEA parser. `GPSReader` buffers UART data and parses `$GPRMC`, `$GPGGA` and `$GPGSA` sentences into a `GPSData` object (fix, lat/lon, speed, time/date, satellites, altitude, HDOP/PDOP/VDOP).
- `timezones.py`: `aus_localtime_from_gps()`. Works out the Australian time zone (including Lord Howe, Eucla and Broken Hill) and daylight saving from lat/lon plus UTC, and returns local time.
- `gps.py`: demo that prints fix, satellites, position and time.
- `gps_raw.py`: dumps raw NMEA output from the UART.

### [LED-4digit-TM1650-micropython](LED-4digit-TM1650-micropython/)
DFRobot DFR0645-R / DFR0645-G 4-digit display. Despite being sold as I2C, the TM1650 uses its own two-wire protocol, which the driver bit-bangs.
- `led_4digit_tm1650.py`: `LED4digdisp` class. Display on/off with brightness, clear, `show_string`, `show_integer`, `show_decimal`, `show_hex`, raw segments, and decimal points. Includes a lookup table for A–Z and symbols. The bottom of the file contains demo code.
- `test/led_4digit_test_1.py`: string and counting test.

### [LED-8digit-HT16K33A-micropython](LED-8digit-HT16K33A-micropython/)
DFRobot DFR0646 8-digit 7-segment display driven by an HT16K33 over I2C.
- `HT16K33LED.py`: `HT16K33` base class (power, brightness, blink rate, buffer) and `HT16K33LED` (glyphs, numbers, characters, left/right-aligned `set_string`, rotation). Based on code by Tony Smith ([@smittytone](https://github.com/smittytone)).
- `LED_8Digit.py`: demo of strings, alignment, animation, counting and blinking.
- `testing/LED_8Digit_orig.py`: original demo.

### [Lux-BH1750-micropython](Lux-BH1750-micropython/)
ROHM BH1750FVI ambient light sensor (Adafruit 4681, GY-302), for the Pico, ESP32-C3 and ESP32-S3. Written from the datasheet.
- `bh1750.py`: asynchronous (`asyncio`) `BH1750` class. One-time and continuous measurement in H (1 lx), H2 (0.5 lx) and L (4 lx) resolution, `wait_lux()` for each new sample, MTreg sensitivity adjustment (0.11 lx to ~100000 lx), optical-window correction, power down/reset.
- `bh1750_test.py`: demo of one-time readings in each resolution, an MTreg sweep, and continuous readings shared between two tasks while a heartbeat task checks the loop never blocks.

### [mux-I2C-TCA9548A-micropython](mux-I2C-TCA9548A-micropython/)
DFRobot DFR0576 1-to-8 I2C multiplexer (TCA9548A).
- `mux.py`: `I2CMultiplex` class. `select_port` (0–7, or 8 to disable all), per-port `scan`, `writeto_mem`, `readfrom_mem`.
- `mux_test_scan.py`: scans all 8 ports and lists the device addresses found.
- `mux_test_ssd1306.py`: drives eight SSD1306 OLEDs that share one address, one on each mux port.
- `ssd1306.py`: copy of the SSD1306 driver used by the OLED test.

### [OLED-SSD1306-micropython](OLED-SSD1306-micropython/)
128x64 blue/yellow OLED (SSD1306). The top 16 rows are yellow and the rest are blue.
- `ssd1306.py`: extended version of the MicroPython SSD1306 driver (`SSD1306_I2C`, `SSD1306_SPI`). Adds shapes (circle, Bresenham line, rectangles) and layout helpers for the two-colour panel: `banner_text`, `banner_text_inverted`, `subbanner_text`, `date_text` (large scaled digits), `year_text` and `text_inverted`.
- `font-pet-me-128.dat`: 8x8 bitmap font loaded by the driver (a copy is also kept in `fonts/`).
- `ssd1306_test.py`: demo of banners, inverted text, invert and circles.

### [Particulates-SEN62-micropython](Particulates-SEN62-micropython/)
Sensirion SEN62 particulate matter, temperature and humidity sensor module, for the Pico, ESP32-C3 and ESP32-S3. Written from the SEN6x datasheet.
- `sen62.py`: asynchronous (`asyncio`) `SEN62` class. PM1.0/2.5/4.0/10 mass and PM0.5–10 number concentrations, compensated and raw RH/T, `wait_measurement()` for each new sample, temperature offset/acceleration parameters, product info, firmware version, decoded device status, reset, fan cleaning and SHT heater. Unknown values come back as `None`. All replies are CRC-checked.
- `sen62_test.py`: demo that reads the product info and status, then takes readings while a heartbeat task keeps running. It picks Pico or ESP32 pins automatically.

### [Temp-Humidity-CHT8305-micropython](Temp-Humidity-CHT8305-micropython/)
DFRobot SEN0546 stainless-steel temperature and humidity probe (Sensylink CHT8305C).
- `CHT8305.py`: `I2C_CHT8305_SEN0546` class. Blocking read (`get_…`) or split request/read (`req_…` / `read_…`), configuration, heater on, soft reset, and manufacturer/version ID.
- `main.py`: demo that scans the bus, reads the IDs, applies the configuration, then reads continuously and soft-resets after errors.

## Python drivers (Raspberry Pi)

### [Air-Quality-ENS160-AHT21-python](Air-Quality-ENS160-AHT21-python/)
ENS160 + AHT21 combo board on I2C bus 1, via `smbus2`. Same classes and methods as the MicroPython driver.
- `ens160_aht21.py`: an `I2C` wrapper that gives `smbus2` the `machine.I2C` method names (every transfer uses `i2c_rdwr`, since the AHT21 has no registers), plus the `AHT21`, `ENS160` and combined `ENS160_AHT21` classes. Each `read()` measures temperature and humidity with the AHT21, feeds them to the ENS160 as compensation, then reads AQI, TVOC and eCO2. CRC-checked AHT21 reads, blocking and `asyncio` methods.
- `ens160_aht21_test.py`: blocking demo. `ens160_aht21_test_async.py`: `asyncio` demo with a heartbeat task.

### [CO2-SCD41-python](CO2-SCD41-python/)
Adafruit SCD-41 CO2, temperature and humidity sensor (Sensirion SCD41), via `smbus2` on bus 1.
- `scd41.py`: asynchronous (`asyncio`) `SCD41` class with the same API as the MicroPython version, except that it uses a `measurements()` async generator instead of `wait_measurement()`.
- `scd41_test.py`: demo that reads the ID and config, then takes periodic and single-shot readings while a heartbeat task keeps running.

### [Compass-I2C-BMM150-python](Compass-I2C-BMM150-python/)
Seeed Grove 3-Axis Digital Compass v2 (Bosch BMM150). Not used in the final Saabpi build.
- `grove_compass.py`: full BMM150 driver (`BMM150_I2C`, `BMM150_SPI`). Covers power and preset modes, data rate, self test, trim compensation, interrupts and thresholds, and `get_compass_degree()`. Adapted from [DFRobot_BMM150](https://github.com/DFRobot/DFRobot_BMM150).
- `grove_compass_test.py`: prints the heading once a second.

### [GPS-USB-UBXG7020KT-python](GPS-USB-UBXG7020KT-python/)
DFRobot TEL0138 USB GPS receiver (u-blox UBX-G7020-KT) on `/dev/ttyACM0`. Requires `pyserial` and `pynmeagps`.
- `df_GPS_speed.py`: `USBGPS.GetGPS()` returns speed (km/h), latitude, longitude, heading and altitude.
- `df_GPS_speed_test.py`, `df_GPS_speed_test2.py`: test scripts.

### [Ignition-Pulse-Saab900-python](Ignition-Pulse-Saab900-python/)
Reads ignition pulses from a 1986–1990 Saab 900 Turbo (Timing Service Instrument socket, pin 5) to calculate engine RPM. Mostly uses `pigpio`. The README includes the relevant Saab service-manual excerpts.
- `read_RPM.py`: `reader` class. Rising-edge timing with weighted smoothing, a watchdog for a stopped engine, and a minimum-RPM cutoff.
- `read_PWM.py`: `reader` class for PWM frequency, pulse width and duty cycle.
- `read_freq.py`: simple frequency reader.
- `callback.py`, `count.py`, `ipc.py`, `monitor.py`, `pulsetimer.py`, `tworising.py`: experiments with pulse counting and timing (`pigpio` and `RPi.GPIO`).
- `test_disp_rpm.py`: shows live RPM on a TM1650 4-digit display.
- `refdocs/`: service-manual figure and TSI socket pinout.

### [LED-4digit-TM1637-python](LED-4digit-TM1637-python/)
Seeed Grove 4-digit display (TM1637), using `grove.py` GPIO. Not used in the final Saabpi build.
- `grove_4digitdisp.py`: `Grove4DigitDisplay` class. Shows strings and integers, sets brightness, controls the colon, and updates single digits.
- `grove_4digitdisp_test.py`: shows "SAAB", then a clock with a blinking colon.

### [LED-4digit-TM1650-python](LED-4digit-TM1650-python/)
DFRobot DFR0645-R / DFR0645-G 4-digit display, bit-banged with `RPi.GPIO`. The README explains the TM1650 signalling protocol and gives brightness notes for the red and green versions.
- `tm1650disp_4digit.py`: `dfDisp` class (same API as the MicroPython version).
- `testing/tm1650disp_4digit_test.py`: tests strings, integers, decimals and hex on one display.
- `testing/tm1650disp_4digit_test_multi.py`: drives four displays at once and tests brightness levels.

### [LED-Bar-MY9221-python](LED-Bar-MY9221-python/)
Seeed Grove LED Bar v2 (MY9221, 10 segments), using `grove.py` GPIO.
- `grove_ledbar.py`: `GroveLedBar` class. `level()` with brightness, `bits()`, `bytes()`, and reversible direction. Based on [zolgear/grove.py](https://github.com/zolgear/grove.py).
- `grove_ledbar_test.py`: climbing level and brightness test.

### [Lux-BH1750-python](Lux-BH1750-python/)
ROHM BH1750FVI ambient light sensor (Adafruit 4681, GY-302), via `smbus2` on bus 1.
- `bh1750.py`: asynchronous (`asyncio`) `BH1750` class with the same API as the MicroPython version, plus a `measurements()` async generator.
- `bh1750_test.py`: demo that finds the sensor at either address, takes one-time readings in each resolution, sweeps MTreg, then streams continuous readings shared between two tasks while a heartbeat task checks the loop never blocks.

### [Mux-I2C-TCA9548A-python](Mux-I2C-TCA9548A-python/)
DFRobot DFR0576 1-to-8 I2C multiplexer (TCA9548A), via `smbus2` on bus 1.
- `df_multiplexer.py`: `i2cmultiplex` class (`select_port`, `scan`, `writeto_mem`, `readfrom_mem`), from [DFRobot_I2C_Multiplexer](https://github.com/DFRobot/DFRobot_I2C_Multiplexer).
- `df_multiplexer_test_scan.py`: scans all 8 ports.

### [OLED-SSD1306-python](OLED-SSD1306-python/)
SSD1306 OLED driver based on [Adafruit_Python_SSD1306](https://github.com/adafruit/Adafruit_Python_SSD1306), adapted for the Core Electronics PiicoDev 128x64 OLED. Requires `Adafruit_GPIO` and `Pillow`.
- `SSD1306.py`: `SSD1306_128_64` and `SSD1306_128_32` display classes (I2C or SPI), with PIL image rendering.
- `displaytext.py`: "Hello, Raspberry Pi!" text example.
- `examples/`: Adafruit examples (`animate.py`, which also selects a mux port, plus `buttons.py`, `image.py`, `shapes.py` and `stats.py`).
- `happycat_oled_32.ppm`, `happycat_oled_64.ppm`: sample images.
- `setup.py`: package setup for Adafruit_SSD1306.

### [Particulates-SEN62-python](Particulates-SEN62-python/)
Sensirion SEN62 particulate matter, temperature and humidity sensor module, via `smbus2` on bus 1.
- `sen62.py`: asynchronous (`asyncio`) `SEN62` class with the same API as the MicroPython version, except that it uses a `measurements()` async generator instead of `wait_measurement()`.
- `sen62_test.py`: demo that reads the product info and status, then takes readings while a heartbeat task keeps running.

### [Temp-Humidity-CHT8305-python](Temp-Humidity-CHT8305-python/)
DFRobot SEN0546 temperature and humidity probe (CHT8305C), via `smbus2`.
- `df_tempprobe.py`: `tempprobe` class. Blocking `get_Temp` / `get_Humi`, or split `req_…` / `read_…`.
- `df_tempprobe_test.py`: prints temperature and humidity every 2 seconds.

### [Temp-Infrared-MLX90614-python](Temp-Infrared-MLX90614-python/)
DFRobot SEN0206 non-contact IR thermometer (MLX90614-DCC), via `smbus2`.
- `df_temp_ir.py`: `MLX90614` class. Reads ambient and object temperatures, retrying reads after I/O errors.
- `df_temp_IR_test.py`: prints object and ambient temperature every 2 seconds.
