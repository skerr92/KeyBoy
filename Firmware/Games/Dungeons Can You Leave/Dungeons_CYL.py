# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Seven reachable dungeons; retained pixel art and deliberate shield combat."""
import gc
import os
import time
import displayio
import terminalio
from adafruit_display_text import label

TILE = 18
OFFSET_X, OFFSET_Y = 3, 24
MAX_HEARTS = 6
DIRECTIONS = ((0, 1), (-1, 0), (1, 0), (0, -1))

FLOORS = (
    ('CELLAR', (
        '#############',
        '#S.+.....B.E#',
        '#.#########.#',
        '#...........#',
        '#.#########.#',
        '#...........#',
        '#.#########.#',
        '#...........#',
        '#.#########.#',
        '#..+........#',
        '#...........#',
        '#############',
    )),
    ('MOSS HALLS', (
        '#############',
        '#S.+..#....E#',
        '#.###.#.###.#',
        '#...#.#...#.#',
        '###.#.###.#.#',
        '#...#.....#.#',
        '#.#######.#.#',
        '#.....#...#.#',
        '#.###.#.###.#',
        '#..+#....B..#',
        '#############',
        '#############',
    )),
    ('EMBER VAULT', (
        '#############',
        '#S.+X.....E.#',
        '#.#####.###.#',
        '#.....#...#.#',
        '#####.###.#.#',
        '#...#...#.#.#',
        '#.m.###.#.#.#',
        '#.#.....#.#.#',
        '#.#######.#.#',
        '#..+.....B..#',
        '#############',
        '#############',
    )),
    ('SHADE MAZE', (
        '#############',
        '#S.+..#....E#',
        '#.###.#.###.#',
        '#.#m#.......#',
        '#.#.#####.###',
        '#.#.....#...#',
        '#.#####.###.#',
        '#.....#...#.#',
        '#####.###.#.#',
        '#..+.B....#.#',
        '#############',
        '#############',
    )),
    ('THORN KEEP', (
        '#############',
        '#S.X..#....E#',
        '#.###.#.###.#',
        '#...#.#...#.#',
        '###.#.###.#.#',
        '#m..#..X..#.#',
        '#.#######.#.#',
        '#.....#...#.#',
        '#.###.#.###.#',
        '#..+#....B..#',
        '#############',
        '#############',
    )),
    ('IRON DEPTHS', (
        '#############',
        '#S.+..#....E#',
        '#.###.#.###.#',
        '#.#X#....m..#',
        '#.#.#####.###',
        '#.#.....#...#',
        '#.#####.###.#',
        '#.....#...#.#',
        '#####.###.#.#',
        '#..+.B....#.#',
        '#############',
        '#############',
    )),
    ('THE LAST GATE', (
        '#############',
        '#S.+..#....E#',
        '#.###.#.###.#',
        '#.#m#.......#',
        '#.#.#####.###',
        '#.#..X..#...#',
        '#.#####.###.#',
        '#...m.#...#.#',
        '#.###.###.#.#',
        '#..+.B....#.#',
        '#############',
        '#############',
    )),
)

# Foundation, mortar, flagstones, brick shadow/face/light, accent, metal,
# linen, lantern gold, warm light, dark red, danger, moss, magic, white.
INK = (0x101421, 0x1A2130, 0x293444, 0x202939, 0x465367, 0x67788B,
       0x799D97, 0x9EB9C3, 0xE9D3AD, 0xD7924C, 0xFFE2A0, 0x6E3448,
       0xD96765, 0x597953, 0x6AB5C5, 0xF1EFE2)
THEMES = ((0x465367,0x67788B,0x799D97,0x597953),
          (0x3E5350,0x67847A,0xA3B889,0x6C8B50),
          (0x59424A,0x8A6359,0xE7A164,0x864E45),
          (0x433F61,0x71638B,0xAC93CB,0x56517D),
          (0x3F5045,0x6E7F58,0xB6BA74,0x64814B),
          (0x3A4C5D,0x6B8593,0xA6C1BC,0x506576),
          (0x504354,0x826A7D,0xD2AE84,0x716077))
BOSSES = ('GATE WARDEN','MOSS GOLEM','CINDER KNIGHT','VEIL REAPER',
          'THORN SENTINEL','IRON COLOSSUS','THE OATHBREAKER')


