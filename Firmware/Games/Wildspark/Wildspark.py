# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Wildspark: six illustrated trails, 27 forms and a party you can actually use.

D-pad walks/selects, A interacts/confirms, B opens partners/retreats, SEL pauses.
Small static background strips and retained actors keep drawing and memory bounded.
"""
import gc
import os
import time
import displayio
import terminalio
from adafruit_display_text import label

TYPES = ("EMBER", "TIDE", "GROVE")
FAMILIES = (
    ("EMBER", ("CINDLE", "FLARROW", "PYREX")), ("EMBER", ("MOTE", "BRASSET", "VOLCRAG")), ("EMBER", ("SPARKIT", "BLAZELYN", "SUNDRIFT")),
    ("TIDE", ("BUBLET", "RIPPLER", "MAELFIN")), ("TIDE", ("SHELLY", "TIDEPIN", "CORALORD")), ("TIDE", ("MISTO", "STREAMEL", "MONSOON")),
    ("GROVE", ("BUDDY", "VINEKIN", "THORNROOT")), ("GROVE", ("MOSSLE", "FERNRO", "GROVEON")), ("GROVE", ("PEBBLEAF", "OAKLET", "VERDANT")),
)
ROUTES = ("MOTHWOOD", "AMBER PASS", "SPRINGBANK", "REED COAST", "THORN HOLLOW", "MOONGLADE")
RELICS = ("SILVER SEED", "WARM SHARD", "RIVER BELL", "HUMMING FEATHER", "THUNDER REED", "MOONSTONE")
INK = (0x102B31, 0x253B3C, 0x355D47, 0x5D8552, 0x8EB465, 0xD4D895,
       0xF1DFB0, 0x513E46, 0x865345, 0xBE875A, 0xE0B97C, 0x476E89,
       0x73ADBD, 0xBCDEE0, 0xB85962, 0xEC9390)
CREATURE_COLORS = (
    (0,0x392C43,0x8A3945,0xCE5A4C,0xF28E56,0xF8C875,0x392C43,0xFFF0CC,0xF9DA78,0xF2B495,0x70576C,0x83AE6B,0x5CAEC4,0x9F7785,0x614258,0xE8B7A2),
    (0,0x233B59,0x326887,0x4A9EB3,0x87CED4,0xD5E7C2,0x233B59,0xF2F7D9,0xF2CF81,0xD78996,0x5D6F91,0x87B6A0,0xB0DEE5,0x7499B0,0x3D526F,0xF3C9A9),
    (0,0x293D38,0x436246,0x719454,0xAFC371,0xE1DFA0,0x293D38,0xF6EDC3,0xE9BF6D,0xDA8292,0x697964,0x8EB79C,0x80B6B0,0x94947B,0x4D5547,0xE3BB86),
)


def _palette(colors=INK, transparent=False):
    p = displayio.Palette(len(colors))
    for i, c in enumerate(colors):
        p[i] = c
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
            if (2*(xx-x)-w+1)**2*h*h + (2*(yy-y)-h+1)**2*w*w <= w*w*h*h:
                b[xx, yy] = c


class _Canvas:
    def __init__(self, width, height, strip=18):
        self.width, self.height, self.strip = width, height, strip
        self.strips = [displayio.Bitmap(width, strip, 16) for _ in range(height // strip)]

    def __setitem__(self, pos, c):
        x, y = pos
        self.strips[y // self.strip][x, y % self.strip] = c

    def fill(self, c):
        for b in self.strips:
            b.fill(c)


def _grid(b, p, x=0, y=0, **kw):
    return displayio.TileGrid(b, pixel_shader=p, x=x, y=y, **kw)


def _solid(w, h, c, x=0, y=0):
    return _grid(displayio.Bitmap(w, h, 1), _palette((c,)), x, y)


def _text(group, value, x, y, c=0xF1DFB0):
    obj = label.Label(terminalio.FONT, text=value, color=c, x=x, y=y)
    group.append(obj)
    return obj


def _set(obj, value):
    if obj.text != value:
        obj.text = value


def _place(obj, x, y):
    x, y = int(x), int(y)
    if obj.x != x:
        obj.x = x
    if obj.y != y:
        obj.y = y


def _form(level):
    return 0 if level < 4 else 1 if level < 8 else 2


def _maximum(level):
    return 22 + level * 4


def _creature(family, stage):
    """Nine silhouettes, three stages, two breathing frames; 2,304-byte atlas."""
    b = displayio.Bitmap(96, 48, 16)
    for frame in range(2):
        x = frame * 48
        bob = frame
        size = 22 + stage * 5
        left, top = 24 - size // 2, 39 - size + bob
        _oval(b, x + 5, 39, 38, 7, 1)
        # Tail/wing/leaf silhouettes are behind the main body.
        if family in (0, 3):
            for side in (0, 1):
                wx = 2 if side == 0 else 32
                _oval(b, x + wx, 20 - stage * 3 + bob, 15, 14 + stage * 4, 2)
                _oval(b, x + wx + 2, 20 - stage * 3 + bob, 10, 9 + stage * 3, 4)
                _rect(b, x + wx + 4, 23 + bob, 7, 2, 5)
        elif family in (2, 5):
            _oval(b, x + 30, 25 + bob, 15, 13, 2)
            _oval(b, x + 32, 22 + bob, 13, 12, 3)
            _oval(b, x + 36, 21 + bob, 7, 6, 4 if family == 2 else 12)
        elif family in (6, 7, 8):
            _oval(b, x + 3, 24 + bob, 17, 9, 2)
            _oval(b, x + 28, 20 + bob, 17, 10, 3)
            _rect(b, x + 5, 27 + bob, 10, 1, 4)
            _rect(b, x + 31, 24 + bob, 10, 1, 5)
        elif family == 4:
            for cx in (2, 34):
                _oval(b, x + cx, 23 + bob, 12, 11, 2)
                _oval(b, x + cx + 1, 21 + bob, 10, 9, 4)
                _rect(b, x + cx + 4, 20 + bob, 2, 5, 0)
        _oval(b, x + left - 1, top - 1, size + 2, size + 3, 1)
        _oval(b, x + left, top, size, size + 1, 2)
        _oval(b, x + left + 1, top, size - 3, size - 3, 3)
        _oval(b, x + left + 3, top + 2, size - 10, size // 2, 4)
        _oval(b, x + 17 - stage, 27 + bob, 15 + stage * 2, 12, 5)
        # Each family has its own signature anatomy, not just a palette swap.
        if family == 0:  # Ember bird: crest, beak, feather bands.
            for dx, h in ((17, 7), (22, 11), (27, 6)):
                _rect(b, x + dx, top - h + 4, 4, h, 3)
                _rect(b, x + dx, top - h + 4, 2, h - 2, 8)
            _rect(b, x + 22, 24 + bob, 7, 4, 8)
            _rect(b, x + 23, 28 + bob, 4, 2, 2)
        elif family == 1:  # Volcanic tortoise: layered shell and magma seams.
            for dx, dy in ((12, 18), (21, 12), (30, 18)):
                _rect(b, x + dx, dy - stage * 2 + bob, 7, 10, 14)
                _rect(b, x + dx + 2, dy - stage * 2 + bob, 2, 7, 8)
            _oval(b, x + 13, 26 + bob, 23, 13, 3)
        elif family == 2:  # Flame lynx: pointed ears, cheek ruff, striped brow.
            for dx in (12 - stage, 30 + stage):
                _rect(b, x + dx, top - 7, 6, 11, 1)
                _rect(b, x + dx + 1, top - 5, 4, 9, 4)
                _rect(b, x + dx + 2, top - 3, 2, 6, 9)
            _rect(b, x + 21, top + 2, 3, 6, 2)
            _rect(b, x + 27, top + 3, 2, 5, 2)
        elif family == 3:  # Tide axolotl: branched external gills and sail.
            for dx in (5, 37):
                for dy in (15, 20, 25):
                    _rect(b, x + dx, dy + bob, 6, 2, 9)
            _rect(b, x + 22, top - 6, 4, 10, 12)
            _rect(b, x + 23, top - 7, 2, 4, 7)
        elif family == 4:  # Shell crab: scalloped carapace and stalked eyes.
            for dx in (15, 21, 27):
                _rect(b, x + dx, top + 3, 2, 12, 2)
                _rect(b, x + dx + 1, top + 3, 1, 8, 12)
            _rect(b, x + 15, 18 + bob, 3, 9, 2)
            _rect(b, x + 30, 18 + bob, 3, 9, 2)
        elif family == 5:  # River otter: ears, pale muzzle, whiskers.
            _oval(b, x + 10, top - 2, 9, 9, 2)
            _oval(b, x + 30, top - 2, 9, 9, 2)
            _oval(b, x + 17, 26 + bob, 16, 9, 7)
            _rect(b, x + 9, 28 + bob, 9, 1, 12)
            _rect(b, x + 31, 29 + bob, 9, 1, 12)
        elif family == 6:  # Seed sprite: crown of leaves, flowers at final form.
            _rect(b, x + 23, top - 7, 2, 10, 2)
            _oval(b, x + 12, top - 8, 13, 7, 4)
            _oval(b, x + 25, top - 10, 13, 8, 11)
            if stage:
                _oval(b, x + 18, top - 8, 12, 9, 9)
                _oval(b, x + 21, top - 6, 6, 5, 8)
        elif family == 7:  # Fern deer: branching antlers and speckled coat.
            for dx in (12, 33):
                _rect(b, x + dx, top - 9, 2, 14, 5)
                _rect(b, x + dx - 3, top - 6, 8, 2, 5)
                _rect(b, x + dx - 3, top - 10, 2, 6, 4)
            for dx, dy in ((15, 27), (31, 31), (19, 35)):
                _rect(b, x + dx, dy + bob, 2, 2, 7)
        else:  # Root golem: bark plates, stone fists and canopy.
            for dx in (10, 17, 27, 34):
                _rect(b, x + dx, 27 + bob, 4, 12, 14)
                _rect(b, x + dx + 1, 28 + bob, 1, 8, 13)
            _oval(b, x + 8, top - 4, 33, 12, 2)
            _oval(b, x + 10, top - 5, 27, 10, 4)
        eye_y = 22 + bob if family != 4 else 18 + bob
        for dx in (16, 29):
            _rect(b, x + dx, eye_y, 4, 5, 1)
            _rect(b, x + dx + 1, eye_y, 2, 2, 7)
        if family != 0:
            _rect(b, x + 23, 28 + bob, 3, 2, 1)
        for dx in (13 - stage, 29 + stage):
            _oval(b, x + dx, 37, 8, 5, 2)
            _rect(b, x + dx + 1, 39, 5, 1, 5)
        if stage == 2:
            _rect(b, x + 5, 9 + bob, 2, 4, 8)
            _rect(b, x + 4, 10 + bob, 4, 2, 7)
            _rect(b, x + 40, 34 - bob, 2, 4, 8)
    return b


def _trainer():
    b = displayio.Bitmap(216, 24, 16)
    for direction in range(4):
        for frame in range(3):
            x = (direction * 3 + frame) * 18
            step = 0 if frame == 0 else (-1 if frame == 1 else 1)
            _oval(b, x + 2, 20, 15, 4, 1)
            _rect(b, x + 5, 16 + step, 4, 7, 7)
            _rect(b, x + 10, 16 - step, 4, 7, 7)
            _rect(b, x + 4, 11, 11, 8, 11)
            _rect(b, x + 5, 11, 9, 4, 12)
            _rect(b, x + 3, 13 + step, 3, 5, 6)
            _rect(b, x + 14, 13 - step, 2, 5, 6)
            _rect(b, x + 5, 4, 9, 8, 8)
            _rect(b, x + 6, 6, 7, 6, 10)
            _rect(b, x + 7, 7, 6, 3, 6)
            if direction == 3:
                _rect(b, x + 5, 6, 9, 5, 8)
                _rect(b, x + 6, 12, 7, 7, 9)
                _rect(b, x + 7, 14, 5, 2, 10)
            else:
                _rect(b, x + (6 if direction == 1 else 12 if direction == 2 else 8), 8, 1, 2, 0)
            _rect(b, x + 4, 2, 11, 5, 14)
            _rect(b, x + 5, 1, 8, 2, 15)
            _rect(b, x + 3, 6, 13, 2, 7)
            _rect(b, x + 5, 11, 9, 2, 14)
    return b


def _tree(b, x, y):
    _oval(b, x + 1, y + 25, 35, 10, 2)
    _rect(b, x + 16, y + 15, 6, 18, 8)
    _rect(b, x + 17, y + 20, 2, 11, 10)
    for dx, dy, w, h in ((0, 10, 34, 20), (2, 3, 23, 22), (15, 2, 21, 24)):
        _oval(b, x + dx, y + dy, w, h, 1)
        _oval(b, x + dx + 1, y + dy, w - 3, h - 5, 2)
        _oval(b, x + dx + 2, y + dy, w - 7, h - 9, 3)
    for dx, dy in ((7, 8), (19, 4), (22, 17), (10, 20)):
        _oval(b, x + dx, y + dy, 10, 6, 4)
        _rect(b, x + dx + 2, y + dy + 1, 4, 1, 5)


def _building(b, x, y, gym=False):
    w = 56
    _rect(b, x + 3, y + 27, w, 32, 7)
    _rect(b, x + 5, y + 29, w - 4, 25, 10)
    for yy in range(y + 32, y + 54, 5):
        _rect(b, x + 5, yy, w - 4, 1, 9)
    for yy in range(25):
        _rect(b, x + 13 - yy // 2, y + yy + 5, 37 + yy, 1, 11 if gym else 14)
        if yy % 5 == 0:
            _rect(b, x + 13 - yy // 2, y + yy + 5, 37 + yy, 1, 13 if gym else 15)
    for wx in (x + 9, x + 42):
        _rect(b, wx, y + 34, 11, 14, 8)
        _rect(b, wx + 1, y + 35, 9, 10, 11)
        _rect(b, wx + 2, y + 36, 3, 7, 13)
        _rect(b, wx, y + 48, 11, 2, 6)
    _rect(b, x + 25, y + 34, 13, 22, 7)
    _rect(b, x + 27, y + 36, 9, 18, 8)
    _rect(b, x + 29, y + 37, 5, 5, 6)
    _rect(b, x + 23, y + 55, 18, 4, 13)
    if gym:
        _oval(b, x + 25, y + 18, 13, 11, 6)
        _rect(b, x + 30, y + 19, 3, 9, 11)
    else:
        _rect(b, x + 29, y + 18, 5, 11, 6)
        _rect(b, x + 26, y + 21, 11, 5, 6)


def _world_art(route):
    b = _Canvas(240, 180)
    b.fill(3)
    for i in range(800):
        x, y = (i * 79 + 11) % 240, (i * 53 + i // 7) % 180
        _rect(b, x, y, 2, 1, 2 if i % 3 else 4)
        if i % 19 == 0:
            _rect(b, x, y - 2, 2, 2, 5 if i % 2 else 15)
    for y in range(180):
        bank = 218 + (y // 17 % 3)
        _rect(b, bank - 3, y, 243 - bank, 1, 5)
        _rect(b, bank, y, 240 - bank, 1, 11)
        if y % 13 == 0:
            _rect(b, bank + 3, y, 11, 1, 12)
    _rect(b, 37, 61, 163, 15, 9)
    _rect(b, 99, 63, 15, 99, 9)
    _rect(b, 0, 144, 240, 14, 9)
    for y in range(67, 160, 10):
        _rect(b, 102, y, 8, 2, 10)
    for x in range(7, 215, 15):
        _rect(b, x, 148, 7, 2, 10)
    for x in (73, 111, 150):
        _tree(b, x, 0)
    _tree(b, -12, 79)
    _tree(b, -6, 108)
    _building(b, 16, 4)
    _building(b, 157, 4, True)
    # Thick grass: silhouettes remain legible behind the trainer and companion.
    for ty in range(4, 7):
        for tx in range(4, 9):
            for dx, dy in ((2, 6), (8, 12), (14, 5)):
                x, y = tx * 20 + dx, ty * 20 + dy
                _rect(b, x, y, 2, 7, 2)
                _rect(b, x - 2, y + 1, 6, 2, 4)
                _rect(b, x, y, 1, 3, 5)
    # A bridge, a shrine and trail markers make actual interactions visible.
    _rect(b, 214, 140, 26, 24, 8)
    for yy in range(142, 164, 4):
        _rect(b, 214, yy, 26, 2, 10)
    _rect(b, 214, 140, 26, 2, 6)
    _rect(b, 214, 163, 26, 2, 6)
    _oval(b, 136, 145, 30, 14, 2)
    _rect(b, 143, 141, 15, 15, 11)
    _rect(b, 141, 139, 19, 4, 13)
    _rect(b, 147, 143, 6, 8, 12)
    for x in (8, 207):
        _rect(b, x, 129, 3, 19, 8)
        _rect(b, x - 5, 127, 15, 7, 10)
        _rect(b, x, 129, 4, 2, 7)
    if route >= 5:
        for x in (26, 192):
            _rect(b, x, 87, 9, 33, 11)
            _rect(b, x - 2, 85, 13, 5, 13)
            _rect(b, x + 2, 93, 2, 19, 12)
    return b.strips


def _world_palette(route):
    colors = list(INK)
    if route in (2, 5):
        colors[2:6] = (0x65563E, 0x8C784D, 0xC5A25B, 0xEDD494)
    elif route in (3, 4):
        colors[2:6] = (0x37675D, 0x598B78, 0x96B18C, 0xD4D8AE)
    elif route == 6:
        colors[2:6] = (0x384D64, 0x5C6F86, 0x91A3AD, 0xCBCCB3)
    return _palette(colors)


def _battle_art():
    b = _Canvas(240, 160, 16)
    b.fill(13)
    _rect(b, 0, 62, 240, 98, 3)
    for x in range(-20, 260, 40):
        _oval(b, x, 35 + (x % 3) * 4, 80, 54, 4)
    _rect(b, 0, 76, 240, 84, 3)
    for x, y in ((8, 46), (202, 42), (105, 54)):
        _tree(b, x, y)
    for i in range(140):
        _rect(b, (i * 61) % 240, 83 + (i * 19) % 77, 3, 1, 4)
    _oval(b, 139, 79, 85, 22, 2)
    _oval(b, 143, 78, 77, 17, 5)
    _oval(b, 11, 112, 100, 27, 2)
    _oval(b, 15, 109, 92, 23, 4)
    return b.strips


class Wildspark:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash = splash
        self._A, self._B, self._U, self._D = A_btn, B_btn, Up_btn, Dwn_btn
        self._L, self._R, self._sel, self._audio = L_btn, R_btn, Sel_btn, Audio
        self._exit = False
        self._family, self._badges, self._route, self._steps, self._tamed = 0, 0, 1, 0, 1
        self._caught, self._relics, self._potions, self._finished = 1, 0, 3, False
        self._party = [None] * 9
        self._party[0] = [3, _maximum(3), 0]
        self._new_game = True
        self._view, self._menu_cache, self._hero_art = {}, None, None
        self._load()

    def _name(self, family=None, level=None):
        family = self._family if family is None else family
        level = self._party[family][0] if level is None else level
        return FAMILIES[family][1][_form(level)]

    def _save(self):
        fields = (self._family, self._badges, self._route, self._steps, self._tamed,
                  self._caught, self._relics, self._potions, int(self._finished))
        party = [','.join(str(v) for v in (i, mon[0], mon[1], mon[2]))
                 for i, mon in enumerate(self._party) if mon is not None]
        try:
            with open('/wildspark.tmp', 'wt') as f:
                f.write('WS2,' + ','.join(str(v) for v in fields) + '|' + ';'.join(party))
            os.rename('/wildspark.tmp', '/wildspark.sav')
            return True
        except OSError:
            return False

    def _load(self):
        try:
            with open('/wildspark.sav', 'rt') as f:
                data = f.readline().strip()
            party = [None] * 9
            if data.startswith('WS2,'):
                header, records = data.split('|', 1)
                values = [int(v) for v in header.split(',')[1:]]
                if len(values) != 9:
                    return
                family, badges, route, steps, tamed, caught, relics, potions, finished = values
                if not (0 <= family < 9 and 0 <= badges <= 3 and 1 <= route <= 6 and steps >= 0
                        and tamed >= 1 and 0 <= caught < (1 << 27) and 0 <= relics < 64
                        and 0 <= potions <= 3 and finished in (0, 1)):
                    return
                for record in records.split(';'):
                    i, level, hp, xp = [int(v) for v in record.split(',')]
                    if not (0 <= i < 9 and party[i] is None and 1 <= level <= 30
                            and 0 <= hp <= _maximum(level) and 0 <= xp < 8 + level * 3):
                        return
                    party[i] = [level, hp, xp]
                if party[family] is None:
                    return
            else:
                values = [int(v) for v in data.split(',')]
                if len(values) != 7:
                    return
                family, level, hp, badges, route, steps, tamed = values
                if not (0 <= family < 9 and 1 <= level <= 30 and hp >= 0
                        and 0 <= badges <= 3 and 1 <= route <= 6 and steps >= 0 and tamed >= 1):
                    return
                party[family] = [level, min(hp, _maximum(level)), 0]
                caught = sum(1 << (family * 3 + stage) for stage in range(_form(level) + 1))
                relics, potions, finished = (1 << (route - 1)) - 1, 3, False
            self._family, self._badges, self._route, self._steps, self._tamed = family, badges, route, steps, tamed
            self._caught, self._relics, self._potions, self._finished = caught, relics, potions, bool(finished)
            self._party, self._new_game = party, False
        except (OSError, ValueError):
            pass

    def _clear(self):
        while len(self._splash):
            self._splash.pop()
        self._view = {}
        gc.collect()

    def _background(self, strips, palette, y=0):
        offset = y
        for strip in strips:
            self._splash.append(_grid(strip, palette, y=offset))
            offset += strip.height

    def _prepare_menu(self):
        if self._menu_cache is not None:
            return
        gc.collect()
        group = displayio.Group(x=8, y=32)
        for y in range(0, 208, 16):
            group.append(_solid(224, 16, INK[0], y=y))
        group.append(_solid(220, 2, INK[10], 2, 2))
        title = _text(group, 'WILDSPARK', 10, 17)
        rows = [_text(group, '', 10, 40 + i * 19) for i in range(5)]
        detail = _text(group, '', 10, 148, INK[13])
        info = _text(group, '', 10, 163, INK[13])
        hint = _text(group, 'A choose / B back', 10, 193, INK[10])
        portrait = _grid(_creature(0, 0), _palette(CREATURE_COLORS[0], True), 165, 133, tile_width=48, tile_height=48)
        portrait.hidden = True
        group.append(portrait)
        self._menu_cache = (group, title, rows, detail, info, hint, portrait)

    def _choose(self, title, items, details=None, portraits=None):
        self._prepare_menu()
        group, heading, rows, detail, info, hint, portrait = self._menu_cache
        _set(heading, title)
        _set(hint, 'Up/Down choose / A select / B back')
        choice, last, dirty = 0, time.monotonic(), True
        a_was, b_was, s_was = not self._A.value, not self._B.value, not self._sel.value
        self._splash.append(group)
        try:
            while not self._exit:
                now = time.monotonic()
                if not self._U.value and not self._D.value:
                    self._exit = True
                    return -1
                if now - last > 0.18:
                    delta = -1 if not self._U.value else (1 if not self._D.value else 0)
                    if delta:
                        choice = (choice + delta) % len(items)
                        last, dirty = now, True
                if dirty:
                    page = choice // 5 * 5
                    for i, row in enumerate(rows):
                        index = page + i
                        row.hidden = index >= len(items)
                        if index < len(items):
                            _set(row, ('> ' if index == choice else '  ') + items[index])
                            row.color = INK[6] if index == choice else INK[12]
                    message = details[choice] if details else ''
                    width = 24 if portraits else 33
                    split = message.rfind(' ', 0, width + 1) if len(message) > width else len(message)
                    if split <= 0:
                        split = width
                    _set(detail, message[:split])
                    _set(info, message[split:].strip() if len(message) > split else '%d / %d' % (choice + 1, len(items)))
                    portrait.hidden = portraits is None
                    if portraits:
                        family, stage, known = portraits[choice]
                        # Replace one small portrait; never keep all 27 forms resident.
                        colors = CREATURE_COLORS[family // 3] if known else (0,) + (INK[11],) * 15
                        replacement = _grid(_creature(family, stage), _palette(colors, True), 165, 133, tile_width=48, tile_height=48)
                        group.remove(portrait)
                        group.append(replacement)
                        portrait = replacement
                        self._menu_cache = (group, heading, rows, detail, info, hint, portrait)
                    dirty = False
                a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
                if (b_down and not b_was) or (s_down and not s_was):
                    return -1
                if a_down and not a_was:
                    return choice
                a_was, b_was, s_was = a_down, b_down, s_down
                time.sleep(0.03)
        finally:
            self._splash.remove(group)
            gc.collect()
        return -1

    def _notice(self, title, text):
        return self._choose(title, ('Continue',), (text,))

    def _partners(self, battle=False):
        families = [i for i, mon in enumerate(self._party) if mon is not None]
        items = [self._name(i) + ' L%d HP%d' % (self._party[i][0], self._party[i][1]) for i in families]
        portraits = [(i, _form(self._party[i][0]), True) for i in families]
        choice = self._choose('YOUR PARTNERS', items, [FAMILIES[i][0] for i in families], portraits)
        if choice < 0:
            return False
        family = families[choice]
        if self._party[family][1] == 0:
            self._notice('PARTNER RESTING', 'Visit the clinic to recover.')
            return False
        changed = family != self._family
        self._family = family
        return changed

    def _guide(self):
        items, details, portraits = [], [], []
        for family, (kind, names) in enumerate(FAMILIES):
            for stage, name in enumerate(names):
                known = bool(self._caught & (1 << (family * 3 + stage)))
                items.append(name if known else '??? / ' + kind + ' form ' + str(stage + 1))
                habitat = family % 3 + 1
                details.append(('CAUGHT / ' if known else 'SEARCH / ') + 'TRAIL %d OR %d' % (habitat, habitat + 3))
                portraits.append((family, stage, known))
        count = sum(1 for i in range(27) if self._caught & (1 << i))
        while not self._exit and self._choose('FIELD GUIDE / %d/27' % count, items, details, portraits) >= 0:
            pass

    def _pause(self, battle=False):
        items = ('Resume', 'Controls', 'Retreat to trail', 'Leave game') if battle else ('Resume', 'Partners', 'Field guide', 'Save journey', 'Leave game')
        choice = self._choose('WILDSPARK / EMBLEMS %d' % self._badges, items)
        if battle:
            if choice == 1:
                self._notice('CATCHING CREATURES', 'Weaken, then Catch at half HP. No items.')
            elif choice == 2:
                self._battle_result = 'RETREAT'
            elif choice == 3:
                self._exit = True
        else:
            if choice == 1:
                self._partners()
            elif choice == 2:
                self._guide()
            elif choice == 3:
                self._notice('JOURNEY SAVE', 'Saved.' if self._save() else 'Save failed: USB/read-only/full.')
            elif choice == 4:
                self._exit = True

    def _choose_starter(self):
        self._clear()
        self._background(_battle_art(), _world_palette(1))
        self._splash.append(_solid(240, 80, INK[0], y=160))
        _text(self._splash, 'WELCOME TO WILDSPARK', 45, 18)
        _text(self._splash, 'Choose your first companion.', 30, 146)
        families = (0, 3, 6)
        for i, family in enumerate(families):
            self._splash.append(_grid(_creature(family, 0), _palette(CREATURE_COLORS[i], True), 14 + i * 78, 70, tile_width=48, tile_height=48))
            _text(self._splash, FAMILIES[family][1][0], 17 + i * 78, 123)
        marker = _text(self._splash, '> CINDLE / EMBER', 25, 183)
        _text(self._splash, 'Left/Right choose / A bond', 35, 215)
        choice, last = 0, time.monotonic()
        a_was = not self._A.value
        while not self._exit:
            if not self._U.value and not self._D.value:
                self._exit = True
                return
            now = time.monotonic()
            if now - last > 0.18:
                delta = -1 if not self._L.value else (1 if not self._R.value else 0)
                if delta:
                    choice, last = (choice + delta) % 3, now
                    _set(marker, '> ' + FAMILIES[families[choice]][1][0] + ' / ' + TYPES[choice])
            down = not self._A.value
            if down and not a_was:
                self._family = families[choice]
                self._party = [None] * 9
                self._party[self._family] = [3, _maximum(3), 0]
                self._caught = 1 << (self._family * 3)
                self._new_game = False
                return
            a_was = down
            time.sleep(0.03)

    def _portrait(self, family, level, x, y):
        return _grid(_creature(family, _form(level)), _palette(CREATURE_COLORS[family // 3], True), x, y, tile_width=48, tile_height=48)

    def _build_battle(self, family, level, gym=False, final=False):
        self._clear()
        self._foe_family, self._foe_level = family, level
        self._foe_max = 18 + level * 3 + (10 if gym else 0) + (16 if final else 0)
        self._foe_hp = self._foe_max
        self._focus, self._turn = 1, 0
        self._gym, self._final, self._battle_result = gym, final, None
        self._battle_note = 'Weaken then Catch. B retreats.' if not (gym or final) else 'Guard against the charged burst.'
        self._background(_battle_art(), _world_palette(self._route))
        self._splash.append(_solid(240, 80, INK[0], y=160))
        ally = self._portrait(self._family, self._party[self._family][0], 34, 80)
        foe = self._portrait(family, level, 157, 39)
        self._splash.append(ally)
        self._splash.append(foe)
        self._view['ally'], self._view['foe'] = ally, foe
        self._view['foe_name'] = _text(self._splash, self._name(family, level) + ' L%d' % level, 112, 12, INK[0])
        self._view['intent'] = _text(self._splash, '', 112, 40, INK[0])
        self._view['ally_name'] = _text(self._splash, '', 6, 141, INK[6])
        bars = []
        for x, y in ((113, 22), (7, 148)):
            b = displayio.Bitmap(90, 5, 2)
            self._splash.append(_grid(b, _palette((INK[7], INK[4])), x, y))
            bars.append(b)
        self._view['bars'] = bars
        self._view['focus'] = _text(self._splash, '', 111, 151, INK[6])
        self._view['commands'] = [_text(self._splash, '', 8 + (i % 2) * 120, 167 + (i // 2) * 16) for i in range(8)]
        self._view['note'] = _text(self._splash, '', 5, 231, INK[10])
        self._sync_battle(0)

    def _sync_battle(self, choice):
        mon = self._party[self._family]
        _set(self._view['ally_name'], '%s L%d HP%d/%d' % (self._name(), mon[0], mon[1], _maximum(mon[0])))
        intent = ('STRIKE', 'GATHERING', 'BURST!')[self._turn % 3]
        _set(self._view['intent'], FAMILIES[self._foe_family][0] + ' / ' + intent)
        _set(self._view['focus'], 'Focus %d/3' % self._focus)
        for b, value, maximum in ((self._view['bars'][0], self._foe_hp, self._foe_max), (self._view['bars'][1], mon[1], _maximum(mon[0]))):
            b.fill(0)
            _rect(b, 0, 0, max(0, int(90 * value / maximum)), 5, 1)
        names = ('Strike +focus', 'Burst -2', 'Guard +focus', 'Catch READY' if self._foe_hp <= self._foe_max // 2 and not (self._gym or self._final) else 'Catch', 'Tonic (%d)' % self._potions, 'Switch', 'Weaken', 'Flee')
        for i, value in enumerate(names):
            _set(self._view['commands'][i], ('>' if i == choice else ' ') + value)
            self._view['commands'][i].color = INK[6] if i == choice else INK[12]
        _set(self._view['note'], self._battle_note)

    @staticmethod
    def _effective(attacker, defender, damage):
        a, d = attacker // 3, defender // 3
        if (a, d) in ((0, 2), (2, 1), (1, 0)):
            return damage * 3 // 2
        if a != d:
            return max(1, damage * 3 // 4)
        return damage

    def _award_xp(self):
        mon = self._party[self._family]
        before = _form(mon[0])
        mon[2] += 5 + self._foe_level * 2
        while mon[0] < 30 and mon[2] >= 8 + mon[0] * 3:
            mon[2] -= 8 + mon[0] * 3
            mon[0] += 1
            mon[1] = min(_maximum(mon[0]), mon[1] + 7)
        if mon[0] == 30:
            mon[2] = 0
        for stage in range(_form(mon[0]) + 1):
            self._caught |= 1 << (self._family * 3 + stage)
        return _form(mon[0]) > before

    def _enemy_turn(self, guard=False):
        intent = self._turn % 3
        self._turn += 1
        if intent == 1:
            self._battle_note = 'Foe is charging. Guard next turn!'
            return
        damage = 3 + self._foe_level // 2
        if intent == 2:
            damage = self._effective(self._foe_family, self._family, damage + 6)
        if guard:
            damage = max(1, damage // 3)
        mon = self._party[self._family]
        mon[1] = max(0, mon[1] - damage)
        self._battle_note += ' Foe -%d HP.' % damage
        self._battle_note = self._battle_note[:38]
        self._audio.play('hit')
        if mon[1] == 0:
            if any(other is not None and other[1] > 0 for other in self._party):
                self._battle_note = 'Partner fainted. Choose Switch.'
            else:
                self._battle_result = 'DEFEAT'

    def _act(self, action):
        mon = self._party[self._family]
        if self._battle_result:
            return
        if mon[1] == 0:
            self._battle_note = 'Partner fainted. Choose Switch.'
            return
        guard = False
        if action == 0:
            self._foe_hp = max(0, self._foe_hp - (4 + mon[0]))
            self._focus = min(3, self._focus + 1)
            self._battle_note = 'Strike! Focus gathered.'
            self._audio.play('strike')
        elif action == 1:
            if self._focus < 2:
                self._battle_note = 'Need 2 focus: Strike or Guard first.'
                return
            self._focus -= 2
            damage = self._effective(self._family, self._foe_family, 7 + mon[0] * 2)
            self._foe_hp = max(0, self._foe_hp - damage)
            self._battle_note = 'Element burst! %d damage.' % damage
            self._audio.play('support')
        elif action == 2:
            self._focus = min(3, self._focus + 1)
            guard = True
            self._battle_note = 'Guard raised.'
        elif action == 3:
            if self._gym or self._final:
                self._battle_note = 'Challenge partners cannot be caught.'
                return
            if self._foe_hp > self._foe_max // 2:
                self._battle_note = 'Use Weaken, then Catch at half HP.'
                return
            f = self._foe_family
            if self._party[f] is None:
                self._party[f] = [self._foe_level, _maximum(self._foe_level), 0]
            self._caught |= 1 << (f * 3 + _form(self._foe_level))
            self._tamed += 1
            self._battle_result = 'BONDED'
            self._audio.play('collect')
            return
        elif action == 6:
            self._foe_hp = max(1, self._foe_hp - (4 + mon[0]))
            self._focus = min(3, self._focus + 1)
            self._battle_note = 'Safe hit! Catch at half HP.'
            self._audio.play('strike')
        elif action == 7:
            self._battle_result = 'RETREAT'
            return
        elif action == 4:
            if self._potions == 0:
                self._battle_note = 'No tonics. Rest at the clinic.'
                return
            if mon[1] == _maximum(mon[0]):
                self._battle_note = 'Already at full health.'
                return
            self._potions -= 1
            mon[1] = min(_maximum(mon[0]), mon[1] + 18)
            self._battle_note = 'Tonic restored 18 HP.'
        else:
            return
        if self._foe_hp <= 0:
            self._battle_result = 'WON'
            self._audio.play('win')
            return  # A defeated foe must never retaliate.
        self._enemy_turn(guard)

    def _battle(self, family, level, gym=False, final=False):
        self._build_battle(family, level, gym, final)
        choice, last, last_anim = 0, time.monotonic(), 0
        a_was, b_was, s_was = not self._A.value, not self._B.value, not self._sel.value
        while not self._exit and self._battle_result is None:
            now = time.monotonic()
            if not self._U.value and not self._D.value:
                self._exit = True
                break
            if now - last > 0.18:
                delta = -2 if not self._U.value else 2 if not self._D.value else -1 if not self._L.value else 1 if not self._R.value else 0
                if delta:
                    choice = (choice + delta) % 8
                    last = now
                    self._sync_battle(choice)
            if now - last_anim > 0.4:
                frame = int(now * 2.5) % 2
                self._view['ally'][0] = frame
                self._view['foe'][0] = 1 - frame
                last_anim = now
            a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
            modal = False
            if s_down and not s_was:
                self._pause(True)
                modal = True
            elif b_down and not b_was:
                self._battle_result = 'RETREAT'
            elif a_down and not a_was:
                if choice == 5:
                    was_fainted = self._party[self._family][1] == 0
                    if self._partners(True):
                        old = self._view['ally']
                        self._splash.remove(old)
                        self._view['ally'] = self._portrait(self._family, self._party[self._family][0], 34, 80)
                        self._splash.append(self._view['ally'])
                        if not was_fainted:
                            self._battle_note = 'Partner switched.'
                            self._enemy_turn()
                    modal = True
                else:
                    self._act(choice)
                self._sync_battle(choice)
            if modal:
                a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
                last = time.monotonic()
                self._sync_battle(choice)
            a_was, b_was, s_was = a_down, b_down, s_down
            time.sleep(0.03)
        won = self._battle_result in ('WON', 'BONDED')
        if not self._exit:
            if won:
                evolved = self._award_xp()
                title = 'EVOLUTION! ' + self._name() if evolved else ('CREATURE CAUGHT!' if self._battle_result == 'BONDED' else 'VICTORY!')
                self._notice(title, 'Partner experience increased.')
            elif self._battle_result == 'DEFEAT':
                self._rest()
                self._notice('BACK ON YOUR FEET', 'Clinic restored your companions.')
        return won

    def _rest(self):
        for mon in self._party:
            if mon is not None:
                mon[1] = _maximum(mon[0])
        self._potions = 3

    def _mini_partner(self):
        art = _creature(self._family, _form(self._party[self._family][0]))
        b = displayio.Bitmap(24, 24, 16)
        for y in range(24):
            for x in range(24):
                b[x, y] = art[x * 2, y * 2]
        return _grid(b, _palette(CREATURE_COLORS[self._family // 3], True))

    def _build_world(self):
        self._clear()
        self._background(_world_art(self._route), _world_palette(self._route), y=40)
        self._splash.append(_solid(240, 40, INK[0]))
        self._splash.append(_solid(240, 20, INK[0], y=220))
        self._view['title'] = _text(self._splash, '', 5, 8)
        self._view['status'] = _text(self._splash, '', 5, 22, INK[13])
        self._view['quest'] = _text(self._splash, '', 5, 34, INK[10])
        self._view['hint'] = _text(self._splash, '', 5, 230, INK[10])
        b = displayio.Bitmap(12, 16, 4)
        for y in range(16):
            width = max(0, 5 - abs(y - 7))
            _rect(b, 6 - width, y, width * 2, 1, 1)
            if width > 1:
                _rect(b, 6, y, width - 1, 1, 2)
        relic = _grid(b, _palette((0, INK[10], INK[6], INK[13]), True), 144, 174)
        relic.hidden = bool(self._relics & (1 << (self._route - 1)))
        self._splash.append(relic)
        self._view['relic'] = relic
        partner = self._mini_partner()
        self._splash.append(partner)
        self._view['partner'] = partner
        self._view['partner_key'] = (self._family, _form(self._party[self._family][0]))
        if self._hero_art is None:
            self._hero_art = _trainer()
        hero = _grid(self._hero_art, _palette(transparent=True), tile_width=18, tile_height=24)
        self._splash.append(hero)
        self._view['hero'] = hero

    @staticmethod
    def _walkable(x, y):
        if not (0 <= x <= 11 and 1 <= y <= 8):
            return False
        if y <= 2 and (x <= 3 or x >= 8):
            return False
        if y <= 1 and 4 <= x <= 7:
            return False
        if x == 0 and 4 <= y <= 6:
            return False
        if x == 11 and y != 7:
            return False
        return True

    def _sync_world(self, pos):
        mon = self._party[self._family]
        _set(self._view['title'], 'R%d %s / EMBLEMS %d' % (self._route, ROUTES[self._route - 1], self._badges))
        _set(self._view['status'], '%s L%d HP%d/%d' % (self._name(), mon[0], mon[1], _maximum(mon[0])))
        found = self._relics & (1 << (self._route - 1))
        quest = 'Relic found. Follow the east trail.' if found else 'Find the glowing shrine to the south.'
        if self._route % 2 == 0 and self._badges < self._route // 2 and found:
            quest = 'Challenge the northern sanctuary.'
        if self._badges == 3:
            quest = 'Rival awaits at the sanctuary.' if not self._finished else 'Champion! Explore and fill the guide.'
        _set(self._view['quest'], quest)
        if tuple(pos) == (2, 3):
            hint = 'A clinic / rest and refill tonics'
        elif tuple(pos) == (9, 3):
            hint = 'A sanctuary challenge'
        elif tuple(pos) == (7, 7):
            hint = 'A recover ' + RELICS[self._route - 1]
        elif tuple(pos) in ((0, 7), (11, 7)):
            hint = 'A follow trail'
        elif 4 <= pos[0] <= 8 and 4 <= pos[1] <= 6:
            hint = 'A search grass / B partners'
        else:
            hint = 'A interact / B partners / SEL menu'
        _set(self._view['hint'], hint)
        self._view['relic'].hidden = bool(found)
        key = (self._family, _form(mon[0]))
        if key != self._view['partner_key']:
            old = self._view['partner']
            x, y = old.x, old.y
            self._splash.remove(old)
            self._view['partner'] = self._mini_partner()
            self._splash.append(self._view['partner'])
            _place(self._view['partner'], x, y)
            self._view['partner_key'] = key

    def _wild_target(self):
        # Nine searches on late trails expose all three families and forms.
        cycle = self._steps // 6
        band = (self._route - 1) % 3
        family = ((cycle + self._route) % 3) * 3 + band
        stage = (cycle // 3) % (3 if self._route >= 4 else 2)
        level = (2 + min(1, self._route // 3),
                 4 + min(3, self._route // 2), 8 + max(0, self._route - 4))[stage]
        return family, level

    def _encounter(self):
        if self._party[self._family][1] == 0:
            self._notice('PARTNER NEEDS REST', 'Visit the clinic or switch partners.')
            return False
        family, level = self._wild_target()
        self._battle(family, level)
        return True

    def _travel(self, delta):
        if delta < 0:
            if self._route == 1:
                return 'This is the first trail.'
            self._route -= 1
            return None
        if self._route == 6:
            return 'The sanctuary holds the final trial.'
        if not self._relics & (1 << (self._route - 1)):
            return 'Recover this trail\'s relic first.'
        if self._route % 2 == 0 and self._badges < self._route // 2:
            return 'Earn this sanctuary\'s emblem first.'
        self._route += 1
        return None

    def _interact(self, pos):
        """Return True only when a route/battle transition needs new scenery."""
        if pos == (2, 3):
            self._rest()
            self._notice('HEARTH CLINIC', 'All partners rested. Tonics refilled.')
        elif pos == (7, 7):
            bit = 1 << (self._route - 1)
            if not self._relics & bit:
                self._relics |= bit
                self._audio.play('collect')
                self._notice(RELICS[self._route - 1], 'Relic recorded in your journey.')
            else:
                self._notice('WAYSTONE', 'This relic is already recovered.')
        elif pos == (9, 3):
            if self._party[self._family][1] == 0:
                self._notice('PARTNER NEEDS REST', 'Visit the clinic before a challenge.')
            elif self._badges == 3:
                if self._battle(8, 12, final=True):
                    self._finished = True
                    self._notice('WILDSPARK CHAMPION', 'Your companions light the way.')
                    self._save_notice()
                return True
            elif self._route >= (self._badges + 1) * 2 and self._relics & (1 << (self._route - 1)):
                if self._battle(self._badges * 3 + 2, 4 + self._badges * 3, gym=True):
                    self._badges += 1
                    self._notice('EMBLEM EARNED', 'A new trail is open. Well done!')
                    self._save_notice()
                return True
            else:
                self._notice('SANCTUARY', 'Recover a relic on trails 2, 4, 6.')
        elif pos in ((0, 7), (11, 7)):
            message = self._travel(-1 if pos[0] == 0 else 1)
            if message:
                self._notice('TRAIL MARKER', message)
            else:
                return True
        elif 4 <= pos[0] <= 8 and 4 <= pos[1] <= 6:
            self._steps += 6
            return self._encounter()
        return False

    def _save_notice(self):
        if not self._save():
            self._notice('SAVE UNAVAILABLE', 'Progress in memory. Save at SEL later.')

    def _world(self):
        pos, previous = [3, 7], [2, 7]
        self._build_world()
        px, py = pos[0] * 20 + 1.0, 40 + pos[1] * 20 - 5.0
        last = time.monotonic()
        last_move, direction, grass_steps, grace = last, 0, 0, 6
        pending_action = False
        a_was, b_was, s_was = not self._A.value, not self._B.value, not self._sel.value
        while not self._exit:
            now = time.monotonic()
            dt, last = now - last, now
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
            tx, ty = pos[0] * 20 + 1, 40 + pos[1] * 20 - 5
            arrived = abs(px - tx) < 0.5 and abs(py - ty) < 0.5
            encounter = False
            if arrived and (dx or dy) and not pending_action and now - last_move > 0.18:
                if self._walkable(pos[0] + dx, pos[1] + dy):
                    previous = pos[:]
                    pos[0] += dx
                    pos[1] += dy
                    self._steps += 1
                    grace = max(0, grace - 1)
                    if 4 <= pos[0] <= 8 and 4 <= pos[1] <= 6:
                        grass_steps += 1
                        encounter = grass_steps >= 6 and grace == 0
                last_move = now
            tx, ty = pos[0] * 20 + 1, 40 + pos[1] * 20 - 5
            speed = min(20, dt * 160)
            px += max(-speed, min(speed, tx - px))
            py += max(-speed, min(speed, ty - py))
            moving = abs(px - tx) > 0.5 or abs(py - ty) > 0.5
            _place(self._view['hero'], px, py)
            frame = direction * 3 + (1 + int(now * 9) % 2 if moving else 0)
            if self._view['hero'][0] != frame:
                self._view['hero'][0] = frame
            _place(self._view['partner'], previous[0] * 20 - 2, previous[1] * 20 + 36)
            a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
            if a_down and not a_was:
                pending_action = True
            modal, rebuild, old_route = False, False, self._route
            if encounter:
                rebuild, modal = self._encounter(), True
                grass_steps, grace = 0, 6
            elif s_down and not s_was:
                self._pause()
                modal = True
            elif b_down and not b_was:
                self._partners()
                modal = True
            elif pending_action and not moving:
                rebuild, modal = self._interact(tuple(pos)), True
                grass_steps, grace = 0, 6
            if rebuild and not self._exit:
                self._build_world()
                if old_route != self._route:
                    pos, previous = [3, 7], [2, 7]
                px, py = pos[0] * 20 + 1.0, 40 + pos[1] * 20 - 5.0
                _place(self._view['hero'], px, py)
            if modal:
                pending_action = False
                last = last_move = time.monotonic()
                a_down, b_down, s_down = not self._A.value, not self._B.value, not self._sel.value
            if not self._exit:
                self._sync_world(pos)
            a_was, b_was, s_was = a_down, b_down, s_down
            time.sleep(0.02)

    def Game(self):
        self._exit = False
        self._prepare_menu()
        if self._new_game:
            self._choose_starter()
        if not self._exit:
            if not any(mon is not None and mon[1] > 0 for mon in self._party):
                self._rest()
            self._world()
        self._clear()
        self._menu_cache, self._hero_art = None, None
        gc.collect()
        return True
