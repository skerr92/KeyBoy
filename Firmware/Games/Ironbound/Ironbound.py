# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Ironbound: eight illustrated, turn-based mech operations and a refit bay."""
import gc
import os
import time
import displayio
import terminalio
from adafruit_display_text import label

GRID,TILE,ORIGIN_X,ORIGIN_Y=8,24,24,28
DIRS=((0,1),(-1,0),(1,0),(0,-1))
MISSIONS=(('ASH DOCK','purge'),('SIGNAL FROST','relay'),('BROKEN CONVOY','salvage'),
          ('RED FOUNDRY','purge'),('GLASS ARRAY','relay'),('DROWNED YARD','salvage'),
          ('BLACK TRANSMITTER','relay'),('CITADEL CORE','commander'))
INK=(0x101A29,0x182939,0x263C4C,0x344E5C,0x56717A,0x7B9BA0,0xACD0C5,
     0xDFEEE0,0x5AB9CE,0x2C6B8D,0xD3A569,0xF6DF9D,0x773E51,0xBD5960,0xEE9480,0x568566)
THEMES=((0x263C4C,0x56717A,0x7B9BA0),(0x284653,0x56899A,0x97BCC0),
        (0x443F3C,0x856C56,0xB6A27D),(0x492D3C,0x885254,0xC28D71),
        (0x343D53,0x696C97,0xA5A6C7),(0x243E41,0x4E7D79,0x8AA69A),
        (0x342E44,0x695B7A,0x9F86A6),(0x3A3545,0x706375,0xB3A192))


def _palette(colors=INK,transparent=False):
    p=displayio.Palette(len(colors))
    for i,c in enumerate(colors):p[i]=c
    if transparent:p.make_transparent(0)
    return p


def _rect(b,x,y,w,h,c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):b[xx,yy]=c


def _oval(b,x,y,w,h,c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):
            if (2*(xx-x)-w+1)**2*h*h+(2*(yy-y)-h+1)**2*w*w<=w*w*h*h:b[xx,yy]=c


