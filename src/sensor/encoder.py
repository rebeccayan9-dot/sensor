import rotaryio
import board


class Rotary:
    """使用 D0, D1 做 A/B，相"""

    def __init__(self, pin_a=board.D0, pin_b=board.D1):
        self.encoder = rotaryio.IncrementalEncoder(pin_a, pin_b)
        self._last = self.encoder.position

    def get_turn(self):
        """返回这次 loop 内的旋转增量（-n, 0, +n）"""
        pos = self.encoder.position
        diff = pos - self._last
        self._last = pos
        return diff
