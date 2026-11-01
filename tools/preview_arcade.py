"""Render the actual retained arcade scenery and actors."""
import sys
import random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from arcade_host import ROOT,load,game,render
out=ROOT/'docs/arcade';out.mkdir(parents=True,exist_ok=True)
for name in ('journey','flight','cows'):
    m=load(name);g=game(m,name)
    if name=='journey':g._level=2;g._setup_level()
    elif name=='flight':
        g._setup_sortie();g._spawn_enemy(True)
        g._enemies[6][0].x,g._enemies[6][0].y=150,55
        g._enemies[6][2]=55;g._sync()
    else:
        random.seed(11)
        g._build_round(5)
        g._splash.append(m.label.Label(m.terminalio.FONT,text='R5 0/6 T47 HP3 W2',color=0xEAE1BC,x=8,y=12))
        g._notice('A lasso  B whistle  SEL menu')
    render(g._splash,out/(name+'.png'))
