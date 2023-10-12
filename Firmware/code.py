import board, displayio, time
from adafruit_st7789 import ST7789
import busio, microcontroller
from digitalio import DigitalInOut, Direction
from adafruit_display_text import label
from adafruit_display_shapes import triangle
import terminalio, random, pwmio

displayio.release_displays()
brightness = 5
bl = pwmio.PWMOut(board.IO38, frequency=100, duty_cycle=int(brightness * 2 * 65535 / 100))
spi = busio.SPI(clock=microcontroller.pin.GPIO36, MOSI=microcontroller.pin.GPIO33)

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

colors = [0xFF0000, 0x00FF00, 0x0000FF]
color_idx = 0

splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(240, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # white

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(220, 220, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000011  # Purple
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=10, y=10)
splash.append(inner_sprite)

dot = displayio.Bitmap(10,10,1)
dot_palette = displayio.Palette(1)
dot_palette[0] = 0xF00000
dot_sprite = displayio.TileGrid(dot, pixel_shader=dot_palette, x=110, y=110)
splash.append(dot_sprite)

x_rand = random.randint(20,220)
y_rand = random.randint(20,220)

#tri_randx1 = random.randint(20,220)
#tri_randx2 = tri_randx1 + 25
#tri_randy1 = random.randint(20,220)
#tri_randy2 = tri_randy1 + 25
#tri_randx3 = tri_randx1 + random.randint(20,220)
#tri_randy3 = tri_randy1 + random.randint(20,220)

#hazard = triangle.Triangle(tri_randx1,tri_randy1,tri_randx2,tri_randy2,tri_randx3,tri_randy3, fill=0xFF0000)
#splash.append(hazard)
dot2g = displayio.Bitmap(10,10,1)
dot2g_palette = displayio.Palette(1)
dot2g_palette[0] = 0xFFFFFF
dot2g_sprite = displayio.TileGrid(dot2g, pixel_shader=dot2g_palette, x=x_rand, y=y_rand)
splash.append(dot2g_sprite)

points = 0
timeleft = 10
# Draw a label
text_group = displayio.Group(scale=2, x=110, y=30)
text = "Points: "
tg2 = displayio.Group(scale=2, x=200, y=30)
t2 = str(points)
tg3 = displayio.Group(scale=2, x=20, y=30)
t3 = str(timeleft)
text_area = label.Label(terminalio.FONT, text=text, color=0xFF00F0)
t2_area = label.Label(terminalio.FONT, text=t2, color=0xF00000)
t3_area = label.Label(terminalio.FONT, text=t3, color=0xF00000)
text_group.append(text_area)  # Subgroup for text scaling
tg2.append(t2_area)
tg3.append(t3_area)
splash.append(text_group)
splash.append(tg2)
splash.append(tg3)

previous_monotonic = time.monotonic()

while True:
    
    print("U ",U.value,"D ", D.value, " R ", R.value, " L ", L.value)
    if U.value == 0:
        if dot_sprite.y == 10:
            dot_sprite.y = 220
        else:
            dot_sprite.y = dot_sprite.y - 2
        print(dot_sprite.y)
    if D.value == 0:
        if dot_sprite.y == 220:
            dot_sprite.y = 10
        else:
            dot_sprite.y = dot_sprite.y + 2
        print(dot_sprite.y)
    if R.value == 0:
        if dot_sprite.x == 220:
            dot_sprite.x = 10
        else:
            dot_sprite.x = dot_sprite.x + 2
    if L.value == 0:
        if dot_sprite.x == 10:
            dot_sprite.x = 220
        else:
            dot_sprite.x = dot_sprite.x - 2
    if A.value == 0:
        if color_idx == 2:
            color_idx = 0
        else:
            color_idx = color_idx + 1
        dot_palette[0] = colors[color_idx]
        time.sleep(0.5)
    if B.value == 0:
        if color_idx == 0:
            color_idx = 2
        color_idx = color_idx - 1
        dot_palette[0] = colors[color_idx]
        time.sleep(0.5)
    if abs(dot_sprite.x - dot2g_sprite.x) < 5 and abs(dot_sprite.y - dot2g_sprite.y) < 5:
        dot2g_sprite.x = random.randint(20,220)
        dot2g_sprite.y = random.randint(20,220)
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
            dot_sprite.x = 110
            dot_sprite.y = 110
            dot2g_sprite.x = random.randint(20,220)
            dot2g_sprite.y = random.randint(20,220)
            t3_area.text = str(timeleft)
            t2_area.text = str(points)
        else:
            timeleft = timeleft - 1
            previous_monotonic = time.monotonic()
            t3_area.text = str(timeleft)

    pass
