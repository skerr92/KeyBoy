"""Generate nearest-neighbor art previews without a board or third-party packages."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from lantern_host import ROOT, game, load, render

m = load()
g = game(m)
g._unlocked = 6
for i, plot in enumerate(m.PLOTS):
    for j, pos in enumerate(plot):
        crop = (i + j // 3) % 4
        g._plants[pos] = [m.CROPS[crop][1] if j % 3 == 2 else j % 3, j % 2 == 0, crop]
g._build_farm()
g._farmer.x, g._farmer.y = 101, 135
g._cursor.x, g._cursor.y = 100, 140
g._sync_hud((5, 5), 999999999)
g._animate(0)
out = ROOT / 'docs/lantern-acre'
out.mkdir(parents=True, exist_ok=True)
render(g._splash, out / 'farm.png')
g._panel('home')
render(g._splash, out / 'cottage.png')
g._splash.pop()
g._elapsed = 390
g._sync_hud((5, 5), 999999999)
g._animate(0)
render(g._splash, out / 'night.png')
g._elapsed=0;g._area=1;g._build_farm()
g._farmer.x,g._farmer.y=21,175
g._cursor.x,g._cursor.y=20,180
g._sync_hud((1,7),999999999);g._animate(0)
render(g._splash,out/'meadow.png')
g._panel('seeds');render(g._splash,out/'seeds.png');g._splash.pop()
g._area=0;g._build_farm();g._day=8;g._new_day();g._panel('home')
from unittest.mock import patch
class MorningClock:
    def __init__(self):self.now=0
    def monotonic(self):return self.now
    def sleep(self,seconds):
        if self.now==0:render(g._splash,out/'morning.png')
        self.now+=seconds
with patch.object(m,'time',MorningClock()):g._morning_card(True)
print('Wrote farm, cottage, night, meadow, seeds and morning previews to',out)
