# SPDX-License-Identifier: MIT
"""Retained, reusable pixel scenery for the three arcade adventures."""
import displayio

COLORS = (0x14283F,0x263D58,0x3C5970,0x638493,0xADD2CE,0xEAE1BC,
          0x234E44,0x39755A,0x78A56A,0xB3CD83,0x614D49,0x956D50,
          0xC49B67,0xEDD49B,0xAB5261,0xF18D72)


def palette(transparent=False):
    p = displayio.Palette(16)
    for i, c in enumerate(COLORS): p[i] = c
    if transparent: p.make_transparent(0)
    return p


def rect(b, x, y, w, h, c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)): b[xx,yy]=c


def oval(b,x,y,w,h,c):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):
            if (2*(xx-x)-w+1)**2*h*h+(2*(yy-y)-h+1)**2*w*w <= w*w*h*h:
                b[xx,yy]=c


class Scenery:
    """One 4-bit scene, split into 1920-byte strips; repaint only between rooms."""
    width=height=240
    def __init__(self):
        self.strips=[displayio.Bitmap(240,16,16) for _ in range(15)]
        self.palette=palette()
    def __setitem__(self,pos,c):
        x,y=pos
        self.strips[y//16][x,y%16]=c
    def attach(self,group):
        for i,b in enumerate(self.strips):
            group.append(displayio.TileGrid(b,pixel_shader=self.palette,y=i*16))
    def draw(self,kind,stage=0):
        for b in self.strips:b.fill(0 if kind=='journey' else 2 if kind=='flight' else 7)
        if kind=='journey':
            rect(self,0,90,240,150,1)
            oval(self,178,33,31,31,4);oval(self,185,29,31,31,0)
            for i in range(65):rect(self,(i*67+13)%240,25+(i*31)%80,1,1,4)
            for i in range(9):
                x=(i*37+stage*9)%240
                rect(self,x,84+i%3*18,8,145,2)
                for y in range(97,207,21):rect(self,x+2,y,3,8,1)
                oval(self,x-17,65+i%3*18,43,22,1)
            for i in range(7):
                x=i*39-8
                rect(self,x,140+i%2*24,5,100,6)
                oval(self,x-12,128+i%2*24,30,18,6)
            rect(self,0,218,240,22,10)
            for i in range(80):rect(self,(i*53)%240,224+(i*17)%16,3,2,11)
        elif kind=='flight':
            for y in range(28,240,16):
                for x in range((y*3)%31,240,41):rect(self,x,y,18,1,3)
            for x,y in ((-21,39),(178,123),(25,188)):
                oval(self,x,y,74,42,4);oval(self,x+7,y+3,60,33,12)
                oval(self,x+13,y+6,48,26,7)
                for i in range(5):oval(self,x+17+i*8,y+9+i%2*5,10,9,6)
            for x,y in ((49,53),(119,175)):
                oval(self,x,y,45,14,3);oval(self,x+3,y-4,37,14,4)
                oval(self,x+9,y-8,19,13,5)
        else:
            for i in range(520):
                x,y=(i*83+19)%240,37+(i*47)%203
                rect(self,x,y,2,1,8 if i%3 else 6)
            rect(self,9,40,222,3,11);rect(self,9,231,222,3,11)
            for x in range(9,234,18):rect(self,x,36,3,10,13);rect(self,x,225,3,10,13)
            rect(self,8,174,58,48,11)
            for y in range(179,221,9):rect(self,10,y,54,1,12)
            for x in (8,64):rect(self,x,174,3,50,13)
            rect(self,8,220,59,3,13)
            rect(self,8,174,16,3,13);rect(self,52,174,15,3,13)
            for x,y in ((11,55),(204,50)):
                rect(self,x+10,y+17,6,26,10);oval(self,x,y,28,29,6)
                oval(self,x+4,y+1,21,20,8)
        hud=38 if kind=='ranch' else 27
        rect(self,0,0,240,hud,0);rect(self,0,hud-1,240,1,3)


def actor(kind, width, height):
    animated=kind in ('hero','cow','rancher')
    b=displayio.Bitmap(width*(2 if animated else 1),height,16)
    if kind=='hero':
        oval(b,0,8,width,10,4);rect(b,5,3,7,7,13)
        rect(b,4,1,8,4,5);rect(b,10,5,2,2,0)
        rect(b,5,10,7,8,7);rect(b,6,10,5,3,9)
        rect(b,4,18,4,4,13);rect(b,10,18,4,4,13)
    elif kind=='cow':
        oval(b,1,3,width-2,height-6,5);oval(b,3,5,7,6,10)
        rect(b,3,height-5,3,5,10);rect(b,width-6,height-5,3,5,10)
        oval(b,width-9,1,9,10,13);rect(b,width-3,4,2,2,0)
        rect(b,width-8,0,2,3,5);rect(b,width-2,0,2,3,5)
    elif kind=='rancher':
        rect(b,5,3,8,9,13);rect(b,3,4,13,3,12);rect(b,6,1,7,4,11)
        rect(b,5,11,8,8,2);rect(b,3,11,3,6,13);rect(b,13,11,3,6,13)
        rect(b,5,18,4,4,10);rect(b,11,18,4,4,10)
    elif kind=='bale':
        rect(b,0,0,width,height,11);rect(b,1,1,width-2,height-2,12)
        for y in range(3,height-2,4):rect(b,2,y,width-4,1,13)
        rect(b,4,0,2,height,10);rect(b,width-6,0,2,height,10)
    elif kind in ('plane', 'raider', 'ace'):
        hull = 4 if kind=='plane' else 15 if kind=='raider' else 12
        center=width//2
        for y in range(2,height-3):
            span=max(2, (width//2-1)-abs(y-height//2)*2)
            rect(b,center-span,y,span*2,1,1)
            rect(b,center-span+1,y,max(1,span*2-2),1,hull)
        rect(b,center-2,0,4,height-1,hull)
        rect(b,center-1,5,2,6,2);rect(b,center-5,height-5,10,2,5)
        for x in (center-7,center+4):
            rect(b,x,height//2-1,3,9,1)
            rect(b,x+1,height//2,1,6,5)
        rect(b,center-width//3,height//2+1,width//3-3,1,5)
        rect(b,center+4,height//2+1,width//3-3,1,5)
        rect(b,center-1,12,2,5,5)
        rect(b,center-2,height-3,4,2,15)
    elif kind=='rope':
        oval(b,0,0,width,height,13);oval(b,2,2,width-4,height-4,0)
        rect(b,width-3,height-4,3,4,12)
    elif kind=='spark':
        oval(b,0,0,width,height,3);oval(b,2,2,width-4,height-4,13)
        rect(b,width//2,1,1,height-2,5)
    else:  # Guardians fill their collision bounds, with horns and visible eyes.
        oval(b,1,4,width-2,height-5,10);oval(b,3,7,width-6,height-11,14)
        rect(b,2,0,4,10,12);rect(b,width-6,0,4,10,12)
        rect(b,5,height//3,4,3,13);rect(b,width-9,height//3,4,3,13)
        rect(b,width//3,height//2,width//3,3,0)
        rect(b,3,height-5,6,5,12);rect(b,width-9,height-5,6,5,12)
    if animated:
        for y in range(height):
            for x in range(width):b[x+width,y]=b[x,y]
        feet=(3,width-6) if kind=='cow' else (4,10) if kind=='hero' else (5,11)
        for i,x in enumerate(feet):
            rect(b,width+x,height-5,4,5,0)
            rect(b,width+x,height-5+i*2,3,3,10 if kind!='hero' else 13)
    return displayio.TileGrid(b,pixel_shader=palette(True),tile_width=width,tile_height=height)


def choose(group, title, options, buttons):
    """Small modal loadout choice; return -1 for the universal exit gesture."""
    import time
    import terminalio
    from adafruit_display_text import label
    a,up,down=buttons
    panel=displayio.Group()
    bitmap=displayio.Bitmap(224,122,1)
    p=displayio.Palette(1);p[0]=COLORS[0]
    panel.append(displayio.TileGrid(bitmap,pixel_shader=p,x=8,y=58))
    panel.append(label.Label(terminalio.FONT,text=title,color=COLORS[13],x=17,y=73))
    rows=[]
    for i,text in enumerate(options):
        row=label.Label(terminalio.FONT,text=text,color=COLORS[5],x=30,y=99+i*23)
        rows.append(row);panel.append(row)
    cursor=label.Label(terminalio.FONT,text='>',color=COLORS[13],x=16,y=99)
    panel.append(cursor);group.append(panel)
    choice,last,held=0,0,not a.value
    try:
        while True:
            now=time.monotonic()
            if not up.value and not down.value:return -1
            if now-last>.18:
                delta=-1 if not up.value else 1 if not down.value else 0
                if delta:
                    choice=(choice+delta)%len(options);last=now;cursor.y=99+choice*23
            pressed=not a.value
            if pressed and not held:return choice
            held=pressed
            time.sleep(.03)
    finally:
        group.remove(panel)
