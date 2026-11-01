# SPDX-License-Identifier: MIT
"""The KeyBoy neon arcade shelf. Released completely before a game loads."""
import time
import displayio
import terminalio
from adafruit_display_text import label

NAMES=('Loose Cows',"Sprite's Journey",'Aerial Dog Fight','Dungeons CYL',
       'Lantern Acre','Wildspark','Ironbound','Last Beacon','Clockwork Courier','Drift Circuit')
GENRES=('RANCH ARCADE','MOONLIT PLATFORMER','COASTAL DOGFIGHT','DUNGEON ADVENTURE',
        'COZY FARM LIFE','CREATURE QUEST','MECH TACTICS','EXTRACTION SHOOTER','CLOCKWORK PUZZLER','ARCADE MOTORSPORT')
TITLES=(('Loose','Cows'),("Sprite's",'Journey'),('Aerial','Dog Fight'),('Dungeons','Can You Leave?'),
        ('Lantern','Acre'),('Wildspark',''),('Ironbound',''),('Last','Beacon'),('Clockwork','Courier'),('Drift','Circuit'))
COLORS=(0x0A1429,0x142641,0x203E58,0x345E72,0x62C6CF,0xB5EDF0,0xFFF0CF,0xF9C46B,
        0xD98562,0xBA526D,0x734C80,0xAB8BC2,0x376D62,0x74AD7F,0xBDCD8C,0x597998)
ACCENTS=(7,5,4,11,14,8,15,9,7,4)


def rect(b,x,y,w,h,c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):b[xx,yy]=c


def oval(b,x,y,w,h,c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):
            if (2*(xx-x)-w+1)**2*h*h+(2*(yy-y)-h+1)**2*w*w<=w*w*h*h:b[xx,yy]=c


def palette(transparent=False):
    p=displayio.Palette(16)
    for i,c in enumerate(COLORS):p[i]=c
    if transparent:p.make_transparent(0)
    return p


