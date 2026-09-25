"""Generate nearest-neighbor art previews without a board or third-party packages."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from lantern_host import ROOT, game, load, render

m = load()
g = game(m)
g._unlocked = 3
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
print('Wrote farm, cottage and night previews to', out)
