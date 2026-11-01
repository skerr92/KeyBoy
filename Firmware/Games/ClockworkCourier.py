# SPDX-License-Identifier: MIT
"""Clockwork Courier: twelve brass-and-steam delivery puzzles with undo."""
import time
import displayio
from KeyBoyScenes import Canvas, Panel, palette, rect, oval, text, set_text, save

ROOMS=('Copper Entry','Valve Hall','Split Shift','Double Back','Twin Boilers','Intake',
       'Pipeworks','Press Room','Switchyard','Liftworks','Moon Engine','Last Delivery')
LEVELS = (
    ('#########', '#       #', '#     @ #', '# $     #', '#     . #', '#       #', '#       #', '#########'),
    ('#########', '#  @    #', '# .   $ #', '#   #   #', '#       #', '#   $ . #', '#       #', '#########'),
    ('#########', '#       #', '#   # . #', '#   @   #', '# $     #', '# . # $ #', '#       #', '#########'),
    ('#########', '#       #', '# .   $ #', '#  #    #', '#    #@ #', '#    $. #', '#       #', '#########'),
    ('#########', '#       #', '# $#  . #', '#  #    #', '#       #', '# .  #$ #', '#  @    #', '#########'),
    ('#########', '#       #', '# +$ #$ #', '#       #', '#  #    #', '#    #. #', '#       #', '#########'),
    ('#########', '#       #', '# $$# . #', '#   #   #', '#   $@. #', '# . #   #', '#       #', '#########'),
    ('#########', '#       #', '# .   . #', '# $##   #', '#    $  #', '# $  #. #', '#@      #', '#########'),
    ('#########', '#      @#', '# .# #$ #', '#       #', '# $$# . #', '# .     #', '#       #', '#########'),
    ('#########', '#       #', '#  $ $. #', '# $# #  #', '# .    @#', '#  #  . #', '#       #', '#########'),
    ('#########', '#       #', '#  .# . #', '# $  @  #', '# #  #$ #', '# .$    #', '#       #', '#########'),
    ('#########', '# @     #', '#  #  . #', '#   $#$ #', '#     . #', '# .# $# #', '#       #', '#########'),
)
PAR = (5, 6, 4, 5, 6, 4, 12, 10, 6, 8, 9, 7)


def _robot():
    b=displayio.Bitmap(40,22,16)
    for frame in range(2):
        x=frame*20
        oval(b,x+1,18,18,4,1)
        rect(b,x+5,2,10,8,6);rect(b,x+4,4,12,4,7)
        rect(b,x+6,4,8,3,1);rect(b,x+7,4,2,2,4);rect(b,x+12,4,2,2,4)
        rect(b,x+9,0,2,3,4);rect(b,x+5,11,10,8,3)
        rect(b,x+7,12,6,3,6);rect(b,x+2,11,3,7,7);rect(b,x+15,11,3,7,7)
        rect(b,x+5,18-frame,4,4,7);rect(b,x+11,17+frame,4,4,7)
    return b


def _cell():
    b=displayio.Bitmap(44,22,16)
    for frame in range(2):
        x=frame*22
        rect(b,x+1,2,20,20,8);rect(b,x+2,2,18,17,7)
        rect(b,x+3,3,16,2,5);rect(b,x+3,16,16,2,8)
        rect(b,x+7,5,8,11,1);rect(b,x+8,6,6,9,4 if frame else 6)
        rect(b,x+10,7,2,7,5)
        for dx,dy in ((3,5),(17,5),(3,14),(17,14)):rect(b,x+dx,dy,2,2,5)
    return b


def _dock():
    b=displayio.Bitmap(44,22,16)
    for frame in range(2):
        x=frame*22
        oval(b,x+1,1,20,20,2);oval(b,x+3,3,16,16,4 if frame else 6)
        oval(b,x+5,5,12,12,1)
        rect(b,x+9,5,4,12,4 if frame else 7);rect(b,x+5,9,12,4,4 if frame else 7)
    return b


