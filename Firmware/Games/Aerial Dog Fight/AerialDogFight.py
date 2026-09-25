# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Aerial Dog Fight — an asset-free top-down arcade dogfight for KeyBoy.

Controls: D-pad flies, A fires, B boosts, and UP + DOWN returns to the menu.
"""

import random
import time
import displayio
from adafruit_display_text import label
import terminalio
from GameMenu import PauseMenu, save_high_score

SCREEN_W = 240
SCREEN_H = 240


def _solid(width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette)


def _art(rows, colors):
    bitmap = displayio.Bitmap(len(rows[0]), len(rows), len(colors))
    palette = displayio.Palette(len(colors))
    palette[0] = 0
    palette.make_transparent(0)
    for index in range(1, len(colors)):
        palette[index] = colors[index]
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            bitmap[x, y] = int(value)
    return displayio.TileGrid(bitmap, pixel_shader=palette)


def _player_plane():
    return _art(("00000100000", "00001200000", "00012220000", "00122222000",
                 "01223332210", "12223332221", "00122222000", "00012121000",
                 "00012021000", "00010001000", "00000000000"),
                (0, 0xD9F6FF, 0x53B9D8, 0x25476B))


def _enemy_plane(ace=False):
    if ace:
        rows = ("00000300000", "00003330000", "00032223000", "00322222300",
                "03221112230", "32221112223", "00322222300", "00032223000",
                "00003030000", "00003030000", "00000000000")
        return _art(rows, (0, 0xF7D887, 0xD7645C, 0x662B44))
    return _art(("00000300000", "00003330000", "00032223000", "00322222300",
                 "03221112230", "32221112223", "00322222300", "00030303000",
                 "00030003000", "00000000000"),
                (0, 0xF4D27F, 0xDB665C, 0x612740))


class AerialDogFight:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B = A_btn, B_btn
        self._U, self._D = Up_btn, Dwn_btn
        self._L, self._R = L_btn, R_btn
        self._pause_menu = PauseMenu(splash, Sel_btn, A_btn, Up_btn, Dwn_btn)
        self._audio = Audio
        self._exit = False
        self._last_shot = 0

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    def _message(self, heading, detail, color=0xB8E7FF):
        self._clear()
        self._splash.append(_solid(SCREEN_W, SCREEN_H, 0x10213D))
        self._splash.append(label.Label(terminalio.FONT, text=heading, color=color, scale=2, x=24, y=90))
        self._splash.append(label.Label(terminalio.FONT, text=detail, color=0xD5E6FF, x=18, y=123))

    def _wait_for_a(self):
        while self._A.value == 0:
            time.sleep(0.03)
        while self._A.value:
            time.sleep(0.03)
        time.sleep(0.12)

    @staticmethod
    def _hit(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _add_bullet(self, bullets, x, y, velocity, color):
        if len(bullets) >= 8:
            return
        sprite = _solid(3, 7, color)
        sprite.x, sprite.y = x, y
        self._splash.append(sprite)
        bullets.append([sprite, velocity])

    def _spawn_enemy(self, enemies, wave, ace=False):
        plane = _enemy_plane(ace)
        plane.x = random.randint(10, 218)
        plane.y = -12
        enemies.append([plane, random.choice((-1, 1)), 1 + wave // 3, 5 if ace else 1,
                        time.monotonic() + random.uniform(0.8, 1.8), ace])
        self._splash.append(plane)

    def _run(self):
        self._clear()
        self._splash.append(_solid(SCREEN_W, SCREEN_H, 0x10213D))
        for x, y in ((18, 30), (61, 78), (112, 37), (161, 93), (211, 48), (36, 160), (194, 182)):
            star = _solid(2, 2, 0x88BDE8)
            star.x, star.y = x, y
            self._splash.append(star)
        player = _player_plane()
        player.x, player.y = 115, 190
        self._splash.append(player)
        score, hull, wave, spawned = 0, 3, 1, 0
        enemies, player_bullets, enemy_bullets = [], [], []
        hud = label.Label(terminalio.FONT, text="S 0  H 3  W 1", color=0xFFFFFF, x=6, y=12)
        self._splash.append(hud)
        last_spawn = 0
        ace_spawned = False
        while not self._exit:
            now = time.monotonic()
            speed = 4 if self._B.value == 0 else 2
            if self._L.value == 0:
                player.x = max(0, player.x - speed)
            if self._R.value == 0:
                player.x = min(SCREEN_W - 11, player.x + speed)
            if self._U.value == 0:
                player.y = max(24, player.y - speed)
            if self._D.value == 0:
                player.y = min(SCREEN_H - 12, player.y + speed)
            a_down = self._A.value == 0
            if a_down and now - self._last_shot > 0.12:
                self._add_bullet(player_bullets, player.x + 4, player.y - 6, -7, 0xA6F4FF)
                self._audio.play("shoot")
                self._last_shot = now
            target_spawns = 4 + wave
            if spawned < target_spawns and now - last_spawn > 0.75:
                self._spawn_enemy(enemies, wave)
                spawned += 1
                last_spawn = now
            if wave == 4 and not ace_spawned and spawned >= target_spawns and not enemies:
                self._spawn_enemy(enemies, wave, True)
                ace_spawned = True
            for bullet in player_bullets[:]:
                bullet[0].y += bullet[1]
                if bullet[0].y < 20:
                    self._splash.remove(bullet[0])
                    player_bullets.remove(bullet)
                    continue
                for enemy in enemies[:]:
                    if self._hit(bullet[0].x, bullet[0].y, 3, 7, enemy[0].x, enemy[0].y, 11, 11):
                        self._splash.remove(bullet[0])
                        player_bullets.remove(bullet)
                        enemy[3] -= 1
                        if enemy[3] <= 0:
                            self._audio.play("collect")
                            self._splash.remove(enemy[0])
                            enemies.remove(enemy)
                            score += 500 if enemy[5] else 100
                        break
            for enemy in enemies[:]:
                enemy[0].x += enemy[1]
                enemy[0].y += enemy[2]
                if enemy[0].x < 2 or enemy[0].x > 227:
                    enemy[1] *= -1
                if now >= enemy[4]:
                    self._add_bullet(enemy_bullets, enemy[0].x + 4, enemy[0].y + 10, 4, 0xFF9B72)
                    enemy[4] = now + (0.55 if enemy[5] else random.uniform(1.1, 2.1))
                if enemy[0].y > SCREEN_H:
                    self._splash.remove(enemy[0])
                    enemies.remove(enemy)
            for bullet in enemy_bullets[:]:
                bullet[0].y += bullet[1]
                if bullet[0].y > SCREEN_H:
                    self._splash.remove(bullet[0])
                    enemy_bullets.remove(bullet)
                    continue
                if self._hit(bullet[0].x, bullet[0].y, 3, 7, player.x, player.y, 11, 11):
                    self._splash.remove(bullet[0])
                    enemy_bullets.remove(bullet)
                    hull -= 1
                    self._audio.play("hit")
            for enemy in enemies[:]:
                if self._hit(player.x, player.y, 11, 11, enemy[0].x, enemy[0].y, 11, 11):
                    self._splash.remove(enemy[0])
                    enemies.remove(enemy)
                    hull -= 1
                    self._audio.play("hit")
            if hull <= 0:
                self._audio.play("lose")
                save_high_score("/dogfight.txt", score)
                return False
            if wave < 4 and spawned >= target_spawns and not enemies:
                wave += 1
                spawned = 0
            if ace_spawned and not enemies:
                self._audio.play("win")
                save_high_score("/dogfight.txt", score)
                return True
            hud.text = "S " + str(score) + "  H " + str(hull) + "  W " + str(wave)
            if self._pause_menu.pressed():
                if self._pause_menu.open("DOG FIGHT", score, "/dogfight.txt"):
                    self._exit = True
            if self._U.value == 0 and self._D.value == 0:
                self._exit = True
            time.sleep(0.027)
        return None

    def Game(self):
        self._exit = False
        self._message("AERIAL DOG FIGHT", "D-pad fly  A fire  B boost")
        self._wait_for_a()
        while not self._exit:
            result = self._run()
            if result is None:
                break
            if result:
                self._message("SKIES CLEARED", "Ace defeated!  Press A", 0xFFE28A)
            else:
                self._message("PLANE DOWN", "Press A to sortie again", 0xFF9A91)
            self._wait_for_a()
        self._clear()
        return True
