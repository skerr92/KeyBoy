"""Connectivity plus playable guardian-to-exit proofs for all seven floors."""
import io
import unittest
from unittest.mock import patch
from dungeons_host import game, load
M=load()


def route(rows,start,goal,door=False):
    todo=[start]; parent={start:None}
    for pos in todo:
        if pos==goal:
            result=[]
            while parent[pos] is not None:
                result.append(pos);pos=parent[pos]
            return list(reversed(result))
        for dx,dy in M.DIRECTIONS:
            p=pos[0]+dx,pos[1]+dy
            if p not in parent and M.DungeonsCYL._passable(rows,p,door):
                parent[p]=pos;todo.append(p)
    return None


def complete(g):
    """Drive real movement/combat/timers. No teleporting, HP edits or god mode."""
    g._guard=True
    for step in range(5000):
        if g._cleared:
            return step
        if g._hearts<=0:
            raise AssertionError('solver died on floor %d'%g._number)
        adjacent=any(e['hp']>0 and abs(g._pos[0]-e['pos'][0])+abs(g._pos[1]-e['pos'][1])==1 for e in [g._boss]+g._shades)
        if adjacent:
            g._strike()
        else:
            goal=g._find(g._rows,'E') if g._door_open else g._boss['pos']
            path=route(g._rows,g._pos,goal,g._door_open)
            if not path:
                raise AssertionError('no path on floor %d'%g._number)
            dest=path[0]
            # Cross spikes early in their long safe interval.
            if dest not in g._traps or g._elapsed%3.2<1.25:
                g._move(dest[0]-g._pos[0],dest[1]-g._pos[1])
        for _ in range(5):
            g._tick(0.05)
        g._sync()
    raise AssertionError('floor never finished')


class Clock:
    def __init__(self,g,script):self.g,self.script,self.now=g,script,0
    def monotonic(self):return self.now
    def sleep(self,t):
        self.now+=t;self.script(self.now,self.g)
        if self.now>60:raise AssertionError('loop stuck')


