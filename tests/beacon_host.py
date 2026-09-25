"""Host loader for Last Beacon; reuse the display doubles/PNG renderer."""
import importlib.util
from unittest.mock import patch
from lantern_host import ROOT, Button, Audio, Group, load as install_display_doubles, render


def load():
    install_display_doubles()
    spec = importlib.util.spec_from_file_location('beacon_under_test', ROOT / 'Firmware/Games/Last_Beacon/Last_Beacon.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def game(module):
    with patch('builtins.open', side_effect=OSError):
        return module.LastBeacon(Group(), *[Button() for _ in range(7)], Audio())
