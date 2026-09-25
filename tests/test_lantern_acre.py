"""Behavior/retention checks; run with python3 tests/test_lantern_acre.py."""
import io
import unittest
from unittest.mock import patch
from lantern_host import Bitmap, Group, game, load

M = load()


class FakeClock:
    def __init__(self, g, script):
        self.now = 0
        self.g = g
        self.script = script

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.script(self.now, self.g)
        if self.now > 10:
            raise AssertionError('loop did not exit')


class LanternTests(unittest.TestCase):
    def setUp(self):
        self.g = game(M)
        self.g._build_farm()

    def test_day_is_480_seconds_and_actions_do_not_advance_clock(self):
        self.g._tend((2, 5))
        self.g._tend((2, 5))
        self.assertEqual(self.g._elapsed, 0)
        self.g._tick(479)
        self.assertEqual(self.g._day, 1)
        self.g._tick(1)
        self.assertEqual(self.g._day, 2)
        self.assertEqual(self.g._plants[(2, 5)], [1, False, 0])

    def test_dry_crops_pause_and_ripe_crops_survive_seasons(self):
        self.g._day = 8
        self.g._plants = {(2, 5): [0, False, 0], (3, 5): [2, True, 0]}
        self.g._new_day()
        self.assertEqual(self.g._season_index(), 1)
        self.assertEqual(self.g._plants[(2, 5)][0], 0)
        self.assertEqual(self.g._plants[(3, 5)][0], 2)
        self.g._tend((4, 5))
        self.assertEqual(self.g._plants[(4, 5)][2], 1)

    def test_plant_water_grow_harvest_sell_each_crop_at_its_price(self):
        for crop, info in enumerate(M.CROPS):
            self.g._day = 1 + crop * 8
            self.g._tend((2, 5))
            for _ in range(info[1]):
                self.g._tend((2, 5))
                self.g._new_day()
            self.g._tend((2, 5))
            self.assertNotIn((2, 5), self.g._plants)
            self.assertEqual(self.g._basket_value, info[2])
            before = self.g._coins
            self.g._sell()
            self.assertEqual(self.g._coins - before, info[2])
        self.assertEqual(self.g._crops, 0)

    def test_copper_can_waters_three_only_and_cart_adds_per_crop_bonus(self):
        self.g._plants = {pos: [0, False, 0] for pos in M.PLOTS[0]}
        self.g._can = True
        self.g._tend((3, 5))
        self.assertEqual(sum(p[1] for p in self.g._plants.values()), 3)
        self.g._crops, self.g._basket_value, self.g._cart = 2, 18, True
        before = self.g._coins
        self.g._sell()
        self.assertEqual(self.g._coins - before, 20)

    def test_economy_rejects_missing_funds_and_duplicate_upgrades(self):
        self.g._coins = 0
        for choice in (0, 2, 3, 4):
            self.assertIn('Need', self.g._buy(choice))
        self.assertEqual(self.g._unlocked, 1)
        self.g._coins = 1000
        for choice in (2, 2, 3, 4):
            self.g._buy(choice)
        self.assertEqual(self.g._coins, 720)
        for choice in (2, 3, 4):
            self.g._buy(choice)
        self.assertEqual(self.g._coins, 720)

    def test_gameplay_retains_scene_and_never_repaints_bitmaps(self):
        scene = tuple(self.g._farm_group)
        bitmaps = {id(o.bitmap): o.bitmap for o in scene if hasattr(o, 'bitmap')}
        writes = {key: b.writes for key, b in bitmaps.items()}
        for pos in M.PLOTS[0]:
            self.g._tend(pos)
            self.g._sync_plots()
            self.g._tend(pos)
            self.g._sync_plots()
        self.g._new_day()
        self.g._coins = 100
        self.g._buy(2)
        for t in (0, 300, 390, 480):
            self.g._elapsed = t % M.DAY_SECONDS
            self.g._animate(t)
            self.g._sync_hud((2, 5), t)
        self.assertEqual(tuple(self.g._farm_group), scene)
        self.assertEqual({key: b.writes for key, b in bitmaps.items()}, writes)
        self.assertEqual(len(self.g._splash), 1)

    def test_all_plots_and_interactions_reachable_from_door(self):
        seen, todo = {M.DOOR}, [M.DOOR]
        while todo:
            x, y = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pos = x + dx, y + dy
                if M.LanternAcre._walkable(*pos) and pos not in seen:
                    seen.add(pos)
                    todo.append(pos)
        self.assertTrue(all(pos in seen for plot in M.PLOTS for pos in plot))
        self.assertIn((9, 3), seen)
        self.assertIn((4, 3), seen)
        self.assertFalse(M.LanternAcre._walkable(2, 2))
        self.assertFalse(M.LanternAcre._walkable(11, 4))

    def test_all_atlas_indices_valid(self):
        self.g._unlocked = 3
        for crop in range(4):
            for age in range(M.CROPS[crop][1] + 1):
                for wet in (False, True):
                    self.g._plants[(2, 5)] = [age, wet, crop]
                    self.g._sync_plots()
        self.assertEqual(self.g._farmer.bitmap.width, 18 * 12)

    def test_load_legacy_save_migrates_time_and_overage_ripe_crops(self):
        with patch('builtins.open', return_value=io.StringIO('72,4,20,20,2,3,1,1|2,5,99,1,0')):
            self.g._load_state()
        self.assertEqual(self.g._day, 72)
        self.assertEqual(self.g._elapsed, 96)
        self.assertEqual(self.g._basket_value, 10)
        self.assertEqual(self.g._plants[(2, 5)], [2, True, 0])

    def test_invalid_save_does_not_partially_mutate_state(self):
        for data in ('LA2,72,80,20,20,2,3,1,1,10,0|2,5,0,1,9',
                     '72,4,20,20,2,3,1,1|2,5,3,1',
                     'LA2,72,-1,20,20,2,3,1,1,10,0|', 'broken'):
            with patch('builtins.open', return_value=io.StringIO(data)):
                self.g._load_state()
            self.assertEqual(self.g._day, 1)
            self.assertEqual(self.g._plants, {})

    def test_save_roundtrip_and_read_only_failure(self):
        class File(io.StringIO):
            def close(self):
                pass
        f = File()
        self.g._plants[(2, 5)] = [1, True, 0]
        self.g._foraged = True
        with patch('builtins.open', return_value=f), patch.object(M.os, 'rename') as rename:
            self.assertTrue(self.g._save_state())
            rename.assert_called_once_with('/lantern_acre.tmp', '/lantern_acre.sav')
        restored = game(M)
        with patch('builtins.open', return_value=io.StringIO(f.getvalue())):
            restored._load_state()
        self.assertEqual(restored._plants, self.g._plants)
        self.assertTrue(restored._foraged)
        with patch('builtins.open', side_effect=OSError), patch.object(M.os, 'rename') as rename:
            self.assertFalse(self.g._save_state())
            rename.assert_not_called()

    def test_modal_consumes_entry_button_and_freezes_time(self):
        self.g._B.value = False
        def script(t, g):
            g._B.value = not (t < 0.2 or t > 0.5)
        clock = FakeClock(self.g, script)
        original = self.g._elapsed
        with patch.object(M, 'time', clock):
            self.g._modal('town')
        self.assertGreater(clock.now, 0.5)
        self.assertEqual(self.g._elapsed, original)
        self.assertEqual(len(self.g._splash), 1)

    def test_sleep_requires_confirmation_for_dry_crops(self):
        self.g._plants[(2, 5)] = [0, False, 0]
        self.g._A.value = False
        def script(t, g):
            g._A.value = not (0.3 < t < 0.4)
            g._B.value = t < 0.6
        with patch.object(M, 'time', FakeClock(self.g, script)):
            self.g._modal('home')
        self.assertEqual(self.g._day, 1)
        self.g._B.value = True
        def confirm(t, g):
            g._A.value = not (0.2 < t < 0.3 or 0.5 < t < 0.6)
        with patch.object(M, 'time', FakeClock(self.g, confirm)), patch.object(self.g, '_save_state', return_value=True):
            self.g._modal('home')
        self.assertEqual(self.g._day, 2)
        self.assertEqual(self.g._plants[(2, 5)][0], 0)

    def test_input_loop_moves_and_does_not_rebuild(self):
        # Start a new game; walk from the door to the farm, exit with U+D.
        g = game(M)
        def script(t, g):
            g._D.value = False
            if t > 1:
                g._U.value = False
        clock = FakeClock(g, script)
        with patch.object(M, 'time', clock), patch.object(g, '_build_farm', wraps=g._build_farm) as build:
            g._farm()
        self.assertEqual(build.call_count, 1)
        self.assertGreater(g._farmer.y, 95)
        self.assertEqual(g._day, 1)

    def test_action_pressed_during_step_is_buffered_until_arrival(self):
        g = game(M)
        def script(t, g):
            g._D.value = t > 0.4
            g._A.value = not (0.36 < t < 0.4)
            if t > 1:
                g._U.value = g._D.value = False
        with patch.object(M, 'time', FakeClock(g, script)):
            g._farm()
        self.assertIn((2, 5), g._plants)
        self.assertEqual(g._seeds, 5)

    def test_menus_reuse_bitmaps_and_labels_after_heap_fragmentation(self):
        cached = self.g._panel_cache
        scene = tuple(self.g._farm_group)
        with patch.object(M.displayio, 'Bitmap', side_effect=AssertionError('menu allocated a bitmap')):
            for i in range(60):
                kind = ('town', 'pause', 'home')[i % 3]
                self.g._coins = i * 137
                panel, funds, rows, hint = self.g._panel(kind)
                self.assertIs(panel, cached[0])
                self.assertIs(rows, cached[2])
                self.assertEqual(sum(not row.hidden for row in rows), len(self.g._menu_items(kind)))
                self.g._splash.remove(panel)
        self.assertEqual(tuple(self.g._farm_group), scene)

    def test_panel_backings_have_no_large_contiguous_bitmap(self):
        for grid in self.g._panel_tiles:
            self.assertLessEqual(grid.bitmap.width * grid.bitmap.height // 4, 2128)
        for grid in self.g._panel_room:
            self.assertLessEqual(grid.bitmap.width * grid.bitmap.height // 2, 1456)


if __name__ == '__main__':
    unittest.main(verbosity=2)