class _Canvas:
    def __init__(self):
        self.width,self.height=240,192
        self.strips=[displayio.Bitmap(240,16,16) for _ in range(12)]
    def __setitem__(self,pos,c):
        x,y=pos;self.strips[y//16][x,y%16]=c


def _grid(b,p,x=0,y=0,**kw):return displayio.TileGrid(b,pixel_shader=p,x=x,y=y,**kw)

def _solid(w,h,c,x=0,y=0):return _grid(displayio.Bitmap(w,h,1),_palette((c,)),x,y)

def _text(group,text,x,y,c=INK[7]):
    obj=label.Label(terminalio.FONT,text=text,color=c,x=x,y=y);group.append(obj);return obj

def _set(obj,text):
    if obj.text!=text:obj.text=text

def _tile(obj,tile):
    if obj[0]!=tile:obj[0]=tile

def _place(obj,x,y):
    if obj.x!=x:obj.x=x
    if obj.y!=y:obj.y=y

def _hide(obj,hidden):
    if obj.hidden!=hidden:obj.hidden=hidden


def _mech_art(kind=0):
    b=displayio.Bitmap(48,28,16)
    for frame in range(2):
        x=frame*24;bob=frame
        _oval(b,x+2,23,21,5,1)
        _rect(b,x+4,18,6,8,3);_rect(b,x+15,18,6,8,3)
        _rect(b,x+4,23,7,3,5);_rect(b,x+15,23,7,3,5)
        _rect(b,x+5,17,4,5,4);_rect(b,x+16,17,4,5,4)
        _rect(b,x+4,7+bob,17,13,1)
        _rect(b,x+5,8+bob,15,10,8 if kind==0 else 13 if kind==1 else 10 if kind==2 else 12)
        _rect(b,x+6,8+bob,13,2,6 if kind==0 else 14)
        _rect(b,x+9,11+bob,7,5,3)
        _rect(b,x+11,12+bob,3,2,11)
        _rect(b,x+7,2+bob,12,7,4)
        _rect(b,x+8,2+bob,10,2,5)
        _rect(b,x+8,6+bob,10,2,1)
        _rect(b,x+10,6+bob,6,1,8 if kind==0 else 14)
        _rect(b,x+1,9+bob,4,10,5)
        _rect(b,x+20,10+bob,3,12,3)
        _rect(b,x+20,20+bob,3,3,7)
        if kind==1:
            _rect(b,x+2,3,3,5,13);_rect(b,x+20,3,3,5,13)
        if kind==2:
            _rect(b,x,6+bob,6,5,10);_rect(b,x+1,0+bob,2,8,7)
        if kind==3:
            _rect(b,x,6,6,7,12);_rect(b,x+18,6,6,7,12)
            _rect(b,x+3,0,3,7,10);_rect(b,x+18,0,3,7,10)
            _rect(b,x+10,0,6,2,11)
    return b


def _props_art():
    # Locked/open extraction, crate, empty crate, terminal, active terminal,
    # target brackets, incoming-fire corners. Bounded 2,304-byte atlas.
    b=displayio.Bitmap(24*8,24,16)
    for t in (0,1):
        x=t*24
        _rect(b,x+2,2,20,20,3)
        for k in (2,19):
            _rect(b,x+k,3,3,18,10 if t==0 else 15)
        _rect(b,x+7,8,10,2,13 if t==0 else 6)
        _rect(b,x+7,14,10,2,13 if t==0 else 6)
        _rect(b,x+10,6,4,12,13 if t==0 else 6)
    for t in (2,3):
        x=t*24
        _rect(b,x+4,6,16,14,1)
        _rect(b,x+5,5,14,12 if t==2 else 3,10)
        _rect(b,x+6,6,12,2,11)
        _rect(b,x+8,8,2,10,4);_rect(b,x+16,8,2,10,4)
    for t in (4,5):
        x=t*24
        _rect(b,x+5,3,15,18,1);_rect(b,x+6,4,13,15,4)
        _rect(b,x+8,6,9,8,9 if t==4 else 15)
        for k in (7,10,13):_rect(b,x+9,k,5,1,8 if t==4 else 6)
        _rect(b,x+8,16,2,1,11);_rect(b,x+13,16,4,1,7)
    for t in (6,7):
        x=t*24
        for xx,yy,w,h in ((1,1,7,2),(1,1,2,7),(16,1,7,2),(21,1,2,7),(1,21,7,2),(1,16,2,7),(16,21,7,2),(21,16,2,7)):
            _rect(b,x+xx,yy,w,h,11 if t==6 else 14)
    return b


def _terrain(game,hangar=False):
    b=_Canvas()
    _rect(b,0,0,240,192,0)
    for x in (6,225):
        _rect(b,x,0,9,192,1)
        for y in range(8,192,24):
            _rect(b,x+2,y,5,2,4);_rect(b,x+3,y+4,3,7,9)
    if hangar:
        _rect(b,24,4,192,12,3)
        _rect(b,27,5,186,3,5)
        for x in (36,192):
            _rect(b,x,15,10,80,4);_rect(b,x+2,16,3,77,5)
            _rect(b,x-5,90,20,7,3)
        for x in (77,158):
            _rect(b,x,16,2,40,4);_rect(b,x-4,52,10,4,10)
        _rect(b,80,91,80,15,3);_rect(b,84,91,72,3,5)
        for x in range(84,156,8):_rect(b,x,97,4,4,10)
        for x in (54,171):
            _rect(b,x,38,15,24,3);_rect(b,x+2,40,11,14,9)
            for y in (42,46,50):_rect(b,x+4,y,7,1,8)
        _rect(b,12,104,216,72,1)
        _rect(b,12,104,216,1,4)
        _rect(b,12,174,216,1,4)
        return b.strips
    for y in range(8):
        for x in range(8):
            px,py=24+x*24,y*24
            _rect(b,px,py,24,24,1)
            _rect(b,px+1,py+1,22,22,2)
            _rect(b,px+2,py+2,20,1,3)
            _rect(b,px+2,py+3,1,18,3)
            _rect(b,px+4,py+20,16,1,0)
            if (x+y)%3==0:_rect(b,px+15,py+7,4,1,4)
            if game._blocked((x,y)) and not hangar:
                _rect(b,px+2,py+3,21,20,0)
                _rect(b,px+2,py+1,19,15,4)
                _rect(b,px+3,py+2,17,2,5)
                _rect(b,px+3,py+16,17,5,3)
                for k in (5,10,15):_rect(b,px+k,py+5,2,8,1)
                _rect(b,px+14,py+3,3,2,10)
            elif game._cover((x,y)) and not hangar:
                _rect(b,px+3,py+17,18,5,3)
                _rect(b,px+4,py+16,16,3,5)
                _rect(b,px+4,py+16,4,2,6)
                _rect(b,px+16,py+16,4,2,6)
            elif (x*3+y)%7==0:
                for k in range(3):_rect(b,px+5+k*4,py+9,2,3,3)
    return b.strips


class Ironbound:
    def __init__(self,splash,A_btn,B_btn,Up_btn,Dwn_btn,L_btn,R_btn,Sel_btn,Audio):
        self._splash=splash
        self._A,self._B,self._U,self._D=A_btn,B_btn,Up_btn,Dwn_btn
        self._L,self._R,self._sel,self._audio=L_btn,R_btn,Sel_btn,Audio
        self._exit=False
        self._mission,self._hull,self._attack,self._armor=1,14,4,0
        self._capacity,self._weapon,self._finished=14,0,False
        self._view={};self._menu=None;self._props=None;self._mech=None
        self._load()

    def _save(self):
        values=(self._mission,self._hull,self._attack,self._armor,self._capacity,self._weapon,int(self._finished))
        try:
            with open('/ironbound.tmp','wt') as f:f.write('IB2,'+','.join(str(v) for v in values))
            os.rename('/ironbound.tmp','/ironbound.sav')
            return True
        except OSError:return False

    def _load(self):
        try:
            with open('/ironbound.sav','rt') as f:data=f.readline().strip()
            modern=data.startswith('IB2,')
            values=[int(v) for v in data.split(',')[1 if modern else 0:]]
            if modern:
                if len(values)!=7:return
                mission,hull,attack,armor,capacity,weapon,finished=values
                if not (14<=capacity<=35 and 0<=hull<=capacity and weapon in (0,1) and finished in (0,1) and (not finished or mission==8)):return
            else:
                if len(values)!=4:return
                mission,hull,attack,armor=values
                if not (0<=hull<=100 and 1<=attack<=30 and 0<=armor<=20):return
                capacity=max(14,min(35,hull));hull=min(hull,capacity)
                attack=min(12,attack);armor=min(3,armor);weapon,finished=0,0
            if not (1<=mission<=8 and 1<=attack<=12 and 0<=armor<=3):return
            self._mission,self._hull,self._attack,self._armor=mission,hull,attack,armor
            self._capacity,self._weapon,self._finished=capacity,weapon,bool(finished)
        except (OSError,ValueError):pass

    def _clear(self):
        while len(self._splash):self._splash.pop()
        self._view={};gc.collect()

    @staticmethod
    def _distance(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])

    def _blocked(self,pos):
        x,y=pos
        if not (0<=x<8 and 0<=y<8):return True
        if x in (0,7) or y in (0,7) or pos in ((3,2),(5,5),(4,3),(6,1),(5,3),(2,2),(6,5),(5,1)):return False
        return (x*5+y*3+self._mission)%11 in (0,1)

    def _cover(self,pos):
        return not self._blocked(pos) and (pos[0]*3+pos[1]*5+self._mission)%7 in (0,1)

    def _line(self,a,b):
        # Supercover traversal: a ray cannot pass diagonally between blockers.
        x,y=a;dx,dy=b[0]-x,b[1]-y
        nx,ny=abs(dx),abs(dy);sx=1 if dx>0 else -1;sy=1 if dy>0 else -1
        ix=iy=0
        while ix<nx or iy<ny:
            left=(1+2*ix)*ny;right=(1+2*iy)*nx
            if left==right:
                if self._blocked((x+sx,y)) or self._blocked((x,y+sy)):return False
                x+=sx;y+=sy;ix+=1;iy+=1
            elif left<right:x+=sx;ix+=1
            else:y+=sy;iy+=1
            if self._blocked((x,y)):return False
        return True

    def _path(self,start,goal,occupied=()):
        todo=[start];parent={start:None}
        for pos in todo:
            if pos==goal:
                out=[]
                while parent[pos] is not None:out.append(pos);pos=parent[pos]
                return out[::-1]
            for dx,dy in DIRS:
                p=pos[0]+dx,pos[1]+dy
                if p not in parent and not self._blocked(p) and (p not in occupied or p==goal):
                    parent[p]=pos;todo.append(p)
        return None

    def _begin(self):
        self._pos=(0,7);self._hull=self._capacity
        self._energy,self._kits,self._turn=3,2,0
        self._relay=0;self._salvage=set();self._extracted=False
        self._note='A aim/interact / B guard / SEL menu'
        positions=((6,1),(5,3),(2,2),(6,5))
        count=min(4,1+self._mission//2)
        self._enemies=[]
        for i in range(count):
            kind=3 if self._mission==8 and i==0 else 2 if i%2 else 1
            hp=(16 if kind==3 else 5+self._mission//2)
            self._enemies.append({'pos':positions[i],'hp':hp,'max':hp,'kind':kind,'intent':'move','target':None,'cooldown':0})
        self._plan()
        self._build_field()

    def _plan(self):
        for e in self._enemies:
            if e['hp']<=0:continue
            if e['cooldown']>0:
                e['intent'],e['target']='recover',None
                continue
            reach=4 if e['kind']==2 else 3 if e['kind']==3 else 1
            if self._distance(e['pos'],self._pos)<=reach and self._line(e['pos'],self._pos):
                e['intent'],e['target']='fire',self._pos
            else:
                occupied=[other['pos'] for other in self._enemies if other is not e and other['hp']>0]
                path=self._path(e['pos'],self._pos,occupied)
                e['intent'],e['target']='move',path[0] if path else e['pos']

    def _enemy_turn(self,guard=False):
        self._turn+=1
        damage=0
        for e in self._enemies:
            if e['hp']<=0:continue
            if e['intent']=='recover':
                e['cooldown']=0
            elif e['intent']=='fire':
                e['cooldown']=1
                if self._pos==e['target'] and self._line(e['pos'],self._pos):
                    raw=4 if e['kind']==3 else 3 if e['kind']==2 else 2
                    damage+=max(0,raw-self._armor-int(self._cover(self._pos))-(3 if guard else 0))
            else:
                target=e['target']
                occupied=any(o is not e and o['hp']>0 and o['pos']==target for o in self._enemies)
                if target!=self._pos and not occupied and not self._blocked(target):e['pos']=target
        self._hull=max(0,self._hull-damage)
        if damage:self._audio.play('hit');self._note+=' Hull -%d.'%damage
        elif guard:self._audio.play('block')
        self._plan()

    def _objective_done(self):
        kind=MISSIONS[self._mission-1][1]
        return (kind not in ('relay','salvage') or (self._relay>=2 if kind=='relay' else len(self._salvage)==2))

    def _gate_open(self):return self._objective_done() and all(e['hp']<=0 for e in self._enemies)

    def _move(self,dx,dy):
        if self._hull<=0 or self._extracted:return False
        p=self._pos[0]+dx,self._pos[1]+dy
        if self._blocked(p) or any(e['hp']>0 and e['pos']==p for e in self._enemies):
            self._note='Blocked. No turn spent.';return False
        if p==(7,0) and not self._gate_open():
            self._note='Complete objective and clear hostiles.';return False
        self._pos=p;self._note='Moved. Incoming fire hits old tiles.'
        if MISSIONS[self._mission-1][1]=='salvage' and p in ((3,2),(5,5)) and p not in self._salvage:
            self._salvage.add(p);self._audio.play('collect');self._note='Recovered cargo %d/2.'%len(self._salvage)
        if p==(7,0) and self._gate_open():
            self._extracted=True;self._audio.play('win');return True
        self._enemy_turn();return True

    def _targets(self):
        reach=5 if self._weapon==1 and self._energy else 3
        return [i for i,e in enumerate(self._enemies) if e['hp']>0 and self._distance(e['pos'],self._pos)<=reach and self._line(self._pos,e['pos'])]

    def _fire(self,index):
        if self._hull<=0 or self._extracted:return False
        if index not in self._targets():self._note='No clear shot. No turn spent.';return False
        rail=self._weapon==1 and self._energy>0
        if rail:self._energy-=1
        enemy=self._enemies[index]
        enemy['hp']=max(0,enemy['hp']-self._attack-(2 if rail else 0))
        self._note='Rail shot.' if rail else 'Cannon fired.'
        self._audio.play('shoot')
        self._enemy_turn();return True

    def _guard(self):
        if self._hull<=0 or self._extracted:return False
        self._energy=min(3,self._energy+1)
        self._note='Guard raised. Energy +1.'
        self._enemy_turn(True)

    def _repair(self):
        if self._hull<=0 or self._extracted:return False
        if self._kits==0 or self._hull==self._capacity:
            self._note='No repair needed or no kits left.';return False
        self._kits-=1;self._hull=min(self._capacity,self._hull+7)
        self._note='Repair +7 hull.';self._audio.play('support')
        self._enemy_turn(True);return True

    def _pulse(self):
        if self._hull<=0 or self._extracted:return False
        targets=[e for e in self._enemies if e['hp']>0 and self._distance(self._pos,e['pos'])<=2 and self._line(self._pos,e['pos'])]
        if self._energy<3 or not targets:self._note='Need 3 energy and a nearby target.';return False
        self._energy-=3
        for e in targets:e['hp']=max(0,e['hp']-5)
        self._note='EMP pulse: 5 damage nearby.';self._audio.play('support')
        self._enemy_turn(True);return True

    def _interact(self):
        if self._hull<=0 or self._extracted:return False
        if MISSIONS[self._mission-1][1]=='relay' and self._distance(self._pos,(4,3))<=1 and self._relay<2:
            self._relay+=1;self._note='Relay synchronized %d/2.'%self._relay
            self._audio.play('select');self._enemy_turn();return True
        return False

    def _background(self,hangar=False):
        self._clear();colors=list(INK)
        colors[2],colors[4],colors[5]=THEMES[self._mission-1]
        p=_palette(colors)
        for i,b in enumerate(_terrain(self,hangar)):self._splash.append(_grid(b,p,y=28+i*16))
        self._splash.append(_solid(240,28,INK[0]))
        self._splash.append(_solid(240,20,INK[0],y=220))
        if self._props is None:self._props=_props_art();self._mech=_mech_art()
        self._sprite_palette=_palette(transparent=True)

    def _prop(self,tile,pos):
        obj=_grid(self._props,self._sprite_palette,tile_width=24,tile_height=24)
        obj[0]=tile;_place(obj,24+pos[0]*24,28+pos[1]*24);self._splash.append(obj);return obj

    def _build_field(self):
        self._background()
        self._view['gate']=self._prop(0,(7,0))
        kind=MISSIONS[self._mission-1][1]
        self._view['cargo']=[self._prop(2,p) for p in ((3,2),(5,5))] if kind=='salvage' else []
        self._view['relay']=self._prop(4,(4,3)) if kind=='relay' else None
        self._view['marks']=[self._prop(7,self._pos) for e in self._enemies]
        self._view['enemies']=[]
        atlases={}
        for e in self._enemies:
            kind=e['kind']
            if kind not in atlases:atlases[kind]=_mech_art(kind)
            obj=_grid(atlases[kind],self._sprite_palette,tile_width=24,tile_height=28)
            self._splash.append(obj);self._view['enemies'].append(obj)
        hero=_grid(self._mech,self._sprite_palette,tile_width=24,tile_height=28)
        self._splash.append(hero);self._view['hero']=hero
        self._view['aim']=self._prop(6,self._pos);self._view['aim'].hidden=True
        self._view['title']=_text(self._splash,'',5,7)
        self._view['stats']=_text(self._splash,'',5,21,INK[6])
        self._view['note']=_text(self._splash,'',5,230,INK[11])
        self._sync()

    def _sync(self,frame=0):
        v=self._view
        _place(v['hero'],24+self._pos[0]*24,24+self._pos[1]*24)
        _tile(v['hero'],frame)
        for e,obj,mark in zip(self._enemies,v['enemies'],v['marks']):
            _place(obj,24+e['pos'][0]*24,24+e['pos'][1]*24);_tile(obj,frame)
            _hide(obj,e['hp']<=0);_hide(mark,e['hp']<=0 or e['intent']!='fire')
            if e['target'] is not None:_place(mark,24+e['target'][0]*24,28+e['target'][1]*24)
        _tile(v['gate'],1 if self._gate_open() else 0)
        for pos,obj in zip(((3,2),(5,5)),v['cargo']):_tile(obj,3 if pos in self._salvage else 2)
        if v['relay'] is not None:_tile(v['relay'],5 if self._relay>=2 else 4)
        alive=sum(e['hp']>0 for e in self._enemies)
        _set(v['title'],'%d/8 %s'%(self._mission,MISSIONS[self._mission-1][0]))
        _set(v['stats'],'H%d/%d E%d K%d HOSTILES %d'%(self._hull,self._capacity,self._energy,self._kits,alive))
        _set(v['note'],self._note[:38])

    def _prepare_menu(self):
        if self._menu is not None:return
        group=displayio.Group(x=8,y=43)
        for y in range(0,180,18):group.append(_solid(224,18,INK[0],y=y))
        group.append(_solid(216,2,INK[8],4,3))
        title=_text(group,'IRONBOUND',10,20,INK[11]);info=_text(group,'',10,42,INK[6])
        rows=[_text(group,'',10,72+i*22) for i in range(4)]
        _text(group,'A choose / B or SEL back',10,166,INK[6])
        self._menu=group,title,info,rows

    def _choose(self,title,items,detail=''):
        self._prepare_menu();group,heading,info,rows=self._menu
        _set(heading,title);_set(info,detail)
        self._splash.append(group)
        choice,last,dirty=0,time.monotonic(),True
        a_was,b_was,s_was=not self._A.value,not self._B.value,not self._sel.value
        try:
            while not self._exit:
                now=time.monotonic()
                if not self._U.value and not self._D.value:self._exit=True;break
                if now-last>.18:
                    delta=-1 if not self._U.value else 1 if not self._D.value else 0
                    if delta:choice=(choice+delta)%len(items);last,dirty=now,True
                if dirty:
                    for i,row in enumerate(rows):
                        row.hidden=i>=len(items)
                        if i<len(items):_set(row,('> ' if i==choice else '  ')+items[i]);row.color=INK[11] if i==choice else INK[7]
                    dirty=False
                a,b,s=not self._A.value,not self._B.value,not self._sel.value
                if a and not a_was:return choice
                if (b and not b_was) or (s and not s_was):return -1
                a_was,b_was,s_was=a,b,s;time.sleep(.025)
        finally:self._splash.remove(group);gc.collect()
        return -1

    def _aim(self):
        targets=self._targets()
        if not targets:self._note='No target in range or line of sight.';return False
        choice,last=0,time.monotonic()
        a_was,b_was,s_was=not self._A.value,not self._B.value,not self._sel.value
        marker=self._view['aim'];marker.hidden=False
        try:
            while not self._exit:
                now=time.monotonic()
                if not self._U.value and not self._D.value:self._exit=True;break
                if now-last>.18:
                    delta=-1 if not self._L.value or not self._U.value else 1 if not self._R.value or not self._D.value else 0
                    if delta:choice=(choice+delta)%len(targets);last=now
                enemy=self._enemies[targets[choice]]
                _place(marker,24+enemy['pos'][0]*24,28+enemy['pos'][1]*24)
                _set(self._view['note'],'HP%d %s / A fire / B cancel'%(enemy['hp'],enemy['intent'].upper()))
                a,b,s=not self._A.value,not self._B.value,not self._sel.value
                if a and not a_was:return self._fire(targets[choice])
                if (b and not b_was) or (s and not s_was):return False
                a_was,b_was,s_was=a,b,s;time.sleep(.025)
        finally:marker.hidden=True
        return False

    def _systems(self):
        choice=self._choose('MECH SYSTEMS',('Repair kit +7 hull','EMP pulse / 3 energy','Mission briefing','Back'),'Kits %d / energy %d'%(self._kits,self._energy))
        if choice==0:return self._repair()
        if choice==1:return self._pulse()
        if choice==2:
            kind=MISSIONS[self._mission-1][1]
            detail='Clear hostiles, then reach E.'
            if kind=='relay':detail='A beside terminal twice, then E.'
            elif kind=='salvage':detail='Collect both crates, then reach E.'
            self._choose('MISSION / '+kind.upper(),('Continue',),detail)
        return False

    def _pause(self):
        choice=self._choose('IRONBOUND / TURN %d'%self._turn,('Resume','Mech systems','Save checkpoint','Leave game'),'Save restarts this mission fresh.')
        if choice==1:self._systems()
        elif choice==2:self._note='Checkpoint saved.' if self._save() else 'Save failed: USB/read-only/full.'
        elif choice==3:self._exit=True

    def _mission_run(self):
        self._begin();last_move=last_anim=time.monotonic()
        a_was,b_was,s_was=not self._A.value,not self._B.value,not self._sel.value
        while not self._exit and self._hull>0 and not self._extracted:
            now=time.monotonic();changed=modal=False
            if not self._U.value and not self._D.value:self._exit=True;break
            a,b,s=not self._A.value,not self._B.value,not self._sel.value
            if s and not s_was:self._pause();modal=True;changed=True
            elif a and not a_was:
                changed=self._interact()
                if not changed:self._aim();modal=True
                changed=True
            elif b and not b_was:self._guard();changed=True
            elif now-last_move>.22:
                direction=1 if not self._L.value else 2 if not self._R.value else 3 if not self._U.value else 0 if not self._D.value else None
                if direction is not None:self._move(*DIRS[direction]);last_move=now;changed=True
            if modal:
                a,b,s=not self._A.value,not self._B.value,not self._sel.value
                last_move=time.monotonic()
            if changed or now-last_anim>.4:
                self._sync(int(now*2.5)%2);last_anim=now
            a_was,b_was,s_was=a,b,s;time.sleep(.025)
        if self._hull<=0:self._audio.play('lose')
        return self._extracted

    def _build_hangar(self):
        self._background(True)
        # Large refit-bay silhouette, generated once for this scene.
        b=displayio.Bitmap(48,56,16)
        for y in range(56):
            for x in range(48):b[x,y]=self._mech[x//2,y//2]
        self._splash.append(_grid(b,self._sprite_palette,96,64))
        _text(self._splash,'IRONBOUND / REFIT BAY',45,12,INK[11])
        _text(self._splash,'%d/8 %s'%(self._mission,MISSIONS[self._mission-1][0]),20,43)
        _text(self._splash,'HULL %d / POWER %d / ARMOR %d'%(self._capacity,self._attack,self._armor),14,142)
        _text(self._splash,'RAIL +2 / RANGE 5 / 1 ENERGY' if self._weapon else 'CANNON / RANGE 3 / NO ENERGY',22,161,INK[6])
        _text(self._splash,'OBJECTIVE: '+MISSIONS[self._mission-1][1].upper(),35,183,INK[11])
        _text(self._splash,'A deploy / B loadout / SEL services',12,230,INK[6])

    def _hangar(self):
        self._build_hangar()
        a_was,b_was,s_was=not self._A.value,not self._B.value,not self._sel.value
        while not self._exit:
            if not self._U.value and not self._D.value:self._exit=True;break
            a,b,s=not self._A.value,not self._B.value,not self._sel.value
            modal=False
            if a and not a_was:return True
            if b and not b_was:
                choice=self._choose('PRIMARY WEAPON',('Cannon / free shots','Rail / long range +2'),'Guard recharges rail energy.')
                if choice>=0:self._weapon=choice;self._build_hangar()
                modal=True
            elif s and not s_was:
                choice=self._choose('HANGAR SERVICES',('Resume','Save checkpoint','Leave game'),'Full repairs and kits on deploy.')
                if choice==1:self._choose('CHECKPOINT',('Continue',),'Saved.' if self._save() else 'Save failed: USB/read-only/full.')
                elif choice==2:self._exit=True
                modal=True
            if modal:a,b,s=not self._A.value,not self._B.value,not self._sel.value
            a_was,b_was,s_was=a,b,s;time.sleep(.03)
        return False

    def _refit(self,choice):
        if choice in (0,1,2) and self._attack==12 and self._capacity==35 and self._armor==3:
            self._hull=self._capacity
            return True
        if choice==0 and self._attack<12:self._attack+=1
        elif choice==1 and self._capacity<35:self._capacity=min(35,self._capacity+3)
        elif choice==2 and self._armor<3:self._armor+=1
        else:return False
        self._hull=self._capacity
        return True

    def Game(self):
        self._exit=False;self._prepare_menu()
        while not self._exit:
            if self._finished:
                self._build_hangar()
                if self._choose('IRONBOUND LIBERATED',('New campaign','Leave game'),'The Citadel commander has fallen.')!=0:break
                self._mission,self._hull,self._capacity,self._attack,self._armor,self._weapon,self._finished=1,14,14,4,0,0,False
            if not self._hangar():break
            won=self._mission_run()
            if self._exit:break
            if not won:
                if self._choose('MECH RECOVERED',('Return to refit bay','Leave game'),'Retry with full hull and supplies.')!=0:break
                continue
            if self._mission==8:
                self._finished=True
            else:
                while not self._exit:
                    choice=self._choose('SECTOR SECURED / REFIT',('Weapon power +1 (max 12)','Hull capacity +3 (max 35)','Armor +1 (max 3)'),'Choose one permanent upgrade.')
                    if self._exit:break
                    if self._refit(choice):break
                    self._choose('REFIT REQUIRED',('Continue',),'Choose an upgrade below its cap.')
                if self._exit:break
                self._mission+=1
                self._audio.play('upgrade')
            if not self._save():self._choose('SAVE UNAVAILABLE',('Continue',),'Progress in memory; save at SEL.')
        self._clear();self._menu=self._props=self._mech=None;gc.collect()
        return True
