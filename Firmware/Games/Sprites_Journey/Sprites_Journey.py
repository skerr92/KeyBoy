# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Sprite's Journey — a compact, asset-free platformer for KeyBoy.

Controls: LEFT/RIGHT move, A jumps, B sends a short magic burst.  B can hurt
guardians from range; collect every spark to open the gate. UP + DOWN exits.
"""

import time
import displayio
from adafruit_display_text import label
import terminalio
from GameMenu import PauseMenu, save_high_score
from KeyBoyArcade import Scenery, actor, rect


SCREEN_W = 240
SCREEN_H = 240
FLOOR_Y = 218
PLAYER_W = 16
PLAYER_H = 22

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
        self._scenery = None

    def _clear(self):
        while len(self._splash):
            self._splash.pop()

    def _sprite(self):
        return actor('hero', PLAYER_W, PLAYER_H)

    def _enemy(self, large=False):
        return actor('guardian', 42 if large else 22, 52 if large else 30)

    def _message(self, title, subtitle, color=0xFFFFFF):
        self._clear()
        self._splash.append(_solid(SCREEN_W, SCREEN_H, 0x18234A))
        title_label = label.Label(terminalio.FONT, text=title, color=color, scale=2, x=18, y=92)
        subtitle_label = label.Label(terminalio.FONT, text=subtitle, color=0xC5D8FF, x=18, y=125)
        self._splash.append(title_label)
        self._splash.append(subtitle_label)

    def _wait_for_a(self):
        while self._A.value == 0:
            if not self._U.value and not self._D.value:self._exit=True;return
            time.sleep(0.03)
        while self._A.value:
            if not self._U.value and not self._D.value:self._exit=True;return
            time.sleep(0.03)
        time.sleep(0.15)

    @staticmethod
    def _overlap(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _setup_level(self):
        self._clear()
        if self._scenery is None:
            self._scenery = Scenery()
        self._scenery.draw('journey', self._level)
        platforms = list(LEVELS[self._level])
        for x, y, width in platforms:
            rect(self._scenery,x,y,width,8,10)
            rect(self._scenery,x,y,width,2,8)
            for xx in range(x+3,x+width-2,7):
                rect(self._scenery,xx,y+3,3,2,12)
        for x,y,width,height in HAZARDS[self._level]:
            for xx in range(x,x+width,5):
                for h in range(height):
                    rect(self._scenery,xx+2-h//3,y+h,1+2*(h//3),1,15)
        # An actual exit gate and collectible route replace the invisible edge.
        rect(self._scenery,223,185,15,33,3)
        rect(self._scenery,227,189,7,29,4)
        self._scenery.attach(self._splash)
        self._sparks = []
        for x,y,width in platforms[1:]:
            spark=actor('spark',8,10)
            spark.x,spark.y=x+width//2-4,y-13
            self._splash.append(spark)
            self._sparks.append(spark)
        self._bolts=[]
        for _ in range(3):
            bolt=actor('spark',8,6);bolt.hidden=True
            self._splash.append(bolt)
            self._bolts.append([bolt,0])
        self._thorns=[]
        for _ in range(3):
            thorn=actor('spark',7,7);thorn.pixel_shader[13]=0xF18D72;thorn.hidden=True
            self._splash.append(thorn)
            self._thorns.append([thorn,-4])
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
            boss_label = label.Label(terminalio.FONT, text=name + " " + str(health), color=0xFFCF70, x=105, y=13)
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
        last_boss_shot = last_boss_move
        last_ground = last_boss_move
        jump_until = 0
        last_magic = -1
        self._room_hp = 3
        hurt_until = 0
        hint = label.Label(terminalio.FONT, text="Gather sparks / A jump / B magic", color=0xEDD49B, x=5, y=33)
        self._splash.append(hint)
        while not self._exit:
            now = time.monotonic()
            move_x = 0
            if self._L.value == 0:
                move_x, facing = -3, -1
            elif self._R.value == 0:
                move_x, facing = 3, 1
            player[0]=int(now*9)%2 if move_x else 0
            player.flip_x=facing<0
            a_down = self._A.value == 0
            b_down = self._B.value == 0
            on_ground = False
            for px, py, pw in platforms:
                if player.y + PLAYER_H >= py - 2 and player.y + PLAYER_H <= py + 5 and player.x + PLAYER_W > px and player.x < px + pw:
                    on_ground = True
                    break
            if on_ground:
                last_ground = now
            if a_down and not self._a_was_down:
                jump_until = now + 0.14
            if jump_until > now and now - last_ground < 0.10:
                velocity_y = -12
                jump_until = 0
                last_ground = -1
                self._audio.play("jump")
            self._a_was_down = a_down
            player.x = max(0, min(SCREEN_W - PLAYER_W, player.x + move_x))
            old_y = player.y
            velocity_y = min(3 if a_down and self._level >= 3 else 8, velocity_y + 1)
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
            enemy_hit=False
            if boss:
                boss_label.color=0xF18D72 if now-last_boss_shot>1 else 0xFFCF70
                if now-last_boss_shot>1.4:
                    for thorn in self._thorns:
                        if thorn[0].hidden:
                            thorn[0].hidden=False
                            thorn[0].x,thorn[0].y=boss.x+boss_data[2]//2,boss.y+boss_data[3]-14
                            thorn[1]=-4 if player.x<boss.x else 4
                            last_boss_shot=now
                            break
            for thorn in self._thorns:
                sprite=thorn[0]
                if not boss:sprite.hidden=True
                if sprite.hidden:continue
                sprite.x+=thorn[1]
                if sprite.x<0 or sprite.x>233:sprite.hidden=True
                elif self._overlap(player.x,player.y,PLAYER_W,PLAYER_H,sprite.x,sprite.y,7,7):
                    sprite.hidden=True;enemy_hit=True
            if b_down and now - last_magic > 0.32:
                for bolt in self._bolts:
                    if bolt[0].hidden:
                        bolt[0].x,bolt[0].y=player.x+4,player.y+7
                        bolt[0].hidden=False
                        bolt[1]=facing*6
                        last_magic=now
                        self._audio.play('shoot')
                        break
            for bolt in self._bolts:
                sprite=bolt[0]
                if sprite.hidden:continue
                sprite.x+=bolt[1]
                if sprite.x<0 or sprite.x>232:
                    sprite.hidden=True
                elif boss and self._overlap(sprite.x,sprite.y,8,6,boss.x,boss.y,boss_data[2],boss_data[3]):
                    sprite.hidden=True
                    boss_hp-=1
                    boss_label.text=boss_data[5]+' '+str(max(0,boss_hp))
                    self._audio.play('hit')
                    if boss_hp<=0:
                        self._audio.play('win')
                        self._splash.remove(boss)
                        self._splash.remove(boss_label)
                        boss=None
                        self._lives=min(5,self._lives+1)
            for spark in self._sparks:
                if not spark.hidden and self._overlap(player.x,player.y,PLAYER_W,PLAYER_H,spark.x,spark.y,8,10):
                    spark.hidden=True
                    self._audio.play('collect')
            remaining=sum(1 for spark in self._sparks if not spark.hidden)
            hint_text = ('SPARKS %d / Clear guardian' % remaining if boss else
                         'SPARKS %d / Reach the gate' % remaining) if remaining or boss else 'GATE OPEN! Head right'
            if hint.text != hint_text:hint.text=hint_text
            self._b_was_down = b_down
            hit = player.y > SCREEN_H or enemy_hit
            for hx, hy, hw, hh in HAZARDS[self._level]:
                hit = hit or self._overlap(player.x, player.y, PLAYER_W, PLAYER_H, hx, hy, hw, hh)
            if boss and self._overlap(player.x, player.y, PLAYER_W, PLAYER_H, boss.x, boss.y, boss_data[2], boss_data[3]):
                hit = True
            if hit and now >= hurt_until:
                self._audio.play("hit")
                self._room_hp -= 1
                if self._room_hp <= 0:
                    self._lose_life()
                    return False
                player.x, player.y = 16, FLOOR_Y - PLAYER_H
                velocity_y = 0
                hurt_until = now + 1.2
            player.hidden = now < hurt_until and int(now*10)%2 == 0
            # Goal: right edge, only after the level's guardian has fallen.
            if player.x >= SCREEN_W - PLAYER_W - 2 and boss is None and remaining == 0:
                self._audio.play("collect")
                save_high_score("/sprites_journey.txt", self._level + 1)
                return True
            if self._pause_menu.pressed():
                paused = time.monotonic()
                if self._pause_menu.open("SPRITE'S JOURNEY", self._level + 1, "/sprites_journey.txt"):
                    self._exit = True
                delay=time.monotonic()-paused
                hurt_until+=delay
                last_magic+=delay
                last_boss_move+=delay
                last_boss_shot+=delay
                self._a_was_down=not self._A.value
            if self._D.value == 0 and self._U.value == 0:  # deliberate two-button quit gesture
                self._exit = True
            hud_text = "HP%d *%d %d/9" % (self._room_hp,self._lives,self._level+1)
            if hud.text != hud_text:hud.text=hud_text
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
                    self._message("MAGIC FOUND", "Hold A to glide! Press A" if self._level == 3 else "Find every spark. Press A", 0xBCEAFF)
                    self._wait_for_a()
        self._clear()
        return True
