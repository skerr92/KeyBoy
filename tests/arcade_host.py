"""Load the three arcade games with the shared display doubles."""
import importlib.util
import sys
from lantern_host import ROOT, Group, Button, Audio, render, load as install


def load(name):
    install()
    for module, path in (('GameMenu','GameMenu.py'),('KeyBoyArcade','KeyBoyArcade.py')):
        spec=importlib.util.spec_from_file_location(module,ROOT/'Firmware/Games'/path)
        mod=importlib.util.module_from_spec(spec);sys.modules[module]=mod;spec.loader.exec_module(mod)
    path={'journey':'Sprites_Journey/Sprites_Journey.py','flight':'Aerial Dog Fight/AerialDogFight.py','cows':'Loose_Cows/Loose_Cows.py'}[name]
    spec=importlib.util.spec_from_file_location(name+'_under_test',ROOT/'Firmware/Games'/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def game(module,name):
    buttons=[Button() for _ in range(7)]
    cls=getattr(module,{'journey':'SpritesJourney','flight':'AerialDogFight','cows':'LooseCows'}[name])
    if name=='cows':return cls(Group(),*buttons[:6],0,buttons[6],Audio())
    return cls(Group(),*buttons,Audio())
