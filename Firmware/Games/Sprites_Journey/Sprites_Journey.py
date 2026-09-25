# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Sprite's Journey — a compact, asset-free platformer for KeyBoy.

Controls: LEFT/RIGHT move, A jumps, B sends a short magic burst.  B can hurt
bosses only while Sprite is close enough; UP + DOWN exits to the launcher.
"""

import time
import displayio
from adafruit_display_text import label
import terminalio
from GameMenu import PauseMenu, save_high_score


SCREEN_W = 240
SCREEN_H = 240
FLOOR_Y = 218
PLAYER_W = 12
PLAYER_H = 14

# x, y, width.  Levels are intentionally short: each is a readable 240px room.
LEVELS = (
    ((0, FLOOR_Y, 240), (24, 176, 44), (92, 146, 46), (170, 180, 42)),
    ((0, FLOOR_Y, 240), (20, 184, 32), (74, 154, 30), (126, 124, 30), (180, 154, 38)),
    ((0, FLOOR_Y, 240), (22, 174, 40), (86, 142, 42), (162, 174, 48)),
    ((0, FLOOR_Y, 240), (16, 184, 26), (58, 151, 27), (106, 177, 26), (148, 142, 28), (196, 166, 28)),
    ((0, FLOOR_Y, 240), (24, 164, 48), (104, 186, 30), (148, 151, 34), (196, 120, 28)),
    ((0, FLOOR_Y, 240), (18, 181, 35), (78, 143, 43), (160, 171, 54)),
    ((0, FLOOR_Y, 240), (14, 160, 27), (57, 188, 28), (103, 145, 28), (148, 174, 28), (194, 132, 31)),
    ((0, FLOOR_Y, 240), (20, 181, 38), (86, 152, 33), (144, 120, 34), (196, 160, 30)),
    ((0, FLOOR_Y, 240), (20, 184, 36), (72, 150, 40), (145, 181, 32), (190, 142, 36)),
)

# level: (x, y, width, height); mini boss level 3/6, final boss level 9.
HAZARDS = ((), ((112, 211, 16, 7),), (), ((90, 211, 15, 7), (177, 211, 15, 7)),
           ((76, 211, 18, 7),), (), ((128, 211, 17, 7),), ((119, 211, 17, 7),), ())
BOSSES = (None, None, (184, 188, 22, 30, 3, "BRAMBLE"), None, None,
          (184, 188, 22, 30, 4, "SHADE"), None, None, (166, 166, 42, 52, 7, "THE CURSE"))


def _solid(width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette)


def _pixel_art(rows, colors):
    """Turn a short palette-keyed pixel map into a transparent TileGrid."""
    height = len(rows)
    width = len(rows[0])
    bitmap = displayio.Bitmap(width, height, len(colors))
    palette = displayio.Palette(len(colors))
    palette[0] = 0
    palette.make_transparent(0)
    for index in range(1, len(colors)):
        palette[index] = colors[index]
    for y in range(height):
        for x in range(width):
            bitmap[x, y] = int(rows[y][x])
    return displayio.TileGrid(bitmap, pixel_shader=palette)


class SpritesJourney:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B = A_btn, B_btn
        self._U, self._D = Up_btn, Dwn_btn
        self._L, self._R = L_btn, R_btn
        self._pause_menu = PauseMenu(splash, Sel_btn, A_btn, Up_btn, Dwn_btn)
        self._audio = Audio
        self._exit = False
        self._a_was_down = False
        self._b_was_down = False
        self._level = 0
        self._lives = 3

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    def _sprite(self):
        # A tiny pale-blue sprite with a visible empty space where wings will be.
        return _pixel_art(("001111110000", "012222221000", "012333321000", "012333321000",
                           "001233210000", "001222210000", "000122100000", "001222210000",
                           "012122121000", "120122102100", "000100010000", "001100011000",
                           "011000001100", "000000000000"),
                          (0, 0xF6F1D3, 0x71D8F5, 0x203D69))

    def _enemy(self, large=False):
        if large:
            rows = ("0000111111111111110000", "0001222222222222221000", "0012333333333333332100",
                    "0123344333333333443210", "0123333433333343333210", "0123333333333333333210",
                    "0123334333333343333210", "0123333433333334333210", "0123333333333333333210",
                    "0012333333333333332100", "0001223333333333221000", "0000112222222222110000")
        else:
            rows = ("0001111000", "0012222100", "0123333210", "0123433210", "0123333210",
                    "0012332100", "0012222100", "0102112010", "1001001001", "0000000000")
        return _pixel_art(rows, (0, 0xD6AA62, 0x642B4A, 0xF06A6A, 0x241533))

    def _message(self, title, subtitle, color=0xFFFFFF):
        self._clear()
        self._splash.append(_solid(SCREEN_W, SCREEN_H, 0x18234A))
        title_label = label.Label(terminalio.FONT, text=title, color=color, scale=2, x=18, y=92)
        subtitle_label = label.Label(terminalio.FONT, text=subtitle, color=0xC5D8FF, x=18, y=125)
        self._splash.append(title_label)
        self._splash.append(subtitle_label)

    def _wait_for_a(self):
        while self._A.value == 0:
            time.sleep(0.03)
        while self._A.value:
            time.sleep(0.03)
        time.sleep(0.15)

    @staticmethod
    def _overlap(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _setup_level(self):
        self._clear()
        self._splash.append(_solid(SCREEN_W, SCREEN_H, 0x17254A))
        # A handful of fixed stars gives each room depth without allocating art files.
        for x, y in ((14, 24), (52, 54), (97, 22), (143, 63), (208, 35), (225, 96), (37, 109)):
            star = _solid(2, 2, 0xA7D9FF)
            star.x, star.y = x, y
            self._splash.append(star)
        platforms = []
        for x, y, width in LEVELS[self._level]:
            tile = _solid(width, 8, 0x5AA66B if y == FLOOR_Y else 0x4C8C98)
            tile.x, tile.y = x, y
            self._splash.append(tile)
            platforms.append((x, y, width))
        for x, y, width, height in HAZARDS[self._level]:
            spike = _solid(width, height, 0xE8786D)
            spike.x, spike.y = x, y
            self._splash.append(spike)
        player = self._sprite()
        player.x, player.y = 16, FLOOR_Y - PLAYER_H
        self._splash.append(player)
        boss_data = BOSSES[self._level]
        boss = None
        health = 0
        if boss_data:
            bx, by, bw, bh, health, name = boss_data
            boss = self._enemy(bw > 25)
            boss.x, boss.y = bx, by
            self._splash.append(boss)
            boss_label = label.Label(terminalio.FONT, text=name + " " + str(health), color=0xFFCF70, x=94, y=13)
            self._splash.append(boss_label)
        else:
            boss_label = None
        hud = label.Label(terminalio.FONT, text="LIVES " + str(self._lives) + "   " + str(self._level + 1) + "/9", color=0xFFFFFF, x=8, y=13)
        self._splash.append(hud)
        return player, platforms, boss, boss_data, health, boss_label, hud

    def _lose_life(self):
        self._lives -= 1
        if self._lives <= 0:
            self._message("THE CURSE STIRS", "Press A to begin again", 0xFF8D85)
            self._wait_for_a()
            self._level, self._lives = 0, 3

    def _play_level(self):
        player, platforms, boss, boss_data, boss_hp, boss_label, hud = self._setup_level()
        velocity_y = 0
        facing = 1
        boss_direction = -1
        last_boss_move = time.monotonic()
        while not self._exit:
            now = time.monotonic()
            move_x = 0
            if self._L.value == 0:
                move_x, facing = -3, -1
            elif self._R.value == 0:
                move_x, facing = 3, 1
            a_down = self._A.value == 0
            b_down = self._B.value == 0
            on_ground = False
            for px, py, pw in platforms:
                if player.y + PLAYER_H >= py - 2 and player.y + PLAYER_H <= py + 5 and player.x + PLAYER_W > px and player.x < px + pw:
                    on_ground = True
                    break
            if a_down and not self._a_was_down and on_ground:
                velocity_y = -10
                self._audio.play("jump")
            self._a_was_down = a_down
            player.x = max(0, min(SCREEN_W - PLAYER_W, player.x + move_x))
            old_y = player.y
            velocity_y = min(8, velocity_y + 1)
            player.y += velocity_y
            if velocity_y >= 0:
                for px, py, pw in platforms:
                    if old_y + PLAYER_H <= py and player.y + PLAYER_H >= py and player.x + PLAYER_W > px and player.x < px + pw:
                        player.y = py - PLAYER_H
                        velocity_y = 0
                        break
            if boss and now - last_boss_move > 0.16:
                boss.x += boss_direction * (3 if boss_data[2] > 25 else 2)
                if boss.x < 128 or boss.x + boss_data[2] > 228:
                    boss_direction *= -1
                last_boss_move = now
            if b_down and not self._b_was_down and boss:
                distance = boss.x - (player.x + PLAYER_W // 2)
                if abs(distance) < 48 and (distance * facing) >= -10 and abs(boss.y - player.y) < 42:
                    boss_hp -= 1
                    self._audio.play("shoot")
                    boss_label.text = boss_data[5] + " " + str(max(0, boss_hp))
                    if boss_hp <= 0:
                        self._audio.play("win")
                        self._splash.remove(boss)
                        self._splash.remove(boss_label)
                        boss = None
            self._b_was_down = b_down
            hit = player.y > SCREEN_H
            for hx, hy, hw, hh in HAZARDS[self._level]:
                hit = hit or self._overlap(player.x, player.y, PLAYER_W, PLAYER_H, hx, hy, hw, hh)
            if boss and self._overlap(player.x, player.y, PLAYER_W, PLAYER_H, boss.x, boss.y, boss_data[2], boss_data[3]):
                hit = True
            if hit:
                self._audio.play("hit")
                self._lose_life()
                return False
            # Goal: right edge, only after the level's guardian has fallen.
            if player.x > 222 and boss is None:
                self._audio.play("collect")
                save_high_score("/sprites_journey.txt", self._level + 1)
                return True
            if self._pause_menu.pressed():
                if self._pause_menu.open("SPRITE'S JOURNEY", self._level + 1, "/sprites_journey.txt"):
                    self._exit = True
            if self._D.value == 0 and self._U.value == 0:  # deliberate two-button quit gesture
                self._exit = True
            hud.text = "LIVES " + str(self._lives) + "   " + str(self._level + 1) + "/9"
            time.sleep(0.028)
        return False

    def Game(self):
        self._message("SPRITE'S JOURNEY", "A jump  B magic  L/R move", 0xBCEAFF)
        self._wait_for_a()
        while not self._exit:
            if self._play_level():
                self._level += 1
                if self._level >= len(LEVELS):
                    self._message("WINGS AWAKEN", "Sprite is free!  Press A", 0xFFE58C)
                    self._wait_for_a()
                    self._level, self._lives = 0, 3
                else:
                    self._message("MAGIC FOUND", "Press A for the next path", 0xBCEAFF)
                    self._wait_for_a()
        self._clear()
        return True
