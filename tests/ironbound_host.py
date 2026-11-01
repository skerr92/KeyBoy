"""Ironbound host adapter using shared display doubles."""
import importlib.util
from unittest.mock import patch
from lantern_host import ROOT, Group, Button, Audio, render, load as install


def load():
    install()
    spec=importlib.util.spec_from_file_location('ironbound_under_test',ROOT/'Firmware/Games/Ironbound/Ironbound.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def game(m):
    with patch('builtins.open',side_effect=OSError):return m.Ironbound(Group(),*[Button() for _ in range(7)],Audio())
