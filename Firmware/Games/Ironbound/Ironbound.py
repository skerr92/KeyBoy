# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Ironbound — compact procedural turn-based tactics for KeyBoy.

D-pad moves one tile, A attacks an adjacent drone, B waits/guards, SEL saves.
Clear each seeded mission to open its extraction point and earn an upgrade.
"""

import time
import displayio
from adafruit_display_text import label
import terminalio
from GameMenu import PauseMenu


GRID = 8
TILE = 25
ORIGIN_X = 20
ORIGIN_Y = 35


def _solid(width, height, color):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette)


class Ironbound:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B = A_btn, B_btn
        self._U, self._D = Up_btn, Dwn_btn
        self._L, self._R = L_btn, R_btn
        self._pause = PauseMenu(splash, Sel_btn, A_btn, Up_btn, Dwn_btn)
        self._audio = Audio
        self._exit = False
        self._mission, self._hull, self._attack, self._armor = 1, 10, 3, 0
        self._load()

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    def _save(self):
        try:
            save_file = open("/ironbound.sav", "wt")
            save_file.write(",".join(str(value) for value in (self._mission, self._hull, self._attack, self._armor)))
            save_file.close()
        except OSError:
            pass

    def _load(self):
        try:
            save_file = open("/ironbound.sav", "rt")
            values = [int(value) for value in save_file.readline().split(",")]
            save_file.close()
            if len(values) == 4 and 1 <= values[0] <= 8:
                self._mission, self._hull, self._attack, self._armor = values
        except (OSError, ValueError):
            pass

    def _message(self, title, detail, color=0xBFE9FF):
        self._clear()
        self._splash.append(_solid(240, 240, 0x101C31))
        self._splash.append(label.Label(terminalio.FONT, text=title, color=color, scale=2, x=30, y=91))
        self._splash.append(label.Label(terminalio.FONT, text=detail, color=0xE3E9F6, x=17, y=124))

    def _wait_a(self):
        while self._A.value == 0:
            time.sleep(0.03)
        while self._A.value:
            time.sleep(0.03)

    @staticmethod
    def _distance(one, two):
        return abs(one[0] - two[0]) + abs(one[1] - two[1])

    def _cover(self, x, y):
        # Deterministic per-mission terrain: it looks procedural yet keeps all tiles walkable.
        return (x * 5 + y * 9 + self._mission * 3) % 13 in (0, 1)

    def _build_mission_scene(self, player, enemies):
        """Build the board once; turns only move its persistent pieces."""
        self._clear()
        self._splash.append(_solid(240, 240, 0x14213B))
        for y in range(GRID):
            for x in range(GRID):
                color = 0x2D4862 if self._cover(x, y) else 0x20344E
                tile = _solid(TILE - 2, TILE - 2, color)
                tile.x, tile.y = ORIGIN_X + x * TILE + 1, ORIGIN_Y + y * TILE + 1
                self._splash.append(tile)
        extraction = _solid(TILE - 5, TILE - 5, 0x5D526D)
        extraction.x, extraction.y = ORIGIN_X + 7 * TILE + 3, ORIGIN_Y + 3
        self._splash.append(extraction)
        for enemy in enemies:
            drone = _solid(15, 15, 0xE86D69)
            drone.x, drone.y = ORIGIN_X + enemy[0] * TILE + 5, ORIGIN_Y + enemy[1] * TILE + 5
            self._splash.append(drone)
            enemy.append(drone)
        mech = _solid(17, 17, 0x8CD6E6)
        self._splash.append(mech)
        mission_name = "COMMANDER" if self._mission == 8 else "SECTOR " + str(self._mission)
        hud = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=8, y=13)
        self._splash.append(hud)
        self._splash.append(label.Label(terminalio.FONT, text="D-pad move  A strike  B guard", color=0xC6D8EE, x=12, y=225))
        self._sync_mission_scene(player, enemies, mech, extraction, hud)
        return mech, extraction, hud

    def _sync_mission_scene(self, player, enemies, mech, extraction, hud):
        mech.x, mech.y = ORIGIN_X + player[0] * TILE + 4, ORIGIN_Y + player[1] * TILE + 4
        for enemy in enemies:
            enemy[3].x, enemy[3].y = ORIGIN_X + enemy[0] * TILE + 5, ORIGIN_Y + enemy[1] * TILE + 5
        extraction.pixel_shader[0] = 0x70D8A3 if not enemies else 0x5D526D
        mission_name = "COMMANDER" if self._mission == 8 else "SECTOR " + str(self._mission)
        hud.text = mission_name + "  H" + str(self._hull) + "  D" + str(len(enemies))

    def _enemy_turn(self, player, enemies):
        for enemy in enemies:
            if self._distance(player, enemy) == 1:
                self._hull -= max(1, 2 + self._mission // 3 - self._armor)
                self._audio.play("hit")
                continue
            dx = 1 if player[0] > enemy[0] else -1 if player[0] < enemy[0] else 0
            dy = 1 if player[1] > enemy[1] else -1 if player[1] < enemy[1] else 0
            proposed = [enemy[0] + dx, enemy[1] + dy]
            occupied = any(proposed[0] == other[0] and proposed[1] == other[1] for other in enemies)
            if 0 <= proposed[0] < GRID and 0 <= proposed[1] < GRID and proposed != player and not occupied:
                enemy[0], enemy[1] = proposed

    def _upgrade(self):
        # Alternating upgrades make mission rewards distinct while avoiding a heavy shop UI.
        if self._mission % 3 == 1:
            self._attack += 1
            return "Weapon core +1"
        if self._mission % 3 == 2:
            self._armor += 1
            return "Plating +1"
        self._hull += 3
        return "Hull +3"

    def _mission_run(self):
        player = [0, 7]
        count = min(5, 1 + self._mission // 2)
        enemies = []
        for number in range(count):
            enemies.append([6 - number % 3, 1 + (number * 2 + self._mission) % 6, 3 + self._mission + (4 if self._mission == 8 else 0)])
        mech, extraction, hud = self._build_mission_scene(player, enemies)
        last_move = 0
        a_was = False
        b_was = False
        while not self._exit:
            self._sync_mission_scene(player, enemies, mech, extraction, hud)
            extraction_open = not enemies
            now = time.monotonic()
            dx, dy = 0, 0
            if self._L.value == 0: dx = -1
            elif self._R.value == 0: dx = 1
            elif self._U.value == 0: dy = -1
            elif self._D.value == 0: dy = 1
            took_turn = False
            if (dx or dy) and now - last_move > 0.15:
                proposed = [player[0] + dx, player[1] + dy]
                if 0 <= proposed[0] < GRID and 0 <= proposed[1] < GRID and not any(proposed == enemy[:2] for enemy in enemies):
                    player = proposed
                    took_turn = True
                last_move = now
            a_down, b_down = self._A.value == 0, self._B.value == 0
            if a_down and not a_was:
                for enemy in enemies[:]:
                    if self._distance(player, enemy) == 1:
                        enemy[2] -= self._attack
                        self._audio.play("shoot")
                        if enemy[2] <= 0:
                            self._splash.remove(enemy[3])
                            enemies.remove(enemy)
                        took_turn = True
                        break
            if b_down and not b_was:
                self._hull = min(18, self._hull + 1)
                self._audio.play("support")
                took_turn = True
            a_was, b_was = a_down, b_down
            if extraction_open and player == [7, 0]:
                return True
            if took_turn:
                self._enemy_turn(player, enemies)
            if self._hull <= 0:
                self._audio.play("lose")
                self._hull = 10 + self._armor * 2
                return False
            if self._pause.pressed():
                if self._pause.open("IRONBOUND", self._mission * 100 + self._attack, save_callback=self._save):
                    self._exit = True
                    return False
            time.sleep(0.035)
        return False

    def Game(self):
        self._exit = False
        self._message("IRONBOUND", "A quiet war of steel. Press A")
        self._wait_a()
        while not self._exit:
            won = self._mission_run()
            if self._exit:
                break
            if won:
                reward = self._upgrade()
                self._audio.play("upgrade")
                if self._mission == 8:
                    self._message("IRONBOUND FREE", "The commander falls. Press A", 0xFFE19C)
                    self._wait_a()
                    self._mission, self._hull, self._attack, self._armor = 1, 10, 3, 0
                else:
                    self._mission += 1
                    self._message("SECTOR SECURED", reward + ". Press A", 0xA9F3C3)
                    self._wait_a()
            else:
                self._message("MECH DISABLED", "Mission restarts. Press A", 0xFFAAA3)
                self._wait_a()
        self._clear()
        return True
