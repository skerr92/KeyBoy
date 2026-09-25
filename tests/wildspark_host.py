"""Wildspark host adapter; share the dependency-free display doubles."""
import importlib.util
from unittest.mock import patch
from lantern_host import ROOT, Group, Button, Audio, render, load as install


def load():
    install()
    spec = importlib.util.spec_from_file_location('wildspark_under_test', ROOT / 'Firmware/Games/Wildspark/Wildspark.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def game(module):
    with patch('builtins.open', side_effect=OSError):
        return module.Wildspark(Group(), *[Button() for _ in range(7)], Audio())
