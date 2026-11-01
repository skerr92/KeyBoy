import io
import unittest
from unittest.mock import patch
from new_games_host import load,game
from drift_driver import drive

M=load('DriftCircuit')

class DriftTests(unittest.TestCase):
    def setUp(self):self.g=game(M)

    def test_every_car_can_finish_every_circuit_with_legal_inputs(self):
        for car in range(3):
            for track in range(3):
                self.g.car=car;self.g._setup(track)
                drive(self.g,M)
                self.assertTrue(self.g.finished,(car,track))
                self.assertEqual(self.g.laps,3)
                self.assertLessEqual(self.g.elapsed,M.TRACKS[track][3])

    def test_countdown_freezes_clock_and_cars(self):
        self.g._setup(0);g=self.g
        before=(g.x,g.y,g.rivals[0][0],g.fuel)
        for _ in range(30):g._step(.025,1,True,False,True)
        self.assertEqual(g.elapsed,0)
        self.assertEqual((g.x,g.y,g.rivals[0][0],g.fuel),before)

    def test_finish_line_cannot_skip_ordered_checkpoints(self):
        g=self.g;g._setup(0);g.countdown=0
        for _ in range(5):
            g.x,g.y=g.points[0];g._step(.025)
        self.assertEqual((g.laps,g.next_cp),(0,1))
        for cp in range(1,len(g.points)):
            g.x,g.y=g.points[cp];g._step(.025)
        self.assertEqual((g.laps,g.next_cp),(0,0))
        g.x,g.y=g.points[0];g._step(.025)
        self.assertEqual((g.laps,g.next_cp),(1,1))

    def test_offroad_limits_speed_and_cannot_boost(self):
        g=self.g;g._setup(0);g.countdown=0;g.x,g.y=120,125;g.speed=80;g.fuel=1
        g._step(.025,0,True,False,True)
        self.assertFalse(g.road);self.assertLessEqual(g.speed,27)
        self.assertGreater(g.fuel,1)

    def test_boost_consumes_finite_fuel_and_recharges(self):
        g=self.g;g._setup(0);g.countdown=0;before=g.fuel
        for _ in range(20):g._step(.025,0,True,False,True)
        self.assertLess(g.fuel,before)
        used=g.fuel
        for _ in range(20):g._step(.025)
        self.assertGreater(g.fuel,used);self.assertLessEqual(g.fuel,2.5)

    def test_recovery_preserves_progress_and_penalizes_all_clocks(self):
        g=self.g;g._setup(1);g.countdown=0;g.next_cp=4;g.laps=1;g.x,g.y=100,100
        g.elapsed=15;before=g.rivals[0][0]
        g._recover()
        self.assertEqual((g.x,g.y),g.points[3]);self.assertEqual(g.elapsed,17)
        self.assertEqual((g.laps,g.next_cp),(1,4));self.assertEqual(g.speed,0)
        self.assertEqual(g.rivals[0][0],before+g.rivals[0][1]*2)

    def test_racing_reuses_terrain_and_never_allocates_bitmaps(self):
        g=self.g;g._setup(2);terrain=tuple(g.canvas.strips)
        with patch.object(M.displayio,'Bitmap',side_effect=AssertionError('new bitmap')):
            drive(g,M)
        self.assertTrue(g.finished);self.assertEqual(tuple(g.canvas.strips),terrain)

    def test_retry_reuses_painted_track(self):
        g=self.g;g._setup(0)
        with patch.object(g,'_paint_track',side_effect=AssertionError('terrain repainted')):
            g._setup(0)
        self.assertEqual(g.elapsed,0);self.assertEqual(g.laps,0)

    def test_timeout_and_finished_states_stop_simulation(self):
        g=self.g;g._setup(0);g.countdown=0;g.elapsed=119.99
        g._step(.025);self.assertTrue(g.timed_out)
        clock=g.elapsed;g._step(.025,0,True);self.assertEqual(g.elapsed,clock)

    def test_best_time_never_regresses_and_roundtrips(self):
        g=self.g;g._setup(1);g.finished=True;g.elapsed=32
        with patch.object(g,'_save',return_value=False):
            g._record();g.elapsed=38;g._record()
        self.assertEqual(g.best,[0,32000,0]);self.assertIn('unavailable',g.save_note)
        g.car=2;g.cups=3;g.cup_best=13
        with patch.object(M,'save',return_value=True) as write:
            g._save();encoded=write.call_args.args[1]
        other=game(M)
        with patch('builtins.open',return_value=io.StringIO(encoded)):other._load()
        self.assertEqual((other.car,other.track,other.cups,other.cup_best,other.best),(2,1,3,13,[0,32000,0]))

    def test_malformed_save_is_transactional(self):
        for data in ('bad','DC1,2,0,1,99|0,0,0','DC1,2,1,3,12|0,-1,0','DC1,2,1,3,12|0,0'):
            g=game(M)
            with patch('builtins.open',return_value=io.StringIO(data)):g._load()
            self.assertEqual((g.car,g.track,g.cups,g.best),(0,0,0,[0,0,0]))

    def test_pause_excludes_menu_time_from_physics(self):
        g=self.g;g._setup(0);g.countdown=0
        class Clock:
            now=0;paused=False
            def monotonic(self):return self.now
            def sleep(self,dt):
                self.now+=dt
                if not self.paused:g.buttons[6].value=False
        clock=Clock();steps=[]
        def menu(*args):
            clock.now+=300;clock.paused=True;g.buttons[6].value=True
            return 0
        def step(dt,*args):
            steps.append(dt)
            if len(steps)==4:g.finished=True
        with patch.object(M,'time',clock),patch.object(g,'_setup'),patch.object(g.panel,'show',side_effect=menu),patch.object(g,'_step',side_effect=step),patch.object(g,'_record'):
            self.assertTrue(g._race(0))
        self.assertTrue(clock.paused)
        self.assertLess(max(steps),.05)

    def test_cup_retry_does_not_double_award_points(self):
        g=self.g;g.position=1
        choices=iter((1,0,0,0,0))
        with patch.object(g,'_race',return_value=True) as race,patch.object(g.panel,'show',side_effect=lambda *a:next(choices)),patch.object(g,'_save',return_value=False):
            g._championship()
        self.assertEqual([c.args[0] for c in race.call_args_list],[0,0,1,2])
        self.assertEqual((g.cups,g.cup_best),(1,15))

if __name__=='__main__':unittest.main()
