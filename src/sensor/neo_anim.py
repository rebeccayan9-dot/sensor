import time
import neopixel
import board
import random


class SlotNeoPixel:
    def __init__(self, pin=board.D10, count=3, brightness=0.4):
        self.px = neopixel.NeoPixel(pin, count, brightness=brightness, auto_write=True)
        self.count = count
        self.colors = [
            (255, 0, 0),     # 红
            (0, 255, 0),     # 绿
            (0, 0, 255),     # 蓝
            (255, 255, 0),   # 黄
            (255, 0, 255),   # 粉
            (0, 255, 255),   # 青
        ]

    def clear(self):
        self.px.fill((0, 0, 0))

    def spin(self, duration=1.5, speed=0.05):
        """老虎机滚动动画：三个灯不停随机换颜色"""
        start = time.monotonic()
        while time.monotonic() - start < duration:
            for i in range(self.count):
                self.px[i] = random.choice(self.colors)
            time.sleep(speed)

    def show_result(self, colors):
        """显示最终结果（3 个颜色）"""
        for i in range(self.count):
            self.px[i] = colors[i]

    def win_flash(self, color=(0, 255, 0), flashes=6, delay=0.15):
        """中奖了：中奖颜色闪烁"""
        for _ in range(flashes):
            self.px.fill(color)
            time.sleep(delay)
            self.clear()
            time.sleep(delay)

    def lose_flash(self, flashes=4, delay=0.15):
        """输了：红色闪烁"""
        for _ in range(flashes):
            self.px.fill((180, 0, 0))
            time.sleep(delay)
            self.clear()
            time.sleep(delay)