class Canvas:
    width=height=240
    def __init__(self):
        self.strips=[displayio.Bitmap(240,16,16) for _ in range(15)]
    def __setitem__(self,pos,c):
        x,y=pos;self.strips[y//16][x,y%16]=c


def icon(b,game):
    """Draw a miniature game emblem without importing any game or asset library."""
    b.fill(0)
    oval(b,3,38,42,8,1)
    if game==0:
        oval(b,4,16,34,22,6);oval(b,9,19,12,11,8)
        rect(b,9,34,5,8,8);rect(b,29,34,5,8,8)
        oval(b,27,11,18,22,7);rect(b,28,8,4,7,6);rect(b,40,8,4,7,6)
        rect(b,38,17,3,4,0);oval(b,35,25,12,7,8)
    elif game==1:
        oval(b,1,16,21,21,4);oval(b,26,16,21,21,4)
        oval(b,5,17,15,13,5);oval(b,28,17,15,13,5)
        rect(b,19,8,12,12,7);rect(b,17,5,15,6,6)
        rect(b,27,12,3,3,0);rect(b,18,22,13,16,12)
        rect(b,20,22,9,5,14);rect(b,18,37,5,7,7);rect(b,28,37,5,7,7)
        rect(b,7,5,1,7,7);rect(b,4,8,7,1,7)
    elif game in (2,7):
        c=4 if game==2 else 9
        for y in range(10,33):
            span=max(3,21-abs(y-24)*2)
            rect(b,24-span,y,span*2,1,c)
        rect(b,21,3,6,38,5 if game==2 else 8)
        rect(b,22,11,4,10,2);rect(b,13,25,4,14,6);rect(b,32,25,4,14,6)
        rect(b,14,39,2,6,8);rect(b,33,39,2,6,8)
        rect(b,18,35,13,4,c)
    elif game==3:
        oval(b,4,11,28,32,10);oval(b,7,13,22,25,11)
        rect(b,17,14,3,24,5);rect(b,8,23,20,3,5)
        for y in range(5,31):rect(b,36-y//5,y,5,1,6)
        rect(b,25,29,15,4,7);rect(b,29,32,5,11,8)
    elif game==4:
        rect(b,7,20,33,24,7);rect(b,9,24,29,17,8)
        for y in range(6,23):rect(b,24-(y-5),y,(y-5)*2,1,9)
        rect(b,13,25,8,9,5);rect(b,28,29,8,15,1)
        rect(b,16,25,2,9,6);rect(b,13,29,8,2,6)
        rect(b,35,7,5,12,8);rect(b,38,1,3,4,15)
        rect(b,2,43,44,3,13)
    elif game==5:
        oval(b,7,14,34,30,8);oval(b,10,13,28,25,7)
        for x in (8,31):
            rect(b,x,4,8,17,9);rect(b,x+2,6,4,11,8)
        oval(b,13,29,23,13,6)
        rect(b,15,20,4,6,0);rect(b,30,20,4,6,0)
        rect(b,15,20,2,2,6);rect(b,30,20,2,2,6)
        rect(b,7,40,10,5,8);rect(b,31,40,10,5,8)
    elif game==8:
        rect(b,10,5,26,19,8);rect(b,12,6,22,15,7)
        rect(b,15,11,16,7,2);rect(b,18,12,3,4,5);rect(b,26,12,3,4,5)
        rect(b,13,24,21,17,3);rect(b,16,27,15,12,7)
        rect(b,22,27,3,12,6);rect(b,16,32,15,2,8)
        rect(b,7,26,6,12,15);rect(b,34,26,6,12,15)
        rect(b,12,41,9,5,8);rect(b,27,41,9,5,8)
    elif game==9:
        rect(b,4,13,6,10,0);rect(b,38,13,6,10,0)
        rect(b,4,31,6,10,0);rect(b,38,31,6,10,0)
        rect(b,10,4,28,39,8);rect(b,12,6,24,36,7)
        rect(b,14,13,20,10,4);rect(b,16,14,16,6,5)
        rect(b,21,25,6,15,6);rect(b,6,40,36,5,6)
        rect(b,13,5,6,4,6);rect(b,29,5,6,4,6)
    else:
        rect(b,15,4,18,12,3);rect(b,18,8,12,4,8)
        rect(b,11,17,27,18,15);rect(b,16,20,17,7,2)
        rect(b,20,21,9,3,4);rect(b,3,16,8,20,3);rect(b,38,16,8,25,3)
        rect(b,12,34,9,11,3);rect(b,29,34,9,11,3)
        rect(b,9,43,14,4,15);rect(b,27,43,14,4,15)


class Launcher:
    def __init__(self,splash,buttons,audio,selected=0):
        self.splash,self.buttons,self.audio=splash,buttons,audio
        self.selected=selected%len(NAMES)
        self.armed=False;self.a_was=False;self.direction=0;self.next_move=0
        self.frame=-1
        self.group=displayio.Group()
        self.background=Canvas();b=self.background
        rect(b,0,0,240,240,0)
        rect(b,0,35,240,16,1)
        for i in range(24):
            h=4+(i*13)%17
            rect(b,i*11,50-h,8,h,2)
            rect(b,i*11+2,52-h,2,2,4 if i%3==0 else 3)
        rect(b,8,51,224,1,4)
        # Hand-built bevelled logo; no additional font assets or giant bitmap.
        glyphs=('11121418141211','1F10101E10101F','11110A04040404',
                '1E11111E11111E','0E11111111110E','11110A04040404')
        for layer,dx,dy in ((0,3,3),(1,0,0)):
            for letter,rows in enumerate(glyphs):
                for y in range(7):
                    bits=int(rows[y*2:y*2+2],16)
                    for x in range(5):
                        if bits&(1<<(4-x)):
                            rect(b,59+letter*21+x*3+dx,9+y*3+dy,3,3,10 if layer==0 else 6 if y<3 else 7 if y<5 else 8)
        rect(b,8,57,224,65,2);rect(b,9,58,222,63,1)
        # Perspective floor under the selected game's floating emblem.
        for y in (102,110,120):rect(b,10,y,220,1,2)
        for x in range(14,232,26):
            for y in range(99,121):
                xx=120+(x-120)*(y-83)//37
                rect(b,xx,y,1,1,2)
        for i,strip in enumerate(b.strips):
            self.group.append(displayio.TileGrid(strip,pixel_shader=palette(),y=i*16))
        p=palette(True)
        self.stars=[]
        star=displayio.Bitmap(3,3,16);rect(star,1,0,1,3,5);rect(star,0,1,3,1,5)
        for x,y in ((13,9),(35,28),(218,8),(202,30)):
            grid=displayio.TileGrid(star,pixel_shader=p,x=x,y=y)
            self.group.append(grid);self.stars.append((grid,x,y))
        self.shine=displayio.TileGrid(displayio.Bitmap(12,1,16),pixel_shader=p,x=8,y=51)
        self.shine.bitmap.fill(6);self.group.append(self.shine)
        self.art=displayio.Bitmap(48,48,16)
        self.emblem=displayio.TileGrid(self.art,pixel_shader=p,x=19,y=67)
        self.group.append(self.emblem)
        self.genre=self._text('',80,69,4)
        self.title1=self._text('',80,88,6)
        self.title2=self._text('',80,103,6)
        self.tag=self._text('PICK YOUR NEXT ADVENTURE',12,42,5)
        self.page=self._text('',184,131,15)
        self._text('GAME LIBRARY',12,131,15)
        highlight=displayio.Bitmap(224,19,16)
        rect(highlight,0,0,224,19,3);rect(highlight,1,1,222,17,2)
        rect(highlight,0,0,3,19,7);rect(highlight,221,0,3,19,7)
        self.cursor=displayio.TileGrid(highlight,pixel_shader=p,x=8,y=138)
        self.group.append(self.cursor)
        self.rows=[self._text('',34,148+i*20,5) for i in range(4)]
        self.numbers=[self._text('',16,148+i*20,15) for i in range(4)]
        self.arrow=self._text('>',214,148,7)
        self._text('U/D PICK  L/R PAGE',12,222,15)
        self.footer=self._text('A  PLAY',174,222,7)
        self._text('TEN WORLDS. ONE KEYBOY.',48,236,3)
        self.select(self.selected,False)
        splash.append(self.group)

    def _text(self,text,x,y,color):
        item=label.Label(terminalio.FONT,text=text,color=COLORS[color],x=x,y=y)
        self.group.append(item);return item

    def select(self,index,sound=True):
        self.selected=index%len(NAMES)
        start=(self.selected//4)*4
        for i,row in enumerate(self.rows):
            row.text=NAMES[start+i] if start+i<len(NAMES) else ''
            row.color=COLORS[6 if start+i==self.selected else 15]
            self.numbers[i].text=str(start+i+1) if start+i<len(NAMES) else ''
        self.page.text='%d / %d' % (start//4+1,(len(NAMES)+3)//4)
        self.cursor.y=138+(self.selected%4)*20
        self.arrow.y=148+(self.selected%4)*20
        self.genre.text=GENRES[self.selected]
        self.genre.color=COLORS[ACCENTS[self.selected]]
        self.title1.text,self.title2.text=TITLES[self.selected]
        icon(self.art,self.selected)
        if sound:self.audio.play('move')

    def animate(self,now):
        frame=int(now*8)
        if frame==self.frame:return
        self.frame=frame
        self.emblem.y=67+(0,0,1,2,2,2,1,0)[frame%8]
        self.shine.x=8+(frame*3)%212
        for i,(star,x,y) in enumerate(self.stars):
            star.hidden=(frame+i*2)%12<3
            star.y=y+(frame//4+i)%2

    def poll(self,now):
        a,b,up,down,left,right,sel=self.buttons
        self.animate(now)
        if not self.armed:
            if all(btn.value for btn in self.buttons[:6]):self.armed=True
            self.a_was=not a.value
            return None
        pressed=not a.value;edge=pressed and not self.a_was;self.a_was=pressed
        direction=0
        if up.value!=down.value:direction=-1 if not up.value else 1
        elif left.value!=right.value:direction=-4 if not left.value else 4
        if direction and (direction!=self.direction or now>=self.next_move):
            if abs(direction)==4:
                page=(self.selected//4+(1 if direction>0 else -1))%((len(NAMES)+3)//4)
                self.select(page*4+min(self.selected%4,len(NAMES)-page*4-1))
            else:self.select(self.selected+direction)
            self.next_move=now+(.32 if direction!=self.direction else .16)
        self.direction=direction
        if edge and all(btn.value for btn in (up,down,left,right)):
            self.audio.play('select')
            self.footer.text='GO!'
            self.genre.text='LOADING ADVENTURE'
            return self.selected
        return None

    def choose(self):
        while True:
            result=self.poll(time.monotonic())
            if result is not None:
                time.sleep(.12)
                self.splash.remove(self.group)
                return result
            time.sleep(.025)
