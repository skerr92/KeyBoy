"""Deterministic player policy using only legal Ironbound actions."""

def complete(g,m):
    for step in range(1000):
     if g._hull<=0:raise Exception(('died',g._mission,step,g._pos))
     alive=[e for e in g._enemies if e['hp']>0]
     if not alive:
      kind=m.MISSIONS[g._mission-1][1]
      if kind=='relay' and g._relay<2:
       if g._interact():continue
       goal=(4,3)
      elif kind=='salvage' and len(g._salvage)<2:goal=next(p for p in ((3,2),(5,5)) if p not in g._salvage)
      else:goal=(7,0)
      path=g._path(g._pos,goal)
      assert path,(g._mission,goal)
      p=path[0];g._move(p[0]-g._pos[0],p[1]-g._pos[1])
     else:
      targets=g._targets()
      if g._hull<=g._capacity-7 and g._kits:g._repair()
      elif g._energy==3 and any(g._distance(g._pos,e['pos'])<=2 and g._line(g._pos,e['pos']) for e in alive):g._pulse()
      elif targets:
       # Take the safest shot after excluding a target killed by the shot.
       target=min(targets,key=lambda i:g._enemies[i]['hp'])
       predicted=sum(max(0,(4 if e['kind']==3 else 3 if e['kind']==2 else 2)-g._armor-int(g._cover(g._pos))) for i,e in enumerate(g._enemies) if e['hp']>0 and e['intent']=='fire' and e['target']==g._pos and not(i==target and e['hp']<=g._attack+(2 if g._weapon and g._energy else 0)))
       if predicted<=1 or (predicted<=3 and g._hull>8):g._fire(target)
       else:g._guard()
      else:
       occupied=[e['pos'] for e in alive]
       candidates=[]
       for y in range(8):
        for x in range(8):
         p=(x,y)
         if g._blocked(p) or p in occupied or p==(7,0):continue
         if any(g._distance(p,e['pos'])<=2 and g._line(p,e['pos']) for e in alive):
          path=g._path(g._pos,p,occupied)
          if path:candidates.append((len(path)-int(g._cover(p)),len(path),path))
       if candidates:
        path=min(candidates,key=lambda v:(v[0],v[1]))[2];p=path[0]
        g._move(p[0]-g._pos[0],p[1]-g._pos[1])
       else:g._guard()
     g._sync()
     if g._extracted:break
    else:raise Exception(('stuck',g._mission,g._pos,[(e['pos'],e['hp']) for e in alive]))
    return step
