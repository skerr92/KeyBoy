"""Render the actual dungeon art; desktop labels approximate terminalio."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from dungeons_host import ROOT, game, load, render
m=load()
g=game(m)
out=ROOT/'docs/dungeons'
out.mkdir(parents=True,exist_ok=True)
for i in range(7):
    g._begin(i)
    g._elapsed=1
    g._sync()
    render(g._splash,out/('floor-%d.png'%(i+1)))
g._begin(6)
g._pos=(4,9)
g._boss['phase']='windup'
g._boss['target']=g._pos
g._guard=True
g._sync()
render(g._splash,out/'combat.png')
print('Wrote seven floor previews and combat to',out)
