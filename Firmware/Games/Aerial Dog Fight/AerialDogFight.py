# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Four coastal sorties, sector refits, fuel-limited boost and a persistent ace.

D-pad flies, A fires, B boosts, SEL pauses. Up+Down returns to the launcher.
All projectiles and planes are allocated before the sortie, never during firing.
"""
import random
import time
import displayio
from adafruit_display_text import label
import terminalio
from GameMenu import PauseMenu, save_high_score
from KeyBoyArcade import Scenery, actor, choose


class AerialDogFight:
    def __init__(self,splash,A_btn,B_btn,Up_btn,Dwn_btn,L_btn,R_btn,Sel_btn,Audio):
        self._splash=splash
        self._A,self._B,self._U,self._D,self._L,self._R=A_btn,B_btn,Up_btn,Dwn_btn,L_btn,R_btn
        self._pause_menu=PauseMenu(splash,Sel_btn,A_btn,Up_btn,Dwn_btn)
        self._audio=Audio
        self._exit=False
        self._scenery=None

    def _clear(self):
        while len(self._splash):self._splash.pop()

    @staticmethod
    def _hit(ax,ay,aw,ah,bx,by,bw,bh):
        return ax<bx+bw and ax+aw>bx and ay<by+bh and ay+ah>by

    def _setup_sortie(self):
        self._clear()
        if self._scenery is None:self._scenery=Scenery()
        self._scenery.draw('flight')
        self._scenery.attach(self._splash)
        self._player=actor('plane',24,26)
        self._player.x,self._player.y=108,190
        self._splash.append(self._player)
        self._px,self._py=108.0,190.0
        self._score,self._hull,self._wave,self._spawned=0,4,1,0
        self._clock,self._shot,self._spawn,self._hurt=0.0,-1.0,-1.0,0.0
        self._fuel,self._weapon=3.0,0
        self._armored=False
        self._ace_spawned,self._ace_dead=False,False
        self._enemies=[]
        for i in range(7):
            ace=i==6
            grid=actor('ace' if ace else 'raider',32 if ace else 24,34 if ace else 26)
            grid.hidden=True;self._splash.append(grid)
            # sprite, x, y, horizontal speed, health, next shot, ace
            self._enemies.append([grid,0.0,0.0,0,0,0.0,ace])
        self._bullets=[]
        for i in range(28):
            grid=actor('spark',4,8)
            grid.hidden=True;self._splash.append(grid)
            # sprite, x, y, vx, vy, hostile; 12 player / 16 hostile slots
            self._bullets.append([grid,0.0,0.0,0.0,0.0,i>=12])
        self._hud=label.Label(terminalio.FONT,text='',color=0xEAE1BC,x=5,y=10)
        self._hint=label.Label(terminalio.FONT,text='',color=0xADD2CE,x=5,y=22)
        self._splash.append(self._hud);self._splash.append(self._hint)
        self._sync()

    def _sync(self):
        text='S%d HP%d SECTOR%d/4' % (self._score,self._hull,self._wave)
        if self._hud.text!=text:self._hud.text=text
        ace=self._enemies[6]
        text=('ACE HP%d / DODGE THE SPREAD' % ace[4] if not ace[0].hidden else
              'BOOST %d%% / %s' % (int(self._fuel*100/3),'TWIN' if self._weapon==0 else 'RAPID'))
        if self._hint.text!=text:self._hint.text=text

    def _fire(self,x,y,hostile=False,spread=0):
        for shot in self._bullets:
            if shot[5]==hostile and shot[0].hidden:
                shot[0].hidden=False
                shot[1],shot[2],shot[3],shot[4]=float(x),float(y),spread,125 if hostile else -250
                shot[0].x,shot[0].y=int(x),int(y)
                return True
        return False

    def _spawn_enemy(self,ace=False):
        slots=self._enemies[6:] if ace else self._enemies[:6]
        for enemy in slots:
            if enemy[0].hidden:
                enemy[0].hidden=False
                enemy[1],enemy[2]=float(random.randint(15,195)),-34.0
                enemy[3]=random.choice((-28,28))
                enemy[4]=20 if ace else 1+(self._wave>=3)
                enemy[5]=self._clock+1.6
                enemy[0].x,enemy[0].y=int(enemy[1]),-34
                return True
        return False

    def _damage(self):
        if self._clock>=self._hurt:
            self._hull-=1
            self._hurt=self._clock+1.1
            self._audio.play('hit')

    def _step(self,dt,mx=0,my=0,fire=False,boost=False):
        dt=min(.05,max(0,dt))
        self._clock+=dt
        boosting=boost and self._fuel>dt
        self._fuel=max(0,self._fuel-dt) if boosting else min(3,self._fuel+dt*.5)
        speed=(145 if boosting else 80) if self._armored else (180 if boosting else 95)
        if mx and my:speed*=.7071
        self._px=max(0,min(216,self._px+mx*speed*dt))
        self._py=max(30,min(214,self._py+my*speed*dt))
        self._player.x,self._player.y=int(self._px),int(self._py)
        self._player.hidden=self._clock<self._hurt and int(self._clock*12)%2==0
        if fire and self._clock-self._shot >= (.24 if self._weapon==0 else .13):
            fired=self._fire(self._px+5,self._py-5)
            if self._weapon==0:self._fire(self._px+16,self._py-5)
            if fired:self._audio.play('shoot');self._shot=self._clock
        target=4+self._wave*2
        if self._spawned<target and self._clock-self._spawn>.95:
            if self._spawn_enemy():self._spawned+=1;self._spawn=self._clock
        for enemy in self._enemies:
            sprite=enemy[0]
            if sprite.hidden:continue
            enemy[1]+=enemy[3]*dt
            enemy[2]+=((0 if enemy[2]>=53 else 45) if enemy[6] else 32+self._wave*8)*dt
            if enemy[1]<5:enemy[1]=5;enemy[3]=abs(enemy[3])
            if enemy[1]>203:enemy[1]=203;enemy[3]=-abs(enemy[3])
            sprite.x,sprite.y=int(enemy[1]),int(enemy[2])
            if self._clock>=enemy[5] and sprite.y>27:
                self._fire(sprite.x+12,sprite.y+25,True)
                if enemy[6]:
                    self._fire(sprite.x+12,sprite.y+25,True,-45)
                    self._fire(sprite.x+12,sprite.y+25,True,45)
                enemy[5]=self._clock+(.8 if enemy[6] else 1.6)
            if sprite.y>240:sprite.hidden=True
            if self._hit(self._px+4,self._py+4,16,18,sprite.x,sprite.y,32 if enemy[6] else 24,34 if enemy[6] else 26):
                self._damage()
                if not enemy[6]:sprite.hidden=True
        for shot in self._bullets:
            sprite=shot[0]
            if sprite.hidden:continue
            shot[1]+=shot[3]*dt;shot[2]+=shot[4]*dt
            sprite.x,sprite.y=int(shot[1]),int(shot[2])
            if sprite.y<27 or sprite.y>240 or sprite.x<0 or sprite.x>239:
                sprite.hidden=True;continue
            if shot[5]:
                if self._hit(sprite.x,sprite.y,4,8,self._px+4,self._py+4,16,18):
                    sprite.hidden=True;self._damage()
            else:
                for enemy in self._enemies:
                    e=enemy[0]
                    if not e.hidden and self._hit(sprite.x,sprite.y,4,8,e.x,e.y,32 if enemy[6] else 24,34 if enemy[6] else 26):
                        sprite.hidden=True;enemy[4]-=1
                        if enemy[4]<=0:
                            e.hidden=True;self._score+=1000 if enemy[6] else 100
                            self._audio.play('collect')
                            if enemy[6]:self._ace_dead=True
                        break
        self._sync()
        if self._hull<=0:return 'lost'
        if self._ace_dead:return 'won'
        if self._spawned>=target and all(e[0].hidden for e in self._enemies):
            if self._wave==4:
                if not self._ace_spawned:self._spawn_enemy(True);self._ace_spawned=True
            else:return 'sector'
        return None

    def _refit(self):
        for shot in self._bullets:shot[0].hidden=True
        choice=choose(self._splash,'SECTOR REFIT',('Twin cannons','Rapid cannon','Repair +2 hull'),(self._A,self._U,self._D))
        if choice<0:self._exit=True
        elif choice<2:self._weapon=choice
        else:self._hull=min(6,self._hull+2)
        self._fuel=3
        self._wave+=1;self._spawned=0;self._spawn=self._clock

    def _run(self):
        self._setup_sortie()
        choice=choose(self._splash,'CHOOSE LOADOUT',('Twin cannons','Rapid cannon','Armor +2 HP / slower'),(self._A,self._U,self._D))
        if choice<0:self._exit=True;return None
        self._weapon=1 if choice==1 else 0
        if choice==2:self._hull=6;self._armored=True
        last=time.monotonic()
        while not self._exit:
            now=time.monotonic();dt=now-last;last=now
            if not self._U.value and not self._D.value:self._exit=True;break
            if self._pause_menu.pressed():
                if self._pause_menu.open('DOG FIGHT',self._score,'/dogfight.txt'):self._exit=True
                last=time.monotonic();continue
            result=self._step(dt,int(not self._R.value)-int(not self._L.value),
                              int(not self._D.value)-int(not self._U.value),not self._A.value,not self._B.value)
            if result=='sector':self._refit();last=time.monotonic()
            elif result:
                save_high_score('/dogfight.txt',self._score)
                self._audio.play('win' if result=='won' else 'lose')
                return result=='won'
            time.sleep(max(.001,.03-(time.monotonic()-now)))
        return None

    def Game(self):
        while not self._exit:
            result=self._run()
            if result is None:break
            choice=choose(self._splash,'SKIES CLEARED' if result else 'PLANE DOWN',('Fly again','Return to launcher'),(self._A,self._U,self._D))
            if choice!=0:self._exit=True
        self._clear()
        return True
