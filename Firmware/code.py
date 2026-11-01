import board, displayio, time, sys, gc
from adafruit_st7789 import ST7789
import busio, microcontroller, pwmio
from digitalio import DigitalInOut, Direction
from adafruit_display_text import label
import terminalio, io
from KeyBoyAudio import KeyBoyAudio
try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

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

display_bus = FourWire(
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
    # Shared arcade helpers are loaded only while their game is running.
    for helper in ("GameMenu", "KeyBoyArcade", "KeyBoyScenes"):
        try:
            del sys.modules[helper]
        except KeyError:
            pass
    gc.collect()
    return result

# Keep only names and the last selection resident while a game is running.
GAMES=(('Loose_Cows.Loose_Cows','LooseCows'),
       ('Sprites_Journey.Sprites_Journey','SpritesJourney'),
       ('AerialDogFight','AerialDogFight'),('Dungeons_CYL','DungeonsCYL'),
       ('Lantern_Acre.Lantern_Acre','LanternAcre'),('Wildspark.Wildspark','Wildspark'),
       ('Ironbound.Ironbound','Ironbound'),('Last_Beacon.Last_Beacon','LastBeacon'),
       ('ClockworkCourier','ClockworkCourier'),('DriftCircuit','DriftCircuit'))
selected=0
while True:
    launcher_module=__import__('KeyBoyLauncher')
    launcher=launcher_module.Launcher(splash,(A,B,U,D,L,R,SEL),audio,selected)
    selected=launcher.choose()
    # Release every menu bitmap and its drawing code before importing a game.
    del launcher
    del launcher_module
    del sys.modules['KeyBoyLauncher']
    gc.collect()
    module_name,class_name=GAMES[selected]
    if selected==0:
        result=run_game(module_name,class_name,(splash,A,B,U,D,L,R,LooseCowsScore,SEL,audio))
        LooseCowsScore=max(LooseCowsScore,result[1])
    else:
        run_game(module_name,class_name,(splash,A,B,U,D,L,R,SEL,audio))
