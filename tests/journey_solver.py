"""Legal controller policy: fight guardians, then visit each spark platform."""
class Clock:
    def __init__(self,g,m):self.m=m;self.now=0;self.g=g;self.stage=0;self.setup=g._setup_level;self.aimed=False
    def monotonic(self):return self.now
    def build(self):
        result=self.setup();self.p,self.platforms,self.boss=result[:3];return result
    def sleep(self,seconds):
        self.now+=seconds;g=self.g;p=self.p;m=self.m
        ground=any(p.y+m.PLAYER_H==y and p.x+m.PLAYER_W>x and p.x<x+w for x,y,w in self.platforms)
        if self.stage<len(g._sparks):
            spark=g._sparks[self.stage];x,y,w=self.platforms[self.stage+1]
            if spark.hidden and ground and p.y+m.PLAYER_H==y:self.stage+=1
        if self.boss is not None and self.boss in g._splash:
            g._L.value=True;g._R.value=not(p.x<80)
            danger=any(not t[0].hidden and abs(t[0].x-p.x)<65 for t in g._thorns)
            g._A.value=not(ground and danger and g._A.value)
        elif self.stage<len(g._sparks):
            x,y,w=self.platforms[self.stage+1];target=x+w//2-8
            g._L.value=not(p.x>target+2);g._R.value=not(p.x<target-2)
            g._A.value=not(ground and g._A.value)
        else:
            g._L.value=True;g._R.value=False;g._A.value=not(ground and g._A.value)
        g._B.value=False
        if self.now>60:raise Exception(('stuck',g._level,self.stage,p.x,p.y,g._room_hp))
