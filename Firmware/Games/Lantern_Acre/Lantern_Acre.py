# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""A retained-scene pixel-art homestead. D-pad walk, A interact, B market.

One day is four minutes of active farm time. Cottage/market/pause stop time.
Farm art is built once; gameplay changes sprite positions and atlas tile indices.
"""
import time
import gc
import os
import displayio
from adafruit_display_text import label
import terminalio

TILE = 20
GRID_Y = 40
DAY_SECONDS = 240
SEASONS = ("SPRING", "SUMMER", "AUTUMN", "WINTER")
# name, watered nights to mature, sale price, seed cost (mixed seeds cost $2)
CROPS = (("TURNIP", 2, 5, 2), ("BEAN", 3, 8, 3),
         ("PUMPKIN", 4, 13, 5), ("ROOT", 3, 10, 4))
PLOTS = (
    ((2, 5), (3, 5), (4, 5), (2, 6), (3, 6), (4, 6), (2, 7), (3, 7), (4, 7)),
    ((7, 4), (8, 4), (9, 4), (7, 5), (8, 5), (9, 5), (7, 6), (8, 6), (9, 6)),
    ((6, 8), (7, 8), (8, 8), (9, 8), (6, 9), (7, 9), (8, 9), (9, 9)),
)
# Meadow coordinates use x+12 in save data; render only the current area's plots.
PLOTS += (
    tuple((x+12,y) for y in (3,4,5) for x in (2,3,4)),
    tuple((x+12,y) for y in (3,4,5) for x in (7,8,9)),
    tuple((x+12,y) for y in (7,8,9) for x in (6,7,8)),
)
PLOT_PRICES = (40,100,140,180,220)
DOOR = (2, 3)
# Shared 32-color palette: shaded foliage, warm timber, slate, water, lamplight.
COLORS = (0x000000, 0x243B35, 0x355741, 0x4E7548, 0x729454, 0xA6B96C,
          0xD0CB89, 0x513E37, 0x75503D, 0x976448, 0xBD8A5B, 0xE2B77C,
          0xF6DCA1, 0x483846, 0x704554, 0xA25B63, 0xD18578, 0xEFBA98,
          0x263D50, 0x3C6173, 0x548D9C, 0x83B5B5, 0xCAE1CE, 0xEFD886,
          0xEFA84F, 0xCE703D, 0x884636, 0xE8EEE0, 0x748B95, 0xABC1BF,
          0xBDCB78, 0xFFEFBA)


# Large scenic bitmaps use tailored 16-color inks (4 bits/pixel).
# Crops/farmer retain the full 32-color atlas; neither is repainted in play.
WORLD_INKS = (1, 2, 3, 4, 5, 7, 8, 10, 12, 13, 15, 16, 18, 20, 21, 28)
ROOM_INKS = (7, 10, 8, 9, 19, 21, 12, 15, 11, 27, 20, 14, 16, 28, 18, 23)
WORLD_MAP = (0, 0, 1, 2, 3, 4, 8, 5, 6, 7, 7, 7, 8, 9, 9, 10, 11, 11, 12, 12, 13, 14, 14, 8, 8, 6, 5, 8, 15, 14, 4, 8)
ROOM_MAP = (0, 0, 0, 10, 0, 0, 0, 0, 2, 3, 1, 8, 6, 0, 11, 7, 12, 0, 14, 4, 10, 5, 0, 15, 15, 12, 0, 9, 13, 0, 0, 0)


class _Canvas:
    """Map the art's common ink numbers directly into a compact bitmap."""
    def __init__(self, width, height, inks):
        self.width, self.height, self.inks = width, height, inks
        self.strip_height = 20 if height == 200 else 13
        self.strips = [displayio.Bitmap(width, self.strip_height, 16)
                       for _ in range(height // self.strip_height)]

    def __setitem__(self, position, color):
        x, y = position
        self.strips[y // self.strip_height][x, y % self.strip_height] = self.inks[color]

    def fill(self, color):
        for strip in self.strips:
            strip.fill(self.inks[color])


def _palette(transparent=False, inks=None):
    colors = COLORS if inks is None else tuple(COLORS[i] for i in inks)
    p = displayio.Palette(len(colors))
    for i, color in enumerate(colors):
        p[i] = color
    if transparent:
        p.make_transparent(0)
    return p


def _rect(b, x, y, w, h, c):
    for yy in range(max(0, y), min(b.height, y + h)):
        for xx in range(max(0, x), min(b.width, x + w)):
            b[xx, yy] = c


def _oval(b, x, y, w, h, c):
    for yy in range(max(0, y), min(b.height, y + h)):
        for xx in range(max(0, x), min(b.width, x + w)):
            if ((2 * (xx - x) - w + 1) ** 2 * h * h +
                    (2 * (yy - y) - h + 1) ** 2 * w * w <= w * w * h * h):
                b[xx, yy] = c


def _tile(b, palette, x=0, y=0, **kwargs):
    return displayio.TileGrid(b, pixel_shader=palette, x=x, y=y, **kwargs)


def _text(group, text, x, y, color=0xF6DCA1):
    obj = label.Label(terminalio.FONT, text=text, color=color, x=x, y=y)
    group.append(obj)
    return obj


def _set_text(obj, text):
    if obj.text != text:
        obj.text = text


def _tree(b, x, y, size=34):
    _oval(b, x + 3, y + size - 6, size, 10, 2)
    _rect(b, x + size // 2 - 3, y + 18, 7, size - 15, 7)
    _rect(b, x + size // 2, y + 20, 2, size - 17, 10)
    # Overlapping leaf clusters make an irregular, shaded canopy silhouette.
    for dx, dy, w, h in ((1, 12, size - 2, size - 16),
                         (0, 7, size // 2, size // 2),
                         (size // 2 - 3, 5, size // 2 + 4, size // 2),
                         (5, 1, size - 12, size - 13)):
        _oval(b, x + dx, y + dy, w, h, 1)
        _oval(b, x + dx, y + dy - 1, w - 2, h - 3, 2)
        _oval(b, x + dx + 1, y + dy - 2, w - 5, h - 5, 3)
    for dx, dy, w, h in ((5, 7, 10, 7), (14, 2, 11, 8),
                         (21, 12, 9, 8), (11, 16, 11, 8), (2, 15, 8, 6)):
        _oval(b, x + dx, y + dy, w, h, 4)
        _rect(b, x + dx + 2, y + dy + 1, 4, 1, 5)
        _rect(b, x + dx + w - 3, y + dy + h - 1, 3, 1, 2)



def _house(b):
    # Deep eaves, stone foundation, clapboard, individual shingles, porch.
    _rect(b, 9, 27, 78, 43, 2)
    _rect(b, 12, 26, 68, 40, 7)
    _rect(b, 14, 29, 64, 32, 11)
    for y in range(32, 61, 6):
        _rect(b, 14, y, 64, 1, 10)
        _rect(b, 15, y + 1, 61, 1, 12)
    _rect(b, 12, 60, 68, 7, 28)
    for x in range(13, 80, 9):
        _rect(b, x, 61, 1, 5, 18)
    _rect(b, 66, 5, 9, 19, 7)
    _rect(b, 67, 5, 7, 16, 16)
    _rect(b, 65, 4, 11, 3, 13)
    for y in range(8, 33):
        left = 10 + (32 - y) // 2
        right = 83 - (32 - y) // 2
        _rect(b, left, y, right - left, 1, 13 if y > 29 else 14)
        if y % 5 == 0:
            _rect(b, left + 1, y, right - left - 2, 1, 16)
        else:
            for x in range(left + (y // 5 % 2) * 5, right, 10):
                _rect(b, x, y, 1, 1, 15)
    _rect(b, 8, 31, 77, 3, 7)
    for x in (20, 61):
        _rect(b, x - 2, 39, 15, 17, 8)
        _rect(b, x, 40, 11, 12, 18)
        _rect(b, x + 1, 41, 9, 9, 21)
        _rect(b, x + 5, 40, 1, 12, 11)
        _rect(b, x, 45, 11, 1, 11)
        _rect(b, x - 2, 53, 15, 3, 12)
        _rect(b, x - 1, 56, 13, 3, 9)
        for dx in (0, 4, 8):
            _rect(b, x + dx, 54, 2, 2, 15)
    _rect(b, 40, 38, 18, 26, 7)
    _rect(b, 42, 39, 14, 25, 9)
    _rect(b, 44, 41, 10, 7, 18)
    _rect(b, 45, 42, 8, 5, 23)
    for x in (44, 49, 54):
        _rect(b, x, 50, 1, 13, 8)
    _rect(b, 53, 53, 2, 2, 23)
    _rect(b, 37, 64, 25, 3, 11)
    _rect(b, 35, 67, 29, 3, 28)
    _rect(b, 34, 70, 31, 2, 29)


def _landscape(canvas=None):
    b = canvas if canvas is not None else _Canvas(240, 200, WORLD_MAP)
    b.fill(3)
    # Deterministic speckle, grass blades and flowers; no per-frame terrain writes.
    seed = 71
    for _ in range(950):
        seed = (seed * 109 + 89) % 65521
        x, y = seed % 240, (seed // 240) % 200
        _rect(b, x, y, 2, 1, 4 if seed % 3 else 2)
        if seed % 11 == 0:
            _rect(b, x, y - 2, 1, 2, 5)
        if seed % 37 == 0:
            _rect(b, x, y - 2, 2, 2, 12 if seed % 2 else 16)
    # A curving creek and pebbled bank occupy the rightmost column.
    for y in range(200):
        bank = 220 + ((y // 18) % 3) * 2
        _rect(b, bank - 3, y, 243 - bank, 1, 6)
        _rect(b, bank, y, 240 - bank, 1, 19)
        _rect(b, bank + 2, y, 238 - bank, 1, 20)
        if y % 13 == 0:
            _rect(b, bank + 5, y, 7, 1, 21)
    # Worn central lane and cottage approach.
    _rect(b, 103, 62, 15, 138, 10)
    _rect(b, 32, 73, 84, 12, 10)
    for y in range(66, 200, 9):
        _rect(b, 105 + y % 4, y, 7, 2, 12)
        _rect(b, 115, y + 3, 2, 1, 8)
    for x in range(0, 220, 20):
        _rect(b, x, 3, 3, 13, 7)
        _rect(b, x, 3, 2, 10, 11)
    _rect(b, 0, 7, 220, 2, 10)
    _rect(b, 0, 12, 220, 2, 8)
    _tree(b, 88, 12, 34)
    _tree(b, 130, 8, 38)
    _tree(b, 178, 12, 36)
    _tree(b, 0, 106, 29)
    _tree(b, 0, 161, 32)
    # Well with stone rim, timber uprights, rope and bucket.
    _oval(b, 171, 57, 30, 15, 2)
    _oval(b, 174, 54, 24, 15, 28)
    _oval(b, 177, 55, 18, 8, 18)
    _rect(b, 175, 43, 3, 17, 8)
    _rect(b, 194, 43, 3, 17, 8)
    _rect(b, 172, 41, 28, 4, 10)
    _rect(b, 185, 45, 1, 12, 12)
    _rect(b, 182, 55, 7, 5, 9)
    # Creekside reeds, a herb patch and lantern posts frame useful landmarks.
    for x, y in ((216, 43), (215, 104), (216, 164), (214, 185)):
        for dx, dy in ((0, 0), (3, -3), (6, 1)):
            _rect(b, x + dx, y + dy, 1, 8, 2)
            _rect(b, x + dx, y + dy - 2, 2, 3, 10)
    for x, y in ((179, 72), (188, 75), (197, 71)):
        _oval(b, x, y, 8, 5, 2)
        _rect(b, x + 3, y - 3, 2, 6, 5)
        _rect(b, x + 1, y - 2, 5, 2, 30)
        _rect(b, x + 3, y - 4, 2, 2, 16)
    for x, y in ((28, 45), (113, 131), (201, 139)):
        _rect(b, x + 5, y + 7, 2, 16, 7)
        _rect(b, x + 3, y + 3, 6, 7, 7)
        _rect(b, x + 4, y + 4, 4, 4, 11)
        _rect(b, x + 2, y + 2, 8, 2, 18)
    _house(b)
    # Shipping chest by the porch.
    _rect(b, 77, 67, 16, 12, 7)
    _rect(b, 78, 68, 14, 9, 10)
    _rect(b, 78, 71, 14, 2, 8)
    _rect(b, 84, 70, 3, 4, 23)
    # East footbridge to the extra growing area.
    _rect(b,205,140,35,20,7)
    for y in range(142,159,4):
        _rect(b,205,y,35,3,10)
        _rect(b,207,y,29,1,12)
    _rect(b,203,138,2,25,11)
    return b.strips


def _meadow(canvas=None):
    b = canvas if canvas is not None else _Canvas(240,200,WORLD_MAP)
    b.fill(3)
    for i in range(750):
        x,y=(i*83+17)%240,(i*37+11)%200
        _rect(b,x,y,2,1,4 if i%3 else 2)
        if i%31==0:_rect(b,x,y-2,2,2,16)
    for y in range(200):
        _rect(b,0,y,18,1,19)
        _rect(b,2,y,12,1,20)
        _rect(b,18,y,3,1,6)
        if y%15==0:_rect(b,4,y,7,1,21)
    _rect(b,25,142,92,16,10)
    _rect(b,103,39,15,161,10)
    for y in range(43,200,9):_rect(b,105,y,8,2,12)
    for x,y,size in ((17,0,33),(58,-3,38),(109,0,35),(159,-3,40),(204,0,35),(205,164,32)):
        _tree(b,x,y,size)
    # Potting shelter, tool rack, and rain barrel frame the northern path.
    _rect(b,23,22,57,24,7)
    _rect(b,25,24,53,20,10)
    for x in range(27,78,8):_rect(b,x,26,2,17,8)
    _rect(b,20,18,63,7,13)
    _rect(b,22,18,59,2,16)
    _oval(b,182,37,20,17,7)
    _rect(b,182,41,20,12,8)
    _oval(b,183,35,18,8,28)
    _oval(b,186,36,12,5,20)
    _rect(b,181,46,22,2,18)
    _rect(b,0,140,31,20,7)
    for y in range(142,159,4):_rect(b,0,y,31,3,10)
    for x,y in ((113,131),(201,139)):
        _rect(b,x+5,y+7,2,16,7)
        _rect(b,x+3,y+3,6,7,7)
        _rect(b,x+4,y+4,4,4,11)
    return b.strips


class _SpriteBanks:
    """Logical atlas drawn once into small, interchangeable tile banks."""
    def __init__(self, tile_width, height, count, per_bank):
        self.width, self.height = tile_width * count, height
        self.bank_width = tile_width * per_bank
        self.per_bank = per_bank
        self.banks = [displayio.Bitmap(self.bank_width, height, 32)
                      for _ in range((count + per_bank - 1) // per_bank)]

    def __setitem__(self, pos, color):
        x, y = pos
        self.banks[x // self.bank_width][x % self.bank_width, y] = color

    def show(self, grid, frame):
        bitmap = self.banks[frame // self.per_bank]
        if grid.bitmap is not bitmap:
            grid.bitmap = bitmap
        if grid[0] != frame % self.per_bank:
            grid[0] = frame % self.per_bank


def _crop_atlas():
    # 0 locked, 1 empty; each crop: seed/sprout/leaf/ripe x dry/wet.
    b = _SpriteBanks(TILE, TILE, 34, 4)
    for tile in range(34):
        x = tile * TILE
        if tile == 0:
            _rect(b, x + 1, 1, 18, 18, 2)
            for dx, dy in ((3, 5), (11, 3), (8, 13)):
                _rect(b, x + dx, dy, 2, 4, 4)
                _rect(b, x + dx - 1, dy + 1, 4, 1, 5)
            _rect(b, x + 14, 14, 4, 3, 28)
            continue
        wet = tile >= 2 and (tile - 2) % 2 == 1
        _rect(b, x + 1, 1, 18, 18, 7)
        _rect(b, x + 2, 2, 16, 15, 8 if wet else 9)
        for y in (4, 9, 14):
            _rect(b, x + 3, y, 14, 1, 7 if wet else 8)
            _rect(b, x + 4, y + 1, 11, 1, 8 if wet else 10)
        if tile == 1:
            continue
        crop, stage = (tile - 2) // 8, ((tile - 2) % 8) // 2
        if wet:
            _rect(b, x + 15, 15, 2, 2, 21)
        if stage == 0:
            _rect(b, x + 8, 9, 4, 2, 7)
            _rect(b, x + 9, 8, 2, 2, 12)
            continue
        _oval(b, x + 4, 13, 12, 4, 7)
        _rect(b, x + 9, 6, 2, 9, 2)
        _oval(b, x + 4, 7, 6, 4, 4)
        _oval(b, x + 10, 5, 6, 4, 5)
        _rect(b, x + 6, 7, 3, 1, 30)
        if stage >= 2:
            _oval(b, x + 3, 10, 7, 4, 3)
            _oval(b, x + 10, 9, 7, 4, 4)
            _rect(b, x + 12, 10, 3, 1, 5)
        if stage == 3:
            if crop == 0:
                _oval(b, x + 6, 10, 9, 7, 27)
                _rect(b, x + 7, 10, 7, 2, 16)
                _rect(b, x + 10, 17, 2, 1, 12)
            elif crop == 1:
                _rect(b, x + 9, 2, 1, 15, 11)
                for dx, dy in ((5, 8), (12, 5), (12, 11)):
                    _oval(b, x + dx, dy, 3, 6, 30)
                    _rect(b, x + dx, dy + 1, 1, 3, 5)
            elif crop == 2:
                _oval(b, x + 3, 9, 15, 9, 25)
                _oval(b, x + 5, 9, 11, 8, 24)
                _rect(b, x + 8, 10, 1, 6, 25)
                _rect(b, x + 12, 10, 1, 6, 25)
                _rect(b, x + 10, 7, 2, 3, 2)
            else:
                _oval(b, x + 6, 10, 9, 7, 16)
                _oval(b, x + 7, 11, 6, 4, 27)
                _rect(b, x + 9, 17, 3, 1, 17)
    return b


def _farmer_atlas():
    # Four directions, three gait frames; brim, hair, hands, overalls and boots.
    b = _SpriteBanks(18, 24, 12, 3)
    for direction in range(4):
        for step in range(3):
            x = (direction * 3 + step) * 18
            _oval(b, x + 2, 20, 15, 4, 2)
            left, right = (0, 0) if step == 0 else ((-1, 1) if step == 1 else (1, -1))
            _rect(b, x + 5, 18 + left, 4, 4, 18)
            _rect(b, x + 10, 18 + right, 4, 4, 18)
            _rect(b, x + 4, 21 + left, 5, 2, 7)
            _rect(b, x + 10, 21 + right, 5, 2, 7)
            _rect(b, x + 4, 11, 11, 8, 13)
            _rect(b, x + 5, 11, 9, 6, 16)
            _rect(b, x + 6, 13, 7, 7, 19)
            _rect(b, x + 7, 13, 1, 4, 21)
            _rect(b, x + 12, 13, 1, 4, 21)
            _rect(b, x + 3, 13 + right, 3, 5, 17)
            _rect(b, x + 14, 13 + left, 2, 5, 17)
            _rect(b, x + 5, 5, 9, 7, 7)
            _rect(b, x + 6, 6, 7, 6, 17)
            _rect(b, x + 7, 7, 6, 3, 12)
            if direction == 3:
                _rect(b, x + 5, 6, 9, 6, 8)
                _rect(b, x + 6, 10, 7, 2, 7)
            elif direction == 0:
                _rect(b, x + 7, 8, 1, 2, 18)
                _rect(b, x + 11, 8, 1, 2, 18)
            else:
                eye = 6 if direction == 1 else 12
                _rect(b, x + eye, 8, 1, 2, 18)
                _rect(b, x + (5 if direction == 1 else 13), 9, 1, 2, 17)
            _rect(b, x + 4, 2, 11, 5, 8)
            _rect(b, x + 5, 1, 9, 4, 11)
            _rect(b, x + 6, 1, 6, 1, 12)
            _rect(b, x + 4, 5, 11, 2, 25)
            _rect(b, x + 1, 6, 17, 2, 11)
            _rect(b, x + 2, 6, 14, 1, 12)
    return b


def _interior():
    b = _Canvas(224, 91, ROOM_MAP)
    b.fill(7)
    _rect(b, 3, 3, 218, 40, 10)
    for y in range(6, 42, 7):
        _rect(b, 3, y, 218, 1, 8)
    _rect(b, 3, 43, 218, 46, 9)
    for y in range(44, 91, 9):
        _rect(b, 3, y, 218, 1, 7)
        for x in range(4 + (y % 2) * 14, 222, 28):
            _rect(b, x, y, 1, 9, 8)
    # Window, curtains, bed and quilt, rug, stove, table, vase, bookshelf.
    _rect(b, 86, 9, 34, 27, 7)
    _rect(b, 89, 11, 28, 21, 19)
    _rect(b, 91, 12, 24, 10, 21)
    _rect(b, 102, 11, 2, 23, 12)
    _rect(b, 89, 22, 28, 2, 12)
    _rect(b, 83, 7, 7, 31, 15)
    _rect(b, 116, 7, 7, 31, 15)
    _rect(b, 12, 29, 48, 53, 7)
    _rect(b, 15, 30, 42, 48, 11)
    _rect(b, 18, 33, 36, 13, 27)
    _rect(b, 17, 47, 38, 26, 19)
    for y in range(48, 72, 6):
        for x in range(18, 54, 6):
            _rect(b, x, y, 5, 5, 20 if (x + y) % 12 else 21)
    _rect(b, 13, 74, 46, 5, 10)
    _rect(b, 76, 55, 66, 29, 14)
    _rect(b, 79, 58, 60, 23, 16)
    _rect(b, 83, 61, 52, 17, 14)
    _rect(b, 91, 64, 36, 11, 24)
    _rect(b, 173, 5, 32, 45, 28)
    _rect(b, 177, 32, 24, 19, 18)
    _rect(b, 182, 38, 14, 12, 25)
    _rect(b, 187, 39, 5, 10, 23)
    _rect(b, 169, 28, 40, 5, 7)
    _rect(b, 148, 58, 42, 5, 11)
    _rect(b, 151, 63, 3, 16, 7)
    _rect(b, 185, 63, 3, 16, 7)
    _oval(b, 163, 48, 9, 11, 20)
    _rect(b, 167, 42, 1, 9, 3)
    _oval(b, 162, 40, 9, 5, 16)
    _rect(b, 132, 8, 27, 30, 7)
    for x in range(135, 156, 4):
        _rect(b, x, 12, 3, 20 - x % 5, 14 + x % 4)
    _rect(b, 131, 34, 30, 3, 11)
    return b.strips


class LanternAcre:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B, self._U, self._D = A_btn, B_btn, Up_btn, Dwn_btn
        self._L, self._R, self._sel = L_btn, R_btn, Sel_btn
        self._audio = Audio
        self._exit = False
        self._day, self._elapsed = 1, 0.0
        self._coins, self._seeds, self._crops = 18, 6, 0
        self._basket_value = 0
        self._unlocked, self._can, self._cart = 1, False, False
        self._plants = {}
        self._area = 0
        self._seed_packets = [0,0,0,0]
        self._selected_seed = -1
        self._panel_cache = None
        self._crop_art = self._farmer_art = None
        self._terrain_canvas = None
        self._foraged = False
        self._note = "Welcome home! A at the cottage door."
        self._note_until = 0
        self._load_state()

    def _save_state(self):
        fields = (self._day, int(self._elapsed), self._coins, self._seeds,
                  self._crops, self._unlocked, int(self._can), int(self._cart), self._basket_value, int(self._foraged),
                  self._area, self._selected_seed) + tuple(self._seed_packets)
        plants = [",".join(str(v) for v in (x, y, p[0], int(p[1]), p[2]))
                  for (x, y), p in self._plants.items()]
        try:
            # Write a sibling first so failed writes leave the previous save intact.
            with open("/lantern_acre.tmp", "wt") as f:
                f.write("LA4," + ",".join(str(v) for v in fields) + "|" + ";".join(plants))
            os.rename("/lantern_acre.tmp", "/lantern_acre.sav")
            return True
        except OSError:
            return False

    def _load_state(self):
        # Validate into locals first: a truncated/invalid save must not half-load.
        try:
            with open("/lantern_acre.sav", "rt") as f:
                fields, plants = f.readline().strip().split("|", 1)
            current = fields.startswith("LA4,")
            expanded = current or fields.startswith("LA3,")
            modern = expanded or fields.startswith("LA2,")
            values = [int(v) for v in fields.split(",")[1 if modern else 0:]]
            if len(values) != (16 if expanded else 10 if modern else 8):
                return
            day, elapsed, coins, seeds, crops, unlocked, can, cart = values[:8]
            basket = values[8] if modern else crops * 5
            foraged = values[9] if modern else 0
            area, selected = values[10:12] if expanded else (0,-1)
            packets = values[12:] if expanded else [0,0,0,0]
            if area not in (0,1) or not -1 <= selected <= 3 or min(packets)<0:
                return
            saved_day_seconds = DAY_SECONDS if current else 480 if modern else 20
            if not (day >= 1 and 0 <= elapsed < saved_day_seconds
                    and min(coins, seeds, crops, basket) >= 0 and 1 <= unlocked <= (6 if expanded else 3)
                    and can in (0, 1) and cart in (0, 1) and foraged in (0, 1)):
                return
            loaded = {}
            for record in plants.split(";"):
                if not record:
                    continue
                x, y, age, wet, crop = [int(v) for v in record.split(",")]
                if not (0 <= self._plot_at((x, y)) < unlocked and 0 <= crop < 4
                        and age >= 0 and wet in (0, 1)):
                    return
                loaded[(x, y)] = [min(age, CROPS[crop][1]), bool(wet), crop]
            self._day = day
            self._elapsed = float(elapsed * DAY_SECONDS / saved_day_seconds)
            self._coins, self._seeds, self._crops = coins, seeds, crops
            self._unlocked, self._can, self._cart = unlocked, bool(can), bool(cart)
            self._basket_value, self._plants = basket, loaded
            self._foraged = bool(foraged)
            self._area, self._selected_seed, self._seed_packets = area, selected, packets
        except (OSError, ValueError):
            pass

    def _season_index(self):
        return ((self._day - 1) // 8) % 4

    def _is_night(self):
        return self._elapsed >= DAY_SECONDS * 0.75

    @staticmethod
    def _plot_at(position):
        for number, plot in enumerate(PLOTS):
            if position in plot:
                return number
        return -1

    def _new_day(self):
        self._elapsed = 0.0
        self._day += 1
        for p in self._plants.values():
            if p[1]:
                p[0] = min(CROPS[p[2]][1], p[0] + 1)
            p[1] = False
        # A small daily forage prevents bankruptcy without replacing farming.
        self._foraged = False
        self._sync_plots()
        self._say("Day %d: water crops, then sleep." % self._day)

    def _tick(self, dt):
        self._elapsed += max(0, dt)
        if self._elapsed >= DAY_SECONDS:
            self._new_day()

    def _say(self, message):
        self._note = message
        self._note_until = time.monotonic() + 4

    def _plot_tile(self, pos):
        if self._plot_at(pos) >= self._unlocked:
            return 0
        p = self._plants.get(pos)
        if p is None:
            return 1
        stage = 3 if p[0] >= CROPS[p[2]][1] else (0 if p[0] == 0 else min(2, p[0]))
        return 2 + p[2] * 8 + stage * 2 + int(p[1])

    def _sync_plots(self):
        for pos, grid in self._plot_sprites.items():
            index = self._plot_tile(pos)
            self._crop_art.show(grid, index)

    def _build_farm(self):
        # Only one area's terrain is live. Retain the large atlases and menus.
        if hasattr(self, '_farm_group') and self._farm_group is not None:
            self._splash.remove(self._farm_group)
            self._farm_group = None
            self._plot_sprites = {}
            self._farmer = self._cursor = None
            self._ambient, self._lamps = [], []
            self._status = self._inventory = self._hint = None
            gc.collect()
        self._palette = _palette(inks=WORLD_INKS)
        transparent = _palette(True)
        self._sprite_palette = transparent
        self._light_phase = -1
        self._farm_group = displayio.Group()
        if self._terrain_canvas is None:
            self._terrain_canvas = _Canvas(240, 200, WORLD_MAP)
        terrain = _meadow(self._terrain_canvas) if self._area else _landscape(self._terrain_canvas)
        for i, strip in enumerate(terrain):
            self._farm_group.append(_tile(strip, self._palette, y=GRID_Y + i * 20))
        if self._crop_art is None:
            self._crop_art, self._farmer_art = _crop_atlas(), _farmer_atlas()
        atlas = self._crop_art
        self._plot_sprites = {}
        for plot in PLOTS[self._area*3:self._area*3+3]:
            for x, y in plot:
                grid = _tile(atlas.banks[0], transparent, (x % 12) * TILE, GRID_Y + y * TILE,
                             tile_width=TILE, tile_height=TILE)
                self._plot_sprites[(x, y)] = grid
                self._farm_group.append(grid)
        self._sync_plots()
        # Four corner marks leave both soil and sprite visible.
        mark = displayio.Bitmap(20, 20, 32)
        for x, y in ((0, 0), (16, 0), (0, 19), (16, 19)):
            _rect(mark, x, y, 4, 1, 12)
        for x, y in ((0, 0), (19, 0), (0, 16), (19, 16)):
            _rect(mark, x, y, 1, 4, 12)
        self._cursor = _tile(mark, transparent)
        self._farm_group.append(self._cursor)
        self._farmer = _tile(self._farmer_art.banks[0], transparent, tile_width=18, tile_height=24)
        self._farm_group.append(self._farmer)
        # Local light sprites: night changes do not dirty the whole terrain palette.
        lamp = displayio.Bitmap(12, 14, 32)
        _oval(lamp, 0, 0, 12, 14, 10)
        _rect(lamp, 4, 2, 4, 10, 7)
        _rect(lamp, 3, 4, 6, 6, 24)
        _rect(lamp, 4, 5, 4, 4, 31)
        self._lamps = []
        for x, y in (((113,171),(201,179)) if self._area else ((28,85),(113,171),(201,179))):
            grid = _tile(lamp, _palette(True), x, y)
            grid.hidden = True
            self._farm_group.append(grid)
            self._lamps.append(grid)
        hud = displayio.Bitmap(240, 40, 2)
        _rect(hud, 0, 38, 240, 2, 1)
        hud_palette = displayio.Palette(2)
        hud_palette[0], hud_palette[1] = COLORS[18], COLORS[10]
        self._farm_group.append(_tile(hud, hud_palette))
        self._status = _text(self._farm_group, "", 5, 7)
        self._inventory = _text(self._farm_group, "", 5, 19, 0xCAE1CE)
        self._hint = _text(self._farm_group, "", 5, 31, 0xABC1BF)
        self._splash.append(self._farm_group)
        _set_text(self._status, "LANTERN ACRE")
        _set_text(self._hint, "Preparing reusable menus...")
        self._prepare_panel()
        # Four tiny retained sprites animate creek glints and chimney smoke.
        self._ambient = []
        for width, height, color, x, y in ((7, 2, 22, 228, 100), (5, 2, 21, 230, 205),
                                           (4, 3, 29, 67, 42), (3, 2, 28, 71, 40)):
            b = displayio.Bitmap(width, height, 32)
            _oval(b, 0, 0, width, height, color)
            grid = _tile(b, transparent, x, y)
            # Place ambient sprites behind HUD, above terrain/actors.
            self._farm_group.insert(len(self._farm_group) - 4, grid)
            if self._area:
                if x>220:x=5
                else:grid.hidden=True
            self._ambient.append((grid, x, y))
        self._ambient_frame = -1

    def _context(self, pos):
        if pos == ((1,7) if self._area else (10,7)):
            return "A cross to " + ("home farm" if self._area else "Lantern Meadow")
        if not self._area and pos == DOOR:
            return "A enter cottage   B market"
        if not self._area and pos == (4, 3):
            return "A ship basket     B market"
        if not self._area and pos == (9, 3):
            return "A forage herbs    B market"
        pos = (pos[0]+self._area*12,pos[1])
        plot = self._plot_at(pos)
        if plot >= self._unlocked:
            return "Overgrown plot: unlock at market"
        if plot < 0:
            return "A interact  B market  SEL pause"
        p = self._plants.get(pos)
        if p is None:
            return "A plant %s   B market" % CROPS[self._planting_crop()][0].lower()
        if p[0] >= CROPS[p[2]][1]:
            return "A harvest %s ($%d)" % (CROPS[p[2]][0].lower(), CROPS[p[2]][2])
        return "%s %d/%d  %s" % (CROPS[p[2]][0], p[0], CROPS[p[2]][1],
                                      "watered" if p[1] else "A water")

    def _sync_hud(self, pos, now):
        hour = 6 + int(self._elapsed * 18 / DAY_SECONDS)
        phase = "NIGHT" if self._is_night() else ("DUSK" if hour >= 17 else "DAY")
        _set_text(self._status, "D%d %s %02d:00 %s" %
                  (self._day, SEASONS[self._season_index()][:3], hour, phase))
        stock = self._seeds if self._selected_seed < 0 else self._seed_packets[self._selected_seed]
        seed = "MIX" if self._selected_seed < 0 else CROPS[self._selected_seed][0][:4]
        _set_text(self._inventory, "$%d %s:%d Basket %d" % (self._coins,seed,stock,self._crops))
        _set_text(self._hint, self._note if now < self._note_until else self._context(pos))
        for lamp in self._lamps:
            if lamp.hidden == self._is_night():
                lamp.hidden = not self._is_night()

    def _animate(self, now):
        # Palette changes occur only at dusk/night/dawn, never on movement or tending.
        # They invalidate world colors once, while keeping every scene object alive.
        hour = 6 + int(self._elapsed * 18 / DAY_SECONDS)
        phase = 2 if self._is_night() else (1 if hour >= 17 else 0)
        if phase != self._light_phase:
            for i, color in enumerate(COLORS):
                r, g, b = color >> 16, (color >> 8) & 255, color & 255
                if phase == 1:
                    r, g, b = r * 9 // 10, g * 3 // 4, b * 4 // 5
                elif phase == 2:
                    r, g, b = r * 9 // 20, g * 11 // 20, min(255, b * 7 // 10 + 12)
                shaded = (r << 16) | (g << 8) | b
                if i in WORLD_INKS:
                    self._palette[WORLD_INKS.index(i)] = shaded
                self._sprite_palette[i] = shaded
            self._light_phase = phase
        frame = int(now * 3) % 4
        if frame != self._ambient_frame:
            for i, (sprite, x, y) in enumerate(self._ambient):
                sprite.x = x + (frame % 2 if i >= 2 else frame)
                sprite.y = y - (frame if i >= 2 else 0)
            self._ambient_frame = frame

    def _tend(self, pos):
        plot = self._plot_at(pos)
        if plot < 0:
            return "Plant in the furrows. B opens market."
        if plot >= self._unlocked:
            return "Unlock this plot at the market."
        p = self._plants.get(pos)
        if p is None:
            stock = self._seeds if self._selected_seed < 0 else self._seed_packets[self._selected_seed]
            if stock == 0:
                return "No selected seeds. B market > Seeds."
            if self._selected_seed < 0:self._seeds -= 1
            else:self._seed_packets[self._selected_seed] -= 1
            self._plants[pos] = [0, False, self._planting_crop()]
            self._audio.play("select")
            return "Planted! A again to water."
        if p[0] >= CROPS[p[2]][1]:
            self._crops += 1
            self._basket_value += CROPS[p[2]][2]
            del self._plants[pos]
            self._audio.play("collect")
            return "Harvested! Ship at home or market."
        count = 0
        for dx in ((-1, 0, 1) if self._can else (0,)):
            nearby = self._plants.get((pos[0] + dx, pos[1]))
            if nearby and not nearby[1] and nearby[0] < CROPS[nearby[2]][1]:
                nearby[1] = True
                count += 1
        if not count:
            return "Already watered. Grows at dawn."
        self._audio.play("move")
        return "Watered %d. Sleep at home to grow." % count

    def _sell(self):
        if not self._crops:
            return "Your basket is empty."
        value = self._basket_value + (self._crops if self._cart else 0)
        self._coins += value
        self._crops, self._basket_value = 0, 0
        self._audio.play("collect")
        return "Shipped for $%d. Thank you!" % value

    def _buy(self, choice):
        if choice == 1:
            return self._sell()
        if choice == 0:
            cost = 6
        elif choice == 2:
            if self._unlocked == 6:
                return "All six plots are yours."
            cost = PLOT_PRICES[self._unlocked-1]
        elif choice == 3:
            if self._can:
                return "Copper can already owned."
            cost = 60
        else:
            if self._cart:
                return "Market cart already owned."
            cost = 80
        if self._coins < cost:
            return "Need $%d more." % (cost - self._coins)
        self._coins -= cost
        if choice == 0:
            self._seeds += 3
        elif choice == 2:
            self._unlocked += 1
            self._sync_plots()
        elif choice == 3:
            self._can = True
        else:
            self._cart = True
        self._audio.play("upgrade")
        return "Purchased. Happy farming!"

    def _menu_items(self, kind):
        if kind == "home":
            return ("Sleep until morning", "Ship basket ($%d)" % self._sale_value(),
                    "Farm journal", "Return outside")
        if kind == "pause":
            return ("Resume", "Save farm", "Save and leave", "Leave without saving")
        if kind == "seeds":
            return ("Mixed seeds x3 ($6)",) + tuple("%s x3 ($%d)" % (crop[0],self._packet_price(i)) for i,crop in enumerate(CROPS)) + ("Choose planting seed",)
        if kind == "planting":
            return ("Mixed seeds (%d)" % self._seeds,) + tuple("%s (%d)" % (crop[0],self._seed_packets[i]) for i,crop in enumerate(CROPS)) + ("Back",)
        plot = "All six plots owned" if self._unlocked == 6 else ("Meadow" if self._unlocked >= 3 else "Home") + " plot ($%d)" % PLOT_PRICES[self._unlocked-1]
        return ("Seed shop / planting seed", "Sell basket ($%d)" % self._sale_value(), plot,
                "Copper can " + ("[OWNED]" if self._can else "($60)"),
                "Market cart " + ("[OWNED]" if self._cart else "($80)"), "Return to farm")

    def _planting_crop(self):
        return self._season_index() if self._selected_seed < 0 else self._selected_seed

    def _packet_price(self,crop):
        # Specific seeds grow year-round; their own season discounts each seed.
        return 3 * max(1,CROPS[crop][3]-int(crop == self._season_index()))

    def _buy_packet(self,crop):
        cost = self._packet_price(crop)
        if self._coins < cost:return "Need $%d more." % (cost-self._coins)
        self._coins -= cost;self._seed_packets[crop] += 3
        self._selected_seed = crop
        self._audio.play("collect")
        return "%s selected. Grows any season." % CROPS[crop][0]

    def _nested_menu(self,child,parent,group):
        self._splash.remove(group)
        try:self._modal(child)
        finally:self._panel(parent)

    def _morning_card(self,saved):
        # Reuse the existing overlay and labels: no bitmap allocation at sleep.
        group,funds,rows,hint = self._panel_cache
        self._panel_room.hidden = True
        for tile in self._panel_tiles:tile[0] = 0
        title = "%s, DAY %d" % (SEASONS[self._season_index()],self._day)
        _set_text(funds,title)
        funds.scale,funds.x,funds.y = 2,max(4,(224-len(title)*12)//2),70
        for row in rows:row.hidden = True
        rows[0].hidden = False;rows[0].x,rows[0].y = 14,105
        _set_text(rows[0],"A new morning on Lantern Acre.")
        _set_text(hint,"Farm saved." if saved else "Save unavailable: USB/read-only.")
        self._sync_hud(DOOR,time.monotonic())
        self._animate(time.monotonic())
        end = time.monotonic()+1.8
        try:
            while time.monotonic()<end and not self._exit:
                if not self._U.value and not self._D.value:self._exit = True
                time.sleep(0.03)
        finally:
            funds.scale,funds.x,funds.y = 1,8,14
            rows[0].x = 12

    def _sale_value(self):
        return self._basket_value + (self._crops if self._cart else 0)

    def _prepare_panel(self):
        """Allocate all menu artwork once, using blocks no larger than 2,128 bytes."""
        if self._panel_cache is not None:
            return
        gc.collect()
        group = displayio.Group(x=8, y=44)
        palette = displayio.Palette(4)
        for i, color in enumerate((7, 18, 8, 12)):
            palette[i] = COLORS[color]
        self._panel_tiles = []
        for band in range(10):
            # Two skins share each atlas strip: cottage and market/pause.
            b = displayio.Bitmap(448, 19, 4)
            for skin in range(2):
                for yy in range(19):
                    y = band * 19 + yy
                    for x in range(224):
                        color = 1 if 2 <= x < 222 and 2 <= y < 188 else 0
                        if 3 <= x < 221 and 3 <= y < 25:
                            color = 2
                        if skin:
                            if 3 <= x < 219 and 25 <= y < 34:
                                color = 2 if ((x - 3) // 18) % 2 else 3
                            if 7 <= x < 217 and 36 <= y < 166:
                                color = 0
                            if 9 <= x < 215 and 38 <= y < 164:
                                color = 2
                        b[skin * 224 + x, yy] = color
            grid = _tile(b, palette, y=band * 19, tile_width=224, tile_height=19)
            self._panel_tiles.append(grid)
            group.append(grid)
        room = displayio.Group(y=24)
        room_palette = _palette(inks=ROOM_INKS)
        for i, strip in enumerate(_interior()):
            room.append(_tile(strip, room_palette, y=i * 13))
        room.hidden = True
        group.append(room)
        self._panel_room = room
        funds = _text(group, "LANTERN MARKET", 8, 14)
        labels = [_text(group, item, 12, 48 + i * 21)
                  for i, item in enumerate(self._menu_items("town"))]
        hint = _text(group, "A choose / B back", 8, 180, 0xCAE1CE)
        self._panel_cache = (group, funds, labels, hint)

    def _panel(self, kind):
        gc.collect()
        group, funds, labels, hint = self._panel_cache
        home = kind == "home"
        for grid in self._panel_tiles:
            grid[0] = 0 if home else 1
        self._panel_room.hidden = not home
        title = {"home": "HEARTH & HOME", "town": "LANTERN MARKET", "pause": "LANTERN ACRE", "seeds": "SEASONAL SEEDS", "planting": "PLANTING SEED"}[kind]
        _set_text(funds, title + "  $%d" % self._coins)
        items = self._menu_items(kind)
        start, spacing = (123, 14) if home else (48, 21)
        for i, row in enumerate(labels):
            row.hidden = i >= len(items)
            if i < len(items):
                row.y = start + i * spacing
                _set_text(row, items[i])
        _set_text(hint, SEASONS[self._season_index()] + " sale / grows year-round" if kind == "seeds" else "A choose / B back")
        self._splash.append(group)
        return group, funds, labels, hint

    def _modal(self, kind):
        group, funds, labels, hint = self._panel(kind)
        choice, last_move = 0, time.monotonic()
        a_was, b_was, sel_was = not self._A.value, not self._B.value, not self._sel.value
        confirm_sleep = False
        item_count = len(self._menu_items(kind))
        dirty = True
        title = funds.text.split("  $")[0]
        try:
            while not self._exit:
                now = time.monotonic()
                if not self._U.value and not self._D.value:
                    self._exit = True
                    break
                if now - last_move > 0.18:
                    delta = -1 if not self._U.value else (1 if not self._D.value else 0)
                    if delta:
                        choice = (choice + delta) % item_count
                        dirty = True
                        last_move = now
                        confirm_sleep = False
                        _set_text(hint, "A choose / B back")
                a_down, b_down, sel_down = not self._A.value, not self._B.value, not self._sel.value
                if (b_down and not b_was) or (sel_down and not sel_was):
                    return
                if a_down and not a_was:
                    dirty = True
                    if kind == "town":
                        if choice == 5:
                            return
                        if choice == 0:
                            self._nested_menu("seeds",kind,group)
                            a_down,b_down,sel_down = not self._A.value,not self._B.value,not self._sel.value
                        else:_set_text(hint, self._buy(choice))
                    elif kind == "seeds":
                        if choice == 5:
                            self._nested_menu("planting",kind,group)
                            a_down,b_down,sel_down = not self._A.value,not self._B.value,not self._sel.value
                        else:_set_text(hint,self._buy(0) if choice == 0 else self._buy_packet(choice-1))
                    elif kind == "planting":
                        if choice < 5:self._selected_seed = choice-1
                        return
                    elif kind == "home":
                        if choice == 0:
                            thirsty = sum(1 for p in self._plants.values() if not p[1] and p[0] < CROPS[p[2]][1])
                            if thirsty and not confirm_sleep:
                                _set_text(hint, "%d dry crops. A sleep anyway." % thirsty)
                                confirm_sleep = True
                            else:
                                self._new_day()
                                saved = self._save_state()
                                self._morning_card(saved)
                                if not saved:
                                    self._say("Morning! Save unavailable (USB?).")
                                return
                        elif choice == 1:
                            _set_text(hint, self._sell())
                        elif choice == 2:
                            ready = sum(1 for p in self._plants.values() if p[0] >= CROPS[p[2]][1])
                            _set_text(hint, "%d ready / %d growing / %d plots" %
                                      (ready, len(self._plants) - ready, self._unlocked))
                        else:
                            return
                    else:
                        if choice == 0:
                            return
                        if choice in (1, 2):
                            saved = self._save_state()
                            _set_text(hint, "Farm saved." if saved else "Save failed: disk read-only/full.")
                            if choice == 2 and saved:
                                self._exit = True
                        else:
                            self._exit = True
                if dirty:
                    for i, item in enumerate(self._menu_items(kind)):
                        _set_text(labels[i], ("> " if i == choice else "  ") + item)
                        color = 0xFFEFBA if i == choice else 0xABC1BF
                        if labels[i].color != color:
                            labels[i].color = color
                    _set_text(funds, title + "  $%d" % self._coins)
                    dirty = False
                a_was, b_was, sel_was = a_down, b_down, sel_down
                time.sleep(0.025)
        finally:
            self._splash.remove(group)

    @staticmethod
    def _walkable(x, y):
        if 12 <= x < 24:
            x -= 12
            return 1 <= x <= 10 and 2 <= y <= 9 and (x,y) != (9,2) and not (x==10 and y>=8)
        if not (0 <= x <= 10 and 1 <= y <= 9):
            return False
        if y <= 2 and x <= 3:  # Cottage facade; approach door from below.
            return False
        if y <= 1 and x >= 4:  # Orchard border.
            return False
        if x == 0 and y >= 5:  # Trees down the west hedge.
            return False
        if (x, y) == (9, 2):  # Stone well.
            return False
        return True

    def _interact(self, pos):
        if pos == ((1,7) if self._area else (10,7)):
            self._area = 1-self._area
            self._build_farm()
            self._say("Lantern Meadow: three extra plots." if self._area else "Welcome back to the home farm.")
            return True
        if not self._area and pos == DOOR:
            self._modal("home")
        elif not self._area and pos == (4,3):
            self._say(self._sell())
        elif not self._area and pos == (9,3):
            if self._foraged:self._say("Herbs regrow tomorrow.")
            else:
                self._coins += 2;self._foraged = True
                self._audio.play("collect");self._say("Gathered wild herbs. +$2")
        else:
            self._say(self._tend((pos[0]+12*self._area,pos[1])))
            self._sync_plots()
        return False

    def _farm(self):
        self._build_farm()
        pos = [1,7] if self._area else [2,3]
        px, py = pos[0] * TILE + 1, GRID_Y + pos[1] * TILE - 5
        self._farmer.x, self._farmer.y = px, py
        last_time = time.monotonic()
        last_move, direction = last_time, 0
        action_until = 0
        a_was, b_was, sel_was = not self._A.value, not self._B.value, not self._sel.value
        self._say("Lantern Meadow. West bridge leads home." if self._area else "Welcome home! A enters the cottage.")
        while not self._exit:
            now = time.monotonic()
            dt = now - last_time
            last_time = now
            self._tick(dt)
            if not self._U.value and not self._D.value:
                self._exit = True
                break
            dx, dy = 0, 0
            if not self._L.value:
                dx, direction = -1, 1
            elif not self._R.value:
                dx, direction = 1, 2
            elif not self._U.value:
                dy, direction = -1, 3
            elif not self._D.value:
                dy, direction = 1, 0
            tx, ty = pos[0] * TILE + 1, GRID_Y + pos[1] * TILE - 5
            arrived = abs(px - tx) < 0.5 and abs(py - ty) < 0.5
            if arrived and (dx or dy) and now - last_move >= 0.16:
                if self._walkable(pos[0] + dx + 12*self._area, pos[1] + dy):
                    pos[0] += dx
                    pos[1] += dy
                last_move = now
            tx, ty = pos[0] * TILE + 1, GRID_Y + pos[1] * TILE - 5
            speed = min(20, dt * 150)
            px += max(-speed, min(speed, tx - px))
            py += max(-speed, min(speed, ty - py))
            moving = abs(px - tx) > 0.5 or abs(py - ty) > 0.5
            x, y = int(px), int(py)
            if self._farmer.x != x:
                self._farmer.x = x
            if self._farmer.y != y:
                self._farmer.y = y
            frame = direction * 3 + (1 + int(now * 9) % 2 if moving else 0)
            self._farmer_art.show(self._farmer, frame)
            cx, cy = pos[0] * TILE, GRID_Y + pos[1] * TILE
            if self._cursor.x != cx:
                self._cursor.x = cx
            if self._cursor.y != cy:
                self._cursor.y = cy
            a_down, b_down, sel_down = not self._A.value, not self._B.value, not self._sel.value
            if a_down and not a_was:
                action_until = now + 0.35
            modal = False
            if sel_down and not sel_was:
                self._modal("pause")
                modal = True
            elif b_down and not b_was:
                self._modal("town")
                modal = True
            elif action_until and now <= action_until and not moving:
                action_until = 0
                old_area = self._area
                transitioned = self._interact(tuple(pos))
                modal = transitioned or (not old_area and tuple(pos) == DOOR)
                if transitioned:
                    pos = [1,7] if self._area else [10,7]
                    px,py = pos[0]*TILE+1,GRID_Y+pos[1]*TILE-5
                    self._farmer.x,self._farmer.y = int(px),int(py)
            if modal:
                action_until = 0
                # Discard menu wall time and consume buttons held on return.
                last_time = time.monotonic()
                a_down, b_down, sel_down = not self._A.value, not self._B.value, not self._sel.value
                last_move = last_time
            a_was, b_was, sel_was = a_down, b_down, sel_down
            self._sync_hud(tuple(pos), time.monotonic())
            self._animate(time.monotonic())
            time.sleep(0.02)

    def Game(self):
        self._exit = False
        self._farm()
        while len(self._splash):
            self._splash.pop()
        return True
