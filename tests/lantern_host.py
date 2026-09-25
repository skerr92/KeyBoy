"""Small displayio double and dependency-free PNG renderer for Lantern Acre.

Run from repo root: python3 tests/test_lantern_acre.py
Preview: python3 tools/preview_lantern_acre.py
This checks game logic/scene retention, not CircuitPython timing or SPI traffic.
"""
import importlib.util
import struct
import sys
import types
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Bitmap:
    def __init__(self, width, height, colors):
        self.width, self.height, self.colors = width, height, colors
        self.pixels = bytearray(width * height)
        self.writes = 0

    def __getitem__(self, key):
        x, y = key
        assert 0 <= x < self.width and 0 <= y < self.height
        return self.pixels[y * self.width + x]

    def __setitem__(self, key, value):
        x, y = key
        assert 0 <= x < self.width and 0 <= y < self.height
        assert 0 <= value < self.colors
        self.pixels[y * self.width + x] = value
        self.writes += 1

    def fill(self, value):
        self.pixels[:] = bytes([value]) * len(self.pixels)
        self.writes += 1


class Palette(list):
    def __init__(self, size):
        super().__init__([0] * size)
        self.transparent = set()

    def make_transparent(self, index):
        self.transparent.add(index)


class TileGrid:
    def __init__(self, bitmap, pixel_shader, x=0, y=0, tile_width=None, tile_height=None):
        self.bitmap, self.pixel_shader = bitmap, pixel_shader
        self.x, self.y, self.hidden = x, y, False
        self.tile_width = tile_width or bitmap.width
        self.tile_height = tile_height or bitmap.height
        assert bitmap.width % self.tile_width == 0
        assert bitmap.height % self.tile_height == 0
        self.index = 0

    def __getitem__(self, index):
        assert index == 0
        return self.index

    def __setitem__(self, index, value):
        assert index == 0
        assert 0 <= value < (self.bitmap.width // self.tile_width) * (self.bitmap.height // self.tile_height)
        self.index = value


class Group(list):
    def __init__(self, x=0, y=0):
        super().__init__()
        self.x, self.y, self.hidden = x, y, False


class Label:
    def __init__(self, font, text, color, x=0, y=0, scale=1):
        self.text, self.color, self.x, self.y, self.scale = text, color, x, y, scale
        self.hidden = False


class Button:
    value = True


class Audio:
    def play(self, name):
        pass


def load():
    sys.modules['displayio'] = types.SimpleNamespace(Bitmap=Bitmap, Palette=Palette, TileGrid=TileGrid, Group=Group)
    sys.modules['terminalio'] = types.SimpleNamespace(FONT=None)
    sys.modules['adafruit_display_text'] = types.SimpleNamespace(label=types.SimpleNamespace(Label=Label))
    spec = importlib.util.spec_from_file_location('lantern_under_test', ROOT / 'Firmware/Games/Lantern_Acre/Lantern_Acre.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def game(module):
    from unittest.mock import patch
    with patch('builtins.open', side_effect=OSError):
        g = module.LanternAcre(Group(), *[Button() for _ in range(7)], Audio())
    return g


# Readable 5x7 approximation of terminalio for the desktop preview only.
FONT = {
'A': '0E11111F111111', 'B': '1E11111E11111E', 'C': '0E11101010110E',
'D': '1E11111111111E', 'E': '1F10101E10101F', 'F': '1F10101E101010',
'G': '0E11101711110F', 'H': '1111111F111111', 'I': '0E04040404040E',
'J': '0702020212120C', 'K': '11121418141211', 'L': '1010101010101F',
'M': '111B1515111111', 'N': '11191513111111', 'O': '0E11111111110E',
'P': '1E11111E101010', 'Q': '0E11111115120D', 'R': '1E11111E141211',
'S': '0F10100E01011E', 'T': '1F040404040404', 'U': '1111111111110E',
'V': '11111111110A04', 'W': '11111115151B11', 'X': '11110A040A1111',
'Y': '11110A04040404', 'Z': '1F01020408101F', '0': '0E11131519110E',
'1': '040C040404040E', '2': '0E11010204081F', '3': '1E01010601011E',
'4': '02060A121F0202', '5': '1F10101E01011E', '6': '0E10101E11110E',
'7': '1F010204080808', '8': '0E11110E11110E', '9': '0E11110F01010E',
':': '00040400040400', '/': '01010204081010', '$': '040F140E051E04',
'>': '10080402040810', '-': '0000001F000000', '.': '00000000000C0C',
'!': '04040404040004', '?': '0E110102040004', '+': '0004041F040400',
'(': '02040808080402', ')': '08040202020408', '&': '0C12140C15120D',
'[': '0E08080808080E', ']': '0E02020202020E', "'": '04040800000000',
}


def render(group, path, scale=3):
    pixels = [0] * (240 * 240)

    def put(x, y, color):
        if 0 <= x < 240 and 0 <= y < 240:
            pixels[y * 240 + x] = color

    def draw(obj, ox=0, oy=0):
        if obj.hidden:
            return
        x, y = ox + obj.x, oy + obj.y
        if isinstance(obj, Group):
            for child in obj:
                draw(child, x, y)
        elif isinstance(obj, TileGrid):
            b, p = obj.bitmap, obj.pixel_shader
            cols = b.width // obj.tile_width
            sx, sy = obj.index % cols * obj.tile_width, obj.index // cols * obj.tile_height
            for yy in range(obj.tile_height):
                for xx in range(obj.tile_width):
                    value = b[sx + xx, sy + yy]
                    if value not in p.transparent:
                        put(x + xx, y + yy, p[value])
        else:
            for i, ch in enumerate(obj.text.upper()):
                rows = FONT.get(ch, '00000000000000')
                for yy in range(7):
                    row = int(rows[yy * 2:yy * 2 + 2], 16)
                    for xx in range(5):
                        if row & (16 >> xx):
                            put(x + i * 6 + xx, y - 3 + yy, obj.color)
    draw(group)
    raw = bytearray()
    for y in range(240):
        row = bytearray([0])
        for x in range(240):
            c = pixels[y * 240 + x]
            row.extend(bytes((c >> 16, (c >> 8) & 255, c & 255)) * scale)
        raw.extend(row * scale)

    def chunk(name, data):
        return struct.pack('!I', len(data)) + name + data + struct.pack('!I', zlib.crc32(name + data) & 0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 240 * scale, 240 * scale, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
