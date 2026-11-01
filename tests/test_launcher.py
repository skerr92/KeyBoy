import importlib.util
import unittest
from unittest.mock import patch
from lantern_host import ROOT,Group,Button,Audio,load as install


def load():
    install()
    spec=importlib.util.spec_from_file_location('launcher_test',ROOT/'Firmware/Games/KeyBoyLauncher.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.m=load();self.buttons=[Button() for _ in range(7)]
        self.g=self.m.Launcher(Group(),self.buttons,Audio())

    def test_all_games_and_pages_are_reachable_without_launching(self):
        self.g.poll(0)
        for i in range(1,11):
            self.buttons[3].value=False
            self.assertIsNone(self.g.poll(i))
            self.assertEqual(self.g.selected,i%10)
            self.buttons[3].value=True;self.g.poll(i+.1)
        self.buttons[5].value=False;self.g.poll(12)
        self.assertEqual(self.g.selected,4)
        self.assertEqual(self.g.page.text,'2 / 3')

    def test_partial_page_and_page_wrap(self):
        self.g.select(9,False)
        self.assertEqual([r.text for r in self.g.rows],['Clockwork Courier','Drift Circuit','',''])
        self.assertEqual(self.g.page.text,'3 / 3')
        self.g.poll(0);self.buttons[5].value=False;self.g.poll(1)
        self.assertEqual(self.g.selected,1)
        self.buttons[5].value=True;self.g.poll(2)
        self.buttons[4].value=False;self.g.poll(3)
        self.assertEqual(self.g.selected,9)
        self.g.select(7);self.buttons[4].value=True;self.g.poll(4)
        self.buttons[5].value=False;self.g.poll(5)
        self.assertEqual(self.g.selected,9)

    def test_held_buttons_cannot_launch_on_return(self):
        self.buttons[0].value=False
        self.assertIsNone(self.g.poll(0))
        self.assertIsNone(self.g.poll(1))
        self.buttons[0].value=True;self.g.poll(2)
        self.buttons[0].value=False
        self.assertEqual(self.g.poll(3),0)

    def test_navigation_and_animation_reuse_bitmaps(self):
        strips=tuple(self.g.background.strips);art=self.g.art
        with patch.object(self.m.displayio,'Bitmap',side_effect=AssertionError('new bitmap')):
            for i in range(80):self.g.select(i);self.g.animate(i*.13)
        self.assertEqual(tuple(self.g.background.strips),strips)
        self.assertIs(self.g.art,art)

    def test_holding_direction_repeats_with_initial_delay(self):
        self.g.poll(0);self.buttons[3].value=False
        self.g.poll(.1);self.assertEqual(self.g.selected,1)
        self.g.poll(.3);self.assertEqual(self.g.selected,1)
        self.g.poll(.43);self.assertEqual(self.g.selected,2)

    def test_simultaneous_navigation_and_a_does_not_launch(self):
        self.g.poll(0);self.buttons[0].value=False;self.buttons[3].value=False
        self.assertIsNone(self.g.poll(1))
        self.buttons[3].value=True
        self.assertIsNone(self.g.poll(2))

    def test_last_selection_is_restored(self):
        g=self.m.Launcher(Group(),[Button() for _ in range(7)],Audio(),7)
        self.assertEqual(g.selected,7)
        self.assertEqual(g.rows[3].text,'Last Beacon')

if __name__=='__main__':unittest.main()
