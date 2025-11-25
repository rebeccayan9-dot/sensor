import time
from game.difficulty import DIFFICULTY, TIME_LIMIT


class Game:
    def __init__(self, moves, leds, oled):
        """
        moves: AccelMoves 实例
        leds:  SlotNeoPixel 实例
        oled:  OLED 实例
        """
        self.moves = moves
        self.leds = leds
        self.oled = oled

    def _perform_motion(self, motion_func, need_time):
        """
        在 TIME_LIMIT 秒内，累计动作时间达到 need_time 就过关
        motion_func(): 返回 True/False，表示当前这一小段时间是否检测到动作
        """
        start = time.monotonic()
        acc_time = 0.0

        while time.monotonic() - start < TIME_LIMIT:
            if motion_func():
                acc_time += 0.1
            time.sleep(0.1)

            if acc_time >= need_time:
                return True

        return False

    def play(self, difficulty_name):
        need_time = DIFFICULTY[difficulty_name]["need_time"]

        # 3 种晃动动作循环用：左右 → 前后 → 上下 → ...
        motion_order = [
            ("Left-Right", self.moves.left_right),
            ("Forward-Back", self.moves.fwd_back),
            ("Up-Down", self.moves.up_down),
        ]

        for level in range(1, 11):
            move_name, func = motion_order[(level - 1) % 3]

            # 显示本关要求
            self.oled.show_level(level, move_name, TIME_LIMIT)

            passed = self._perform_motion(func, need_time)

            if not passed:
                # 失败
                self.oled.show_lose_icons()
                self.leds.lose_flash()
                self.oled.show_game_over_level(level)
                return False  # 游戏失败

            # 这一关过了 → 老虎机滚动（灯 + OLED）
            self.oled.show_spin()
            self.leds.spin(duration=1.5)

        # 10 关全部通过 → 赢
        self.leds.win_flash()
        self.oled.show_win_icons()
        self.oled.show_game_clear()
        return True
