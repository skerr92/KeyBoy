# SPDX-FileCopyrightText: Copyright (c) 2023 Seth Kerr
#
# SPDX-License-Identifier: MIT

import time, displayio
from digitalio import DigitalInOut, Direction
from adafruit_display_text import label
import terminalio, adafruit_imageload, random

__version__ = "0.0.0+auto.0"
__repo__ = ""

class AerialDogFight:

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
        self.Fighter, self.palette = adafruit_imageload.load("/lib/Aerial Dog Fight/Fighter Jet.gif",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)
        self.Enemy, self.epalette = adafruit_imageload.load("/lib/Aerial Dog Fight/Enemy Jet.gif",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)

    def TearDownGame(self):
        while len(self._splash) > 0:
            self._splash.pop()

    def ToggleMenu(self):
        if self._pause == True:
            self._splash.append(self.menu_group)
        if self._pause == False:
            self._splash.remove(self.menu_group)
    
    def Game(self):
        self._exit = False

        background = displayio.TileGrid(s)