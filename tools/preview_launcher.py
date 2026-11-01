import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_launcher import load
from lantern_host import ROOT,Group,Button,Audio,render
m=load();g=m.Launcher(Group(),[Button() for _ in range(7)],Audio())
out=ROOT/'docs/launcher';out.mkdir(parents=True,exist_ok=True)
for i in range(len(m.NAMES)):
    g.select(i,False);g.animate(0)
    render(g.splash,out/('game-%d.png'%(i+1)))
