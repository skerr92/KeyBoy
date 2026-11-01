"""Run: python3 tests/test_last_beacon.py (no third-party packages required)."""
import io
import unittest
from unittest.mock import patch
from beacon_host import load, game

M = load()


class Clock:
    def __init__(self, g, script):
        self.g, self.script, self.now = g, script, 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.script(self.now, self.g)
        if self.now > 12:
            raise AssertionError('Input loop did not finish')


class BeaconTests(unittest.TestCase):
    def setUp(self):
        self.g = game(M)
        self.g._start_mission()

    def enemy(self, x=120, y=100, hp=20, kind=0, slot=0):
        e = self.g._enemies[slot]
        e[:6] = [True, float(x), float(y), hp, kind, 0.0]
        e[6].hidden = False
        return e

    def test_every_loadout_and_contract_selectable(self):
        for row, field, count in ((0, '_mission', len(M.MISSIONS)), (1, '_weapon', len(M.WEAPONS)), (2, '_support', len(M.SUPPORTS))):
            seen = set()
            for _ in range(count):
                self.g._change_loadout(row, 1)
                seen.add(getattr(self.g, field))
            self.assertEqual(seen, set(range(count)))
            self.g._change_loadout(row, -1)
            self.assertEqual(getattr(self.g, field), count - 1)

    def test_salvage_and_complete_extraction_sequence(self):
        for obj in self.g._objectives:
            self.g._x, self.g._y = obj[:2]
            self.g._update_objectives(0.1)
        self.assertEqual(self.g._phase, 'BEACON')
        self.g._x, self.g._y = M.EXTRACT
        self.g._update_objectives(0.1)
        self.assertEqual(self.g._phase, 'INBOUND')
        self.g._update_objectives(18)
        self.assertEqual(self.g._phase, 'BOARD')
        self.g._update_objectives(0.1)
        self.assertEqual(self.g._result, 'EXTRACTED')

    def test_shuttle_leaves_when_player_does_not_board(self):
        self.g._phase, self.g._extract_clock = 'INBOUND', 1
        self.g._update_objectives(1)
        self.assertEqual(self.g._phase, 'BOARD')
        self.g._update_objectives(12)
        self.assertEqual(self.g._result, 'MISSED SHUTTLE')

    def test_deadline_takes_precedence_over_boarding(self):
        self.g._time = 0.1
        self.g._phase, self.g._board_clock = 'BOARD', 10
        self.g._x, self.g._y = M.EXTRACT
        self.g._step(0.2)
        self.assertEqual(self.g._result, 'SIGNAL LOST')
        self.assertEqual(self.g._settle(), 0)

    def test_uplink_progress_pauses_when_contested_and_resumes(self):
        self.g._mission = 2
        self.g._start_mission()
        obj = self.g._objectives[0]
        self.g._x, self.g._y = obj[:2]
        e = self.enemy(obj[0] + 15, obj[1])
        self.g._update_objectives(3)
        self.assertEqual(obj[2], 6)
        e[0] = False
        self.g._update_objectives(3)
        self.assertEqual(obj[2], 3)
        self.g._x, self.g._y = 118, 202
        self.g._update_objectives(3)
        self.assertEqual(obj[2], 3)
        self.g._x, self.g._y = obj[:2]
        self.g._update_objectives(3)
        self.assertTrue(obj[3])

    def test_hives_require_damage_not_contact(self):
        self.g._mission = 1
        self.g._start_mission()
        obj = self.g._objectives[0]
        self.g._x, self.g._y = obj[:2]
        self.g._update_objectives(10)
        self.assertFalse(obj[3])
        for _ in range(4):
            self.g._bullet(obj[0], obj[1], 0, 0, 0, 6)
            self.g._update_shots(0.02)
        self.assertTrue(obj[3])

    def test_reload_consumes_reserve_and_sidearm_prevents_softlock(self):
        self.g._mag, self.g._reserve = 1, 5
        self.g._fire()
        self.assertEqual(self.g._mag, 0)
        self.assertGreater(self.g._reload, 0)
        self.g._step(1.4)
        self.assertEqual((self.g._mag, self.g._reserve), (5, 0))
        self.g._mag, self.g._shot_clock = 0, 0
        before = sum(s[0] for s in self.g._shots)
        self.g._fire()
        self.assertEqual(sum(s[0] for s in self.g._shots), before + 1)
        self.assertEqual(self.g._mag, 0)

    def test_weapon_patterns_and_pool_exhaustion(self):
        for weapon, count in ((0, 1), (1, 3), (2, 1)):
            self.g._weapon = weapon
            self.g._start_mission()
            self.g._fire()
            self.assertEqual(sum(s[0] for s in self.g._shots), count)
            self.assertEqual(self.g._shots[0][7], int(weapon == 2))
        for shot in self.g._shots:
            shot[0] = True
        self.g._shot_clock = 0
        mag = self.g._mag
        self.g._fire()
        self.assertEqual(self.g._mag, mag)

    def test_bullets_hit_enemies_and_stop_at_cover(self):
        e = self.enemy(118, 170, hp=2)
        self.g._bullet(118, 178, 0, -1, 100, 2)
        self.g._update_shots(0.05)
        self.assertFalse(e[0])
        self.g._bullet(90, 61, 0, 1, 100, 10)
        self.g._update_shots(0.05)
        self.assertFalse(any(s[0] for s in self.g._shots))

    def test_lancer_pierces_two_distinct_enemies(self):
        first = self.enemy(118, 160, hp=5)
        second = self.enemy(118, 140, hp=5, slot=1)
        self.g._bullet(118, 166, 0, -1, 100, 6, 1)
        for _ in range(7):
            self.g._update_shots(0.04)
        self.assertFalse(first[0])
        self.assertFalse(second[0])
        self.assertEqual(self.g._kills, 2)

    def test_firing_locks_facing_for_strafing(self):
        self.g._step(0.02, 1, 0, True)
        self.assertEqual((self.g._aim_x, self.g._aim_y), (0, -1))
        self.g._step(0.02, 1, 0, False)
        self.assertEqual((self.g._aim_x, self.g._aim_y), (1, 0))

    def test_telegraphed_hits_have_shared_invulnerability(self):
        for i in range(3):
            self.enemy(118, 202, slot=i)
        self.g._update_enemies(0.02)
        self.assertEqual(self.g._hp, 6)
        self.g._update_enemies(0.3)
        self.assertEqual(self.g._hp, 5)
        self.assertGreater(self.g._invincible, 0)

    def test_support_strike_is_delayed_and_cooldown_prevents_spam(self):
        e = self.enemy(118, 150)
        self.g._use_support()
        self.assertTrue(e[0])
        self.assertEqual(self.g._support_left, 2)
        self.g._use_support()
        self.assertEqual(self.g._support_left, 2)
        self.g._step(0.9)
        self.assertFalse(e[0])

    def test_sentry_expiry_and_resupply_caps(self):
        self.g._support = 1
        self.g._start_mission()
        self.enemy(118, 150)
        self.g._use_support()
        self.g._step(0.02)
        self.assertTrue(any(s[0] for s in self.g._shots))
        self.g._step(14)
        self.assertTrue(self.g._view['turret'].hidden)
        self.g._support = 2
        self.g._start_mission()
        self.g._hp, self.g._reserve = 2, 0
        self.g._use_support()
        self.assertEqual((self.g._hp, self.g._reserve), (5, 54))
        self.g._resupply()
        self.assertEqual((self.g._hp, self.g._reserve), (6, 90))

    def test_supply_cache_is_not_wasted_at_full_resources(self):
        self.g._x, self.g._y = 112, 48
        self.g._step(0.02)
        self.assertFalse(self.g._supply_taken[0])
        self.g._hp = 2
        self.g._step(0.02)
        self.assertTrue(self.g._supply_taken[0])
        self.assertEqual(self.g._hp, 5)

    def test_scene_and_bitmaps_retained_for_full_operation(self):
        scene = tuple(self.g._splash)
        bitmaps = {id(o.bitmap): o.bitmap for o in scene if hasattr(o, 'bitmap')}
        writes = {i: b.writes for i, b in bitmaps.items()}
        for _ in range(250):
            self.g._step(0.02, firing=True)
        self.g._use_support()
        for _ in range(50):
            self.g._step(0.02, firing=True)
        self.assertEqual(tuple(self.g._splash), scene)
        self.assertEqual({i: b.writes for i, b in bitmaps.items()}, writes)
        self.assertEqual(len(self.g._shots), M.SHOT_LIMIT)
        self.assertEqual(len(self.g._enemies), M.ENEMY_LIMIT)

    def test_objectives_supplies_and_extraction_reachable_with_collision(self):
        # Traverse the continuous arena on a 2-pixel grid with the player's radius.
        todo, seen = [(118, 202)], {(118, 202)}
        while todo:
            x, y = todo.pop()
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                pos = (x + dx, y + dy)
                if pos not in seen and not M.LastBeacon._blocked(*pos):
                    seen.add(pos)
                    todo.append(pos)
        for tx, ty in M.OBJECTIVE_POS + (M.EXTRACT, (112, 48), (19, 108)):
            self.assertTrue(any(M._d2(x, y, tx, ty) < 18 ** 2 for x, y in seen), (tx, ty))
        self.assertTrue(M.LastBeacon._blocked(80, 70))
        self.assertFalse(M.LastBeacon._blocked(118, 202))

    def test_settlement_only_rewards_extraction_once(self):
        self.g._result = 'TROOPER LOST'
        self.assertEqual(self.g._settle(), 0)
        self.g._result = 'EXTRACTED'
        reward = self.g._settle()
        self.assertGreater(reward, M.MISSIONS[0][6])
        self.assertEqual(self.g._credits, reward)
        self.assertEqual(self.g._cleared, 1)
        self.assertEqual(self.g._settle(), 0)

    def test_refit_costs_and_limits(self):
        self.g._credits = 1000
        for _ in range(4):
            self.g._upgrade(0)
            self.g._upgrade(1)
        self.assertEqual((self.g._armor, self.g._power), (3, 3))
        self.assertEqual(self.g._credits, 370)
        self.g._credits, self.g._armor = 0, 0
        self.assertIn('Need', self.g._upgrade(0))

    def test_old_save_migration_and_invalid_data_are_transactional(self):
        with patch('builtins.open', return_value=io.StringIO('5,3,4,3')):
            self.g._load()
        self.assertEqual((self.g._mission, self.g._power, self.g._credits, self.g._cleared), (4, 2, 20, 15))
        for data in ('LB2,0,0,99,0,0,0,0', 'LB2,0,0,0,-1,0,0,0', 'bad', '1,2,3'):
            with patch('builtins.open', return_value=io.StringIO(data)):
                self.g._load()
            self.assertEqual(self.g._mission, 4)

    def test_save_roundtrip_and_read_only_failure(self):
        class File(io.StringIO):
            def close(self):
                pass
        f = File()
        self.g._weapon, self.g._cleared, self.g._credits = 2, 7, 91
        with patch('builtins.open', return_value=f), patch.object(M.os, 'rename') as rename:
            self.assertTrue(self.g._save())
            rename.assert_called_once_with('/last_beacon.tmp', '/last_beacon.sav')
        restored = game(M)
        with patch('builtins.open', return_value=io.StringIO(f.getvalue())):
            restored._load()
        self.assertEqual((restored._weapon, restored._cleared, restored._credits), (2, 7, 91))
        with patch('builtins.open', side_effect=OSError):
            self.assertFalse(self.g._save())

    def test_field_menu_freezes_all_clocks_and_consumes_entry_button(self):
        self.g._sel.value = False
        def script(t, g):
            g._sel.value = t > 0.1
            g._B.value = t < 0.5
        before = self.g._time
        scene = tuple(self.g._splash)
        with patch.object(M, 'time', Clock(self.g, script)):
            self.g._menu('field')
        self.assertEqual(self.g._time, before)
        self.assertEqual(tuple(self.g._splash), scene)

    def test_ship_launch_selection_and_input_guard(self):
        g = game(M)
        g._A.value = False
        def script(t, g):
            g._A.value = not (t < 0.1 or t > 1.05)
            g._U.value = not (0.2 < t < 0.3)  # wrap from first row to Deploy
        clock = Clock(g, script)
        with patch.object(M, 'time', clock):
            self.assertTrue(g._ship())
        self.assertGreater(clock.now, 1)
        self.assertEqual(g._mission, 0)

    def test_mission_loop_discards_pause_wall_time(self):
        g = game(M)
        def script(t, g):
            g._sel.value = not (0.2 < t < 0.3)
            g._B.value = not (0.8 < t < 0.9)
            if t > 1.1:
                g._U.value = g._D.value = False
        with patch.object(M, 'time', Clock(g, script)), patch.object(g, '_drop_in'):
            g._mission_run()
        self.assertGreater(g._time, M.MISSIONS[0][4] - 0.7)
        self.assertLess(g._time, M.MISSIONS[0][4] - 0.2)

    def test_return_from_debrief_reuses_bridge_scene(self):
        g = game(M)
        g._build_ship()
        scene = tuple(g._splash)
        def script(t, g):
            g._U.value = not (0.2 < t < 0.3)
            g._A.value = t < 0.5
        with patch.object(M, 'time', Clock(g, script)), patch.object(g, '_build_ship') as build:
            self.assertTrue(g._ship())
        build.assert_not_called()
        self.assertEqual(tuple(g._splash), scene)


    def test_new_weapons_and_pool_reservation(self):
        for weapon,pellets in ((3,1),(4,5)):
            self.g._weapon=weapon;self.g._start_mission()
            self.g._fire()
            self.assertEqual(sum(s[0] for s in self.g._shots),pellets)
            self.assertEqual(self.g._mag,M.WEAPONS[weapon][1]-1)
        self.g._shot_clock=0
        for s in self.g._shots:s[0]=True
        for s in self.g._shots[:4]:s[0]=False
        mag=self.g._mag
        self.g._fire()
        self.assertEqual(self.g._mag,mag)

    def test_shield_blocks_damage_then_expires(self):
        self.g._support=3;self.g._start_mission();self.g._use_support()
        e=self.enemy(self.g._x+5,self.g._y);e[5]=.01
        before=self.g._hp
        self.g._update_enemies(.02)
        self.assertEqual(self.g._hp,before)
        self.g._step(6.1)
        e[5]=.01;self.g._invincible=0
        self.g._update_enemies(.02)
        self.assertLess(self.g._hp,before)
        self.assertEqual(self.g._support_left,1)

    def test_stasis_slows_motion_and_windups_without_killing(self):
        self.g._support=4;self.g._start_mission();self.g._use_support()
        e=self.enemy(118,165);before=e[2]
        self.g._update_enemies(.1)
        slowed=abs(e[2]-before)
        e[2]=before;self.g._stasis_time=0
        self.g._update_enemies(.1)
        self.assertAlmostEqual(slowed/abs(e[2]-before),.35,places=4)
        self.assertTrue(e[0])
        self.g._stasis_time=8;e[1],e[2]=self.g._x+5,self.g._y;e[5]=.2
        self.g._update_enemies(.1)
        self.assertAlmostEqual(e[5],.165)

    def test_new_choices_and_completion_bits_roundtrip(self):
        import io
        with patch('builtins.open',return_value=io.StringIO('LB2,7,4,4,300,255,2,3')):
            self.g._load()
        self.assertEqual((self.g._mission,self.g._weapon,self.g._support,self.g._cleared),(7,4,4,255))
        self.g._build_ship()
        for row in range(5):self.g._sync_ship(row)

    def test_all_eight_contract_objectives_and_extraction(self):
        for mission,info in enumerate(M.MISSIONS):
            self.g._mission=mission;self.g._start_mission()
            for obj in self.g._objectives:
                self.g._x,self.g._y=obj[:2]
                if info[1]=='PURGE':
                    while not obj[3]:
                        self.g._bullet(obj[0],obj[1],0,0,0,6)
                        self.g._update_shots(.02)
                else:self.g._update_objectives(6.1)
            self.g._update_objectives(.1)
            self.assertEqual(self.g._phase,'BEACON')
            self.g._x,self.g._y=M.EXTRACT
            self.g._update_objectives(.1);self.g._update_objectives(18);self.g._update_objectives(.1)
            self.assertEqual(self.g._result,'EXTRACTED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
