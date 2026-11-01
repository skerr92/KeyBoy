# SPDX-License-Identifier: MIT
"""Drift Circuit: three coastal/canyon/night races, car handling and a cup."""
import math
import time
import displayio
from KeyBoyScenes import INK, Canvas, Panel, palette, rect, oval, text, set_text, save

TAU=math.pi*2
TRACKS=(
    ('Palm Coast',((120,53),(181,53),(207,80),(207,173),(179,204),(60,204),(31,175),(31,82),(59,53)),15,26),
    ('Copper Canyon',((120,53),(192,53),(207,92),(160,117),(207,164),(182,206),(121,195),(72,207),(32,174),(77,139),(32,98),(54,53)),14,40),
    ('Neon Harbor',((112,51),(182,51),(207,78),(192,108),(137,107),(137,147),(205,158),(203,197),(78,206),(32,174),(32,89),(60,51)),14,35),
)
# name, top speed, acceleration, steering radians/sec, grip
CARS=(('Comet',82,76,3.8,8),('Needle',75,88,4.5,11),('Bulwark',90,62,3.3,6))


def _angle(value):return (value+math.pi)%TAU-math.pi


class CarArt:
    def __init__(self):
        self.banks=[displayio.Bitmap(80,24,16) for _ in range(4)]
        for frame in range(16):
            angle=frame*TAU/16;c,s=math.cos(angle),math.sin(angle)
            bitmap=self.banks[frame//4];offset=(frame%4)*20
            for y in range(24):
                for x in range(20):
                    dx,dy=x-9.5,y-11.5
                    u,v=dx*c+dy*s,-dx*s+dy*c
                    color=0
                    if abs(v)<5.5 and 3<abs(u)<7:color=1
                    if abs(v)<4.1 and -9<u<8:
                        color=7
                        if abs(v)>3:color=8
                        if 1<u<5 and abs(v)<3:color=4
                        if -3<u<1 and abs(v)<1.2:color=5
                        if u>6:color=5
                    if -9<u<-7 and abs(v)<5:color=5
                    bitmap[offset+x,y]=color

    def grid(self,color=7):
        p=palette(transparent=True)
        p[7]=INK[color]
        return displayio.TileGrid(self.banks[0],pixel_shader=p,tile_width=20,tile_height=24)

    def show(self,grid,x,y,angle):
        frame=int((angle%TAU)*16/TAU+.5)%16
        if grid.bitmap is not self.banks[frame//4]:grid.bitmap=self.banks[frame//4]
        if grid[0]!=frame%4:grid[0]=frame%4
        grid.x,grid.y=int(x)-10,int(y)-12


class DriftCircuit:
    def __init__(self,splash,A,B,U,D,L,R,SEL,audio):
        self.root,self.buttons,self.audio=splash,(A,B,U,D,L,R,SEL),audio
        self.car=self.track=self.cups=self.cup_best=0
        self.best=[0,0,0];self.exit=False;self.save_note=''
        self._load()
        self.canvas=Canvas();self.panel=Panel(splash,self.buttons,audio)
        self.art=CarArt()

    def _load(self):
        try:
            with open('/drift_circuit.sav','rt') as f:data=f.read(160).strip()
            head,tail=data.split('|');fields=head.split(',')
            if fields[0]!='DC1' or len(fields)!=5:return
            car,track,cups,best=tuple(int(v) for v in fields[1:])
            times=[int(v) for v in tail.split(',')]
            if not (0<=car<3 and 0<=track<3 and 0<=cups<=9999 and 0<=best<=15):return
            if len(times)!=3 or any(v<0 or v>122000 for v in times):return
            self.car,self.track,self.cups,self.cup_best=car,track,cups,best;self.best=times
        except (OSError,ValueError):pass

    def _save(self):
        return save('/drift_circuit.sav','DC1,%d,%d,%d,%d|'%(self.car,self.track,self.cups,self.cup_best)+','.join(str(v) for v in self.best))

    def _clear(self):
        while len(self.root):self.root.pop()

    def _setup(self,track):
        self.track=track
        self.points=TRACKS[track][1];self.width=TRACKS[track][2]
        self.segments=[];self.cumulative=[0.0]
        for i,start in enumerate(self.points):
            end=self.points[(i+1)%len(self.points)]
            dx,dy=end[0]-start[0],end[1]-start[1]
            length=math.sqrt(dx*dx+dy*dy)
            self.segments.append((start[0],start[1],dx,dy,length))
            self.cumulative.append(self.cumulative[-1]+length)
        self.length=self.cumulative[-1]
        self.x,self.y=float(self.points[0][0]),float(self.points[0][1])
        self.heading=math.atan2(self.segments[0][3],self.segments[0][2])
        self.speed=self.vx=self.vy=0.0
        self.elapsed=0.0;self.countdown=2.4;self.fuel=2.5
        self.laps=0;self.next_cp=1;self.finished=False;self.timed_out=False
        self.rivals=[[-18.0,55+track*1.5],[-36.0,51+track*1.5]]
        self.position=1;self.road=True;self.note_until=0;self.notice=''
        self.skid_slot=0;self.skid_time=0;self.fuel_draw=-1
        self._build()

    def _road_distance2(self,x,y):
        nearest=100000.0
        for sx,sy,dx,dy,length in self.segments:
            t=max(0.0,min(1.0,((x-sx)*dx+(y-sy)*dy)/(length*length)))
            ex,ey=x-(sx+t*dx),y-(sy+t*dy)
            nearest=min(nearest,ex*ex+ey*ey)
        return nearest

    def _racing_line(self,distance):
        distance%=self.length
        for i,seg in enumerate(self.segments):
            if distance<=self.cumulative[i+1]:
                x,y,dx,dy,length=seg;t=(distance-self.cumulative[i])/length
                return x+dx*t,y+dy*t,math.atan2(dy,dx)
        return float(self.points[0][0]),float(self.points[0][1]),0.0

    def _stamp_road(self,radius,color):
        # Rasterize each road capsule once per scanline. Stamping overlapping
        # circles along the centreline repainted each pixel many times on-device.
        for sx,sy,dx,dy,length in self.segments:
            ex,ey=sx+dx,sy+dy
            nx,ny=-dy*radius/length,dx*radius/length
            corners=((sx+nx,sy+ny),(ex+nx,ey+ny),(ex-nx,ey-ny),(sx-nx,sy-ny))
            for y in range(max(0,min(sy,ey)-radius),min(240,max(sy,ey)+radius+1)):
                low=240;high=-1
                for cx,cy in ((sx,sy),(ex,ey)):
                    offset=y-cy
                    if abs(offset)<=radius:
                        span=math.sqrt(radius*radius-offset*offset)
                        low=min(low,cx-span);high=max(high,cx+span)
                for i in range(4):
                    ax,ay=corners[i];bx,by=corners[(i+1)%4]
                    if ay!=by and min(ay,by)<=y<=max(ay,by):
                        x=ax+(bx-ax)*(y-ay)/(by-ay)
                        low=min(low,x);high=max(high,x)
                if high>=low:
                    left=int(math.ceil(low));right=int(math.floor(high))
                    rect(self.canvas,left,y,right-left+1,1,color)

    def _paint_track(self):
        b=self.canvas
        b.fill(12 if self.track==0 else 8 if self.track==1 else 0)
        # Static palms, sandstone or harbour lamps are outside the racing surface.
        for i in range(210):
            x,y=(i*83+13)%240,37+(i*47)%183
            rect(b,x,y,3,1,13 if self.track==0 else 7 if self.track==1 else 2)
        if self.track==0:
            oval(b,68,95,103,75,2);oval(b,73,99,93,67,3)
            for i in range(9):rect(b,84+(i*19)%65,109+(i*13)%40,13,1,4)
            for x,y in ((8,70),(219,185),(97,117)):
                rect(b,x,y,3,17,8);oval(b,x-8,y-5,21,10,13);oval(b,x-2,y-10,10,21,14)
        elif self.track==1:
            for x,y in ((91,83),(98,150),(10,122),(218,61)):
                oval(b,x-11,y-9,23,21,9);oval(b,x-9,y-10,20,13,7);rect(b,x-5,y-9,10,3,6)
        else:
            for x,y in ((75,84),(66,129),(165,177),(214,118)):
                rect(b,x,y,19,28,1);rect(b,x+2,y+3,15,2,10)
                for yy in range(y+7,y+24,6):rect(b,x+3,yy,3,2,4);rect(b,x+12,yy,3,2,6)
        self._stamp_road(self.width+3,5 if self.track!=2 else 10)
        self._stamp_road(self.width,1)
        # Dashed centre line and start gantry make the course readable.
        for distance in range(0,int(self.length),18):
            x,y,angle=self._racing_line(distance)
            rect(b,int(x)-1,int(y)-1,3,3,3)
        sx,sy=self.points[0]
        for y in range(sy-self.width,sy+self.width,4):
            for x in range(sx-3,sx+5,4):rect(b,x,y,4,4,5 if ((y//4)+(x//4))%2 else 2)
        rect(b,0,0,240,34,0);rect(b,0,33,240,1,3)
        rect(b,0,222,240,18,0)
        self.drawn_track=self.track

    def _build(self):
        self._clear()
        if getattr(self,'drawn_track',-1)!=self.track:self._paint_track()
        self.canvas.attach(self.root)
        self.skids=[]
        skid=displayio.Bitmap(2,2,2);skid.fill(1);p=palette((0,0x080F19));p.make_transparent(0)
        for _ in range(10):
            grid=displayio.TileGrid(skid,pixel_shader=p);grid.hidden=True
            self.root.append(grid);self.skids.append(grid)
        self.other_cars=[]
        for color in (4,10):
            grid=self.art.grid(color);self.root.append(grid);self.other_cars.append(grid)
        self.player=self.art.grid(7);self.root.append(self.player)
        flag=displayio.Bitmap(9,14,16)
        rect(flag,1,0,1,14,5);rect(flag,2,0,7,6,6);rect(flag,4,1,2,4,7)
        self.checkpoint=displayio.TileGrid(flag,pixel_shader=palette(transparent=True));self.root.append(self.checkpoint)
        self.hud=text(self.root,'',6,10,5)
        self.stats=text(self.root,'',6,24,4)
        self.hint=text(self.root,'',5,232,6)
        self.meter=displayio.Bitmap(34,3,2)
        self.root.append(displayio.TileGrid(self.meter,pixel_shader=palette((0x20364E,0xF2BD68)),x=198,y=26))
        self._sync()

    def _progress(self):
        previous=(self.next_cp-1)%len(self.points)
        sx,sy,dx,dy,length=self.segments[previous]
        t=max(0,min(1,((self.x-sx)*dx+(self.y-sy)*dy)/(length*length)))
        return self.laps*self.length+self.cumulative[previous]+t*length

    def _sync(self):
        self.art.show(self.player,self.x,self.y,self.heading)
        for rival,grid in zip(self.rivals,self.other_cars):self.art.show(grid,*self._racing_line(rival[0]))
        self.checkpoint.x,self.checkpoint.y=self.points[self.next_cp][0]-4,self.points[self.next_cp][1]-18
        self.checkpoint.hidden=self.finished
        self.position=1+sum(1 for rival in self.rivals if rival[0]>self._progress())
        set_text(self.hud,TRACKS[self.track][0].upper()+'  %.1fs'%self.elapsed)
        set_text(self.stats,'LAP %d/3  P%d  %s'%(min(3,self.laps+1),self.position,CARS[self.car][0].upper()))
        fuel=int(self.fuel*34/2.5)
        if fuel!=self.fuel_draw:
            self.meter.fill(0);rect(self.meter,0,0,fuel,3,1);self.fuel_draw=fuel
        hint='READY %d'%int(self.countdown+1) if self.countdown>0 else 'FINISH!' if self.finished else self.notice if self.elapsed<self.note_until else 'A gas B brake UP boost DN recover'
        set_text(self.hint,hint)

    def _recover(self):
        if self.finished or self.countdown>0:return
        previous=(self.next_cp-1)%len(self.points)
        self.x,self.y=self.points[previous]
        self.heading=math.atan2(self.segments[previous][3],self.segments[previous][2])
        self.speed=self.vx=self.vy=0.0
        self.elapsed+=2;self.note_until=self.elapsed+1;self.notice='RECOVERED +2s'
        for rival in self.rivals:rival[0]+=rival[1]*2
        self.audio.play('hit');self._sync()

    def _step(self,dt,steer=0,gas=False,brake=False,boost=False):
        if self.finished or self.timed_out:return
        dt=max(0,min(.05,dt))
        if self.countdown>0:
            self.countdown=max(0,self.countdown-dt);self._sync();return
        self.elapsed+=dt
        _,top,accel,turn,grip=CARS[self.car]
        self.road=self._road_distance2(self.x,self.y)<=self.width*self.width
        turbo=boost and gas and self.fuel>=dt and self.road
        self.fuel=max(0,self.fuel-dt) if turbo else min(2.5,self.fuel+dt*(.65 if brake and steer and self.speed>25 and self.road else .3))
        maximum=top+(30 if turbo else 0) if self.road else 27
        if gas:self.speed=min(maximum,self.speed+accel*dt)
        else:self.speed=max(0,self.speed-18*dt)
        if brake:self.speed=max(0,self.speed-70*dt)
        if self.speed>maximum:self.speed=max(maximum,self.speed-100*dt)
        self.heading=_angle(self.heading+steer*turn*(1.2 if brake else 1)*dt)
        traction=(grip*.55 if brake and steer else grip) if self.road else 10
        blend=min(1,traction*dt)
        self.vx+=(math.cos(self.heading)*self.speed-self.vx)*blend
        self.vy+=(math.sin(self.heading)*self.speed-self.vy)*blend
        self.x=max(8,min(232,self.x+self.vx*dt));self.y=max(39,min(216,self.y+self.vy*dt))
        for rival in self.rivals:rival[0]+=rival[1]*dt
        tx,ty=self.points[self.next_cp]
        if (self.x-tx)**2+(self.y-ty)**2<=12*12 and self._road_distance2(self.x,self.y)<=self.width*self.width:
            if self.next_cp==0:
                self.laps+=1;self.audio.play('collect')
                if self.laps>=3:self.finished=True;self.audio.play('win')
            self.next_cp=(self.next_cp+1)%len(self.points)
        if brake and self.speed>25 and self.road and self.elapsed-self.skid_time>.12:
            grid=self.skids[self.skid_slot];grid.x,grid.y=int(self.x),int(self.y);grid.hidden=False
            self.skid_slot=(self.skid_slot+1)%len(self.skids);self.skid_time=self.elapsed
        self.timed_out=self.elapsed>=120 and not self.finished
        self._sync()

    def _controls(self):
        self.panel.show('DRIVING SCHOOL',('A accelerates','Left / Right steers','B brakes into tight turns','Up spends rechargeable boost','Down recovers for +2 seconds'),
            ('Chase the next yellow checkpoint','Steering works even when stopped','Braking while turning refills boost','Off-road driving slows your car','SEL pauses all race clocks'))

    def _record(self):
        if not self.finished:return
        ms=int(self.elapsed*1000)
        if self.best[self.track]==0 or ms<self.best[self.track]:self.best[self.track]=ms
        self.save_note='Record saved' if self._save() else 'Save unavailable: USB/read-only'

    def _race(self,track):
        self._setup(track)
        a,b,u,d,l,r,sel=self.buttons
        down_held,sel_held=not d.value,not sel.value
        last=time.monotonic()
        while not self.exit and not self.finished and not self.timed_out:
            now=time.monotonic();dt=now-last;last=now
            if not u.value and not d.value:self.exit=True;return None
            if not sel.value and not sel_held:
                choice=self.panel.show('PIT STOP',('Resume','Restart race','Driving school','Save records','Return to garage'),
                    ('Race time is paused','Begin this circuit again','Controls and recovery','Keep best times and cup record','Abandon this race'))
                if choice==1:self._setup(track)
                elif choice==2:self._controls()
                elif choice==3:
                    self.save_note='Records saved' if self._save() else 'Save unavailable: USB/read-only'
                    self.notice=self.save_note;self.note_until=self.elapsed+2
                elif choice in (4,-2):
                    if choice==-2:self.exit=True
                    return None
                last=time.monotonic();down_held,sel_held=not d.value,not sel.value
                continue
            if not d.value and not down_held:self._recover()
            self._step(dt,int(not r.value)-int(not l.value),not a.value,not b.value,not u.value)
            down_held,sel_held=not d.value,not sel.value
            time.sleep(max(.001,.025-(time.monotonic()-now)))
        if self.finished:self._record();return True
        return False

    def _championship(self):
        track=0;points=0
        while track<3 and not self.exit:
            result=self._race(track)
            if result is None:return
            if not result:
                choice=self.panel.show('TIME LIMIT',('Retry circuit','Return to garage'),('Down recovers a stranded car','No cup progress lost on retry'))
                if choice==0:continue
                if choice==-2:self.exit=True
                return
            earned=(5,3,1)[self.position-1]
            choice=self.panel.show('FINISH P%d / +%d POINTS'%(self.position,earned),('Next circuit' if track<2 else 'Claim cup','Retry circuit','Return to garage'),
                (self.save_note,'Try for a better finishing place','Best times are retained'))
            if choice==1:continue
            if choice!=0:
                if choice==-2:self.exit=True
                return
            points+=earned;track+=1
        if track==3:
            self.cups=min(9999,self.cups+1);self.cup_best=max(self.cup_best,points)
            saved=self._save()
            medal='GOLD' if points>=13 else 'SILVER' if points>=9 else 'BRONZE'
            self.panel.show(medal+' CUP / %d POINTS'%points,('Back to garage',),('Cup saved' if saved else 'Save unavailable: USB/read-only',))

    def Game(self):
        self._setup(self.track)
        while not self.exit:
            choice=self.panel.show('DRIFT CIRCUIT',('Three-race championship','Time trial','Garage / choose car','Driving school','Leave game'),
                ('Best cup: %d/15 points'%self.cup_best,'Replay any circuit for a record',CARS[self.car][0]+' is ready','Learn steering, boost and recovery','Return to KeyBoy'))
            if choice==0:self._championship()
            elif choice==1:
                details=tuple('Best %.2fs / Gold %ds'%(self.best[i]/1000,TRACKS[i][3]) if self.best[i] else 'No record / Gold %ds'%TRACKS[i][3] for i in range(3))
                index=self.panel.show('TIME TRIAL',tuple(t[0] for t in TRACKS),details,self.track)
                if index==-2:self.exit=True
                elif index>=0:
                    result=self._race(index)
                    if result is not None:
                        medal='GOLD' if self.elapsed<=TRACKS[index][3] else 'SILVER' if self.elapsed<=TRACKS[index][3]*1.3 else 'BRONZE'
                        self.panel.show((medal+' / %.2fs'%self.elapsed) if result else 'TIME LIMIT',('Back to garage',),(self.save_note if result else 'Down recovers a stranded car',))
            elif choice==2:
                index=self.panel.show('CHOOSE YOUR CAR',tuple(c[0] for c in CARS),('Balanced speed and road grip','Sharp handling, lower top speed','Fast straights, earlier braking'),self.car)
                if index==-2:self.exit=True
                elif index>=0:self.car=index
            elif choice==3:self._controls()
            elif choice in (4,-2,-1):self.exit=True
        self._clear();return True