class ClockworkCourier:
    def __init__(self,splash,A,B,U,D,L,R,SEL,audio):
        self.root,self.buttons,self.audio=splash,(A,B,U,D,L,R,SEL),audio
        self.selected=0;self.best=[(0,0)]*12;self.exit=False
        self._load()
        self.canvas=Canvas();self.panel=Panel(splash,self.buttons,audio)
        self.robot_art,self.cell_art,self.dock_art=_robot(),_cell(),_dock()
        self.shader=palette(transparent=True)
        self.history=bytearray(128*3)
        self.save_note=''

    def _load(self):
        try:
            with open('/clockwork.sav','rt') as f:data=f.read(512).strip()
            head,records=data.split('|')
            version,index=head.split(',');index=int(index)
            best=[tuple(int(x) for x in record.split(',')) for record in records.split(';')]
            if version!='CC1' or not 0<=index<12 or len(best)!=12:return
            gap=False
            for record in best:
                if len(record)!=2:return
                moves,pushes=record
                if not (0<=pushes<=moves<=99999) or (moves==0)!=(pushes==0):return
                if moves==0:gap=True
                elif gap:return
            self.best=best
            self.selected=min(index,self.unlocked())
        except (OSError,ValueError):pass

    def _save(self):
        return save('/clockwork.sav','CC1,%d|'%self.selected+';'.join('%d,%d'%record for record in self.best))

    def unlocked(self):
        for i,record in enumerate(self.best):
            if record[0]==0:return i
        return 11

    def medal(self,index):
        moves,pushes=self.best[index]
        return 0 if moves==0 else 3 if pushes<=PAR[index] else 2 if pushes<=PAR[index]+3 else 1

    def _clear(self):
        while len(self.root):self.root.pop()

    def _start(self,index):
        self.selected=index
        self.floor=set();self.goals=set();self.boxes=set()
        for y,row in enumerate(LEVELS[index]):
            for x,char in enumerate(row):
                p=y*9+x
                if char!='#':self.floor.add(p)
                if char in '.+':self.goals.add(p)
                if char=='$':self.boxes.add(p)
                if char in '@+':self.player=p
        self.moves=self.pushes=self.history_head=self.history_count=0
        self.won=False;self.warning='';self.anim_frame=-1
        self._build()

    def _build(self):
        self._clear();b=self.canvas;b.fill(0)
        # Copper pipework and riveted room walls, drawn only between puzzles.
        for x in (7,231):
            rect(b,x,42,3,181,8);rect(b,x,42,1,181,6)
            for y in range(51,220,21):rect(b,x-1,y,5,3,7)
        for y,row in enumerate(LEVELS[self.selected]):
            for x,char in enumerate(row):
                px,py=16+x*23,39+y*23
                if char=='#':
                    rect(b,px,py,23,23,2);rect(b,px,py,23,3,3)
                    rect(b,px+1,py+3,20,17,1);rect(b,px+3,py+5,16,12,2)
                    rect(b,px+2,py+3,2,2,6);rect(b,px+18,py+17,2,2,6)
                else:
                    rect(b,px,py,23,23,8 if (x+y)%2 else 9)
                    rect(b,px+1,py+1,21,20,9 if (x+y)%2 else 8)
                    rect(b,px+3,py+19,17,1,7)
                    rect(b,px+4,py+3,2,1,7)
        # Four workshop districts tint walls, without rebuilding objects in play.
        colors=((0x38586A,0x67899A),(0x655343,0xAB815D),(0x405B5D,0x78AAA1),(0x524767,0xAA90BF))[self.selected//3]
        self.canvas.shader[2],self.canvas.shader[3]=colors
        self.canvas.attach(self.root)
        self.docks=[]
        for p in sorted(self.goals):
            grid=displayio.TileGrid(self.dock_art,pixel_shader=self.shader,tile_width=22,tile_height=22)
            grid.x,grid.y=17+(p%9)*23,40+(p//9)*23
            self.root.append(grid);self.docks.append((p,grid))
        self.crates=[]
        for _ in range(len(self.boxes)):
            grid=displayio.TileGrid(self.cell_art,pixel_shader=self.shader,tile_width=22,tile_height=22)
            self.root.append(grid);self.crates.append(grid)
        self.robot=displayio.TileGrid(self.robot_art,pixel_shader=self.shader,tile_width=20,tile_height=22)
        self.root.append(self.robot)
        self.heading=text(self.root,'CLOCKWORK COURIER',7,10,6)
        self.hud=text(self.root,'',7,25,4)
        self.hint=text(self.root,'',7,234,5)
        self._sync()

    def _sync(self):
        for p,grid in self.docks:grid[0]=int(p in self.boxes)
        for p,grid in zip(sorted(self.boxes),self.crates):
            grid.x,grid.y=17+(p%9)*23,40+(p//9)*23
            grid[0]=int(p in self.goals)
        self.robot.x,self.robot.y=18+(self.player%9)*23,40+(self.player//9)*23
        self.robot[0]=self.moves%2
        set_text(self.hud,'%02d/12  MOVE %d  PUSH %d/%d'%(self.selected+1,self.moves,self.pushes,PAR[self.selected]))
        set_text(self.hint,self.warning or 'D-pad push  B undo  A workshop')

    def _move(self,dx,dy):
        if self.won or abs(dx)+abs(dy)!=1:return False
        target=self.player+dx+dy*9
        if target not in self.floor or abs(target%9-self.player%9)+abs(target//9-self.player//9)!=1:return False
        destination=target+dx+dy*9
        push=target in self.boxes
        if push and (destination not in self.floor or destination in self.boxes):return False
        slot=self.history_head*3
        self.history[slot]=self.player
        self.history[slot+1]=target if push else 255
        self.history[slot+2]=destination if push else 255
        self.history_head=(self.history_head+1)%128;self.history_count=min(128,self.history_count+1)
        if push:
            self.boxes.remove(target);self.boxes.add(destination);self.pushes+=1
            self.audio.play('collect' if destination in self.goals else 'move')
        self.player=target;self.moves+=1;self.warning=''
        if push and destination not in self.goals:
            walls=lambda offset:destination+offset not in self.floor
            if (walls(1) or walls(-1)) and (walls(9) or walls(-9)):
                self.warning='Cell cornered. B undo / A restart'
        self.won=self.boxes==self.goals
        if self.won:
            old=self.best[self.selected]
            if old[0]==0 or (self.pushes,self.moves)<(old[1],old[0]):self.best[self.selected]=(self.moves,self.pushes)
            self.save_note='Saved progress' if self._save() else 'Save unavailable: USB/read-only'
            self.audio.play('win')
        self._sync();return True

    def _undo(self):
        if not self.history_count:return False
        self.history_head=(self.history_head-1)%128;self.history_count-=1
        slot=self.history_head*3;self.player=self.history[slot]
        origin,destination=self.history[slot+1],self.history[slot+2]
        if origin!=255:self.boxes.remove(destination);self.boxes.add(origin);self.pushes-=1
        self.moves-=1;self.won=False;self.warning='';self._sync()
        self.audio.play('select');return True

    def _pause(self):
        choice=self.panel.show('WORKSHOP',('Resume','Restart room','Room selection','Save progress','Leave game'),
                               ('Keep delivering','Undo is also available with B','Replay rooms for gold medals','Save completed rooms','Return to KeyBoy'))
        if choice==1:self._start(self.selected)
        elif choice==2:return 'hub'
        elif choice==3:
            self.warning='Progress saved' if self._save() else 'Save unavailable: USB/read-only';self._sync()
        elif choice in (4,-2):self.exit=True
        return None

    def _play(self):
        a,b,u,d,l,r,sel=self.buttons
        held_a,held_s=not a.value,not sel.value
        direction=None;repeat=0;undo_held=not b.value
        while not self.exit:
            now=time.monotonic()
            if not u.value and not d.value:self.exit=True;break
            if self.won:
                stars=self.medal(self.selected)
                options=('Next delivery','Replay for gold','Workshop') if self.selected<11 else ('Workshop','Replay for gold','Leave game')
                choice=self.panel.show('DELIVERED! %d/3 MEDALS'%stars,options,(self.save_note,)*3)
                if choice==-2:self.exit=True;break
                if self.selected==11:
                    if choice==1:self._start(self.selected)
                    elif choice==2:self.exit=True
                    else:return
                elif choice==0:self._start(self.selected+1)
                elif choice==1:self._start(self.selected)
                else:return
                held_a,held_s,undo_held=not a.value,not sel.value,not b.value;direction=None
                continue
            if (not a.value and not held_a) or (not sel.value and not held_s):
                if self._pause()=='hub':return
                held_a,held_s,undo_held=not a.value,not sel.value,not b.value
                direction=None;repeat=time.monotonic()+.15
                continue
            step=(0,-1) if not u.value else (0,1) if not d.value else (-1,0) if not l.value else (1,0) if not r.value else None
            if not b.value and not undo_held:self._undo()
            elif step and (step!=direction or now>=repeat):
                self._move(*step);repeat=now+(.25 if step!=direction else .14)
            direction=step
            held_a,held_s,undo_held=not a.value,not sel.value,not b.value
            time.sleep(.025)

    def Game(self):
        self._start(self.selected)
        while not self.exit:
            choice=self.panel.show('CLOCKWORK COURIER',('Play room %d'%(self.selected+1),'Choose room','How to play','Save progress','Leave game'),
                (ROOMS[self.selected],'%d / 36 medals'%sum(self.medal(i) for i in range(12)),'Push every power cell onto a dock','Completed rooms and best scores','Return to KeyBoy'))
            if choice==0:self._start(self.selected);self._play()
            elif choice==1:
                options=tuple('%02d %s%s'%(i+1,ROOMS[i], ' LOCKED' if i>self.unlocked() else '') for i in range(12))
                details=tuple('Gold: %d pushes / earned %d/3'%(PAR[i],self.medal(i)) for i in range(12))
                index=self.panel.show('DELIVERY ROUTE',options,details,self.selected)
                if index==-2:self.exit=True
                elif 0<=index<=self.unlocked():self._start(index)
            elif choice==2:
                self.panel.show('DELIVERY NOTES',('Push cells; never pull','B reverses the last move','A opens restart/workshop','Gold rewards fewer pushes','Ready'),
                    ('Fill every glowing floor dock','Last 128 moves are reversible','No time limit or lost lives','Replay any completed room','12 deliveries restore the clock'))
            elif choice==3:
                self.warning='Progress saved' if self._save() else 'Save unavailable: USB/read-only';self._sync()
            elif choice in (4,-2,-1):self.exit=True
        self._clear();return True
