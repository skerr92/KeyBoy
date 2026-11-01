"""Legal controller inputs, with no position/checkpoint edits during a race."""
import math

def drive(game,module,limit=5000):
    for frame in range(limit):
        tx,ty=game.points[game.next_cp]
        error=module._angle(math.atan2(ty-game.y,tx-game.x)-game.heading)
        steer=1 if error>.055 else -1 if error<-.055 else 0
        game._step(.025,steer,abs(error)<.8,abs(error)>.45,
                   abs(error)<.12 and (tx-game.x)**2+(ty-game.y)**2>45**2)
        if game.finished or game.timed_out:return frame
    raise AssertionError('Race did not finish')
