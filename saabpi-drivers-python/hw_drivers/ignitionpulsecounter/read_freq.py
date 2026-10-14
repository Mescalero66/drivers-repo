# MIT License
# Copyright (c) 2024 Mescalero
# <https://github.com/Mescalero66/saabpi>
# Project v1.1 - Released 20240224

import time
import pigpio

class reader:
    def __init__(self, pi, gpio):

        self.pi = pi
        self.gpio = gpio

        self._high_tick = None
        self._period = None
        self._high = None

        pi.set_mode(gpio, pigpio.INPUT)

        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

    def _cbf(self, gpio, level, tick):

        if level == 1:
            if self._high_tick is not None:
                self._period = pigpio.tickDiff(self._high_tick, tick)

            self._high_tick = tick

        elif level == 0:
            if self._high_tick is not None:
                self._high = pigpio.tickDiff(self._high_tick, tick)

    def frequency(self):
        if self._period is not None:
            return 1000000.0 / self._period
        else:
            return 0.0

if __name__ == "__main__":

    import time
    import pigpio
    import read_PWM

    PWM_GPIO = 12

    pi = pigpio.pi()

    p = read_PWM.reader(pi, PWM_GPIO)

    while True:
        f = str(int(p.frequency()))
        print(f)