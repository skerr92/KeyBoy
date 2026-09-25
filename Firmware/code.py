import board, displayio, time, sys, gc
from adafruit_st7789 import ST7789
import busio, microcontroller, pwmio
from digitalio import DigitalInOut, Direction
from adafruit_display_text import label
import terminalio, io
from KeyBoyAudio import KeyBoyAudio

displayio.release_displays()
brightness = 5
bl = pwmio.PWMOut(board.IO38, frequency=100, duty_cycle=int(brightness * 2 * 65535 / 100))
spi = busio.SPI(clock=microcontroller.pin.GPIO36, MOSI=microcontroller.pin.GPIO33)
LooseCowsScore = 0
try:
    game1_score = io.open('/cows.txt','rt')
    temp = game1_score.readline()
    game1_score.close()
    if (int(temp) > 0):
        LooseCowsScore = int(temp)
        print("Loose Cows High Score: ", LooseCowsScore)
except OSError:
    print("no score file")


tft_dc = board.IO35
tft_cs = microcontroller.pin.GPIO34

# setup user buttons
R = DigitalInOut(board.IO18)
R.direction = Direction.INPUT

L = DigitalInOut(board.IO17)
L.direction = Direction.INPUT

U = DigitalInOut(board.IO15)
U.direction = Direction.INPUT

D = DigitalInOut(board.IO16)
D.direction = Direction.INPUT

A = DigitalInOut(board.IO13)
A.direction = Direction.INPUT

B = DigitalInOut(board.IO14)
B.direction = Direction.INPUT

SEL = DigitalInOut(board.IO40)
SEL.direction = Direction.INPUT

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=board.IO37
)

display = ST7789(display_bus, width=240, height=240, rowstart=80, rotation=0)

splash = displayio.Group()
display.root_group = splash
audio = KeyBoyAudio()

def run_game(module_name, class_name, constructor_args):
    """Load one game on demand, then release its display objects and module code."""
    module = __import__(module_name, None, None, (class_name,))
    game = getattr(module, class_name)(*constructor_args)
    result = game.Game()
    del game
    del module
    while len(splash):
        splash.pop()
    module_parts = module_name.split(".")
    while module_parts:
        try:
            del sys.modules[".".join(module_parts)]
        except KeyError:
            pass
        module_parts.pop()
    # GameMenu is imported only by game modules, never by this launcher.
    try:
        del sys.modules["GameMenu"]
    except KeyError:
        pass
    gc.collect()
    return result

game_selected = 1;

menu_bitmap = displayio.Bitmap(240,240,1)
menu_palette = displayio.Palette(1)
menu_palette[0] = 0x101A36
menu_group = displayio.Group()
menu = displayio.TileGrid(menu_bitmap, pixel_shader=menu_palette, x=0, y=0)
menu_group.append(menu)
# A light, low-memory parallax starfield gives the launcher a living backdrop.
menu_stars = []
for star_x, star_y, speed, color in ((18, 72, 1, 0x709AD8), (52, 112, 2, 0xFFFFFF),
                                     (91, 58, 1, 0xA8C6F0), (138, 166, 2, 0xFFFFFF),
                                     (181, 86, 1, 0x789CD0), (219, 135, 2, 0xFFFFFF),
                                     (31, 205, 1, 0xA8C6F0), (204, 45, 1, 0xFFFFFF)):
    star_bitmap = displayio.Bitmap(2, 2, 1)
    star_palette = displayio.Palette(1)
    star_palette[0] = color
    star = displayio.TileGrid(star_bitmap, pixel_shader=star_palette, x=star_x, y=star_y)
    menu_group.append(star)
    menu_stars.append([star, speed])
