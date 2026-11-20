import sys, json; sys.path.insert(0,'tmp/d2'); import d2lib as L
b=L.Board()
FIX=[('RX12',3.0,69.65,90),('RX5',7.9,69.65,90),('Q51',2.68,75.6,180),('Q52',7.43,75.6,180)]
rm=set()
for ref,x,y,r in FIX:
    g=L.part_geom(ref,x,y,r); res=b.check(g)
    print(ref,'check',res if res is None else [tuple(round(c,2) for c in b.gvias[i].centroid.coords[0]) for i in res])
    if res: rm|=set(res)
    b.placed.append(g)
S=(7.4,77.6,24,84.5)
plan=[dict(ref='CDG12',region=S,attract={'P12_DG':[(4.16,76.47)]}),dict(ref='RDG12',region=S),
      dict(ref='CDG5',region=S,attract={'P5_DG':[(8.9,76.47)]}),dict(ref='RDG5',region=S)]
res=L.place(b,plan,step=0.2)
for r in res:
    if r[1]: rm|=set(r[2])
print('remove GND vias',[tuple(round(c,2) for c in b.gvias[i].centroid.coords[0]) for i in sorted(rm)])
L.dump(b,'tmp/d2/placed_bl.json')
