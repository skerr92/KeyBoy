"""Render Last Beacon art from its actual sprite/scene builders; no dependencies."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from beacon_host import ROOT, game, load, render

m = load()
g = game(m)
g._build_ship()
g._sync_ship(4)
out = ROOT / 'docs/last-beacon'
out.mkdir(parents=True, exist_ok=True)
render(g._splash, out / 'ship.png')
for mission, name in ((0, 'ashfall'), (1, 'bracken'), (2, 'frost')):
    g._mission = mission
    g._start_mission()
    g._x, g._y = 116, 136
    g._aim_x, g._aim_y = 1, 0
    for i, (x, y, kind) in enumerate(((158, 131, 0), (195, 143, 1), (34, 101, 2), (110, 88, 0))):
        e = g._enemies[i]
        e[:6] = [True, x, y, 5, kind, 0.0]
        e[6].hidden = False
        e[6][0] = kind * 2
        m._place(e[6], x - 10, y - 10)
    g._bullet(134, 136, 1, 0, 190, 2)
    g._sync_field(True)
    render(g._splash, out / (name + '.png'))
for objective in g._objectives:
    g._complete(objective)
g._x, g._y = 163, 191
g._phase = 'BOARD'
g._board_clock = 8
g._view['craft'].hidden = False
g._sync_field(False)
render(g._splash, out / 'extraction.png')
print('Wrote ship, three biomes and extraction previews to', out)
