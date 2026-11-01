"""Campaign completion, tactical rules, persistence and retained scenes."""
import io
import unittest
from unittest.mock import patch
from ironbound_host import load,game
from ironbound_solver import complete
M=load()


class Clock:
    def __init__(self,g,script):self.g,self.script,self.now=g,script,0
    def monotonic(self):return self.now
    def sleep(self,t):
        self.now+=t;self.script(self.now,self.g)
        if self.now>10:raise AssertionError('input loop stuck')


class IronboundTests(unittest.TestCase):
    def setUp(self):self.g=game(M)
    def begin(self,mission=1):self.g._mission=mission;self.g._begin();return self.g
    def test_all_tiles_and_objectives_reachable_on_eight_maps(self):
        for mission in range(1,9):
            g=self.begin(mission)
            for y in range(8):
                for x in range(8):
                    if not g._blocked((x,y)):
                        self.assertIsNotNone(g._path((0,7),(x,y)),(mission,x,y))
            for p in ((3,2),(5,5),(4,3),(7,0)):
                self.assertFalse(g._blocked(p))
    def test_48_legal_mission_completions_across_weapons_and_refits(self):
        for weapon in (0,1):
            for refit in (0,1,2):
                g=game(M);g._weapon=weapon
                for mission in range(1,9):
                    with self.subTest(weapon=weapon,refit=refit,mission=mission):
                        g._mission=mission;g._begin()
                        complete(g,M)
                        self.assertTrue(g._extracted)
                        self.assertTrue(g._objective_done())
                        self.assertGreater(g._hull,0)
                        self.assertTrue(all(e['hp']==0 for e in g._enemies))
                        g._refit(refit)
    def test_legacy_save_migration_keeps_campaign_and_upgrades(self):
        with patch('builtins.open',return_value=io.StringIO('6,18,5,2')):self.g._load()
        self.assertEqual((self.g._mission,self.g._hull,self.g._attack,self.g._armor,self.g._capacity),(6,18,5,2,18))
        self.assertEqual(self.g._weapon,0)
    def test_invalid_save_never_partially_updates(self):
        for text in ('broken','9,10,3,1','1,-1,3,0','IB2,4,10,4,0,5,0,0','IB2,2,14,4,0,14,0,1'):
            with patch('builtins.open',return_value=io.StringIO(text)):self.g._load()
            self.assertEqual((self.g._mission,self.g._hull,self.g._attack),(1,14,4))
    def test_atomic_save_roundtrip_and_read_only_failure(self):
        class File(io.StringIO):
            def close(self):pass
        f=File();g=self.g;g._mission=8;g._finished=True;g._weapon=1
        with patch('builtins.open',return_value=f),patch.object(M.os,'rename') as rename:
            self.assertTrue(g._save());rename.assert_called_once_with('/ironbound.tmp','/ironbound.sav')
        other=game(M)
        with patch('builtins.open',return_value=io.StringIO(f.getvalue())):other._load()
        self.assertEqual((other._mission,other._finished,other._weapon),(8,True,1))
        with patch('builtins.open',side_effect=OSError):self.assertFalse(g._save())
    def test_invalid_move_and_shot_do_not_consume_turn(self):
        g=self.begin();self.assertFalse(g._move(-1,0));self.assertFalse(g._fire(0));self.assertEqual(g._turn,0)
        self.assertEqual(g._energy,3)
    def test_line_of_sight_cannot_cross_walls_or_diagonal_corners(self):
        g=self.begin()
        with patch.object(g,'_blocked',side_effect=lambda p:p==(2,1)):
            self.assertFalse(g._line((1,1),(3,1)))
            self.assertFalse(g._line((1,1),(2,2)))
            self.assertTrue(g._line((1,2),(3,2)))
    def test_enemies_plan_cardinal_steps_and_cannot_stack(self):
        g=self.begin(8)
        for _ in range(10):
            for e in g._enemies:
                if e['intent']=='move':self.assertLessEqual(g._distance(e['pos'],e['target']),1)
            g._guard()
            positions=[e['pos'] for e in g._enemies if e['hp']>0]
            self.assertEqual(len(positions),len(set(positions)))
            self.assertNotIn(g._pos,positions)
    def test_dodge_makes_targeted_attack_miss_then_enemy_recovers(self):
        g=self.begin();e=g._enemies[0];e.update(pos=(1,7),intent='fire',target=(0,7))
        self.assertTrue(g._move(0,-1))
        self.assertEqual(g._hull,14);self.assertEqual(e['intent'],'recover')
        g._guard();self.assertNotEqual(e['intent'],'recover')
    def test_guard_cover_armor_and_energy(self):
        g=self.begin();e=g._enemies[0];e.update(pos=(1,7),intent='fire',target=(0,7),kind=3)
        g._energy=0;g._armor=1
        g._guard();self.assertEqual((g._hull,g._energy),(14,1))
    def test_destroyed_enemy_never_fires_back(self):
        g=self.begin();e=g._enemies[0];e.update(pos=(1,7),intent='fire',target=(0,7),hp=1)
        self.assertTrue(g._fire(0));self.assertEqual(g._hull,14);self.assertEqual(e['hp'],0)
    def test_rail_energy_range_and_free_fallback(self):
        g=self.begin();g._weapon=1;e=g._enemies[0];e.update(pos=(0,3),hp=30,intent='recover',cooldown=1)
        self.assertIn(0,g._targets());g._fire(0)
        self.assertEqual((e['hp'],g._energy),(24,2))
        g._energy=0;self.assertNotIn(0,g._targets())
        e['pos']=(0,5);self.assertTrue(g._fire(0));self.assertEqual(g._energy,0)
    def test_repair_and_pulse_reject_waste_without_turn(self):
        g=self.begin();self.assertFalse(g._repair());self.assertEqual(g._kits,2)
        self.assertFalse(g._pulse());self.assertEqual((g._energy,g._turn),(3,0))
        g._hull=3;self.assertTrue(g._repair());self.assertEqual((g._hull,g._kits),(10,1))
    def test_pulse_cost_damage_and_line_of_sight(self):
        g=self.begin();e=g._enemies[0];e.update(pos=(0,5),hp=5,intent='fire',target=g._pos)
        self.assertTrue(g._pulse());self.assertEqual((e['hp'],g._energy,g._turn),(0,0,1))
        self.assertEqual(g._hull,14)
    def test_relay_requires_two_actions_and_cargo_is_collected_once(self):
        g=self.begin(2);g._pos=(4,3)
        self.assertTrue(g._interact());self.assertFalse(g._objective_done())
        self.assertTrue(g._interact());self.assertTrue(g._objective_done())
        turns=g._turn;self.assertFalse(g._interact());self.assertEqual(g._turn,turns)
        g=self.begin(3);g._pos=(3,1);g._move(0,1);g._move(0,-1);g._move(0,1)
        self.assertEqual(len(g._salvage),1);self.assertFalse(g._objective_done())
    def test_exit_requires_objectives_and_all_hostiles(self):
        g=self.begin(2);g._pos=(7,1)
        self.assertFalse(g._move(0,-1))
        for e in g._enemies:e['hp']=0
        self.assertFalse(g._gate_open());g._relay=2
        self.assertTrue(g._move(0,-1));self.assertTrue(g._extracted)
        self.assertEqual(g._turn,0)
    def test_no_actions_after_death_or_extraction(self):
        g=self.begin();g._hull=0
        for action in (lambda:g._move(0,-1),lambda:g._fire(0),g._guard,g._repair,g._pulse,g._interact):
            self.assertFalse(action())
        self.assertEqual(g._turn,0)
    def test_checkpoint_retry_refills_and_resets_board(self):
        g=self.begin(5);g._hull=1;g._kits=0;g._relay=2;g._begin()
        self.assertEqual((g._hull,g._kits,g._relay,g._mission),(14,2,0,5))
    def test_refit_choices_and_caps(self):
        g=self.g
        self.assertTrue(g._refit(0));self.assertEqual(g._attack,5)
        self.assertTrue(g._refit(1));self.assertEqual(g._capacity,17)
        g._armor=3;self.assertFalse(g._refit(2));self.assertFalse(g._refit(-1))
    def test_retained_scene_and_no_bitmap_writes_during_whole_mission(self):
        g=self.begin(3);scene=tuple(g._splash);bitmaps=[o.bitmap for o in scene if hasattr(o,'bitmap')]
        writes=[b.writes for b in bitmaps]
        with patch.object(M.displayio,'Bitmap',side_effect=AssertionError('allocated during play')):complete(g,M)
        self.assertEqual(tuple(g._splash),scene);self.assertEqual([b.writes for b in bitmaps],writes)
    def test_small_bitmap_allocations_and_distinct_actor_variants(self):
        g=self.begin();actors=[M._mech_art(i) for i in range(4)]
        self.assertEqual(len({bytes(b.pixels) for b in actors}),4)
        for b in actors+M._terrain(g)+[M._props_art()]:self.assertLessEqual(b.width*b.height//2,2304)
    def test_menu_consumes_entry_press_and_aim_cancel_spends_no_turn(self):
        g=self.begin();g._prepare_menu();g._A.value=False
        clock=Clock(g,lambda t,g:setattr(g._A,'value',t<.3))
        with patch.object(M,'time',clock),patch.object(M.displayio,'Bitmap',side_effect=AssertionError('menu allocation')):
            self.assertEqual(g._choose('TEST',('Resume','Leave')),0)
        self.assertGreaterEqual(clock.now,.3);self.assertEqual(g._turn,0)
        g._A.value=True;g._enemies[0]['pos']=(0,5)
        clock=Clock(g,lambda t,g:setattr(g._B,'value',t<.2))
        with patch.object(M,'time',clock):self.assertFalse(g._aim())
        self.assertEqual(g._turn,0);self.assertTrue(g._view['aim'].hidden)
    def test_aim_confirmation_fires_once(self):
        g=self.begin();g._enemies[0]['pos']=(0,5)
        clock=Clock(g,lambda t,g:setattr(g._A,'value',t<.2))
        with patch.object(M,'time',clock):self.assertTrue(g._aim())
        self.assertEqual(g._turn,1)
    def test_full_campaign_reaches_persistent_finale(self):
        g=self.g;missions=[]
        def run():
            missions.append(g._mission);g._begin();complete(g,M);return g._extracted
        with patch.object(g,'_hangar',return_value=True),patch.object(g,'_mission_run',side_effect=run),patch.object(g,'_save',return_value=True),patch.object(g,'_choose',side_effect=[2,2,2,0,0,0,0,1]):
            self.assertTrue(g.Game())
        self.assertEqual(missions,list(range(1,9)))
        self.assertTrue(g._finished)
        self.assertEqual(len(g._splash),0)

    def test_maxed_legacy_mech_can_accept_reward_without_softlock(self):
        g=self.g;g._attack,g._capacity,g._armor=12,35,3
        self.assertTrue(g._refit(0))
        self.assertEqual(g._hull,35)

    def test_one_turn_when_move_and_guard_pressed_together(self):
        g=self.g
        def script(t,g):
            g._B.value=not(.25<t<.3);g._R.value=not(.25<t<.3)
            if t>.35:g._U.value=g._D.value=False
        with patch.object(M,'time',Clock(g,script)):g._mission_run()
        self.assertEqual(g._turn,1)


if __name__=='__main__':unittest.main()
