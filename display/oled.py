import board
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306


class OLED:
    def __init__(self):
        displayio.release_displays()
        i2c = board.I2C()
        bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        self.display = adafruit_displayio_ssd1306.SSD1306(bus, width=128, height=64)

    def _show_lines(self, lines):
        group = displayio.Group()
        y = 6
        for text in lines:
            if text is None:
                text = ""
            lbl = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
            lbl.anchor_point = (0.5, 0)
            lbl.anchored_position = (64, y)
            group.append(lbl)
            y += 14
        self.display.root_group = group

    def show_difficulty_menu(self, current):
        self._show_lines([
            "MOTION SLOT",
            "Choose difficulty:",
            f"> {current}",
            "Press knob to start",
        ])

    def show_start(self, difficulty):
        self._show_lines([
            "START!",
            f"Mode: {difficulty}",
            "Get ready to shake",
        ])

    def show_level(self, level, move_name, time_limit):
        self._show_lines([
            f"Level {level}/10",
            f"Move: {move_name}",
            f"Time limit: {int(time_limit)}s",
            "Shake now!",
        ])

    def show_spin(self):
        # 老虎机滚动时
        self._show_lines([
            "Spinning...",
            " [ ● ]  [ ● ]  [ ● ]",
            "Good luck!"
        ])

    def show_win_icons(self):
        # 赢：3 个一样的“图案”
        self._show_lines([
            "YOU WIN!",
            " [ ♥ ]  [ ♥ ]  [ ♥ ]",
            "Slot Jackpot!"
        ])

    def show_lose_icons(self):
        # 输：3 个不一样的“图案”
        self._show_lines([
            "GAME OVER",
            " [ X ]  [ O ]  [ Δ ]",
            "Try again!"
        ])

    def show_game_over_level(self, level):
        self._show_lines([
            "GAME OVER",
            f"Failed at Level {level}",
            "Press RESTART",
        ])

    def show_game_clear(self):
        self._show_lines([
            "ALL 10 LEVELS!",
            "YOU WIN!",
            "Press RESTART",
        ])
