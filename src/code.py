from sensors.accelerometer import Accelerometer
from sensors.buttons import Button
from sensors.encoder import Rotary
from sensors.neo_anim import SlotNeoPixel
from display.oled import OLED
from game.logic import Game

import time, board

oled = OLED()
accel = Accelerometer()
leds = SlotNeoPixel()
btn = Button(board.D9)
rot = Rotary()
game = Game(accel, leds, oled)

diffs = ["Easy", "Medium", "Hard"]
idx = 0

oled.show(["Slot Machine", "Press Button"])

while True:
    btn.update()
    turn = rot.get_turn()

    if turn != 0:
        idx = (idx + turn) % len(diffs)
        oled.show(["Select Difficulty", f"> {diffs[idx]}"])

    if btn.pressed:
        difficulty = diffs[idx]
        oled.show(["Starting...", difficulty])
        time.sleep(1)
        game.play_game(difficulty)
        oled.show(["Slot Machine", "Press Button"])
