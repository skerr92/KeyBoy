import board, displayio, time
from adafruit_st7789 import ST7789
import busio, microcontroller, pwmio
from digitalio import DigitalInOut, Direction
from Loose_Cows import Loose_Cows
from adafruit_display_text import label
import terminalio, adafruit_imageload, io, storage

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

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=board.IO37
)

display = ST7789(display_bus, width=240, height=240, rowstart=80, rotation=0)

splash = displayio.Group()
display.show(splash)
game = Loose_Cows.LooseCows(splash, A, B, U, D, L, R, LooseCowsScore)
game_selected = 1;

menu_bitmap = displayio.Bitmap(240,240,1)
menu_palette = displayio.Palette(1)
menu_palette[0] = 0xFFFFFF
menu_group = displayio.Group()
menu = displayio.TileGrid(menu_bitmap, pixel_shader=menu_palette, x=0, y=0)
menu_group.append(menu)
game1_group = displayio.Group(scale=2, x=80,y=100)
game1_text = "Loose Cows"
game1_txt_area = label.Label(terminalio.FONT, text=game1_text, color=0x000000)
game1_group.append(game1_txt_area)
menu_group.append(game1_group)
game_selector = displayio.Bitmap(15,15,1)
game_selector_p = displayio.Palette(1)
game_selector_p[0] = 0xFF0000
selector_sprite = displayio.TileGrid(game_selector, pixel_shader=game_selector_p, x=50, y=95)
menu_group.append(selector_sprite)
nogame = True
menu_up = False
while True:
    if game_selected == 0:
        splash.remove(menu_group)
        menu_up = False
        [nogame, LooseCowsScore] = game.Game()
        try:
            game1_score = io.open("/cows.txt", mode='wt')
            game1_score.write(str(LooseCowsScore))
            game1_score.close()
        except OSError:
            print("Can't save in programming mode")
        time.sleep(1)
    if nogame:
        game_selected = 1
        if menu_up == False:
            splash.append(menu_group)
            menu_up = True
    if game_selected == 1:
        if A.value == 0:
            game_selected = 0
            nogame = False
    time.sleep(0.5)