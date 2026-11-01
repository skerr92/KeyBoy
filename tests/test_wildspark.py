"""Wildspark progression, combat, save migration, and retained scene checks."""
import io
import unittest
from unittest.mock import patch
from wildspark_host import game, load

M = load()


class Clock:
    def __init__(self, g, script):
        self.now, self.g, self.script = 0, g, script
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds
        self.script(self.now, self.g)
        if self.now > 5:
            raise AssertionError('input loop failed to exit')


class WildsparkTests(unittest.TestCase):
    def setUp(self):
        self.g = game(M)

    def battle(self, family=3, level=4, **kwargs):
        self.g._build_battle(family, level, **kwargs)

    def test_legacy_save_preserves_progress_and_opens_previous_trails(self):
        with patch('builtins.open', return_value=io.StringIO('4,8,17,2,5,83,9')):
            self.g._load()
        self.assertEqual(self.g._party[4], [8, 17, 0])
        self.assertEqual((self.g._family, self.g._badges, self.g._route, self.g._steps, self.g._tamed), (4, 2, 5, 83, 9))
        self.assertEqual(self.g._relics, 15)
        self.assertEqual(self.g._caught, 7 << 12)

    def test_invalid_saves_are_transactional(self):
        for data in ('garbage', '0,3,1,0,9,0,1', 'WS2,0,0,1,0,1,1,0,3,0|0,3,99,0',
                     'WS2,0,0,1,0,1,1,0,3,0|0,3,20,0;0,4,20,0',
                     'WS2,0,0,1,0,1,1,0,3,0|3,3,20,0'):
            with patch('builtins.open', return_value=io.StringIO(data)):
                self.g._load()
            self.assertEqual(self.g._party[0], [3, 34, 0])
            self.assertTrue(self.g._new_game)

    def test_party_save_roundtrip_and_atomic_replace(self):
        class File(io.StringIO):
            def close(self):
                pass
        self.g._party[6] = [9, 43, 7]
        self.g._family, self.g._relics, self.g._finished = 6, 63, True
        f = File()
        with patch('builtins.open', return_value=f), patch.object(M.os, 'rename') as rename:
            self.assertTrue(self.g._save())
            rename.assert_called_once_with('/wildspark.tmp', '/wildspark.sav')
        restored = game(M)
        with patch('builtins.open', return_value=io.StringIO(f.getvalue())):
            restored._load()
        self.assertEqual(restored._party, self.g._party)
        self.assertEqual((restored._family, restored._relics, restored._finished), (6, 63, True))
        with patch('builtins.open', side_effect=OSError):
            self.assertFalse(self.g._save())

    def test_type_triangle_and_resistance(self):
        for a, d in ((0, 6), (6, 3), (3, 0)):
            self.assertEqual(self.g._effective(a, d, 12), 18)
            self.assertEqual(self.g._effective(d, a, 12), 9)
        self.assertEqual(self.g._effective(0, 2, 12), 12)

    def test_insufficient_focus_does_not_spend_turn(self):
        self.battle()
        self.g._act(1)
        self.assertEqual((self.g._turn, self.g._focus, self.g._foe_hp), (0, 1, self.g._foe_max))

    def test_strike_focus_and_element_burst(self):
        self.battle(6)
        self.g._act(0)
        self.assertEqual(self.g._focus, 2)
        before = self.g._foe_hp
        self.g._act(1)
        self.assertEqual(self.g._focus, 0)
        self.assertEqual(before - self.g._foe_hp, 19)

    def test_knockout_never_retaliates(self):
        self.battle()
        self.g._foe_hp = 1
        self.g._act(0)
        self.assertEqual(self.g._battle_result, 'WON')
        self.assertEqual(self.g._party[0][1], 34)
        self.assertEqual(self.g._turn, 0)

    def test_charge_telegraphs_burst_and_guard_reduces_it(self):
        self.battle()
        self.g._turn = 1
        self.g._enemy_turn()
        self.assertEqual(self.g._party[0][1], 34)
        self.g._act(2)
        self.assertEqual(self.g._party[0][1], 29)  # Tide burst 16 / guard 3.
        self.assertEqual(self.g._focus, 2)

    def test_bond_requires_half_health_and_creates_usable_partner(self):
        self.battle(4, 5)
        self.g._act(3)
        self.assertEqual(self.g._turn, 0)
        self.assertIsNone(self.g._party[4])
        self.g._foe_hp = self.g._foe_max // 2
        self.g._act(3)
        self.assertEqual(self.g._party[4], [5, 42, 0])
        self.assertEqual(self.g._battle_result, 'BONDED')
        self.assertTrue(self.g._caught & (1 << 13))
        with patch.object(self.g, '_choose', return_value=1):
            self.assertTrue(self.g._partners())
        self.assertEqual(self.g._family, 4)

    def test_duplicate_bonds_do_not_reset_partner_progress(self):
        self.g._party[3] = [10, 21, 9]
        self.battle(3, 3)
        self.g._foe_hp = 1
        self.g._act(3)
        self.assertEqual(self.g._party[3], [10, 21, 9])

    def test_safe_weakening_allows_strong_partner_to_catch_weak_foe(self):
        self.g._party[0] = [30, 142, 0]
        self.battle(4, 2)
        self.g._act(6)
        self.assertEqual(self.g._foe_hp, 1)
        self.assertIsNone(self.g._battle_result)
        self.g._act(3)
        self.assertEqual(self.g._battle_result, 'BONDED')
        self.assertIsNotNone(self.g._party[4])

    def test_all_27_forms_can_be_encountered_and_caught(self):
        seen = set()
        for route in (4, 5, 6):
            self.g._route = route
            for search in range(9):
                self.g._steps = search * 6
                family, level = self.g._wild_target()
                seen.add((family, M._form(level)))
                self.g._rest()
                self.battle(family, level)
                while self.g._foe_hp > self.g._foe_max // 2:
                    self.g._party[self.g._family][1] = 100
                    self.g._act(6)
                self.g._act(3)
                self.assertEqual(self.g._battle_result, 'BONDED')
        self.assertEqual(len(seen), 27)
        self.assertEqual(self.g._caught, (1 << 27) - 1)
        self.assertTrue(all(mon is not None for mon in self.g._party))

    def test_bosses_cannot_be_bonded(self):
        for kind in ('gym', 'final'):
            self.battle(**{kind: True})
            self.g._foe_hp = 1
            self.g._act(3)
            self.assertIsNone(self.g._battle_result)
            self.assertEqual(self.g._turn, 0)

    def test_tonics_do_not_waste_items_or_turns(self):
        self.battle()
        self.g._act(4)
        self.assertEqual((self.g._potions, self.g._turn), (3, 0))
        self.g._party[0][1], self.g._turn = 10, 1
        self.g._act(4)
        self.assertEqual((self.g._potions, self.g._party[0][1]), (2, 28))
        self.g._potions = 0
        self.g._act(4)
        self.assertEqual(self.g._turn, 2)

    def test_faint_requires_switch_or_defeat_and_clinic_heals_everyone(self):
        self.battle()
        self.g._party[0][1] = 1
        self.g._party[6] = [4, 10, 0]
        self.g._enemy_turn()
        self.assertIsNone(self.g._battle_result)
        turn = self.g._turn
        self.g._act(0)
        self.assertEqual(self.g._turn, turn)
        with patch.object(self.g, '_choose', return_value=1):
            self.assertTrue(self.g._partners())
        self.g._party[6][1] = 1
        self.g._turn = 0
        self.g._enemy_turn()
        self.assertEqual(self.g._battle_result, 'DEFEAT')
        self.g._rest()
        self.assertEqual((self.g._party[0][1], self.g._party[6][1], self.g._potions), (34, 38, 3))

    def test_xp_evolution_and_level_cap(self):
        self.g._foe_level = 7
        self.assertTrue(self.g._award_xp())
        self.assertEqual(self.g._party[0][0], 4)
        self.assertEqual(self.g._caught & 3, 3)
        self.g._party[0] = [7, 50, 28]
        self.assertTrue(self.g._award_xp())
        self.assertEqual(self.g._party[0][0], 8)
        self.g._party[0] = [30, 142, 97]
        self.g._award_xp()
        self.assertEqual(self.g._party[0], [30, 142, 0])

    def test_all_landmarks_reachable(self):
        seen, todo = {(3, 7)}, [(3, 7)]
        while todo:
            x, y = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = x + dx, y + dy
                if self.g._walkable(*p) and p not in seen:
                    seen.add(p)
                    todo.append(p)
        self.assertTrue({(2, 3), (9, 3), (7, 7), (0, 7), (11, 7)} <= seen)

    def test_six_relics_three_emblems_and_finale(self):
        with patch.object(self.g, '_notice'), patch.object(self.g, '_battle', return_value=True), patch.object(self.g, '_save', return_value=True):
            for route in range(1, 7):
                self.assertEqual(self.g._route, route)
                self.assertIsNotNone(self.g._travel(1))
                self.g._interact((7, 7))
                if route % 2 == 0:
                    self.assertIsNotNone(self.g._travel(1))
                    self.assertTrue(self.g._interact((9, 3)))
                    self.assertEqual(self.g._badges, route // 2)
                if route < 6:
                    self.assertIsNone(self.g._travel(1))
            self.g._interact((9, 3))
            self.assertTrue(self.g._finished)
            self.assertEqual(self.g._relics, 63)

    def test_failed_challenge_does_not_grant_emblem(self):
        self.g._route, self.g._relics = 2, 2
        with patch.object(self.g, '_battle', return_value=False):
            self.assertTrue(self.g._interact((9, 3)))
        self.assertEqual(self.g._badges, 0)

    def test_world_updates_retain_scenery_and_bitmap_pixels(self):
        self.g._build_world()
        scene = tuple(self.g._splash)
        writes = [o.bitmap.writes for o in scene if hasattr(o, 'bitmap')]
        with patch.object(M.displayio, 'Bitmap', side_effect=AssertionError('allocated during walking')):
            for pos in ((3, 7), (7, 7), (2, 3), (9, 3), (6, 5)):
                self.g._sync_world(pos)
                M._place(self.g._view['hero'], pos[0] * 20, pos[1] * 20)
        self.assertEqual(tuple(self.g._splash), scene)
        self.assertEqual([o.bitmap.writes for o in scene if hasattr(o, 'bitmap')], writes)

    def test_27_unique_forms_and_small_art_allocations(self):
        forms = [M._creature(f, s) for f in range(9) for s in range(3)]
        self.assertEqual(len({bytes(b.pixels) for b in forms}), 27)
        for b in forms + M._world_art(1) + M._battle_art():
            self.assertLessEqual(b.width * b.height // 2, 2304)

    def test_menu_consumes_entry_press_reuses_background_and_wraps_detail(self):
        self.g._prepare_menu()
        group = self.g._menu_cache[0]
        scene = tuple(group)
        self.g._A.value = False
        def script(t, g):
            g._A.value = t < 0.3
        clock = Clock(self.g, script)
        with patch.object(M, 'time', clock), patch.object(M.displayio, 'Bitmap', side_effect=AssertionError('menu backing rebuilt')):
            self.assertEqual(self.g._choose('TEST', ('Continue',), ('Clinic restored your companions safely.',)), 0)
        self.assertGreaterEqual(clock.now, 0.3)
        self.assertEqual(tuple(group), scene)
        self.assertNotIn(group, self.g._splash)
        self.assertLessEqual(len(self.g._menu_cache[3].text), 33)
        self.assertIn('safely.', self.g._menu_cache[4].text)

    def test_walking_buffers_action_until_arrival_without_rebuilding(self):
        original = self.g._build_world
        calls, actions = [], []
        def build():
            calls.append(1)
            original()
        def interact(pos):
            actions.append(pos)
            self.g._exit = True
            return False
        def script(t, g):
            g._R.value = not (0.16 < t < 0.30)
            g._A.value = not (0.22 < t < 0.28)
        with patch.object(M, 'time', Clock(self.g, script)), patch.object(self.g, '_build_world', side_effect=build), patch.object(self.g, '_interact', side_effect=interact):
            self.g._world()
        self.assertEqual(actions, [(4, 7)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.g._steps, 1)

    def test_forced_switch_is_free_but_voluntary_switch_uses_turn(self):
        for fainted in (False, True):
            g = game(M)
            g._party[0][1] = 0 if fainted else 34
            g._party[3] = [4, 38, 0]
            def script(t, state):
                state._L.value = not (0.19 < t < 0.65)
                state._A.value = not (0.72 < t < 0.78)
                state._B.value = not (t > 0.95)
            with patch.object(M, 'time', Clock(g, script)), patch.object(g, '_choose', return_value=1):
                g._battle(6, 4)
            self.assertEqual(g._family, 3)
            self.assertEqual(g._turn, 0 if fainted else 1)

    def test_idle_battle_keeps_scene_until_back_press(self):
        original = self.g._build_battle
        snapshots = []
        def build(*args):
            original(*args)
            snapshots.append(tuple(self.g._splash))
        def script(t, g):
            if t > 0.6:
                g._B.value = False
        with patch.object(M, 'time', Clock(self.g, script)), patch.object(self.g, '_build_battle', side_effect=build):
            self.assertFalse(self.g._battle(3, 4))
        self.assertEqual(tuple(self.g._splash), snapshots[0])
        self.assertEqual(self.g._turn, 0)


if __name__ == '__main__':
    unittest.main()
