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

    def test_area_changes_reuse_all_terrain_buffers(self):
        self.g._build_farm()
        terrain = self.g._terrain_canvas
        strips = tuple(terrain.strips)
        for area in (1, 0, 1, 0):
            self.g._area = area
            self.g._build_farm()
            self.assertIs(self.g._terrain_canvas, terrain)
            self.assertEqual(tuple(terrain.strips), strips)

    def test_day_is_240_seconds_and_actions_do_not_advance_clock(self):
        self.g._tend((2, 5))
        self.g._tend((2, 5))
        self.assertEqual(self.g._elapsed, 0)
        self.g._tick(239)
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
        for choice in (3, 4):
            self.g._buy(choice)
        self.assertEqual(self.g._coins, 720)
        for _ in range(3):self.g._buy(2)
        self.assertEqual((self.g._unlocked,self.g._coins),(6,180))
        self.g._buy(2)
        self.assertEqual(self.g._coins,180)

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
        for t in (0, 150, 195, 240):
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
        self.assertTrue(all(pos in seen for plot in M.PLOTS[:3] for pos in plot))
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
        self.assertEqual(self.g._farmer.bitmap.width, 18 * 3)
        for frame in range(12):
            self.g._farmer_art.show(self.g._farmer,frame)
            self.assertIs(self.g._farmer.bitmap,self.g._farmer_art.banks[frame//3])

    def test_farm_load_avoids_large_contiguous_sprite_allocations(self):
        allocations=[]
        def bounded(w,h,colors):
            bits=1 if colors<=2 else 2 if colors<=4 else 4 if colors<=16 else 8
            size=((w*bits+31)//32)*4*h
            self.assertLessEqual(size,2400)
            allocations.append(size)
            return Bitmap(w,h,colors)
        with patch.object(M.displayio,'Bitmap',side_effect=bounded):
            fresh=game(M);fresh._build_farm()
        self.assertTrue(allocations)

    def test_load_legacy_save_migrates_time_and_overage_ripe_crops(self):
        with patch('builtins.open', return_value=io.StringIO('72,4,20,20,2,3,1,1|2,5,99,1,0')):
            self.g._load_state()
        self.assertEqual(self.g._day, 72)
        self.assertEqual(self.g._elapsed, 48)
        self.assertEqual(self.g._basket_value, 10)
        self.assertEqual(self.g._plants[(2, 5)], [2, True, 0])

    def test_old_eight_minute_saves_keep_time_of_day(self):
        for data in ('LA2,7,390,20,6,2,3,1,1,10,0|2,5,1,1,0',
                     'LA3,7,390,20,6,2,3,1,1,10,0,1,2,1,2,3,4|2,5,1,1,0'):
            with patch('builtins.open', return_value=io.StringIO(data)):
                self.g._load_state()
            self.assertEqual(self.g._day, 7)
            self.assertEqual(self.g._elapsed, 195)
            self.assertEqual(self.g._plants[(2, 5)], [1, True, 0])

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
        self.g._elapsed = 195
        self.g._plants[(2, 5)] = [1, True, 0]
        self.g._foraged = True
        with patch('builtins.open', return_value=f), patch.object(M.os, 'rename') as rename:
            self.assertTrue(self.g._save_state())
            rename.assert_called_once_with('/lantern_acre.tmp', '/lantern_acre.sav')
        restored = game(M)
        with patch('builtins.open', return_value=io.StringIO(f.getvalue())):
            restored._load_state()
        self.assertTrue(f.getvalue().startswith("LA4,"))
        self.assertEqual(restored._elapsed, 195)
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


    def test_meadow_plots_and_both_bridges_reachable(self):
        todo=[(13,7)];seen=set(todo)
        while todo:
            x,y=todo.pop()
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                pos=x+dx,y+dy
                if M.LanternAcre._walkable(*pos) and pos not in seen:seen.add(pos);todo.append(pos)
        self.assertTrue(all(pos in seen for plot in M.PLOTS[3:] for pos in plot))
        self.assertTrue(M.LanternAcre._walkable(10,7))

    def test_repeated_area_changes_reuse_atlases_and_menu_and_keep_crops(self):
        g=self.g;g._unlocked=6
        g._plants={(2,5):[1,True,0],(14,3):[1,True,2]}
        cache,art,farmer=g._panel_cache,g._crop_art,g._farmer_art
        for _ in range(6):
            old=g._area
            self.assertTrue(g._interact((1,7) if old else (10,7)))
            self.assertNotEqual(g._area,old)
            self.assertIs(g._panel_cache,cache);self.assertIs(g._crop_art,art);self.assertIs(g._farmer_art,farmer)
            self.assertEqual(len(g._splash),1)
            self.assertTrue(all(pos[0]//12==g._area for pos in g._plot_sprites))
        g._new_day()
        self.assertEqual(g._plants[(2,5)],[2,False,0])
        self.assertEqual(g._plants[(14,3)],[2,False,2])

    def test_specific_seeds_seasonal_prices_and_stock_selection(self):
        g=self.g;g._coins=100
        self.assertEqual(g._packet_price(0),3)
        self.assertEqual(g._packet_price(2),15)
        g._buy_packet(2)
        self.assertEqual((g._selected_seed,g._seed_packets[2],g._coins),(2,3,85))
        g._tend((2,5))
        self.assertEqual(g._plants[(2,5)],[0,False,2])
        self.assertEqual((g._seed_packets[2],g._seeds),(2,6))
        g._day=17
        self.assertEqual(g._packet_price(2),12)
        g._coins=0
        g._buy_packet(2)
        self.assertEqual(g._seed_packets[2],2)
        g._seed_packets[2]=0;g._tend((3,5))
        self.assertNotIn((3,5),g._plants)

    def test_la3_roundtrip_includes_meadow_seed_inventory_and_selection(self):
        class File(io.StringIO):
            def close(self):pass
        g=self.g;g._unlocked=6;g._area=1;g._selected_seed=2;g._seed_packets=[1,2,3,4]
        g._plants[(14,3)]=[1,True,2]
        f=File()
        with patch('builtins.open',return_value=f),patch.object(M.os,'rename'):self.assertTrue(g._save_state())
        restored=game(M)
        with patch('builtins.open',return_value=io.StringIO(f.getvalue())):restored._load_state()
        self.assertEqual((restored._area,restored._selected_seed,restored._seed_packets,restored._unlocked),(1,2,[1,2,3,4],6))
        self.assertEqual(restored._plants,g._plants)

    def test_seed_pages_and_morning_card_allocate_no_bitmap(self):
        g=self.g
        with patch.object(M.displayio,'Bitmap',side_effect=AssertionError('bitmap allocated')):
            for kind in ('seeds','planting'):
                panel=g._panel(kind)[0];g._splash.remove(panel)
            group=g._panel('home')[0]
            g._day=8;g._new_day();titles=[]
            def script(t,g):titles.append(g._panel_cache[1].text)
            with patch.object(M,'time',FakeClock(g,script)):g._morning_card(True)
            self.assertIn('SUMMER, DAY 9',titles)
            self.assertEqual(g._elapsed,0)
            self.assertEqual(g._panel_cache[1].scale,1)
            g._splash.remove(group)

    def test_nested_seed_selection_returns_cleanly_to_market(self):
        g=self.g
        def script(t,g):
            g._A.value=not(.20<t<.28 or .8<t<.88 or 1.4<t<1.48)
            g._U.value=not(.45<t<.49)
            g._D.value=not(1.1<t<1.14)
            g._B.value=not(1.7<t<1.78 or 2.0<t<2.08)
        with patch.object(M,'time',FakeClock(g,script)):g._modal('town')
        self.assertEqual(g._selected_seed,0)
        self.assertEqual(len(g._splash),1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
