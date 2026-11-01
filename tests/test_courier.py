import io
import unittest
from unittest.mock import patch
from new_games_host import load,game
from courier_solutions import SOLUTIONS

M=load('ClockworkCourier')
DIR={'L':(-1,0),'R':(1,0),'U':(0,-1),'D':(0,1)}


class CourierTests(unittest.TestCase):
    def setUp(self):self.g=game(M)

    def test_all_twelve_rooms_complete_and_earn_gold(self):
        with patch.object(self.g,'_save',return_value=False):
            for i,solution in enumerate(SOLUTIONS):
                self.g._start(i)
                for action in solution:self.assertTrue(self.g._move(*DIR[action]),(i,action))
                self.assertTrue(self.g.won,i)
                self.assertEqual(self.g.boxes,self.g.goals)
                self.assertEqual(self.g.medal(i),3)
                self.assertEqual(self.g.unlocked(),min(11,i+1))
        self.assertEqual(sum(self.g.medal(i) for i in range(12)),36)

    def test_undo_restores_entire_room_and_counters(self):
        self.g._start(6)
        original=(self.g.player,set(self.g.boxes))
        for action in SOLUTIONS[6][:-1]:self.g._move(*DIR[action])
        for _ in SOLUTIONS[6][:-1]:self.assertTrue(self.g._undo())
        self.assertEqual((self.g.player,self.g.boxes),original)
        self.assertEqual((self.g.moves,self.g.pushes),(0,0))
        self.assertFalse(self.g._undo())

    def test_blocked_moves_do_not_consume_history(self):
        self.g._start(0);self.g.player=10
        self.assertFalse(self.g._move(-1,0));self.assertFalse(self.g._move(0,-1))
        self.assertFalse(self.g._move(1,1))
        self.assertEqual(self.g.moves,0);self.assertEqual(self.g.history_count,0)

    def test_undo_ring_is_bounded(self):
        self.g._start(0);self.g.player=10;history=self.g.history
        for _ in range(150):
            self.g._move(1,0);self.g._move(-1,0)
        self.assertEqual(self.g.history_count,128)
        self.assertIs(self.g.history,history)
        for _ in range(128):self.g._undo()
        self.assertEqual(self.g.moves,172)
        self.assertFalse(self.g._undo())

    def test_movement_and_undo_never_allocate_bitmaps(self):
        self.g._start(7);terrain=tuple(self.g.canvas.strips)
        with patch.object(M.displayio,'Bitmap',side_effect=AssertionError('new bitmap')),patch.object(self.g,'_save',return_value=False):
            for action in SOLUTIONS[7]:self.g._move(*DIR[action])
            for _ in SOLUTIONS[7]:self.g._undo()
        self.assertEqual(tuple(self.g.canvas.strips),terrain)

    def test_best_record_does_not_regress(self):
        self.g._start(0);self.g.best[0]=(11,5)
        self.g._move(-1,0);self.g._undo()
        with patch.object(self.g,'_save',return_value=True):
            for action in SOLUTIONS[0]:self.g._move(*DIR[action])
        self.assertEqual(self.g.best[0],(11,5))

    def test_save_roundtrip_and_malformed_data_rejection(self):
        self.g.best[:2]=[(11,5),(14,6)];self.g.selected=2
        with patch.object(M,'save',return_value=True) as write:
            self.assertTrue(self.g._save());encoded=write.call_args.args[1]
        g=game(M)
        with patch('builtins.open',return_value=io.StringIO(encoded)):g._load()
        self.assertEqual(g.best,self.g.best);self.assertEqual(g.selected,2)
        for data in ('bad','CC1,0|0,1','CC1,0|'+';'.join(['0,0','10,4']+['0,0']*10)):
            clean=game(M)
            with patch('builtins.open',return_value=io.StringIO(data)):clean._load()
            self.assertEqual(clean.best,[(0,0)]*12)

if __name__=='__main__':unittest.main()
