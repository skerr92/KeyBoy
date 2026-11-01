import unittest
from unittest.mock import patch
from arcade_host import load,game


class ArcadeTests(unittest.TestCase):
    def test_all_rooms_reuse_scenery_and_match_guardian_collision_sizes(self):
        m=load('journey');g=game(m,'journey');terrain=None
        for i in range(9):
            g._level=i
            hero,platforms,boss,data,hp,_,_=g._setup_level()
            if terrain is not None:self.assertIs(g._scenery,terrain)
            terrain=g._scenery
            self.assertEqual((hero.tile_width,hero.tile_height),(m.PLAYER_W,m.PLAYER_H))
            self.assertEqual(len(g._sparks),len(platforms)-1)
            if boss:self.assertEqual((boss.bitmap.width,boss.bitmap.height),data[2:4])

    def test_all_nine_rooms_complete_using_controller_inputs(self):
        from journey_solver import Clock
        m=load('journey')
        for level in range(9):
            g=game(m,'journey');g._level=level;c=Clock(g,m)
            with patch.object(m,'time',c),patch.object(g,'_setup_level',c.build),patch.object(m,'save_high_score'):
                self.assertTrue(g._play_level(), 'room %d' % (level+1))
            self.assertTrue(all(s.hidden for s in g._sparks))

    def test_flight_projectiles_are_pooled_and_ace_cannot_escape(self):
        m=load('flight');g=game(m,'flight');g._setup_sortie()
        g._wave=4;g._spawned=12;g._ace_spawned=True;g._spawn_enemy(True)
        ids=tuple(id(b[0]) for b in g._bullets)
        with patch.object(m.displayio,'Bitmap',side_effect=AssertionError('combat allocated bitmap')):
            for _ in range(500):
                g._hull=99
                g._step(.03,fire=True)
        self.assertEqual(tuple(id(b[0]) for b in g._bullets),ids)
        ace=g._enemies[6]
        if not g._ace_dead:
            self.assertFalse(ace[0].hidden)
            self.assertLess(ace[0].y,60)

    def test_both_loadouts_can_complete_all_sectors_and_ace(self):
        m=load('flight')
        for weapon in (0,1):
            m.random.seed(7)
            g=game(m,'flight');g._setup_sortie();g._weapon=weapon
            for frame in range(6000):
                enemies=[e for e in g._enemies if not e[0].hidden and e[2]<g._py]
                target=min(enemies,key=lambda e:abs(e[1]-g._px)) if enemies else None
                mx=0
                if target:
                    d=target[1]+target[3]*max(0,(g._py-target[2])/250)-g._px
                    mx=1 if d>3 else -1 if d<-3 else 0
                incoming=any(b[5] and not b[0].hidden and 0<g._py-b[2]<40 and abs(b[1]-g._px-10)<24 for b in g._bullets)
                if incoming:mx=-1 if g._px>100 else 1
                result=g._step(.03,mx,0,True,incoming)
                if result=='sector':
                    with patch.object(m,'choose',return_value=2):g._refit()
                elif result:
                    self.assertEqual(result,'won')
                    break
            else:self.fail('sortie did not finish')
            self.assertTrue(g._ace_dead)
            self.assertGreater(g._score,3000)

    def test_boost_is_limited_and_recovers(self):
        m=load('flight');g=game(m,'flight');g._setup_sortie()
        for _ in range(100):g._step(.05,boost=True)
        self.assertLess(g._fuel,.1)
        for _ in range(100):g._step(.05)
        self.assertGreater(g._fuel,2)

    def test_armor_trades_speed_for_survivability(self):
        m=load('flight');g=game(m,'flight');g._setup_sortie()
        start=g._px;g._step(.05,mx=1);light=g._px-start
        g._armored=True
        start=g._px;g._step(.05,mx=1);heavy=g._px-start
        self.assertLess(heavy,light)

    def test_multiple_hits_share_invulnerability_window(self):
        m=load('flight');g=game(m,'flight');g._setup_sortie()
        g._damage();g._damage();g._damage()
        self.assertEqual(g._hull,3)
        g._clock=2;g._damage()
        self.assertEqual(g._hull,2)

    def test_ace_must_be_destroyed_for_victory(self):
        m=load('flight');g=game(m,'flight');g._setup_sortie()
        g._wave=4;g._spawned=12
        self.assertIsNone(g._step(.03))
        self.assertTrue(g._ace_spawned)
        ace=g._enemies[6];ace[1]=80;ace[2]=53;ace[4]=1
        g._fire(92,80)
        self.assertEqual(g._step(.03),'won')
        self.assertEqual(g._score,1000)

    def test_whistles_respect_hay_and_fences(self):
        m=load('cows');g=game(m,'cows')
        rancher,cows,obstacles,quota=g._build_round(4)
        cow=cows[0];cow[0].x,cow[0].y=80,90
        rancher.x,rancher.y=130,90
        g._whistle_cow(cow,rancher,[(100,90)])
        self.assertLessEqual(cow[0].x,84)
        self.assertFalse(g._blocked(cow[0].x,cow[0].y,[(100,90)]))
        cow[0].x,cow[0].y=10,46;rancher.x,rancher.y=0,0
        g._whistle_cow(cow,rancher,[])
        self.assertGreaterEqual(cow[0].x,10);self.assertGreaterEqual(cow[0].y,42)

    def test_ranch_controller_can_deliver_a_full_round(self):
        m=load('cows');m.random.seed(11);g=game(m,'cows');build=g._build_round
        class Clock:
            now=0
            def monotonic(self):return self.now
            def sleep(self,dt):
                self.now+=dt
                rancher,cows=self.rancher,self.cows
                tethered=next((c for c in cows if c[3]),None)
                if tethered:tx,ty=40,190
                elif cows:tx,ty=cows[0][0].x,cows[0][0].y
                else:return
                g._L.value=g._R.value=g._U.value=g._D.value=True
                if abs(rancher.x-tx)>8:
                    if rancher.x<tx:g._R.value=False
                    else:g._L.value=False
                elif abs(rancher.y-ty)>8:
                    if rancher.y<ty:g._D.value=False
                    else:g._U.value=False
                g._A.value=not(tethered is None and abs(rancher.x-tx)<g._rope and abs(rancher.y-ty)<g._rope)
                if self.now>34:raise AssertionError('herding did not complete')
        clock=Clock()
        def setup(number):
            result=build(number);clock.rancher,clock.cows=result[:2]
            if number==2:g._exit=True
            return result
        with patch.object(m,'time',clock),patch.object(g,'_build_round',setup),patch.object(m,'save_high_score') as save:
            result=g.Game()
        self.assertTrue(result[0]);self.assertGreaterEqual(result[1],2)
        self.assertTrue(save.called)

    def test_pause_panel_is_reused_without_bitmap_allocations(self):
        import sys
        m=load('journey');g=game(m,'journey');menu=sys.modules['GameMenu']
        class Clock:
            now=0
            def monotonic(self):return self.now
            def sleep(self,dt):
                self.now+=dt
                g._A.value=self.now<.12
        with patch.object(menu,'time',Clock()):
            self.assertFalse(g._pause_menu.open('TEST',1))
        cache=g._pause_menu._cache
        g._A.value=True
        with patch.object(menu,'time',Clock()),patch.object(m.displayio,'Bitmap',side_effect=AssertionError('new menu bitmap')):
            self.assertFalse(g._pause_menu.open('TEST AGAIN',2))
        self.assertIs(g._pause_menu._cache,cache)
        self.assertEqual(len(g._splash),0)

    def test_ranch_rounds_have_reachable_unblocked_herds(self):
        m=load('cows');g=game(m,'cows')
        for round_number in range(1,16):
            rancher,cows,obstacles,quota=g._build_round(round_number)
            self.assertGreaterEqual(len(cows),quota)
            self.assertLessEqual(len(cows),7)
            for cow in cows:self.assertFalse(g._blocked(cow[0].x,cow[0].y,obstacles))
            self.assertTrue(any(cow[4]==2 for cow in cows) if len(cows)>=3 else True)


if __name__=='__main__':unittest.main()
