"""Actual scene previews for the puzzle and racing additions."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from new_games_host import ROOT,load,game,render
for name,folder in (('ClockworkCourier','clockwork-courier'),('DriftCircuit','drift-circuit')):
    m=load(name);g=game(m);out=ROOT/'docs'/folder;out.mkdir(parents=True,exist_ok=True)
    if name=='ClockworkCourier':
        for level in (0,6,11):
            g._start(level);render(g.root,out/('room-%d.png'%(level+1)))
    else:
        for track in range(3):
            g._setup(track);g.countdown=0;g._sync()
            render(g.root,out/('track-%d.png'%(track+1)))
