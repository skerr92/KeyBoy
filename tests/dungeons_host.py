"""Dungeons host adapter using the shared display doubles."""
import importlib.util
from unittest.mock import patch
from lantern_host import ROOT, Group, Button, Audio, render, load as install


def load():
    install()
    spec=importlib.util.spec_from_file_location('dungeons_under_test',ROOT/'Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def game(module):
    with patch('builtins.open',side_effect=OSError):
        return module.DungeonsCYL(Group(),*[Button() for _ in range(7)],Audio())