title_group = displayio.Group(scale=3, x=66, y=17)
title_group.append(label.Label(terminalio.FONT, text="KEYBOY", color=0xFFE39A))
menu_group.append(title_group)
tagline = label.Label(terminalio.FONT, text="tiny games / big journeys", color=0xB9D7FF, x=18, y=43)
menu_group.append(tagline)
game1_group = displayio.Group(x=84,y=70)
game1_text = "Loose Cows"
game1_txt_area = label.Label(terminalio.FONT, text=game1_text, color=0xFFFFFF)
game1_group.append(game1_txt_area)
menu_group.append(game1_group)
game2_group = displayio.Group(x=66,y=95)
game2_txt_area = label.Label(terminalio.FONT, text="Sprite's Journey", color=0xFFFFFF)
game2_group.append(game2_txt_area)
menu_group.append(game2_group)
game3_group = displayio.Group(x=70,y=120)
game3_txt_area = label.Label(terminalio.FONT, text="Aerial Dog Fight", color=0xFFFFFF)
game3_group.append(game3_txt_area)
menu_group.append(game3_group)
game4_group = displayio.Group(x=80,y=145)
game4_txt_area = label.Label(terminalio.FONT, text="Dungeons CYL", color=0xFFFFFF)
game4_group.append(game4_txt_area)
menu_group.append(game4_group)
game5_group = displayio.Group(x=78,y=170)
game5_txt_area = label.Label(terminalio.FONT, text="Lantern Acre", color=0xFFFFFF)
game5_group.append(game5_txt_area)
menu_group.append(game5_group)
game6_group = displayio.Group(x=84,y=195)
game6_txt_area = label.Label(terminalio.FONT, text="Wildspark", color=0xFFFFFF)
game6_group.append(game6_txt_area)
menu_group.append(game6_group)
game7_group = displayio.Group(x=84,y=220)
game7_txt_area = label.Label(terminalio.FONT, text="Ironbound", color=0xFFFFFF)
game7_group.append(game7_txt_area)
menu_group.append(game7_group)
game_selector = displayio.Bitmap(15,15,1)
game_selector_p = displayio.Palette(1)
game_selector_p[0] = 0xFF0000
selector_sprite = displayio.TileGrid(game_selector, pixel_shader=game_selector_p, x=54, y=64)
menu_group.append(selector_sprite)
game8_group = displayio.Group(x=84,y=220)
game8_txt_area = label.Label(terminalio.FONT, text="Last Beacon", color=0xFFFFFF)
game8_group.append(game8_txt_area)
game_rows = (game1_group, game2_group, game3_group, game4_group, game5_group, game6_group, game7_group, game8_group)
menu_page = 0
page_label = label.Label(terminalio.FONT, text="PAGE 1/2", color=0x8FB7E8, x=178, y=43)
menu_group.append(page_label)

def show_menu_page():
    for row in game_rows:
        try:
            menu_group.remove(row)
        except ValueError:
            pass
    start = menu_page * 4
    for row_index in range(4):
        row = game_rows[start + row_index]
        row.y = 70 + row_index * 27
        menu_group.append(row)
    page_label.text = "PAGE " + str(menu_page + 1) + "/2"
    selector_sprite.y = 64 + (game_selected - start - 1) * 27

show_menu_page()
nogame = True
menu_up = False
input_armed = False
launch_game = 0
reset_menu = True
while True:
    if launch_game == 1:
        splash.remove(menu_group)
        menu_up = False
        [nogame, LooseCowsScore] = run_game("Loose_Cows.Loose_Cows", "LooseCows", (splash, A, B, U, D, L, R, LooseCowsScore, SEL, audio))
        try:
            game1_score = io.open("/cows.txt", mode='wt')
            game1_score.write(str(LooseCowsScore))
            game1_score.close()
        except OSError:
            print("Can't save in programming mode")
        time.sleep(1)
    elif launch_game == 2:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Sprites_Journey.Sprites_Journey", "SpritesJourney", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 3:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("AerialDogFight", "AerialDogFight", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 4:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Dungeons_CYL", "DungeonsCYL", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 5:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Lantern_Acre.Lantern_Acre", "LanternAcre", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 6:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Wildspark.Wildspark", "Wildspark", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 7:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Ironbound.Ironbound", "Ironbound", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    elif launch_game == 8:
        splash.remove(menu_group)
        menu_up = False
        nogame = run_game("Last_Beacon.Last_Beacon", "LastBeacon", (splash, A, B, U, D, L, R, SEL, audio))
        time.sleep(1)
    if launch_game:
        launch_game = 0
        reset_menu = True
    if reset_menu:
        game_selected = 1
        menu_page = 0
        show_menu_page()
        input_armed = False
        reset_menu = False
        if menu_up == False:
            splash.append(menu_group)
            menu_up = True
    if menu_up:
        for star, speed in menu_stars:
            star.y = star.y + speed
            if star.y > 238:
                star.y = 52
    if not input_armed:
        if A.value and B.value and U.value and D.value and L.value and R.value:
            input_armed = True
        time.sleep(0.05)
        continue
    if A.value == 0:
        launch_game = game_selected
        nogame = False
    elif D.value == 0 and game_selected < 8:
        game_selected += 1
        menu_page = (game_selected - 1) // 4
        show_menu_page()
        time.sleep(0.2)
    elif U.value == 0 and game_selected > 1:
        game_selected -= 1
        menu_page = (game_selected - 1) // 4
        show_menu_page()
        time.sleep(0.2)
    time.sleep(0.05)
