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
from KeyBoyArcade import Scenery, actor, choose
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
        self._scenery = None
        self._rope = 25
        self._extra_whistles = 0
        self._boots = 0

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    @staticmethod
    def _overlap(x, y, ox, oy, size=16):
        return x < ox + size and x + 20 > ox and y < oy + size and y + 22 > oy

    def _blocked(self, x, y, obstacles):
        if x < 10 or y < 42 or x > 212 or y > 208:
            return True
        for obstacle in obstacles:
            if self._overlap(x, y, obstacle[0], obstacle[1], 20):
                return True
        return False

    def _new_cow(self, cows, obstacles):
        while True:
            x = random.randint(72, 210)
            y = random.randint(50, 210)
            if not self._blocked(x, y, obstacles) and not any(self._overlap(x,y,c[0].x,c[0].y,20) for c in cows):
                break
        sprite = actor('cow',20,18)
        sprite.x,sprite.y=x,y
        value=2 if len(cows)%3==2 else 1
        if value==2:sprite.pixel_shader[5]=0xD8AF65
        self._splash.append(sprite)
        cows.append([sprite, random.choice((-2, 2)), random.choice((-2, 2)), False, value])

    def _whistle_cow(self,cow,rancher,obstacles):
        # Move in short collision-checked steps; whistles cannot trap cows in hay.
        for _ in range(6):
            dx=2 if rancher.x>cow[0].x else -2
            dy=2 if rancher.y>cow[0].y else -2
            if not self._blocked(cow[0].x+dx,cow[0].y,obstacles):cow[0].x+=dx
            if not self._blocked(cow[0].x,cow[0].y+dy,obstacles):cow[0].y+=dy

    def _build_round(self, round_number):
        self._clear()
        if self._scenery is None:self._scenery=Scenery()
        self._scenery.draw('ranch',round_number)
        self._scenery.attach(self._splash)
        obstacles = []
        for number in range(min(5, round_number // 2)):
            while True:
                x = random.randrange(82, 210, 20)
                y = random.randrange(62, 170, 20)
                if not self._blocked(x, y, obstacles):
                    break
            bale = actor('bale',20,20)
            bale.x, bale.y = x, y
            self._splash.append(bale)
            obstacles.append([x, y])
        rancher=actor('rancher',18,22)
        rancher.x,rancher.y=28,192
        cows = []
        quota = min(6, round_number + 1)
        for unused in range(quota + (1 if round_number >= 3 else 0)):
            self._new_cow(cows, obstacles)
        self._splash.append(rancher)
        self._lasso=actor('rope',12,12)
        self._lasso.hidden=True
        self._splash.append(self._lasso)
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
            timeleft = max(28, 28 + quota * 4 - round_number)
            whistles = 2 + self._extra_whistles
            combo = 1
            last_delivery = 0
            hud = label.Label(terminalio.FONT, text="R%d 0/%d T%d HP%d W%d" % (round_number,quota,timeleft,lives,whistles), color=0xEAE1BC, x=8, y=12)
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
                    dy, frame = -4-self._boots, 0
                elif self._D.value == 0:
                    dy, frame = 4+self._boots, 0
                elif self._L.value == 0:
                    dx, frame = -4-self._boots, 0
                elif self._R.value == 0:
                    dx, frame = 4+self._boots, 0
                if (dx or dy) and not self._blocked(rancher.x + dx, rancher.y + dy, obstacles):
                    rancher.x += dx
                    rancher.y += dy
                    rancher[0] = int(now*9)%2
                    if dx:rancher.flip_x=dx<0
                a_down = self._A.value == 0
                b_down = self._B.value == 0
                tethered = None
                for cow in cows:
                    if cow[3]:
                        tethered = cow
                        break
                if a_down and not a_was_down and tethered is not None:
                    tethered[3]=False
                    tethered=None
                    note.text='Released. A lasso / B whistle'
                elif a_down and not a_was_down and tethered is None:
                    for cow in cows:
                        if abs(rancher.x - cow[0].x) < self._rope and abs(rancher.y - cow[0].y) < self._rope:
                            cow[3] = True
                            self._audio.play("lasso")
                            note.text = "Cow lassoed — bring it home!"
                            break
                if b_down and not b_was_down and whistles > 0:
                    whistles -= 1
                    self._audio.play("support")
                    for cow in cows:
                        if not cow[3]:
                            self._whistle_cow(cow, rancher, obstacles)
                    note.text = "WHISTLE! " + str(whistles) + " left"
                a_was_down, b_was_down = a_down, b_down
                if tethered:
                    tethered[0].x = rancher.x - 20 if rancher.x>=30 else rancher.x+18
                    tethered[0].y = rancher.y + 2
                    tethered[0][0]=int(now*8)%2 if dx or dy else 0
                    if rancher.x <= 48 and rancher.y >= 176:
                        self._splash.remove(tethered[0])
                        cows.remove(tethered)
                        delivered += 1
                        if now - last_delivery < 4:
                            combo = min(5, combo + 1)
                        else:
                            combo = 1
                        score += combo * tethered[4]
                        self._audio.play("collect")
                        self._HighScore=max(self._HighScore,score)
                        last_delivery = now
                        note.text = "CORRALLED! combo x" + str(combo)
                        tethered=None
                self._lasso.hidden=tethered is None
                if tethered:
                    self._lasso.x,self._lasso.y=rancher.x-9,rancher.y+6
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
                                cow[0][0]=1-cow[0][0]
                                if cow[1]:cow[0].flip_x=cow[1]<0
                    last_cow_move = now
                if self._system_menu.pressed():
                    paused=time.monotonic()
                    if self._system_menu.open("LOOSE COWS", max(score, self._HighScore), "/cows.txt"):
                        self._exit = True
                    delay=time.monotonic()-paused
                    previous_second+=delay;last_cow_move+=delay;last_delivery+=delay
                    a_was_down=not self._A.value;b_was_down=not self._B.value
                if not self._U.value and not self._D.value:self._exit=True
                if now - previous_second >= 1:
                    timeleft -= 1
                    previous_second = now
                hud_text = "R" + str(round_number) + "  " + str(delivered) + "/" + str(quota) + "  T" + str(timeleft) + " HP" + str(lives) + " W" + str(whistles)
                if hud.text != hud_text:hud.text=hud_text
                time.sleep(0.035)
            if self._exit:
                break
            if delivered >= quota:
                round_number += 1
                self._audio.play("win")
                note.text = "ROUND CLEAR! Next herd..."
                save_high_score('/cows.txt',score)
                time.sleep(0.8)
                if round_number%3==1:
                    upgrade=choose(self._splash,'RANCH UPGRADE',('Longer lasso','Extra whistle','Quicker boots'),(self._A,self._U,self._D))
                    if upgrade<0:self._exit=True
                    elif upgrade==0:self._rope=min(49,self._rope+8)
                    elif upgrade==1:self._extra_whistles=min(4,self._extra_whistles+1)
                    else:self._boots=min(3,self._boots+1)
            else:
                lives -= 1
                self._audio.play("lose")
                self._HighScore = max(score,self._HighScore)
                save_high_score("/cows.txt", self._HighScore)
                if lives == 0:
                    note.text = "HERD LOST! Score " + str(score)
                    time.sleep(1.2)
                    score, round_number, lives = 0, 1, 3
                    self._rope,self._extra_whistles,self._boots=25,0,0
                else:
                    self._clear()
                    backdrop = _solid(240, 240, 0x2E485D)
                    self._splash.append(backdrop)
                    self._splash.append(label.Label(terminalio.FONT, text="COWS SCATTERED", color=0xFFE29B, scale=2, x=34, y=95))
                    self._splash.append(label.Label(terminalio.FONT, text="Try again — " + str(lives) + " ranch stars left", color=0xFFFFFF, x=28, y=125))
                    time.sleep(1.2)
        save_high_score("/cows.txt", self._HighScore)
        self._clear()
        return [True, self._HighScore]