class DungeonTests(unittest.TestCase):
    def setUp(self):self.g=game(M)

    def test_all_landmarks_reachable_before_locked_gate(self):
        for number,(name,rows) in enumerate(M.FLOORS):
            with self.subTest(floor=name):
                self.assertEqual({len(r) for r in rows},{13})
                start=self.g._find(rows,'S')
                for target in ('B','m','+','X','.'):
                    for y,row in enumerate(rows):
                        for x,c in enumerate(row):
                            if c==target:
                                self.assertIsNotNone(route(rows,start,(x,y)),(name,target,x,y))
                self.assertIsNotNone(route(rows,start,self.g._find(rows,'E'),True))

    def test_complete_all_seven_with_real_combat_and_no_damage(self):
        hearts=6
        for number in range(7):
            with self.subTest(floor=number+1):
                self.g._begin(number,hearts)
                complete(self.g)
                self.assertTrue(self.g._door_open)
                self.assertEqual(self.g._boss['hp'],0)
                self.assertEqual(self.g._best,number+1)
                self.assertEqual(self.g._hearts,6)
                hearts=self.g._hearts

    def test_levels_two_and_five_have_open_bridge_to_guardian(self):
        for number in (1,4):
            self.assertEqual(M.FLOORS[number][1][9][8],'.')
            self.g._begin(number)
            self.assertIsNotNone(route(self.g._rows,self.g._pos,self.g._boss['pos']))

    def test_closed_exit_blocks_and_dead_guardian_opens_same_sprite(self):
        self.g._begin(0)
        g=self.g
        g._pos=(10,1)
        gate=g._view['door']
        self.assertFalse(g._move(1,0))
        g._strike()
        g._attack_cooldown=0
        g._strike()
        g._sync()
        self.assertTrue(g._door_open)
        self.assertIs(g._view['door'],gate)
        self.assertEqual(gate[0],1)
        self.assertTrue(g._move(1,0))
        self.assertTrue(g._cleared)

    def test_sword_cooldown_range_and_guard_damage(self):
        self.g._begin(0);g=self.g
        g._strike()
        self.assertEqual(g._boss['hp'],4)
        g._pos=(8,1)
        self.assertFalse(g._strike())
        g._attack_cooldown=0;g._guard=True
        g._strike()
        self.assertEqual(g._boss['hp'],3)
        g._attack_cooldown=0;g._guard=False
        g._strike()
        self.assertEqual(g._boss['hp'],1)

    def test_windup_targets_tile_and_guard_blocks(self):
        self.g._begin(0);g=self.g
        g._pos=(8,1);g._boss['timer']=0
        g._enemy_tick(g._boss,0.01,True)
        self.assertEqual(g._boss['phase'],'windup')
        self.assertEqual(g._boss['target'],(8,1))
        self.assertEqual(g._hearts,6)
        g._guard=True;g._enemy_tick(g._boss,0.7,True)
        self.assertEqual(g._hearts,6)
        self.assertEqual(g._boss['phase'],'recover')
        g._boss['timer']=0;g._enemy_tick(g._boss,0.01,True)
        g._guard=False;g._pos=(7,1)
        g._enemy_tick(g._boss,0.7,True)
        self.assertEqual(g._hearts,6)

    def test_unblocked_attack_hurts_once_and_dead_enemy_cannot_attack(self):
        self.g._begin(0);g=self.g
        g._pos=(8,1)
        g._boss.update(phase='windup',target=g._pos,timer=0)
        g._enemy_tick(g._boss,0.01,True)
        self.assertEqual(g._hearts,5)
        g._damage();self.assertEqual(g._hearts,5)
        g._boss.update(hp=0,phase='windup',timer=0)
        g._hurt=0;g._enemy_tick(g._boss,0.01,True)
        self.assertEqual(g._hearts,5)

    def test_enemies_path_cardinally_and_do_not_overlap_hero(self):
        for number in range(7):
            self.g._begin(number);g=self.g
            step=g._next_step(g._boss['pos'],g._pos)
            self.assertEqual(sum(abs(a-b) for a,b in zip(step,g._boss['pos'])),1)
            self.assertTrue(g._passable(g._rows,step))
        g._pos=(4,9);g._boss['timer']=0
        g._enemy_tick(g._boss,0.1,True)
        self.assertNotEqual(g._pos,g._boss['pos'])

    def test_spikes_safe_warning_live_and_shield_does_not_block_them(self):
        self.g._begin(2);g=self.g
        g._pos=g._traps[0];g._guard=True
        for elapsed,phase in ((0,4),(1.9,5),(2.6,6)):
            g._elapsed=elapsed
            self.assertEqual(g._trap_phase(),phase)
            g._tick(0.01)
        self.assertEqual(g._hearts,5)

    def test_supplies_preserved_at_full_health_then_consumed_once(self):
        self.g._begin(0);g=self.g
        g._pos=(2,1);g._move(1,0)
        self.assertFalse(g._supplies[(3,1)])
        g._hearts=2;g._move(-1,0);g._move(1,0)
        self.assertEqual(g._hearts,4)
        self.assertTrue(g._supplies[(3,1)])
        g._move(-1,0);g._move(1,0)
        self.assertEqual(g._hearts,4)

    def test_retry_resets_floor_and_preserves_best(self):
        self.g._best=4
        self.g._begin(3,1);self.g._boss['hp']=0
        self.g._begin(3)
        self.assertEqual((self.g._hearts,self.g._boss['hp'],self.g._best),(6,7,4))

    def test_play_retains_every_bitmap_even_when_gate_opens(self):
        self.g._begin(0);g=self.g
        scene=tuple(g._splash)
        bitmaps=[o.bitmap for o in scene if hasattr(o,'bitmap')]
        writes=[b.writes for b in bitmaps]
        with patch.object(M.displayio,'Bitmap',side_effect=AssertionError('allocated during play')):
            complete(g)
        self.assertEqual(tuple(g._splash),scene)
        self.assertEqual([b.writes for b in bitmaps],writes)

    def test_art_allocations_and_guardian_variants(self):
        forms=[M._guardian_art(n) for n in range(7)]
        self.assertEqual(len({bytes(b.pixels) for b in forms}),7)
        for b in forms+M._terrain(0)+[M._hero_art(),M._objects_art()]:
            self.assertLessEqual(b.width*b.height//2,2304)

    def test_best_load_and_atomic_save_failure(self):
        with patch('builtins.open',return_value=io.StringIO('5')):
            g=M.DungeonsCYL(self.g._splash,self.g._A,self.g._B,self.g._U,self.g._D,self.g._L,self.g._R,self.g._sel,self.g._audio)
        self.assertEqual(g._best,5)
        class File(io.StringIO):
            def close(self):pass
        f=File()
        with patch('builtins.open',return_value=f),patch.object(M.os,'rename') as rename:
            self.assertTrue(g._save_best())
            self.assertEqual(f.getvalue(),'5')
            rename.assert_called_once_with('/dungeons.tmp','/dungeons.txt')
        with patch('builtins.open',side_effect=OSError):
            self.assertFalse(g._save_best())

    def test_menu_retains_scene_consumes_entry_press_and_freezes_time(self):
        self.g._begin(0);g=self.g
        g._prepare_menu();scene=tuple(g._splash)
        g._A.value=False
        def script(t,g):g._A.value=t<0.3
        clock=Clock(g,script)
        with patch.object(M,'time',clock),patch.object(M.displayio,'Bitmap',side_effect=AssertionError('menu allocation')):
            self.assertEqual(g._choose('TEST',('Resume','Leave')),0)
        self.assertGreaterEqual(clock.now,0.3)
        self.assertEqual(tuple(g._splash),scene)
        self.assertEqual(g._elapsed,0)

    def test_campaign_reaches_final_victory_and_exits(self):
        g=self.g
        floors=[]
        def play(number,hearts):
            floors.append(number)
            g._begin(number,hearts)
            complete(g)
            return g._cleared,g._hearts
        with patch.object(g,'_choose',side_effect=[0]*7+[1]),patch.object(g,'_play_floor',side_effect=play),patch.object(g,'_save_best',return_value=True):
            self.assertTrue(g.Game())
        self.assertEqual(floors,list(range(7)))
        self.assertEqual(g._best,7)
        self.assertEqual(len(g._splash),0)

    def test_campaign_death_retries_same_floor_at_full_health(self):
        g=self.g
        calls=[]
        def play(number,hearts):
            calls.append((number,hearts))
            if len(calls)==3:
                return False,0
            return True,4
        # Welcome, floors 1/2, retry floor 3, leave after clearing it.
        with patch.object(g,'_choose',side_effect=[0,0,0,0,1]),patch.object(g,'_play_floor',side_effect=play),patch.object(g,'_save_best',return_value=True):
            g.Game()
        self.assertEqual(calls,[(0,6),(1,6),(2,6),(2,6)])

    def test_pause_discards_wall_time_and_up_down_exits(self):
        g=self.g
        def script(t,g):
            g._sel.value=not (0.1<t<0.2)
            if t>1:g._U.value=g._D.value=False
        clock=Clock(g,script)
        def pause():clock.now+=50
        with patch.object(M,'time',clock),patch.object(g,'_pause',side_effect=pause):
            g._play_floor(0)
        self.assertTrue(g._exit)
        self.assertLess(g._elapsed,1)


if __name__=='__main__':unittest.main()
