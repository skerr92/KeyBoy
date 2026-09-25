# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Loose Cows — escalating, corral-based herding for KeyBoy.

D-pad moves the rancher. A lassos a nearby cow; lead it into the corral.
B whistles the loose herd closer (limited each round). SEL opens the system menu.
"""

import time
import random
import displayio
from adafruit_display_text import label
import terminalio
import adafruit_imageload
from GameMenu import PauseMenu, save_high_score


def _solid(width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette)


class LooseCows:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, HighScore, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B = A_btn, B_btn
        self._U, self._D = Up_btn, Dwn_btn
        self._L, self._R = L_btn, R_btn
        self._HighScore = HighScore
        self._audio = Audio
        self._system_menu = PauseMenu(splash, Sel_btn, A_btn, Up_btn, Dwn_btn)
        self._exit = False
        self.farmer, self.palette = adafruit_imageload.load(
            "/lib/Loose_Cows/farmer sprites_16b2.gif", bitmap=displayio.Bitmap, palette=displayio.Palette)
        self.field, self.fpalette = adafruit_imageload.load(
            "/lib/Loose_Cows/background_sheet.gif", bitmap=displayio.Bitmap, palette=displayio.Palette)

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    @staticmethod
    def _overlap(x, y, ox, oy, size=16):
        return x < ox + size and x + 16 > ox and y < oy + size and y + 16 > oy

    def _blocked(self, x, y, obstacles):
        if x < 10 or y < 42 or x > 214 or y > 214:
            return True
        for obstacle in obstacles:
            if self._overlap(x, y, obstacle[0], obstacle[1], 20):
                return True
        return False

    def _new_cow(self, cows, obstacles):
        while True:
            x = random.randint(72, 210)
            y = random.randint(50, 210)
            if not self._blocked(x, y, obstacles):
                break
        sprite = displayio.TileGrid(self.farmer, pixel_shader=self.palette,
                                    width=1, height=1, tile_width=16, tile_height=16, x=x, y=y)
        sprite[0] = 3
        self._splash.append(sprite)
        cows.append([sprite, random.choice((-2, 2)), random.choice((-2, 2)), False])

    def _build_round(self, round_number):
        self._clear()
        background = displayio.TileGrid(self.field, pixel_shader=self.fpalette, width=15, height=15,
                                        tile_width=16, tile_height=16)
        self._splash.append(background)
        for x in range(15):
            for y in range(15):
                background[x, y] = 4
        corral = _solid(58, 48, 0x9A6539)
        corral.x, corral.y = 8, 174
        gate = _solid(28, 5, 0xE8C47A)
        gate.x, gate.y = 24, 174
        self._splash.append(corral)
        self._splash.append(gate)
        obstacles = []
        for number in range(min(5, round_number // 2)):
            while True:
                x = random.randrange(82, 210, 20)
                y = random.randrange(62, 170, 20)
                if not self._blocked(x, y, obstacles):
                    break
            bale = _solid(20, 20, 0xD69C48)
            bale.x, bale.y = x, y
            self._splash.append(bale)
            obstacles.append([x, y])
        rancher = displayio.TileGrid(self.farmer, pixel_shader=self.palette, width=1, height=1,
                                     tile_width=16, tile_height=16, x=28, y=192)
        cows = []
        quota = min(6, round_number + 1)
        for unused in range(quota + (1 if round_number >= 3 else 0)):
            self._new_cow(cows, obstacles)
        self._splash.append(rancher)
        return rancher, cows, obstacles, quota

    def _notice(self, text, color=0xFFFFFF):
        notice = label.Label(terminalio.FONT, text=text, color=color, x=8, y=29)
        self._splash.append(notice)
        return notice

    def Game(self):
        self._exit = False
        score, round_number, lives = 0, 1, 3
        while not self._exit:
            rancher, cows, obstacles, quota = self._build_round(round_number)
            delivered = 0
            timeleft = max(9, 18 - round_number)
            whistles = 2
            combo = 1
            last_delivery = 0
            hud = label.Label(terminalio.FONT, text="R1  0/2  T18  *1", color=0x000000, x=8, y=12)
            self._splash.append(hud)
            note = self._notice("A lasso  B whistle  SEL menu")
            previous_second = time.monotonic()
            last_cow_move = time.monotonic()
            a_was_down = False
            b_was_down = False
            while not self._exit and timeleft > 0 and delivered < quota:
                now = time.monotonic()
                dx, dy, frame = 0, 0, rancher[0]
                if self._U.value == 0:
                    dy, frame = -4, 0
                elif self._D.value == 0:
                    dy, frame = 4, 0
                elif self._L.value == 0:
                    dx, frame = -4, 1
                elif self._R.value == 0:
                    dx, frame = 4, 2
                if (dx or dy) and not self._blocked(rancher.x + dx, rancher.y + dy, obstacles):
                    rancher.x += dx
                    rancher.y += dy
                    rancher[0] = frame
                a_down = self._A.value == 0
                b_down = self._B.value == 0
                tethered = None
                for cow in cows:
                    if cow[3]:
                        tethered = cow
                        break
                if a_down and not a_was_down and tethered is None:
                    for cow in cows:
                        if abs(rancher.x - cow[0].x) < 25 and abs(rancher.y - cow[0].y) < 25:
                            cow[3] = True
                            self._audio.play("lasso")
                            note.text = "Cow lassoed — bring it home!"
                            break
                if b_down and not b_was_down and whistles > 0:
                    whistles -= 1
                    self._audio.play("support")
                    for cow in cows:
                        if not cow[3]:
                            cow[0].x += 12 if rancher.x > cow[0].x else -12
                            cow[0].y += 12 if rancher.y > cow[0].y else -12
                    note.text = "WHISTLE! " + str(whistles) + " left"
                a_was_down, b_was_down = a_down, b_down
                if tethered:
                    tethered[0].x = rancher.x - 10
                    tethered[0].y = rancher.y + 4
                    if rancher.x < 62 and rancher.y > 166:
                        self._splash.remove(tethered[0])
                        cows.remove(tethered)
                        delivered += 1
                        if now - last_delivery < 4:
                            combo = min(5, combo + 1)
                        else:
                            combo = 1
                        score += combo
                        self._audio.play("collect")
                        last_delivery = now
                        note.text = "CORRALLED! combo x" + str(combo)
                if now - last_cow_move > 0.18:
                    for cow in cows:
                        if not cow[3]:
                            if random.randint(0, 4) == 0:
                                cow[1] = random.choice((-2, 0, 2))
                                cow[2] = random.choice((-2, 0, 2))
                            next_x, next_y = cow[0].x + cow[1], cow[0].y + cow[2]
                            if self._blocked(next_x, next_y, obstacles) or next_x < 70:
                                cow[1] *= -1
                                cow[2] *= -1
                            else:
                                cow[0].x, cow[0].y = next_x, next_y
                    last_cow_move = now
                if self._system_menu.pressed():
                    if self._system_menu.open("LOOSE COWS", max(score, self._HighScore), "/cows.txt"):
                        self._exit = True
                if now - previous_second >= 1:
                    timeleft -= 1
                    previous_second = now
                hud.text = "R" + str(round_number) + "  " + str(delivered) + "/" + str(quota) + "  T" + str(timeleft) + "  *" + str(combo)
                time.sleep(0.035)
            if self._exit:
                break
            if delivered >= quota:
                round_number += 1
                self._audio.play("win")
                note.text = "ROUND CLEAR! Next herd..."
                time.sleep(0.8)
            else:
                lives -= 1
                self._audio.play("lose")
                if score > self._HighScore:
                    self._HighScore = score
                    save_high_score("/cows.txt", score)
                if lives == 0:
                    note.text = "HERD LOST! Score " + str(score)
                    time.sleep(1.2)
                    score, round_number, lives = 0, 1, 3
                else:
                    self._clear()
                    backdrop = _solid(240, 240, 0x2E485D)
                    self._splash.append(backdrop)
                    self._splash.append(label.Label(terminalio.FONT, text="COWS SCATTERED", color=0xFFE29B, scale=2, x=34, y=95))
                    self._splash.append(label.Label(terminalio.FONT, text="Try again — " + str(lives) + " ranch stars left", color=0xFFFFFF, x=28, y=125))
                    time.sleep(1.2)
        self._clear()
        return [True, self._HighScore]
