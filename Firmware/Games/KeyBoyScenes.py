# SPDX-License-Identifier: MIT
"""Small retained drawing and modal helpers for the puzzle and racing games."""
import displayio
import terminalio
import time
import os
from adafruit_display_text import label

INK=(0x101E32,0x20364E,0x38586A,0x67899A,0xA9D6DB,0xF4E3B1,0xF2BD68,0xCF8154,
     0x85523F,0x553B44,0xBA566E,0xE8929A,0x315D50,0x5C9364,0xA3BE79,0xCDC2DB)


def palette(colors=INK,transparent=False):
    p=displayio.Palette(len(colors))
    for i,color in enumerate(colors):p[i]=color
    if transparent:p.make_transparent(0)
    return p


def rect(b,x,y,w,h,color):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):b[xx,yy]=color


def oval(b,x,y,w,h,color):
    for yy in range(max(0,y),min(b.height,y+h)):
        for xx in range(max(0,x),min(b.width,x+w)):
            if (2*(xx-x)-w+1)**2*h*h+(2*(yy-y)-h+1)**2*w*w<=w*w*h*h:b[xx,yy]=color


def text(group,value,x,y,color=5):
    item=label.Label(terminalio.FONT,text=value,color=INK[color],x=x,y=y)
    group.append(item);return item


def set_text(item,value):
    if item.text!=value:item.text=value


class Canvas:
    width=height=240
    def __init__(self):
        self.strips=[displayio.Bitmap(240,16,16) for _ in range(15)]
        self.shader=palette()
    def __setitem__(self,pos,color):
        x,y=pos;self.strips[y//16][x,y%16]=color
    def fill(self,color):
        for b in self.strips:b.fill(color)
    def attach(self,group):
        for i,b in enumerate(self.strips):group.append(displayio.TileGrid(b,pixel_shader=self.shader,y=i*16))


def save(path,data):
    try:
        with open(path+'.tmp','wt') as f:f.write(data)
        os.rename(path+'.tmp',path)
        return True
    except OSError:return False


class Panel:
    def __init__(self,root,buttons,audio):
        self.root,self.buttons,self.audio=root,buttons,audio
        self.group=displayio.Group()
        p=palette((INK[0],INK[3]))
        for i in range(11):
            b=displayio.Bitmap(216,16,2)
            rect(b,0,0,1,16,1);rect(b,215,0,1,16,1)
            if i==0:rect(b,0,0,216,1,1)
            if i==10:rect(b,0,15,216,1,1)
            self.group.append(displayio.TileGrid(b,pixel_shader=p,x=12,y=32+i*16))
        self.title=text(self.group,'',23,49,6)
        self.rows=[text(self.group,'',30,75+i*22) for i in range(5)]
        self.detail=text(self.group,'',22,188,4)
        self.hint=text(self.group,'A choose  B back',22,201,3)

    def show(self,title,options,details=(),selected=0):
        selected=max(0,min(len(options)-1,selected))
        self.title.text=title
        self.root.append(self.group)
        a,b,u,d,l,r,sel=self.buttons
        held,back,select=not a.value,not b.value,not sel.value
        previous=-1;direction=0;repeat=0
        try:
            while True:
                now=time.monotonic()
                if not u.value and not d.value:return -2
                if selected!=previous:
                    start=max(0,min(selected-2,len(options)-5))
                    for i,row in enumerate(self.rows):
                        index=start+i
                        row.text=('> ' if index==selected else '  ')+options[index] if index<len(options) else ''
                        row.color=INK[6 if index==selected else 5]
                    self.detail.text=details[selected] if details else ''
                    previous=selected
                delta=-1 if not u.value else 1 if not d.value else 0
                if delta and (delta!=direction or now>=repeat):
                    selected=(selected+delta)%len(options)
                    repeat=now+(.3 if delta!=direction else .16)
                    self.audio.play('move')
                direction=delta
                pressed=not a.value;cancel=not b.value;select_now=not sel.value
                if pressed and not held:
                    self.audio.play('select');return selected
                if (cancel and not back) or (select_now and not select):return -1
                held,back,select=pressed,cancel,select_now
                time.sleep(.025)
        finally:self.root.remove(self.group)
