# SPDX-FileCopyrightText: Copyright (c) 2023 Seth Kerr
#
# SPDX-License-Identifier: MIT

import time, displayio
from digitalio import DigitalInOut, Direction
from adafruit_display_text import label
import terminalio, adafruit_imageload, random

__version__ = "0.0.0+auto.0"
__repo__ = ""

class LooseCows:

    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn):
        self._splash = splash
        self._A = A_btn
        self._B = B_btn
        self._U = Up_btn
        self._D = Dwn_btn
        self._L = L_btn
        self._R = R_btn
        self._exit = False
        self._pause = False
        self._menu_bitmap = displayio.Bitmap(120,120,1)
        self._color_palette = displayio.Palette(1)
        self._color_palette[0] = 0xFFFFFF #white
        self.menu_group = displayio.Group()
        self._menu = displayio.TileGrid(self._menu_bitmap, pixel_shader=self._color_palette,
                                        x=60, y=60)
        self._continue_group = displayio.Group(scale=2, x=80, y=70)
        self._continue_text = "Continue"
        self._cont_txt_area = label.Label(terminalio.FONT, text=self._continue_text, color=0x000000)
        self._continue_group.append(self._cont_txt_area)
        self._exit_group = displayio.Group(scale=2, x=80, y=90)
        self._exit_text = "Exit"
        self._exit_txt_area = label.Label(terminalio.FONT, text=self._exit_text, color=0xFF0000)
        self._exit_group.append(self._exit_txt_area)
        self.menu_group.append(self._menu)
        self.menu_group.append(self._continue_group)
        self.menu_group.append(self._exit_group)
        self._select = displayio.Bitmap(10,10,1)
        self._select_palette = displayio.Palette(1)
        self._select_palette[0] = 0x000000
        self._select_sprite = displayio.TileGrid(self._select, pixel_shader=self._select_palette,
                                                 x=65, y=70)
        self._select_pos = 0
        self.menu_group.append(self._select_sprite)
        self.farmer, self.palette = adafruit_imageload.load("/lib/Loose_Cows/farmer sprites_16b2.gif",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)

        self.field, self.fpalette = adafruit_imageload.load("/lib/Loose_Cows/background_sheet.gif",
                                                    bitmap=displayio.Bitmap,
                                                    palette = displayio.Palette)

    def TearDownGame(self):
        while len(self._splash) > 0:
            print("tearing down game")
            self._splash.pop()

    def ToggleMenu(self):
        if self._pause == True:
            self._splash.append(self.menu_group)
        if self._pause == False:
            self._splash.remove(self.menu_group)

    def Game(self):
        self._exit = False
        background = displayio.TileGrid(self.field, pixel_shader=self.fpalette,
                                        width = 15,
                                        height = 15,
                                        tile_width = 16,
                                        tile_height = 16)

        self._splash.append(background)

        background[0,0] = 0
        background[14,0] = 2
        background[0,14] = 6
        background[14,14] = 8

        for x in range(1,14):
            background[x,0] = 1
            background[x,14] = 7
            
        for y in range(1,14):
            background[0,y] = 3
            background[14,y] = 5
            
        for x in range(1,14):
            for y in range(1,14):
                background[x,y] = 4

        sprite = displayio.TileGrid(self.farmer, pixel_shader=self.palette,
                                    width = 1,
                                    height = 1,
                                    tile_width = 16,
                                    tile_height = 16,
                                    x=110, y=110)
        self._splash.append(sprite)

        x_rand = random.randint(20,220)
        y_rand = random.randint(20,220)

        cow_sprite = displayio.TileGrid(self.farmer, pixel_shader=self.palette, 
                                    width = 1,
                                    height = 1,
                                    tile_width = 16,
                                    tile_height = 16,
                                    x=x_rand, y=y_rand)
        cow_sprite[0] = 3
        self._splash.append(cow_sprite)

        points = 0
        timeleft = 10
        # Draw a label
        text_group = displayio.Group(scale=2, x=140, y=30)
        text = "COWS: "
        tg2 = displayio.Group(scale=2, x=200, y=30)
        t2 = str(points)
        tg3 = displayio.Group(scale=2, x=20, y=30)
        t3 = str(timeleft)
        text_area = label.Label(terminalio.FONT, text=text, color=0x000000)
        t2_area = label.Label(terminalio.FONT, text=t2, color=0x000000)
        t3_area = label.Label(terminalio.FONT, text=t3, color=0x000000)
        text_group.append(text_area)  # Subgroup for text scaling
        tg2.append(t2_area)
        tg3.append(t3_area)
        self._splash.append(text_group)
        self._splash.append(tg2)
        self._splash.append(tg3)

        previous_monotonic = time.monotonic()

        while self._exit == False:
            if self._pause == False:
                if self._U.value == 0:
                    sprite[0] = 0
                    if sprite.y == 10:
                        sprite.y = 220
                    else:
                        sprite.y = sprite.y - 4
                if self._D.value == 0:
                    sprite[0] = 0
                    if sprite.y == 220:
                        sprite.y = 10
                    else:
                        sprite.y = sprite.y + 4
                if self._R.value == 0:
                    sprite[0] = 2
                    if sprite.x == 220:
                        sprite.x = 10
                    else:
                        sprite.x = sprite.x + 4
                if self._L.value == 0:
                    sprite[0] = 1
                    if sprite.x == 10:
                        sprite.x = 220
                    else:
                        sprite.x = sprite.x - 4
                if self._A.value == 0:
                    self._pause = True
                    self.ToggleMenu()
                    time.sleep(0.5)
                if abs(sprite.x - cow_sprite.x) < 7 and abs(sprite.y - cow_sprite.y) < 7:
                    cow_sprite.x = random.randint(20,220)
                    cow_sprite.y = random.randint(20,220)
                    points = points + 1
                    if points < 10:
                        timeleft = 10
                    elif points < 25:
                        timeleft = 7
                    elif points < 35:
                        timeleft = 5
                    elif points < 50:
                        timeleft = 3
                    t2_area.text = str(points)
                    t3_area.text = str(timeleft)
                time.sleep(0.05)
                if (time.monotonic() - previous_monotonic) >= 1:
                    if timeleft == 0:
                        timeleft = 10
                        points = 0
                        sprite.x = 110
                        sprite.y = 110
                        cow_sprite.x = random.randint(20,220)
                        cow_sprite.y = random.randint(20,220)
                        t3_area.text = str(timeleft)
                        t2_area.text = str(points)
                    else:
                        timeleft = timeleft - 1
                        previous_monotonic = time.monotonic()
                        t3_area.text = str(timeleft)
            elif self._pause == True:
                if self._B.value == 0:
                    self._pause = False
                    self.ToggleMenu()
                if self._U.value == 0 or self._D.value == 0:
                    if self._select_pos == 0:
                        self._select_pos = 1
                        self._select_sprite.y = 85
                    elif self._select_pos == 1:
                        self._select_pos = 0
                        self._select_sprite.y = 70
                    time.sleep(0.5)
                if self._A.value == 0:
                    if self._select_pos == 0:
                        self._pause = False
                        self.ToggleMenu()
                    elif self._select_pos == 1:
                        self._pause = False
                        self.ToggleMenu()
                        self._exit = True
        self.TearDownGame()
        return True