def _palette(colors=INK, transparent=False):
    p = displayio.Palette(len(colors))
    for i, c in enumerate(colors):
        p[i] = c
    if transparent:
        p.make_transparent(0)
    return p


def _rect(b, x, y, w, h, c):
    for yy in range(max(0, y), min(b.height, y+h)):
        for xx in range(max(0, x), min(b.width, x+w)):
            b[xx, yy] = c


def _oval(b, x, y, w, h, c):
    for yy in range(max(0, y), min(b.height, y+h)):
        for xx in range(max(0, x), min(b.width, x+w)):
            if (2*(xx-x)-w+1)**2*h*h+(2*(yy-y)-h+1)**2*w*w <= w*w*h*h:
                b[xx, yy] = c


class _Canvas:
    def __init__(self):
        self.width, self.height = 234, 216
        self.strips = [displayio.Bitmap(234, 18, 16) for _ in range(12)]
    def __setitem__(self, pos, c):
        x,y = pos
        self.strips[y//18][x,y%18] = c


def _grid(b, p, x=0, y=0, **kw):
    return displayio.TileGrid(b, pixel_shader=p, x=x, y=y, **kw)


def _solid(w, h, color, x=0, y=0):
    return _grid(displayio.Bitmap(w,h,1), _palette((color,)), x,y)


def _text(group, text, x, y, color=INK[8]):
    obj = label.Label(terminalio.FONT, text=text, color=color, x=x, y=y)
    group.append(obj)
    return obj


def _set(obj, text):
    if obj.text != text:
        obj.text = text


def _tile(obj, index):
    if obj[0] != index:
        obj[0] = index


def _place(obj, x, y):
    if obj.x != x:
        obj.x = x
    if obj.y != y:
        obj.y = y


def _hide(obj, hidden):
    if obj.hidden != hidden:
        obj.hidden = hidden


def _terrain(number):
    rows = FLOORS[number][1]
    b = _Canvas()
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            px,py = x*18,y*18
            _rect(b,px,py,18,18,1 if c=='#' else 2)
            if c == '#':
                # Offset courses, beveled lintels, mortar, and chipped corners.
                for by in (1,9):
                    shift = 0 if by==1 else 8
                    for bx in range(-shift,18,9):
                        left,right = max(px,px+bx),min(px+18,px+bx+8)
                        _rect(b,left,py+by,right-left,7,4)
                        _rect(b,left,py+by,right-left,1,5)
                        _rect(b,left,py+by+6,right-left,1,3)
                if (x*7+y*3)%5==0:
                    _rect(b,px+3,py+2,3,2,13)
                    _rect(b,px+5,py+4,2,4,13)
                if y+1 < len(rows) and rows[y+1][x] != '#':
                    _rect(b,px,py+15,18,3,0)
                    _rect(b,px+1,py+15,16,1,6)
            else:
                _rect(b,px+1,py+1,16,1,3)
                _rect(b,px+1,py+2,1,14,3)
                _rect(b,px+3,py+15,13,1,1)
                if (x+y*3)%4==0:
                    _rect(b,px+6,py+5,3,1,4)
                    _rect(b,px+8,py+6,1,3,1)
                if c=='B':
                    _oval(b,px+1,py+1,16,16,3)
                    _oval(b,px+3,py+3,12,12,6)
                    _oval(b,px+5,py+5,8,8,2)
                if c=='S':
                    for k in range(4):
                        _rect(b,px+3,py+3+k*3,12,2,4+k%2)
    return b.strips


def _hero_art():
    b = displayio.Bitmap(16*12,22,16)
    for direction in range(4):
        for gait in range(3):
            x=(direction*3+gait)*16
            bob=1 if gait==2 else 0
            _oval(b,x+2,18,13,4,1)
            _rect(b,x+3,9+bob,10,9,11)  # cloak
            _rect(b,x+4,10+bob,8,6,14)
            _rect(b,x+5,11+bob,2,5,7)
            _rect(b,x+4,17,3,3+(gait==1),3)
            _rect(b,x+10,17,3,3+(gait==2),3)
            _oval(b,x+3,1+bob,11,10,3)
            _rect(b,x+4,2+bob,9,6,7)
            _rect(b,x+5,2+bob,7,1,15)
            _rect(b,x+4,7+bob,9,2,1)
            if direction != 3:
                _rect(b,x+(4 if direction==1 else 9 if direction==2 else 6),7+bob,3,1,10)
            _rect(b,x+8,0+bob,3,4,12)
            _rect(b,x+1,11+bob,4,6,9)
            _rect(b,x+2,12+bob,2,3,10)
            _rect(b,x+14,9+bob,1,9,7)
            _rect(b,x+13,15+bob,3,1,9)
    return b


def _guardian_art(number):
    b = displayio.Bitmap(24*3,28,16)
    for frame in range(3):
        x=frame*24
        bob=frame==1
        _oval(b,x+2,23,21,5,1)
        _rect(b,x+5,19,5,6,3)
        _rect(b,x+15,19,5,6,3)
        _oval(b,x+3,7+bob,20,15,11)
        _rect(b,x+6,9+bob,13,11,4)
        _rect(b,x+8,10+bob,3,9,5)
        _rect(b,x+5,19,15,2,9)
        _oval(b,x+5,1+bob,16,12,3)
        _rect(b,x+7,2+bob,12,7,5)
        _rect(b,x+9,2+bob,8,2,7)
        _rect(b,x+7,8+bob,12,3,1)
        _rect(b,x+9,8+bob,3,2,12 if frame==2 else 10)
        _rect(b,x+15,8+bob,3,2,12 if frame==2 else 10)
        # Distinct crown, vines, horns, hood, thorns, rivets, royal mantle.
        if number in (0,6):
            for k in (7,12,17):
                _rect(b,x+k,0,2,4,9)
            _rect(b,x+7,3,12,1,10)
        elif number in (1,4):
            for k in (3,19):
                _rect(b,x+k,3,2,17,13)
                _rect(b,x+k-2,5,6,2,6)
            _rect(b,x+11,0,4,3,13)
        elif number==2:
            _rect(b,x+3,0,3,7,9)
            _rect(b,x+20,0,3,7,9)
        elif number==3:
            _rect(b,x+5,1,3,11,11)
            _rect(b,x+19,1,3,11,11)
        else:
            for k in (5,19):
                _rect(b,x+k,13,2,2,15)
                _rect(b,x+k,17,2,2,15)
        if number==6:
            _rect(b,x+2,11+bob,3,12,11)
            _rect(b,x+21,11+bob,3,12,11)
            _rect(b,x+11,13+bob,4,3,9)
        if number==4:
            for k in (1,20):
                _rect(b,x+k,1,2,5,6)
                _rect(b,x+k+1,0,2,2,9)
        _rect(b,x+1,9 if frame==2 else 14,2,10,7)
        _rect(b,x,16 if frame==2 else 21,5,2,9)
    return b


def _objects_art():
    # Gate closed/open, cache, spent cache, spike safe/warn/live, torch x2,
    # shade x2, sword sweep, guarded shield, enemy target rune.
    b = displayio.Bitmap(18*14,18,16)
    for tile in (0,1):
        x=tile*18
        _oval(b,x+1,0,16,18,5)
        _rect(b,x+2,7,14,11,5)
        _oval(b,x+4,2,10,16,0 if tile==0 else 14)
        _rect(b,x+4,8,10,10,0 if tile==0 else 14)
        if tile==0:
            for k in (5,8,11):
                _rect(b,x+k,5,1,13,7)
            _rect(b,x+7,11,4,3,9)
        else:
            _rect(b,x+7,6,4,9,10)
            _rect(b,x+5,9,8,2,15)
    for tile in (2,3):
        x=tile*18
        _rect(b,x+3,6,13,10,3)
        _rect(b,x+3,5,12,8 if tile==2 else 3,9)
        _rect(b,x+4,6,10,2,10)
        _rect(b,x+3,12,12,3,11)
        _rect(b,x+8,7,2,8,7)
    for tile in (4,5,6):
        x=tile*18
        _rect(b,x+2,3,14,13,1)
        for k in (4,9,14):
            _rect(b,x+k-1,7,3,7,3)
            _rect(b,x+k,6 if tile==4 else 3,1,8,5 if tile==4 else 9 if tile==5 else 12)
            if tile==6:
                _rect(b,x+k-1,10,3,4,7)
    for tile in (7,8):
        x=tile*18
        _oval(b,x+2,0,14,15,3)
        _rect(b,x+8,9,3,8,9)
        _oval(b,x+5,2+(tile==7),8,10,12)
        _oval(b,x+7,3,4,8,9)
        _rect(b,x+8,6,2,4,10)
    for tile in (9,10):
        x=tile*18
        _oval(b,x+2,14,14,3,1)
        _oval(b,x+3,tile-8,12,14,11)
        _oval(b,x+5,tile-7,8,10,6)
        _rect(b,x+5,6,8,3,1)
        _rect(b,x+6,7,2,1,15)
        _rect(b,x+11,7,2,1,15)
        for k in (4,8,12):
            _rect(b,x+k,12,2,3+(tile%2),6)
    for k in range(2,16):
        _rect(b,11*18+k,3+abs(9-k)//2,2,2,10)
    _oval(b,12*18+3,1,13,16,14)
    _oval(b,12*18+5,3,9,12,7)
    _rect(b,12*18+9,5,1,8,15)
    for x,y,w,h in ((1,1,6,1),(1,1,1,6),(11,1,6,1),(16,1,1,6),(1,16,6,1),(1,11,1,6),(11,16,6,1),(16,11,1,6)):
        _rect(b,13*18+x,y,w,h,12)
    return b


class DungeonsCYL:
    def __init__(self, splash, A_btn, B_btn, Up_btn, Dwn_btn, L_btn, R_btn, Sel_btn, Audio):
        self._splash=splash
        self._A,self._B,self._U,self._D=A_btn,B_btn,Up_btn,Dwn_btn
        self._L,self._R,self._sel,self._audio=L_btn,R_btn,Sel_btn,Audio
        self._exit=False
        self._view={}
        self._menu=None
        self._hero_bitmap=self._object_bitmap=None
        self._best=0
        try:
            with open('/dungeons.txt','rt') as f:
                self._best=max(0,min(7,int(f.readline())))
        except (OSError,ValueError):
            pass

    def _clear(self):
        while len(self._splash):
            self._splash.pop()
        self._view={}
        gc.collect()

    @staticmethod
    def _find(rows, target):
        for y,row in enumerate(rows):
            for x,c in enumerate(row):
                if c==target:
                    return (x,y)
        return None

    @staticmethod
    def _passable(rows, pos, door_open=False):
        x,y=pos
        return 0<=y<len(rows) and 0<=x<len(rows[y]) and rows[y][x]!='#' and (door_open or rows[y][x]!='E')

    def _save_best(self):
        try:
            with open('/dungeons.tmp','wt') as f:
                f.write(str(self._best))
            os.rename('/dungeons.tmp','/dungeons.txt')
            return True
        except OSError:
            return False

    def _begin(self, number, hearts=MAX_HEARTS):
        self._number,self._rows=number,FLOORS[number][1]
        self._pos=self._find(self._rows,'S')
        self._hearts=min(MAX_HEARTS,max(1,hearts))
        self._boss={'pos':self._find(self._rows,'B'),'hp':4+number,'phase':'hunt','timer':0.7,'target':None}
        self._shades=[{'pos':(x,y),'hp':2,'phase':'hunt','timer':1.1,'target':None} for y,row in enumerate(self._rows) for x,c in enumerate(row) if c=='m']
        self._supplies={(x,y):False for y,row in enumerate(self._rows) for x,c in enumerate(row) if c=='+'}
        self._traps=[(x,y) for y,row in enumerate(self._rows) for x,c in enumerate(row) if c=='X']
        self._elapsed=0.0
        self._walk_from,self._walk_start=self._pos,-1.0
        self._hurt=self._attack_cooldown=self._swing=0.0
        self._facing=0
        self._guard=False
        self._door_open=self._cleared=False
        self._note='A sword / Hold B shield / SEL menu'
        self._note_until=3.0
        self._build_floor()

    def _object(self, tile, pos):
        obj=_grid(self._object_bitmap,self._sprite_palette,tile_width=18,tile_height=18)
        obj[0]=tile
        obj.x=OFFSET_X+pos[0]*18
        obj.y=OFFSET_Y+pos[1]*18
        self._splash.append(obj)
        return obj

    def _build_floor(self):
        self._clear()
        colors=list(INK)
        colors[4],colors[5],colors[6],colors[13]=THEMES[self._number]
        palette=_palette(colors)
        self._sprite_palette=_palette(colors,True)
        for i,b in enumerate(_terrain(self._number)):
            self._splash.append(_grid(b,palette,OFFSET_X,OFFSET_Y+i*18))
        if self._hero_bitmap is None:
            self._hero_bitmap=_hero_art()
            self._object_bitmap=_objects_art()
        self._view['door']=self._object(0,self._find(self._rows,'E'))
        self._view['supplies']=[(pos,self._object(2,pos)) for pos in self._supplies]
        self._view['traps']=[self._object(4,pos) for pos in self._traps]
        self._view['torches']=[]
        for y,row in enumerate(self._rows[:-1]):
            for x,c in enumerate(row):
                if c=='#' and self._rows[y+1][x]!='#' and (x+y)%5==0:
                    self._view['torches'].append(self._object(7,(x,y)))
        self._view['targets']=[self._object(13,self._pos) for _ in range(1+len(self._shades))]
        boss=_grid(_guardian_art(self._number),self._sprite_palette,tile_width=24,tile_height=28)
        self._splash.append(boss)
        self._view['boss']=boss
        self._view['shades']=[self._object(9,s['pos']) for s in self._shades]
        hero=_grid(self._hero_bitmap,_palette(transparent=True),tile_width=16,tile_height=22)
        self._splash.append(hero)
        self._view['hero']=hero
        self._view['sword']=self._object(11,self._pos)
        self._view['shield']=self._object(12,self._pos)
        self._splash.append(_solid(240,24,INK[0]))
        self._splash.append(_solid(234,14,INK[0],3,226))
        self._view['title']=_text(self._splash,'',5,6)
        self._view['status']=_text(self._splash,'',5,18,INK[7])
        self._view['note']=_text(self._splash,'',5,233,INK[10])
        self._sync()

    def _tell(self, text):
        self._note,self._note_until=text,self._elapsed+2.4

    def _move(self, dx, dy):
        if self._hearts<=0 or self._cleared:
            return False
        self._facing=DIRECTIONS.index((dx,dy))
        pos=(self._pos[0]+dx,self._pos[1]+dy)
        if not self._passable(self._rows,pos,self._door_open):
            if self._find(self._rows,'E')==pos:
                self._tell('Gate sealed: defeat the guardian.')
            return False
        if any(e['hp']>0 and e['pos']==pos for e in [self._boss]+self._shades):
            self._tell('Enemy ahead: A strike / B guard.')
            return False
        self._walk_from,self._walk_start=self._pos,self._elapsed
        self._pos=pos
        if pos in self._supplies and not self._supplies[pos]:
            if self._hearts<MAX_HEARTS:
                self._hearts=min(MAX_HEARTS,self._hearts+2)
                self._supplies[pos]=True
                self._audio.play('collect')
                self._tell('Supply cache: +2 hearts.')
            else:
                self._tell('Cache kept for when you need it.')
        if self._rows[pos[1]][pos[0]]=='E' and self._door_open:
            self._cleared=True
            self._best=max(self._best,self._number+1)
            self._audio.play('win')
        return True

    def _strike(self):
        if self._attack_cooldown>0 or self._hearts<=0 or self._cleared:
            return False
        self._attack_cooldown=0.38 if not self._guard else 0.65
        self._swing=0.16
        self._audio.play('strike')
        for enemy in [self._boss]+self._shades:
            distance=abs(self._pos[0]-enemy['pos'][0])+abs(self._pos[1]-enemy['pos'][1])
            if enemy['hp']>0 and distance==1:
                enemy['hp']=max(0,enemy['hp']-(1 if self._guard else 2))
                if enemy['hp']==0:
                    self._audio.play('collect')
                    if enemy is self._boss:
                        self._door_open=True
                        self._tell('Guardian defeated! Find the gold gate.')
        return True

    def _damage(self, amount=1):
        if self._hurt>0 or self._hearts<=0:
            return
        self._hearts=max(0,self._hearts-amount)
        self._hurt=0.9
        self._audio.play('hit')

    def _next_step(self, start, goal):
        # Cardinal BFS gives a legal first step, never a diagonal wall skip.
        todo=[start]
        parent={start:None}
        for pos in todo:
            if pos==goal:
                while parent[pos] is not None and parent[pos]!=start:
                    pos=parent[pos]
                return pos
            for dx,dy in DIRECTIONS:
                p=(pos[0]+dx,pos[1]+dy)
                if p not in parent and self._passable(self._rows,p,False):
                    parent[p]=pos
                    todo.append(p)
        return start

    def _enemy_tick(self, enemy, dt, boss):
        if enemy['hp']<=0:
            return
        enemy['timer']-=dt
        if enemy['timer']>0:
            return
        distance=abs(enemy['pos'][0]-self._pos[0])+abs(enemy['pos'][1]-self._pos[1])
        if enemy['phase']=='windup':
            if self._pos==enemy['target']:
                if self._guard:
                    self._tell('Blocked! Strike during recovery.')
                    self._audio.play('block')
                else:
                    self._damage()
            enemy['phase'],enemy['timer']='recover',0.85 if boss else 1.0
        elif distance==1:
            enemy['phase'],enemy['timer']='windup',0.65 if boss else 0.8
            enemy['target']=self._pos
        else:
            enemy['phase'],enemy['timer']='hunt',0.48 if boss else 0.7
            # Shades stay local; guardians wake within five path steps/tiles.
            if distance <= (6 if boss else 4):
                proposed=self._next_step(enemy['pos'],self._pos)
                occupied=any(e is not enemy and e['hp']>0 and e['pos']==proposed for e in [self._boss]+self._shades)
                if proposed!=self._pos and not occupied:
                    enemy['pos']=proposed

    def _trap_phase(self):
        phase=self._elapsed%3.2
        return 4 if phase<1.8 else 5 if phase<2.5 else 6

    def _tick(self, dt):
        if self._hearts<=0 or self._cleared:
            return
        dt=min(dt,0.1)
        self._elapsed+=dt
        self._hurt=max(0,self._hurt-dt)
        self._attack_cooldown=max(0,self._attack_cooldown-dt)
        self._swing=max(0,self._swing-dt)
        self._enemy_tick(self._boss,dt,True)
        for enemy in self._shades:
            self._enemy_tick(enemy,dt,False)
        if self._trap_phase()==6 and self._pos in self._traps:
            self._damage()

    def _sync(self):
        v=self._view
        hero=v['hero']
        progress=min(1.0,(self._elapsed-self._walk_start)/0.13)
        px=self._walk_from[0]+(self._pos[0]-self._walk_from[0])*progress
        py=self._walk_from[1]+(self._pos[1]-self._walk_from[1])*progress
        _place(hero,OFFSET_X+int(px*18)+1,OFFSET_Y+int(py*18)-4)
        _tile(hero,self._facing*3+(1+int(self._elapsed*10)%2 if progress<1 else 0))
        _hide(hero,self._hurt>0 and int(self._elapsed*12)%2==0)
        frame=int(self._elapsed*3)%2
        for enemy,obj,target in zip([self._boss]+self._shades,[v['boss']]+v['shades'],v['targets']):
            is_boss=enemy is self._boss
            _place(obj,OFFSET_X+enemy['pos'][0]*18-(3 if is_boss else 0),OFFSET_Y+enemy['pos'][1]*18-(10 if is_boss else 0))
            _hide(obj,enemy['hp']<=0)
            _tile(obj,(2 if enemy['phase']=='windup' else frame) if is_boss else 9+frame)
            _hide(target,enemy['hp']<=0 or enemy['phase']!='windup')
            if not target.hidden:
                _place(target,OFFSET_X+enemy['target'][0]*18,OFFSET_Y+enemy['target'][1]*18)
        _tile(v['door'],1 if self._door_open else 0)
        for pos,obj in v['supplies']:
            _tile(obj,3 if self._supplies[pos] else 2)
        for obj in v['torches']:
            _tile(obj,7+frame)
        for obj in v['traps']:
            _tile(obj,self._trap_phase())
        for name,visible in (('sword',self._swing>0),('shield',self._guard)):
            obj=v[name]
            _hide(obj,not visible)
            _place(obj,hero.x+(5 if name=='sword' else -4),hero.y+(1 if name=='sword' else 6))
        _set(v['title'],'%d/7 %s' % (self._number+1,FLOORS[self._number][0]))
        state='GATE OPEN' if self._door_open else 'GUARDIAN %d' % self._boss['hp']
        _set(v['status'],'HP %d/%d  %s' % (self._hearts,MAX_HEARTS,state))
        note=self._note if self._elapsed<self._note_until else ('Find the glowing gate.' if self._door_open else 'A sword / Hold B shield / SEL menu')
        _set(v['note'],note)

    def _prepare_menu(self):
        if self._menu is not None:
            return
        group=displayio.Group(x=8,y=43)
        for y in range(0,180,18):
            group.append(_solid(224,18,INK[0],y=y))
        group.append(_solid(216,2,INK[9],4,3))
        title=_text(group,'DUNGEONS',10,20,INK[10])
        detail=_text(group,'',10,42,INK[7])
        rows=[_text(group,'',12,72+i*22) for i in range(4)]
        _text(group,'A choose / B or SEL back',10,166,INK[7])
        self._menu=(group,title,detail,rows)

    def _choose(self, title, items, detail=''):
        self._prepare_menu()
        group,heading,info,rows=self._menu
        _set(heading,title)
        _set(info,detail)
        choice,dirty,last=0,True,time.monotonic()
        a_was,b_was,s_was=not self._A.value,not self._B.value,not self._sel.value
        self._splash.append(group)
        try:
            while not self._exit:
                now=time.monotonic()
                if not self._U.value and not self._D.value:
                    self._exit=True
                    break
                if now-last>0.18:
                    delta=-1 if not self._U.value else 1 if not self._D.value else 0
                    if delta:
                        choice=(choice+delta)%len(items)
                        last,dirty=now,True
                if dirty:
                    for i,obj in enumerate(rows):
                        obj.hidden=i>=len(items)
                        if i<len(items):
                            _set(obj,('> ' if i==choice else '  ')+items[i])
                            obj.color=INK[10] if i==choice else INK[8]
                    dirty=False
                a,b,s=not self._A.value,not self._B.value,not self._sel.value
                if a and not a_was:
                    return choice
                if (b and not b_was) or (s and not s_was):
                    return -1
                a_was,b_was,s_was=a,b,s
                time.sleep(0.025)
        finally:
            self._splash.remove(group)
            gc.collect()
        return -1

    def _pause(self):
        result=self._choose('DUNGEONS / BEST %d' % self._best,('Resume','Retry this floor','Save best','Leave game'),BOSSES[self._number])
        if result==1:
            return 'retry'
        if result==2:
            self._tell('Best saved.' if self._save_best() else 'Save failed: USB/read-only/full.')
        if result==3:
            self._exit=True
        return None

    def _play_floor(self, number, hearts=MAX_HEARTS):
        self._begin(number,hearts)
        last=last_move=time.monotonic()
        a_was,s_was=not self._A.value,not self._sel.value
        self._walking=False
        while not self._exit and self._hearts>0 and not self._cleared:
            now=time.monotonic()
            dt,last=now-last,now
            if not self._U.value and not self._D.value:
                self._exit=True
                break
            s_down=not self._sel.value
            if s_down and not s_was:
                result=self._pause()
                if result=='retry':
                    self._begin(number)
                last=last_move=time.monotonic()
                a_was,s_was=not self._A.value,not self._sel.value
                continue
            self._guard=not self._B.value
            a_down=not self._A.value
            if a_down and not a_was:
                self._strike()
            self._walking=False
            if now-last_move>(0.24 if self._guard else 0.15):
                direction=1 if not self._L.value else 2 if not self._R.value else 3 if not self._U.value else 0 if not self._D.value else None
                if direction is not None:
                    self._walking=self._move(*DIRECTIONS[direction])
                    last_move=now
            self._tick(dt)
            self._sync()
            a_was,s_was=a_down,s_down
            time.sleep(0.025)
        return self._cleared,self._hearts

    def Game(self):
        self._exit=False
        self._prepare_menu()
        self._begin(0)
        choice=self._choose('DUNGEONS: CAN YOU LEAVE?',('Enter the dungeon','Leave game'),'A sword / B shield / 7 floors')
        if choice!=0:
            self._exit=True
        number,hearts=0,MAX_HEARTS
        while not self._exit:
            won,hearts=self._play_floor(number,hearts)
            if self._exit:
                break
            if not won:
                self._audio.play('lose')
                if self._choose('FALLEN, NOT FORGOTTEN',('Retry this floor','Leave game'),'Retry restores all six hearts.')!=0:
                    break
                hearts=MAX_HEARTS
            else:
                saved=self._save_best()
                detail='Best recorded / +2 hearts.' if saved else 'Best in memory; USB save failed.'
                number+=1
                if number==len(FLOORS):
                    if self._choose('THE LAST GATE OPENS',('Play again','Leave game'),detail)!=0:
                        break
                    number,hearts=0,MAX_HEARTS
                else:
                    if self._choose('FLOOR CLEARED',('Descend to next floor','Leave game'),detail)!=0:
                        break
                    hearts=min(MAX_HEARTS,hearts+2)
        self._clear()
        self._menu=self._hero_bitmap=self._object_bitmap=None
        gc.collect()
        return True
