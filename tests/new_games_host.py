"""Host adapters for Clockwork Courier and Drift Circuit."""
import importlib.util
import sys
from unittest.mock import patch
from lantern_host import ROOT,Group,Button,Audio,render,load as install


def load(name):
    install()
    for module in ('KeyBoyScenes',name):
        spec=importlib.util.spec_from_file_location(module,ROOT/'Firmware/Games'/(module+'.py'))
        m=importlib.util.module_from_spec(spec);sys.modules[module]=m;spec.loader.exec_module(m)
    return m


def game(m):
    with patch('builtins.open',side_effect=OSError):
        return getattr(m,m.__name__)(Group(),*[Button() for _ in range(7)],Audio())
