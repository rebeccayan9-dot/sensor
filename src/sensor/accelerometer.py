import board
import busio
import adafruit_adxl34x
import math


class Accelerometer:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_adxl34x.ADXL345(i2c)

    def get_raw(self):
        """返回 (x, y, z) 原始加速度 m/s^2"""
        return self.sensor.acceleration

    def magnitude(self):
        x, y, z = self.sensor.acceleration
        return math.sqrt(x * x + y * y + z * z)

    def shake_strength(self):
        """去掉重力后的晃动强度（>=0）"""
        mag = self.magnitude() - 9.81
        return max(0, mag)


class AccelMoves:
    """左右晃 / 前后晃 / 上下晃 3 种动作"""

    def __init__(self, accel: Accelerometer):
        self.accel = accel

    # 左右晃：X 轴幅度大
    def left_right(self, th=3.0):
        x, y, z = self.accel.get_raw()
        return abs(x) > th

    # 前后晃：Y 轴幅度大
    def fwd_back(self, th=3.0):
        x, y, z = self.accel.get_raw()
        return abs(y) > th

    # 上下晃：Z 相对重力 9.81 变化大
    def up_down(self, th=3.0):
        x, y, z = self.accel.get_raw()
        return abs(z - 9.81) > th
