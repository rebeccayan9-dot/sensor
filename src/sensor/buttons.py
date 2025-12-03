import digitalio
from adafruit_debouncer import Debouncer


class Button:
    """通用去抖按键，低电平为按下"""

    def __init__(self, pin):
        p = digitalio.DigitalInOut(pin)
        p.direction = digitalio.Direction.INPUT
        p.pull = digitalio.Pull.UP
        self._debounced = Debouncer(p)

    def update(self):
        self._debounced.update()

    @property
    def pressed(self):
        """在按下瞬间 True（只触发一次）"""
        return self._debounced.fell
