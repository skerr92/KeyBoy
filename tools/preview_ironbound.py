"""Render Ironbound's actual game art; text approximates terminalio."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from ironbound_host import ROOT,load,game,render
m=load();g=game(m);out=ROOT/'docs/ironbound';out.mkdir(parents=True,exist_ok=True)
g._build_hangar();render(g._splash,out/'hangar.png')
for i in range(1,9):
    g._mission=i;g._begin();render(g._splash,out/('mission-%d.png'%i))
g._mission=5;g._begin();g._pos=(3,4)
g._enemies[0]['pos']=(3,3);g._enemies[1]['pos']=(5,4)
g._plan();g._note='Red brackets: move or guard.';g._sync()
render(g._splash,out/'tactics.png')
print('Wrote hangar and eight mission previews to',out)
