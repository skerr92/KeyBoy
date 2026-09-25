"""Render actual Wildspark artwork, with approximated desktop terminal text."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from wildspark_host import ROOT, Group, load, game, render
m = load()
g = game(m)
out = ROOT / 'docs/wildspark'
out.mkdir(parents=True, exist_ok=True)
for route, name in ((1, 'mothwood'), (4, 'coast'), (6, 'moonglade')):
    g._route = route
    g._build_world()
    g._sync_world([5, 5])
    m._place(g._view['hero'], 101, 135)
    m._place(g._view['partner'], 78, 136)
    render(g._splash, out / (name + '.png'))
g._route = 1
g._build_battle(3, 4)
g._sync_battle(1)
render(g._splash, out / 'battle.png')
for stage in range(3):
    root = Group()
    root.append(m._solid(240, 240, m.INK[0]))
    for family in range(9):
        x, y = (family % 3) * 80 + 14, (family // 3) * 80 + 3
        root.append(m._grid(m._creature(family, stage), m._palette(m.CREATURE_COLORS[family // 3], True), x, y, tile_width=48, tile_height=48))
        m._text(root, m.FAMILIES[family][1][stage], x - 6, y + 58)
        m._text(root, m.FAMILIES[family][0], x, y + 71, m.INK[12])
    render(root, out / ('forms-' + str(stage + 1) + '.png'))
# Capture the actual reusable portrait menu before the scripted Back press.
from unittest.mock import patch
class PreviewClock:
    def __init__(self):
        self.now = 0
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        if self.now == 0:
            render(g._splash, out / 'partners.png')
        self.now += seconds
        g._B.value = False
g._route = 1
g._build_world()
g._sync_world((3, 7))
m._place(g._view['hero'], 61, 175)
m._place(g._view['partner'], 38, 176)
g._party[3] = [5, 42, 0]
g._party[6] = [8, 54, 0]
with patch.object(m, 'time', PreviewClock()):
    g._partners()
print('Wrote Wildspark route, battle and 27-form previews to', out)
