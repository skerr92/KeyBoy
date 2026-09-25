# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Last Beacon: ship, loadout, drop, objective, extraction, repeat.

A fires (hold to strafe), B deploys selected support, SEL pauses. Menus freeze
mission time. Terrain, actor pools and effects are retained for an entire drop.
"""
import gc
import os
import random
import time
import displayio
import terminalio
from adafruit_display_text import label

# name, objective, biome, objective count, deadline, threat, reward
MISSIONS = (("ASHFALL RELAY", "SALVAGE", 0, 3, 100, 1, 45),
            ("BRACKEN FRONT", "PURGE", 1, 3, 110, 2, 60),
            ("FROST ARRAY", "UPLINK", 2, 2, 120, 2, 65),
            ("CINDER WASTES", "SALVAGE", 0, 4, 100, 3, 80),
            ("LAST TRANSMISSION", "UPLINK", 2, 3, 150, 4, 100))
# name, magazine, reserve, cadence, damage, reload, pellets, speed
WEAPONS = (("CARBINE", 18, 90, 0.16, 2, 1.3, 1, 190),
           ("SCATTERGUN", 6, 36, 0.65, 3, 1.7, 3, 170),
           ("LANCER", 6, 30, 0.48, 6, 1.9, 1, 230))
SUPPORTS = ("ORBITAL", "SENTRY", "RESUPPLY")
OBJECTIVE_POS = ((35, 65), (199, 61), (39, 184), (147, 120))
ROCKS = ((76, 62, 28, 22), (139, 154, 25, 21), (52, 119, 26, 20), (177, 102, 29, 19))
EXTRACT = (198, 193)
ENEMY_LIMIT = 12
SHOT_LIMIT = 20
# Transparent, outline, armor dark/mid/light, steel, visor and warm accents.
INK = (0x000000, 0x111B29, 0x263344, 0x40566A, 0x688297, 0xA9BCC4,
       0xE1EAD8, 0x46BCC0, 0xAEF3DC, 0x6F3547, 0xB75251, 0xF38A58,
       0xF2C66D, 0x354D3A, 0x6D9558, 0xB3C87B)
BIOMES = ((0x211E2B, 0x36303D, 0x4A4149, 0x65535A, 0x876968, 0xAC8780,
           0xDEC3A0, 0x386875, 0x72C9C3, 0x503044, 0x8F434C, 0xD87349,
           0xF6BB6B, 0x3A3A40, 0x73715A, 0xB8A478),
          (0x132A29, 0x213F38, 0x345448, 0x4B6C55, 0x718665, 0xA1A387,
           0xD6D5A4, 0x245761, 0x61ABA0, 0x442E45, 0x78495A, 0xC47C6A,
           0xF2CC7A, 0x253A36, 0x63815B, 0xB0BB78),
          (0x24394F, 0x385469, 0x597586, 0x7E9AA7, 0xADC5CC, 0xCEE0DC,
           0xF0EFD7, 0x35647D, 0x81C5D4, 0x3E354F, 0x6B5470, 0xAA8F98,
           0xF3D68F, 0x304856, 0x668486, 0xAEC5B1))


def _palette(colors=INK, transparent=False):
    p = displayio.Palette(len(colors))
    for i, c in enumerate(colors):
        p[i] = c
    if transparent:
        p.make_transparent(0)
    return p


def _rect(b, x, y, w, h, color):
    for yy in range(max(0, y), min(b.height, y + h)):
        for xx in range(max(0, x), min(b.width, x + w)):
            b[xx, yy] = color


def _oval(b, x, y, w, h, color):
    for yy in range(max(0, y), min(b.height, y + h)):
        for xx in range(max(0, x), min(b.width, x + w)):
            if (2 * (xx - x) - w + 1) ** 2 * h * h + (2 * (yy - y) - h + 1) ** 2 * w * w <= w * w * h * h:
                b[xx, yy] = color


def _grid(b, p, x=0, y=0, **kwargs):
    return displayio.TileGrid(b, pixel_shader=p, x=x, y=y, **kwargs)


def _solid(w, h, color, x=0, y=0):
    return _grid(displayio.Bitmap(w, h, 1), _palette((color,)), x, y)


def _text(group, value, x, y, color=0xE1EAD8):
    obj = label.Label(terminalio.FONT, text=value, x=x, y=y, color=color)
    group.append(obj)
    return obj


def _set(obj, value):
    if obj.text != value:
        obj.text = value


def _place(sprite, x, y):
    x, y = int(x), int(y)
    if sprite.x != x:
        sprite.x = x
    if sprite.y != y:
        sprite.y = y


def _d2(x, y, tx, ty):
    return (x - tx) ** 2 + (y - ty) ** 2


def _unit(x, y):
    length = (x * x + y * y) ** 0.5
    return (x / length, y / length) if length else (0, -1)


def _ship_art():
    b = _StripCanvas(240, 112, 14)
    b.fill(1)
    # Panoramic observation window, orbital limb and pinprick stars.
    _rect(b, 5, 3, 230, 55, 3)
    _rect(b, 8, 5, 224, 49, 1)
    for i in range(38):
        x, y = (i * 67 + 13) % 221 + 10, (i * 19 + 7) % 45 + 7
        _rect(b, x, y, 1, 1, 5 if i % 3 else 7)
    _oval(b, 132, 12, 79, 66, 7)
    _oval(b, 137, 16, 74, 65, 3)
    _oval(b, 143, 21, 67, 62, 2)
    for x, y, w, h in ((158, 22, 21, 9), (179, 35, 19, 12), (150, 44, 18, 11)):
        _oval(b, x, y, w, h, 4)
        _oval(b, x + 3, y + 2, w - 5, h - 5, 3)
    for x in (8, 79, 153, 229):
        _rect(b, x, 4, 3, 52, 4)
    _rect(b, 0, 56, 240, 56, 2)
    for y in range(59, 112, 13):
        _rect(b, 0, y, 240, 1, 3)
        for x in range((y % 2) * 15, 240, 30):
            _rect(b, x, y, 1, 13, 1)
    # Consoles and suspended tactical hologram.
    _rect(b, 80, 51, 67, 30, 1)
    _rect(b, 83, 52, 61, 22, 4)
    _rect(b, 87, 54, 53, 14, 2)
    for x in range(90, 137, 8):
        _rect(b, x, 57, 5, 1, 7)
        _rect(b, x, 61, 3, 2, 8)
    _rect(b, 88, 71, 53, 3, 5)
    _rect(b, 87, 78, 6, 10, 1)
    _rect(b, 135, 78, 6, 10, 1)
    _oval(b, 97, 31, 35, 19, 7)
    _oval(b, 100, 33, 29, 14, 2)
    _rect(b, 112, 30, 2, 22, 8)
    _rect(b, 95, 40, 39, 1, 8)
    # Weapon rack, gun silhouettes and ammo drawers.
    _rect(b, 10, 61, 48, 42, 1)
    _rect(b, 12, 63, 44, 36, 3)
    for y in (68, 78, 88):
        _rect(b, 16, y, 33, 3, 5)
        _rect(b, 19, y + 3, 6, 4, 2)
        _rect(b, 29, y + 2, 5, 4, 1)
        _rect(b, 40, y - 2, 4, 2, 12)
    _rect(b, 12, 100, 44, 3, 4)
    # Armored drop pod: ribs, hatch glass, lit ramp and hazard stripes.
    _rect(b, 174, 51, 50, 50, 1)
    _rect(b, 179, 47, 40, 51, 4)
    _rect(b, 185, 50, 28, 46, 2)
    _rect(b, 189, 55, 20, 30, 1)
    _rect(b, 192, 57, 14, 24, 7)
    _rect(b, 194, 59, 3, 20, 8)
    for y in (55, 67, 79, 91):
        _rect(b, 178, y, 6, 3, 5)
        _rect(b, 214, y, 6, 3, 5)
    _rect(b, 179, 98, 40, 10, 1)
    for x in range(181, 219, 8):
        _rect(b, x, 100, 4, 5, 12)
    _rect(b, 180, 108, 39, 2, 7)
    return b.strips


class _StripCanvas:
    """Small static strips avoid a 23 KB contiguous allocation on fragmented heaps."""
    def __init__(self, width, height, strip_height):
        self.width, self.height, self.strip_height = width, height, strip_height
        self.strips = [displayio.Bitmap(width, strip_height, 16) for _ in range(height // strip_height)]

    def __setitem__(self, position, color):
        x, y = position
        self.strips[y // self.strip_height][x, y % self.strip_height] = color

    def fill(self, color):
        for strip in self.strips:
            strip.fill(color)


def _terrain(biome):
    b = _StripCanvas(240, 190, 19)
    b.fill(1)
    seed = 319 + biome * 77
    for _ in range(1200):
        seed = (seed * 109 + 89) % 65521
        x, y = seed % 240, seed // 240 % 190
        _rect(b, x, y, 2 + seed % 3, 1, 2 if seed % 3 else 0)
        if seed % 19 == 0:
            _rect(b, x + 1, y - 2, 1, 3, 3)
    # Impact craters, broken roads, bunker debris and perimeter ecology.
    for x, y, w in ((14, 73, 25), (110, 21, 29), (91, 137, 24), (192, 121, 34)):
        _oval(b, x, y, w, w // 2, 2)
        _oval(b, x + 3, y + 2, w - 6, w // 2 - 4, 0)
        _rect(b, x + 5, y + 1, w // 2, 1, 3)
    for y in range(6, 184, 10):
        _rect(b, 116 + (y // 30) % 3, y, 16, 6, 2)
        _rect(b, 119, y, 8, 1, 3)
    for x, y, w, h in ROCKS:
        y -= 30
        _oval(b, x - 2, y + h - 7, w + 5, 12, 0)
        _oval(b, x, y, w, h, 2)
        _oval(b, x + 2, y, w - 5, h - 5, 3)
        _oval(b, x + 4, y + 1, w - 11, h - 10, 4)
        _rect(b, x + w // 2, y + 5, 2, h - 9, 1)
        _rect(b, x + 6, y + 4, 6, 1, 5)
    for x, y in ((8, 17), (222, 48), (18, 149), (224, 176), (148, 6)):
        if biome == 1:
            for dx, dy in ((0, 4), (5, 0), (10, 5)):
                _oval(b, x + dx, y + dy, 9, 12, 13)
                _oval(b, x + dx + 1, y + dy, 6, 8, 14)
                _rect(b, x + dx + 3, y + dy + 1, 2, 4, 15)
        elif biome == 2:
            for dx, dy in ((0, 0), (5, 5), (9, -2)):
                _rect(b, x + dx, y + dy, 3, 10, 7)
                _rect(b, x + dx, y + dy, 1, 8, 8)
                _rect(b, x + dx, y + dy, 2, 2, 6)
        else:
            _oval(b, x, y, 14, 8, 9)
            _rect(b, x + 4, y + 3, 8, 1, 11)
            _rect(b, x + 7, y + 4, 5, 1, 12)
    # Wreckage and biome-specific surface patterns remain below moving actors.
    for x, y in ((84, 97), (151, 53)):
        _rect(b, x, y, 15, 8, 0)
        _rect(b, x + 1, y, 12, 5, 3)
        _rect(b, x + 2, y + 1, 3, 2, 5)
        _rect(b, x + 8, y + 1, 4, 1, 4)
        _rect(b, x + 13, y + 5, 5, 2, 2)
    for x, y in ((18, 58), (151, 91), (77, 165)):
        if biome == 0:
            for n in range(4):
                _rect(b, x + n * 4, y + (n % 2) * 3, 5, 2, 0)
                _rect(b, x + n * 4, y + (n % 2) * 3, 3, 1, 10)
        elif biome == 1:
            for n in range(6):
                _rect(b, x + n * 3, y + n % 3, 1, 5, 14)
                _rect(b, x + n * 3 - 1, y + n % 3, 3, 1, 15)
        else:
            _oval(b, x, y, 22, 7, 3)
            _rect(b, x + 3, y + 1, 13, 1, 5)
            _rect(b, x + 6, y + 2, 15, 1, 4)
    # Extraction apron and edge landing lights, drawn once.
    _rect(b, 179, 145, 39, 37, 0)
    _rect(b, 182, 148, 33, 31, 2)
    for x, y in ((182, 148), (210, 148), (182, 173), (210, 173)):
        _rect(b, x, y, 5, 5, 4)
    _rect(b, 193, 155, 3, 18, 5)
    _rect(b, 193, 155, 13, 3, 5)
    _rect(b, 193, 163, 10, 2, 5)
    _rect(b, 193, 170, 13, 3, 5)
    return b.strips


def _trooper_art():
    b = displayio.Bitmap(18 * 12, 24, 16)
    for direction in range(4):
        for frame in range(3):
            x = (direction * 3 + frame) * 18
            step = 0 if frame == 0 else (1 if frame == 1 else -1)
            _oval(b, x + 1, 20, 16, 4, 1)
            _rect(b, x + 4, 17 + step, 4, 6, 1)
            _rect(b, x + 10, 17 - step, 4, 6, 1)
            _rect(b, x + 4, 17 + step, 3, 4, 4)
            _rect(b, x + 10, 17 - step, 3, 4, 3)
            _rect(b, x + 3, 9, 12, 10, 1)
            _rect(b, x + 4, 9, 10, 7, 3)
            _rect(b, x + 5, 10, 8, 3, 5)
            _rect(b, x + 5, 14, 3, 3, 4)
            _rect(b, x + 10, 14, 3, 3, 4)
            _rect(b, x + 2, 10, 3, 5, 12)
            _rect(b, x + 14, 10, 3, 5, 12)
            _rect(b, x + 4, 2, 11, 8, 1)
            _rect(b, x + 5, 1, 9, 8, 4)
            _rect(b, x + 6, 2, 7, 2, 6)
            _rect(b, x + 5, 5, 9, 3, 1)
            if direction != 3:
                _rect(b, x + (5 if direction == 1 else 8 if direction == 2 else 6), 5,
                      5 if direction else 7, 2, 7)
                _rect(b, x + (5 if direction == 1 else 11 if direction == 2 else 7), 5, 2, 1, 8)
            else:
                _rect(b, x + 6, 5, 7, 4, 3)
            # Directional weapon silhouette extends past the gauntlets.
            gx, gy, w, h = ((8, 13, 4, 10), (0, 12, 11, 4), (9, 12, 9, 4), (10, 0, 4, 13))[direction]
            _rect(b, x + gx, gy, w, h, 1)
            _rect(b, x + gx + 1, gy, max(1, w - 2), max(1, h - 2), 5)
    return b


def _enemy_art():
    b = displayio.Bitmap(20 * 6, 20, 16)
    for kind in range(3):
        for frame in range(2):
            x = (kind * 2 + frame) * 20
            dark, mid, bright = ((13, 14, 15), (9, 10, 11), (2, 3, 5))[kind]
            _oval(b, x + 1, 15, 18, 5, 1)
            for yy in (6, 10, 14):
                shift = frame if yy != 10 else -frame
                _rect(b, x + 1, yy + shift, 6, 2, dark)
                _rect(b, x + 13, yy - shift, 6, 2, dark)
                _rect(b, x, yy + shift - 1, 2, 4, mid)
                _rect(b, x + 18, yy - shift - 1, 2, 4, mid)
            _oval(b, x + 4, 4, 12, 14, dark)
            _oval(b, x + 5, 3, 10, 12, mid)
            _oval(b, x + 6, 4, 7, 5, bright)
            _rect(b, x + 9, 8, 2, 7, dark)
            _rect(b, x + 5, 2, 3, 3, 1)
            _rect(b, x + 12, 2, 3, 3, 1)
            _rect(b, x + 6, 3, 2, 1, 12)
            _rect(b, x + 12, 3, 2, 1, 12)
            if kind == 2:
                _rect(b, x + 4, 8, 12, 2, 4)
                _rect(b, x + 5, 12, 10, 2, 4)
    return b


def _objective_art():
    # Core, secured core, hive, destroyed hive, uplink, active uplink, supplies.
    b = displayio.Bitmap(28 * 8, 28, 16)
    for frame in range(8):
        x = frame * 28
        _oval(b, x + 2, 20, 24, 7, 1)
        if frame in (0, 1):
            _rect(b, x + 6, 9, 16, 14, 2)
            _rect(b, x + 8, 11, 12, 10, 4)
            _rect(b, x + 11, 4, 6, 16, 7 if frame == 0 else 3)
            _rect(b, x + 12, 5, 2, 12, 8 if frame == 0 else 5)
            _rect(b, x + 5, 21, 18, 3, 5)
        elif frame in (2, 3):
            _oval(b, x + 2, 6, 24, 18, 9)
            _oval(b, x + 4, 5, 20, 15, 10 if frame == 2 else 2)
            for dx, dy in ((6, 10), (13, 7), (18, 13)):
                _oval(b, x + dx, dy, 5, 7, 1)
                if frame == 2:
                    _rect(b, x + dx + 1, dy + 2, 2, 3, 11)
            _rect(b, x + 4, 21, 5, 2, 10)
            _rect(b, x + 21, 20, 5, 3, 9)
        elif frame in (4, 5):
            _rect(b, x + 5, 11, 18, 13, 2)
            _rect(b, x + 7, 13, 14, 8, 4)
            _rect(b, x + 9, 14, 10, 5, 7 if frame == 5 else 11)
            _rect(b, x + 13, 2, 2, 11, 5)
            _rect(b, x + 8, 3, 12, 2, 6)
            _rect(b, x + 5, 1, 3, 7, 4)
            _rect(b, x + 20, 1, 3, 7, 4)
        elif frame == 7:
            # Deployable tripod and twin-barrel sentry, distinct from an uplink.
            _rect(b, x + 6, 21, 17, 3, 2)
            _rect(b, x + 7, 17, 3, 8, 4)
            _rect(b, x + 19, 17, 3, 8, 4)
            _rect(b, x + 12, 10, 5, 12, 3)
            _rect(b, x + 8, 8, 14, 8, 1)
            _rect(b, x + 9, 9, 12, 5, 4)
            _rect(b, x + 9, 2, 3, 10, 5)
            _rect(b, x + 18, 2, 3, 10, 5)
            _rect(b, x + 14, 10, 3, 2, 7)
        else:
            _rect(b, x + 5, 9, 18, 14, 1)
            _rect(b, x + 6, 10, 16, 12, 13)
            _rect(b, x + 7, 11, 14, 3, 14)
            _rect(b, x + 12, 13, 4, 8, 6)
            _rect(b, x + 10, 15, 8, 3, 6)
    return b


def _craft_art():
    b = displayio.Bitmap(48, 38, 16)
    _oval(b, 1, 29, 46, 8, 1)
    _rect(b, 3, 13, 11, 18, 2)
    _rect(b, 34, 13, 11, 18, 2)
    _rect(b, 4, 13, 8, 14, 4)
    _rect(b, 36, 13, 8, 14, 4)
    _rect(b, 5, 27, 6, 5, 11)
    _rect(b, 37, 27, 6, 5, 11)
    _rect(b, 6, 28, 4, 5, 12)
    _rect(b, 38, 28, 4, 5, 12)
    _rect(b, 11, 17, 26, 9, 3)
    for y in range(2, 32):
        half = min(10, 3 + y // 2)
        _rect(b, 24 - half, y, half * 2, 1, 5 if y < 24 else 3)
    _rect(b, 18, 9, 12, 8, 1)
    _rect(b, 19, 10, 10, 5, 7)
    _rect(b, 20, 10, 3, 4, 8)
    _rect(b, 19, 23, 10, 10, 1)
    _rect(b, 20, 26, 8, 8, 4)
    _rect(b, 21, 28, 6, 1, 6)
    _rect(b, 21, 31, 6, 1, 6)
    return b


def _effect_art():
    # One pooled effect; indexed ring, warning reticle, blast, drop dust.
    b = displayio.Bitmap(48 * 4, 48, 4)
    for frame in range(4):
        x = frame * 48
        if frame == 0:
            for dx, dy in ((3, 3), (37, 3), (3, 42), (37, 42)):
                _rect(b, x + dx, dy, 8, 2, 1)
            _rect(b, x + 23, 17, 2, 14, 2)
            _rect(b, x + 17, 23, 14, 2, 2)
        else:
            _oval(b, x + 3, 3, 42, 42, 1)
            _oval(b, x + 7, 7, 34, 34, 2)
            _oval(b, x + 12, 12, 24, 24, 3 if frame == 2 else 0)
            if frame == 2:
                for dx, dy, w, h in ((1, 15, 9, 6), (33, 1, 5, 12), (36, 31, 11, 5), (12, 37, 5, 10)):
                    _rect(b, x + dx, dy, w, h, 2)
                _rect(b, x + 16, 17, 10, 4, 3)
                _rect(b, x + 26, 29, 7, 3, 1)
            if frame == 3:
                _oval(b, x + 8, 8, 32, 32, 0)
    return b


class LastBeacon:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B, self._U, self._D = A_btn, B_btn, Up_btn, Dwn_btn
        self._L, self._R, self._sel, self._audio = L_btn, R_btn, Sel_btn, Audio
        self._exit = False
        self._mission, self._weapon, self._support = 0, 0, 0
        self._credits, self._cleared, self._armor, self._power = 0, 0, 0, 0
        self._art, self._view = {}, {}
        self._enemies, self._shots, self._objectives = [], [], []
        self._load()

    def _load(self):
        try:
            with open("/last_beacon.sav", "rt") as f:
                data = f.readline().strip().split(",")
            if data[0] == "LB2":
                values = [int(v) for v in data[1:]]
                if len(values) != 7:
                    return
                mission, weapon, support, credits, cleared, armor, power = values
                if not (0 <= mission < 5 and 0 <= weapon < 3 and 0 <= support < 3
                        and credits >= 0 and 0 <= cleared < 32 and 0 <= armor <= 3 and 0 <= power <= 3):
                    return
            else:
                values = [int(v) for v in data]
                if len(values) != 4 or not 1 <= values[0] <= 5 or min(values[1:]) < 0:
                    return
                mission, weapon, support, credits = values[0] - 1, 0, 0, max(0, values[3] - 2) * 20
                cleared = (1 << mission) - 1
                armor, power = min(3, max(0, values[1] - 5)), min(3, max(0, values[2] - 2))
            self._mission, self._weapon, self._support = mission, weapon, support
            self._credits, self._cleared, self._armor, self._power = credits, cleared, armor, power
        except (OSError, ValueError):
            pass

    def _save(self):
        try:
            with open("/last_beacon.tmp", "wt") as f:
                f.write("LB2," + ",".join(str(v) for v in (self._mission, self._weapon, self._support,
                        self._credits, self._cleared, self._armor, self._power)))
            os.rename("/last_beacon.tmp", "/last_beacon.sav")
            return True
        except OSError:
            return False

    def _assets(self):
        if self._art:
            return
        self._art = {"palette": _palette(transparent=True), "trooper": _trooper_art(),
                     "enemy": _enemy_art(), "objective": _objective_art(),
                     "craft": _craft_art(), "effect": _effect_art()}
        b = displayio.Bitmap(6 * 3, 6, 4)
        _rect(b, 2, 1, 2, 4, 1)
        _rect(b, 7, 2, 4, 2, 2)
        _rect(b, 13, 1, 4, 4, 3)
        self._art["shot"] = b
        self._art["shot_palette"] = _palette((0, INK[12], INK[8], INK[11]), True)
        self._art["effect_palette"] = _palette((0, INK[10], INK[11], INK[12]), True)

    def _release_scene(self):
        while len(self._splash):
            self._splash.pop()
        self._view = {}
        self._enemies, self._shots, self._objectives = [], [], []
        gc.collect()

    def _sprite(self, name, w, h, x=0, y=0, hidden=False):
        grid = _grid(self._art[name], self._art.get(name + "_palette", self._art["palette"]),
                     x, y, tile_width=w, tile_height=h)
        grid.hidden = hidden
        self._splash.append(grid)
        return grid

    def _build_ship(self):
        self._release_scene()
        self._splash.append(_solid(240, 21, INK[1]))
        title = _text(self._splash, "BOARDING WAYFARER...", 7, 9, INK[8])
        self._assets()
        ship_palette = _palette()
        for i, strip in enumerate(_ship_art()):
            self._splash.append(_grid(strip, ship_palette, y=21 + i * 14))
        self._view["title"] = title
        _set(title, "L.B.S. WAYFARER")
        self._view["cash"] = _text(self._splash, "$%d" % self._credits, 181, 9, INK[12])
        self._view["soldier"] = self._sprite("trooper", 18, 24, 62, 103)
        self._splash.append(_solid(240, 107, INK[1], y=133))
        self._view["rows"] = [_text(self._splash, "", 7, 142 + i * 14) for i in range(5)]
        self._view["detail"] = _text(self._splash, "", 7, 216, INK[8])
        self._view["help"] = _text(self._splash, "L/R change  A choose  SEL menu", 7, 231, INK[5])

    def _ship_rows(self):
        return ("DROP: " + MISSIONS[self._mission][0], "GUN: " + WEAPONS[self._weapon][0],
                "KIT: " + SUPPORTS[self._support], "REFIT / ARMORY", "DEPLOY TO SURFACE")

    def _sync_ship(self, choice):
        for i, text in enumerate(self._ship_rows()):
            row = self._view["rows"][i]
            _set(row, ("> " if i == choice else "  ") + text)
            color = INK[12] if i == choice else INK[5]
            if row.color != color:
                row.color = color
        mission = MISSIONS[self._mission]
        details = ("%s x%d / %ds / %s" % (mission[1], mission[3], mission[4], "CLEARED" if self._cleared & (1 << self._mission) else "NEW"),
                   ("18 shots / fast / all-rounder", "6 shots / spread / close range", "6 shots / piercing / heavy hit")[self._weapon],
                   ("3 strikes / mark ahead / delayed", "2 sentries / 14s covering fire", "2 drops / heal + refill ammo")[self._support],
                   "$%d  Armor %d/3  Power %d/3" % (self._credits, self._armor, self._power),
                   "A launch! Complete goal, then extract.")
        _set(self._view["detail"], details[choice])
        _set(self._view["cash"], "$%d" % self._credits)
        x = (104, 61, 61, 61, 164)[choice]
        _place(self._view["soldier"], x, 103)

    def _menu(self, kind):
        """Small overlay; all mission clocks stop while this method owns input."""
        gc.collect()
        group = displayio.Group(x=12, y=47)
        group.append(_solid(216, 154, INK[1]))
        group.append(_solid(212, 2, INK[7], 2, 2))
        _text(group, "FIELD COMMS" if kind == "field" else "SHIP SERVICES", 10, 16, INK[8])
        labels = [_text(group, "", 10, 40 + i * 21) for i in range(4)]
        note = _text(group, "A choose / B back", 10, 137, INK[12])
        self._splash.append(group)
        choice, last = 0, time.monotonic()
        a_was, b_was, s_was = not self._A.value, not self._B.value, not self._sel.value
        try:
            while not self._exit:
                now = time.monotonic()
                if not self._U.value and not self._D.value:
                    self._exit = True
                    return
                if now - last > 0.18:
                    move = -1 if not self._U.value else (1 if not self._D.value else 0)
                    if move:
                        choice = (choice + move) % 4
                        last = now
                if kind == "refit":
                    options = ("Armor +1 " + ("MAX" if self._armor == 3 else "$%d" % (60 + self._armor * 30)),
                               "Power +1 " + ("MAX" if self._power == 3 else "$%d" % (80 + self._power * 40)),
                               "Save career", "Return to bridge")
                elif kind == "field":
                    options = ("Resume operation", "Controls", "Abort to ship", "Leave game")
                else:
                    options = ("Return to bridge", "Save career", "Controls", "Leave game")
                for i, value in enumerate(options):
                    _set(labels[i], ("> " if choice == i else "  ") + value)
                a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
                if (b_down and not b_was) or (s_down and not s_was):
                    return
                if a_down and not a_was:
                    if kind == "refit":
                        if choice < 2:
                            _set(note, self._upgrade(choice))
                        elif choice == 2:
                            _set(note, "Career saved." if self._save() else "Save failed: USB read-only/full.")
                        else:
                            return
                    elif kind == "field":
                        if choice == 0:
                            return
                        if choice == 1:
                            _set(note, "Hold A strafe / B kit / auto reload")
                        elif choice == 2:
                            self._result = "ABORTED"
                            return
                        else:
                            self._exit = True
                    else:
                        if choice == 0:
                            return
                        if choice == 1:
                            _set(note, "Career saved." if self._save() else "Save failed: USB read-only/full.")
                        elif choice == 2:
                            _set(note, "A fire / B kit / SEL pause")
                        else:
                            self._exit = True
                a_was, b_was, s_was = a_down, b_down, s_down
                time.sleep(0.025)
        finally:
            self._splash.remove(group)

    def _upgrade(self, choice):
        level = self._armor if choice == 0 else self._power
        if level == 3:
            return "Already fully upgraded."
        cost = (60 + level * 30) if choice == 0 else (80 + level * 40)
        if self._credits < cost:
            return "Need $%d more." % (cost - self._credits)
        self._credits -= cost
        if choice == 0:
            self._armor += 1
        else:
            self._power += 1
        self._audio.play("upgrade")
        return "Installed. $%d remaining." % self._credits

    def _ship(self):
        # Debrief already owns the bridge; return by updating its labels only.
        if "rows" not in self._view:
            self._build_ship()
        _set(self._view["title"], "L.B.S. WAYFARER")
        _set(self._view["help"], "L/R change  A choose  SEL menu")
        choice, last = 0, time.monotonic()
        a_was, s_was = not self._A.value, not self._sel.value
        self._sync_ship(choice)
        while not self._exit:
            now = time.monotonic()
            if not self._U.value and not self._D.value:
                self._exit = True
                return False
            changed = False
            if now - last > 0.18:
                if not self._U.value or not self._D.value:
                    choice = (choice + (-1 if not self._U.value else 1)) % 5
                    last, changed = now, True
                elif choice < 3 and (not self._L.value or not self._R.value):
                    self._change_loadout(choice, -1 if not self._L.value else 1)
                    last, changed = now, True
            a_down, s_down = not self._A.value, not self._sel.value
            modal = False
            if s_down and not s_was:
                self._menu("ship")
                modal = True
            elif a_down and not a_was:
                if choice == 4:
                    return True
                if choice == 3:
                    self._menu("refit")
                    modal = True
                else:
                    self._change_loadout(choice, 1)
                    changed = True
            if modal:
                a_down, s_down = not self._A.value, not self._sel.value
                last, changed = time.monotonic(), True
            if changed:
                self._sync_ship(choice)
            a_was, s_was = a_down, s_down
            time.sleep(0.025)
        return False

    def _change_loadout(self, row, delta):
        if row == 0:
            self._mission = (self._mission + delta) % len(MISSIONS)
        elif row == 1:
            self._weapon = (self._weapon + delta) % len(WEAPONS)
        elif row == 2:
            self._support = (self._support + delta) % len(SUPPORTS)

    def _start_mission(self):
        self._release_scene()
        self._assets()
        mission, weapon = MISSIONS[self._mission], WEAPONS[self._weapon]
        self._x, self._y, self._aim_x, self._aim_y = 118.0, 202.0, 0.0, -1.0
        self._hp, self._time = 6 + self._armor * 2, float(mission[4])
        self._mag, self._reserve = weapon[1], weapon[2]
        self._reload, self._shot_clock, self._invincible = 0.0, 0.0, 0.0
        self._support_left = 3 if self._support == 0 else 2
        self._support_cd, self._strike, self._turret_time, self._turret_shot = 0.0, 0.0, 0.0, 0.0
        self._strike_x, self._strike_y = 0, 0
        self._phase, self._extract_clock, self._board_clock = "OBJECTIVE", 0.0, 0.0
        self._spawn_clock, self._age, self._kills = 2.8, 0.0, 0
        self._result, self._effect_time = None, 0.0
        self._paid = False
        self._supply_taken = [False, False]
        self._notice, self._notice_time = "", 0.0
        terrain_palette = _palette(BIOMES[mission[2]])
        for i, strip in enumerate(_terrain(mission[2])):
            self._splash.append(_grid(strip, terrain_palette, y=30 + i * 19))
        for i in range(mission[3]):
            x, y = OBJECTIVE_POS[i]
            grid = self._sprite("objective", 28, 28, x - 14, y - 14)
            grid[0] = {"SALVAGE": 0, "PURGE": 2, "UPLINK": 4}[mission[1]]
            # x, y, remaining work/health, completed, sprite
            self._objectives.append([x, y, 20.0 if mission[1] == "PURGE" else 6.0, False, grid])
        self._view["supplies"] = []
        for x, y in ((112, 48), (19, 108)):
            grid = self._sprite("objective", 28, 28, x - 14, y - 14)
            grid[0] = 6
            self._view["supplies"].append(grid)
        for _ in range(ENEMY_LIMIT):
            grid = self._sprite("enemy", 20, 20, hidden=True)
            # active, x, y, hp, kind, attack windup, sprite
            self._enemies.append([False, 0.0, 0.0, 0, 0, 0.0, grid])
        self._view["turret"] = self._sprite("objective", 28, 28, hidden=True)
        self._view["turret"][0] = 7
        self._view["craft"] = self._sprite("craft", 48, 38, hidden=True)
        self._view["trooper"] = self._sprite("trooper", 18, 24)
        for _ in range(SHOT_LIMIT):
            grid = self._sprite("shot", 6, 6, hidden=True)
            # active, x, y, vx, vy, lifetime, damage, pierce, last hit slot, sprite
            self._shots.append([False, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, -1, grid])
        self._view["effect"] = self._sprite("effect", 48, 48, hidden=True)
        self._splash.append(_solid(240, 30, INK[1]))
        self._splash.append(_solid(240, 20, INK[1], y=220))
        self._view["status"] = _text(self._splash, "", 5, 7, INK[8])
        self._view["ammo"] = _text(self._splash, "", 5, 21, INK[6])
        self._view["hint"] = _text(self._splash, "", 5, 229, INK[12])
        self._sync_field(False)

    @staticmethod
    def _blocked(x, y, radius=6):
        if x < 8 + radius or x > 232 - radius or y < 36 + radius or y > 213 - radius:
            return True
        for rx, ry, w, h in ROCKS:
            if rx - radius < x < rx + w + radius and ry - radius < y < ry + h + radius:
                return True
        return False

    def _move(self, x, y, dx, dy, radius=6):
        if not self._blocked(x + dx, y, radius):
            x += dx
        if not self._blocked(x, y + dy, radius):
            y += dy
        return x, y

    def _notice_set(self, text):
        self._notice, self._notice_time = text, 2.2

    def _effect(self, x, y, frame, seconds):
        grid = self._view["effect"]
        _place(grid, x - 24, y - 24)
        grid[0], grid.hidden = frame, False
        self._effect_time = seconds

    def _spawn(self):
        count = sum(1 for e in self._enemies if e[0])
        if count >= min(ENEMY_LIMIT, 4 + MISSIONS[self._mission][5] * 2):
            return
        for enemy in self._enemies:
            if not enemy[0]:
                side = random.randrange(4)
                x, y = ((16, random.randint(45, 204)), (224, random.randint(45, 204)),
                        (random.randint(16, 224), 43), (random.randint(16, 224), 204))[side]
                if _d2(x, y, self._x, self._y) < 42 ** 2 or self._blocked(x, y, 5):
                    return
                threat = MISSIONS[self._mission][5]
                kind = random.randrange(3 if threat >= 3 else 2)
                enemy[:6] = [True, float(x), float(y), (4, 3, 10)[kind] + threat // 2, kind, 0.0]
                enemy[6].hidden = False
                _place(enemy[6], x - 10, y - 10)
                return

    def _target(self, x, y, ax, ay, all_round=False):
        best, distance = None, 150 ** 2
        for e in self._enemies:
            if e[0]:
                dx, dy = e[1] - x, e[2] - y
                d = dx * dx + dy * dy
                if d < distance and (all_round or dx * ax + dy * ay > d ** 0.5 * 0.25):
                    best, distance = (e[1], e[2]), d
        if MISSIONS[self._mission][1] == "PURGE" and not all_round:
            for obj in self._objectives:
                dx, dy = obj[0] - x, obj[1] - y
                d = dx * dx + dy * dy
                if not obj[3] and d < distance and dx * ax + dy * ay > d ** 0.5 * 0.25:
                    best, distance = (obj[0], obj[1]), d
        return best

    def _bullet(self, x, y, dx, dy, speed, damage, pierce=0):
        for shot in self._shots:
            if not shot[0]:
                shot[:9] = [True, x, y, dx * speed, dy * speed, 1.3, damage, pierce, -1]
                shot[9][0] = 1 if pierce else (2 if self._weapon == 1 else 0)
                shot[9].hidden = False
                _place(shot[9], x - 3, y - 3)
                return True
        return False

    def _fire(self):
        if self._reload > 0 or self._shot_clock > 0:
            return
        weapon = WEAPONS[self._weapon]
        sidearm = self._mag == 0 and self._reserve == 0
        if not sidearm and self._mag == 0:
            self._reload = weapon[5]
            return
        # Do not spend a round when the fixed projectile pool is full.
        needed = 1 if sidearm else weapon[6]
        if sum(1 for s in self._shots if not s[0]) < needed:
            return
        target = self._target(self._x, self._y, self._aim_x, self._aim_y)
        dx, dy = _unit(target[0] - self._x, target[1] - self._y) if target else (self._aim_x, self._aim_y)
        for spread in ((0,) if needed == 1 else (-0.23, 0, 0.23)):
            vx, vy = _unit(dx - dy * spread, dy + dx * spread)
            self._bullet(self._x + dx * 8, self._y + dy * 8, vx, vy,
                         180 if sidearm else weapon[7], 1 if sidearm else weapon[4] + self._power,
                         1 if self._weapon == 2 and not sidearm else 0)
        self._shot_clock = 0.4 if sidearm else weapon[3]
        if not sidearm:
            self._mag -= 1
            if not self._mag and self._reserve:
                self._reload = weapon[5]
        self._audio.play("shoot")

    def _use_support(self):
        if self._support_left == 0:
            self._notice_set("Support depleted. Use supply crates.")
            return
        if self._support_cd > 0:
            self._notice_set("Support cooling down.")
            return
        self._support_left -= 1
        self._support_cd = 8.0
        self._audio.play("support")
        if self._support == 0:
            target = self._target(self._x, self._y, self._aim_x, self._aim_y)
            self._strike_x = max(20, min(220, target[0] if target else self._x + self._aim_x * 48))
            self._strike_y = max(45, min(205, target[1] if target else self._y + self._aim_y * 48))
            self._strike = 0.85
            self._effect(self._strike_x, self._strike_y, 0, 0.85)
            self._notice_set("Orbital marked. Impact in one second.")
        elif self._support == 1:
            self._turret_time, self._turret_shot = 14.0, 0.0
            _place(self._view["turret"], self._x - 14, self._y - 14)
            self._view["turret"].hidden = False
            self._notice_set("Sentry online. 14 seconds of cover.")
        else:
            self._resupply()
            self._effect(self._x, self._y, 3, 0.4)
            self._notice_set("Resupplied: armor and ammunition.")

    def _resupply(self):
        self._hp = min(6 + self._armor * 2, self._hp + 3)
        self._reserve = min(WEAPONS[self._weapon][2], self._reserve + WEAPONS[self._weapon][1] * 3)
        if self._mag == 0 and self._reload <= 0:
            self._reload = WEAPONS[self._weapon][5]

    def _kill(self, enemy):
        enemy[0], enemy[6].hidden = False, True
        self._kills += 1

    def _complete(self, obj):
        obj[3] = True
        obj[4][0] += 1
        self._audio.play("collect")

    def _blast(self):
        for e in self._enemies:
            if e[0] and _d2(e[1], e[2], self._strike_x, self._strike_y) < 48 ** 2:
                self._kill(e)
        if MISSIONS[self._mission][1] == "PURGE":
            for obj in self._objectives:
                if not obj[3] and _d2(obj[0], obj[1], self._strike_x, self._strike_y) < 48 ** 2:
                    obj[2] -= 16
                    if obj[2] <= 0:
                        self._complete(obj)
        self._effect(self._strike_x, self._strike_y, 2, 0.35)

    def _update_shots(self, dt):
        for shot in self._shots:
            if not shot[0]:
                continue
            shot[1] += shot[3] * dt
            shot[2] += shot[4] * dt
            shot[5] -= dt
            if shot[5] <= 0 or self._blocked(shot[1], shot[2], 0):
                shot[0], shot[9].hidden = False, True
                continue
            for i, e in enumerate(self._enemies):
                if e[0] and i != shot[8] and _d2(shot[1], shot[2], e[1], e[2]) < 11 ** 2:
                    e[3] -= shot[6]
                    if e[3] <= 0:
                        self._kill(e)
                    if shot[7]:
                        shot[7] -= 1
                        shot[8] = i
                    else:
                        shot[0] = False
                    break
            if shot[0] and MISSIONS[self._mission][1] == "PURGE":
                for obj in self._objectives:
                    if not obj[3] and _d2(shot[1], shot[2], obj[0], obj[1]) < 14 ** 2:
                        obj[2] -= shot[6]
                        shot[0] = False
                        if obj[2] <= 0:
                            self._complete(obj)
                        break
            shot[9].hidden = not shot[0]
            _place(shot[9], shot[1] - 3, shot[2] - 3)

    def _update_enemies(self, dt):
        for i, e in enumerate(self._enemies):
            if not e[0]:
                continue
            distance = _d2(self._x, self._y, e[1], e[2])
            if e[5] > 0:
                e[5] -= dt
                if e[5] <= 0 and distance < 21 ** 2 and self._invincible <= 0:
                    self._hp -= 2 if e[4] == 2 else 1
                    self._invincible = 0.8
                    self._audio.play("hit")
            elif distance < 18 ** 2:
                e[5] = 0.35 if e[4] == 2 else 0.22
            else:
                dx, dy = _unit(self._x - e[1], self._y - e[2])
                speed = (24, 35, 17)[e[4]] * dt
                nx, ny = self._move(e[1], e[2], dx * speed, dy * speed, 5)
                if abs(nx - e[1]) + abs(ny - e[2]) < speed * 0.1:
                    # Slide around a rock instead of stalling in a straight chase.
                    nx, ny = self._move(e[1], e[2], -dy * speed, dx * speed, 5)
                e[1], e[2] = nx, ny
            frame = e[4] * 2 + (1 if e[5] > 0 else int(self._age * 7 + i) % 2)
            if e[6][0] != frame:
                e[6][0] = frame
            _place(e[6], e[1] - 10, e[2] - 10)

    def _update_objectives(self, dt):
        kind = MISSIONS[self._mission][1]
        for obj in self._objectives:
            if obj[3] or _d2(self._x, self._y, obj[0], obj[1]) > 20 ** 2:
                continue
            if kind == "SALVAGE":
                self._complete(obj)
                self._notice_set("Signal core secured.")
            elif kind == "UPLINK":
                contested = any(e[0] and _d2(e[1], e[2], obj[0], obj[1]) < 31 ** 2 for e in self._enemies)
                if contested:
                    self._notice_set("Uplink contested: clear nearby bugs.")
                else:
                    obj[2] -= dt
                    self._notice_set("UPLINK: hold nearby %ds" % max(1, int(obj[2] + 0.99)))
                    if obj[2] <= 0:
                        self._complete(obj)
                        self._notice_set("Uplink transmitted.")
        if self._phase == "OBJECTIVE" and all(obj[3] for obj in self._objectives):
            self._phase = "BEACON"
            self._notice_set("Goal complete! Reach E to call evac.")
        near = _d2(self._x, self._y, EXTRACT[0], EXTRACT[1]) < 23 ** 2
        if self._phase == "BEACON" and near:
            self._phase, self._extract_clock = "INBOUND", 18.0
            self._notice_set("Shuttle called! Survive 18 seconds.")
        elif self._phase == "INBOUND":
            self._extract_clock -= dt
            if self._extract_clock <= 0:
                self._phase, self._board_clock = "BOARD", 12.0
                self._view["craft"].hidden = False
                self._notice_set("SHUTTLE DOWN! Reach E before lift-off.")
        elif self._phase == "BOARD":
            self._board_clock -= dt
            if near:
                self._result = "EXTRACTED"
            elif self._board_clock <= 0:
                self._result = "MISSED SHUTTLE"

    def _step(self, dt, dx=0, dy=0, firing=False, support=False):
        if self._result:
            return
        self._time -= dt
        self._age += dt
        if self._time <= 0:
            self._time, self._result = 0, "SIGNAL LOST"
            return
        # Physics uses bounded steps, while the deadline always follows real time.
        motion = min(0.06, max(0, dt))
        self._shot_clock -= dt
        self._invincible -= dt
        self._support_cd -= dt
        self._notice_time -= dt
        self._effect_time -= dt
        if self._effect_time <= 0:
            self._view["effect"].hidden = True
        if self._reload > 0:
            self._reload -= dt
            if self._reload <= 0:
                amount = min(WEAPONS[self._weapon][1] - self._mag, self._reserve)
                self._mag += amount
                self._reserve -= amount
        moving = bool(dx or dy)
        if moving:
            ux, uy = _unit(dx, dy)
            self._x, self._y = self._move(self._x, self._y, ux * 67 * motion, uy * 67 * motion)
            if not firing:
                self._aim_x, self._aim_y = ux, uy
        if firing:
            self._fire()
        if support:
            self._use_support()
        if self._strike > 0:
            self._strike -= dt
            if self._strike <= 0:
                self._blast()
        if self._turret_time > 0:
            self._turret_time -= dt
            self._turret_shot -= dt
            turret = self._view["turret"]
            x, y = turret.x + 14, turret.y + 14
            if self._turret_shot <= 0:
                target = self._target(x, y, 0, -1, True)
                if target:
                    ux, uy = _unit(target[0] - x, target[1] - y)
                    self._bullet(x, y, ux, uy, 195, 3)
                    self._turret_shot = 0.3
            turret.hidden = self._turret_time <= 0
        self._update_shots(motion)
        self._update_enemies(motion)
        for i, grid in enumerate(self._view["supplies"]):
            if not self._supply_taken[i] and _d2(self._x, self._y, grid.x + 14, grid.y + 14) < 18 ** 2:
                # Leave a crate available until it can actually help.
                if self._hp < 6 + self._armor * 2 or self._reserve < WEAPONS[self._weapon][2]:
                    self._supply_taken[i], grid.hidden = True, True
                    self._resupply()
                    self._notice_set("Supply cache: armor + ammunition.")
                    self._audio.play("collect")
        if self._hp <= 0:
            self._hp, self._result = 0, "TROOPER LOST"
        else:
            self._update_objectives(dt)
        self._spawn_clock -= dt
        if self._spawn_clock <= 0:
            self._spawn()
            self._spawn_clock = max(0.6, 2.2 - MISSIONS[self._mission][5] * 0.23 - (0.5 if self._phase in ("INBOUND", "BOARD") else 0))
        self._sync_field(moving)

    def _sync_field(self, moving):
        trooper = self._view["trooper"]
        _place(trooper, self._x - 9, self._y - 16)
        direction = (2 if self._aim_x > 0 else 1) if abs(self._aim_x) > abs(self._aim_y) else (0 if self._aim_y > 0 else 3)
        frame = direction * 3 + (1 + int(self._age * 9) % 2 if moving else 0)
        if trooper[0] != frame:
            trooper[0] = frame
        hidden = self._invincible > 0 and int(self._age * 12) % 2 == 0
        if trooper.hidden != hidden:
            trooper.hidden = hidden
        remain = max(0, int(self._time + 0.99))
        done = sum(1 for obj in self._objectives if obj[3])
        _set(self._view["status"], "%02d:%02d  HP %d  GOAL %d/%d" % (remain // 60, remain % 60, self._hp, done, len(self._objectives)))
        ammo = "RELOAD" if self._reload > 0 else ("SIDEARM" if self._mag == 0 and self._reserve == 0 else "%d/%d" % (self._mag, self._reserve))
        _set(self._view["ammo"], "%s %s  KIT %d" % (WEAPONS[self._weapon][0][:7], ammo, self._support_left))
        if self._phase == "INBOUND":
            hint = "EVAC inbound %ds / stay alive" % max(0, int(self._extract_clock + 0.99))
            if self._extract_clock < 3:
                craft = self._view["craft"]
                craft.hidden = False
                _place(craft, EXTRACT[0] - 24, EXTRACT[1] - 24 - int(self._extract_clock * 22))
        elif self._phase == "BOARD":
            hint = "BOARD at E! Leaving in %ds" % max(0, int(self._board_clock + 0.99))
            _place(self._view["craft"], EXTRACT[0] - 24, EXTRACT[1] - 24)
        elif self._phase == "BEACON":
            hint = "Reach E (lower right) to call evac"
        elif self._notice_time > 0:
            hint = self._notice
        else:
            hint = {"SALVAGE": "Collect cyan cores / B support", "PURGE": "Destroy red hives / B support", "UPLINK": "Hold at antennas / clear nearby bugs"}[MISSIONS[self._mission][1]]
        _set(self._view["hint"], hint)

    def _drop_in(self):
        craft = self._view["craft"]
        craft.hidden = False
        self._view["trooper"].hidden = True
        _set(self._view["hint"], "DROP POD INBOUND - STAND BY")
        for frame in range(35):
            if not self._U.value and not self._D.value:
                self._exit = True
                break
            _place(craft, 94, 35 + frame * 4)
            time.sleep(0.025)
        craft.hidden = True
        self._view["trooper"].hidden = False
        self._effect(self._x, self._y, 3, 0.4)
        self._notice_set("A fire/strafe  B kit  SEL pause")

    def _mission_run(self):
        self._start_mission()
        self._drop_in()
        last = time.monotonic()
        # A held from Deploy cannot fire until it is released once.
        armed = bool(self._A.value)
        b_was, s_was = not self._B.value, not self._sel.value
        while not self._exit and not self._result:
            now = time.monotonic()
            dt, last = now - last, now
            if not self._U.value and not self._D.value:
                self._exit = True
                break
            a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
            if not a_down:
                armed = True
            if s_down and not s_was:
                self._menu("field")
                last = time.monotonic()
                b_was, s_was = not self._B.value, not self._sel.value
                armed = bool(self._A.value)
                continue
            dx = (not self._R.value) - (not self._L.value)
            dy = (not self._D.value) - (not self._U.value)
            self._step(dt, dx, dy, a_down and armed, b_down and not b_was)
            b_was, s_was = b_down, s_down
            # Budget the whole frame, rather than adding a fixed delay after work.
            time.sleep(max(0.001, 0.033 - (time.monotonic() - now)))
        return self._result

    def _settle(self):
        if self._result != "EXTRACTED" or self._paid:
            return 0
        self._paid = True
        reward = MISSIONS[self._mission][6] + int(self._time) // 10
        if not self._cleared & (1 << self._mission):
            reward += 20
        self._credits += reward
        self._cleared |= 1 << self._mission
        self._audio.play("win")
        return reward

    def _debrief(self):
        reward = self._settle()
        result, kills = self._result, self._kills
        self._build_ship()
        _set(self._view["title"], result)
        lines = ("PAYMENT +$%d" % reward if reward else "NO EXTRACTION PAYMENT", "ELIMINATIONS %d" % kills,
                 "Career saved." if self._save() else "Save unavailable (USB/read-only).",
                 "Re-arm aboard the Wayfarer.", "A RETURN TO BRIDGE")
        for row, value in zip(self._view["rows"], lines):
            _set(row, value)
        _set(self._view["detail"], "Complete goals, call E, board in time.")
        _set(self._view["help"], "A continue / Up+Down leave")
        a_was = not self._A.value
        while not self._exit:
            if not self._U.value and not self._D.value:
                self._exit = True
                return
            down = not self._A.value
            if down and not a_was:
                return
            a_was = down
            time.sleep(0.03)

    def Game(self):
        self._exit = False
        while not self._exit:
            if not self._ship():
                break
            self._mission_run()
            if not self._exit:
                self._debrief()
        self._release_scene()
        self._art = {}
        gc.collect()
        return True
