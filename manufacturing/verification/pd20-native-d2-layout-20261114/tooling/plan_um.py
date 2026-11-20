import sys, json; sys.path.insert(0,'tmp/d2'); import d2lib as L
b=L.Board()
for q in json.load(open('tmp/d2/placed_bl.json')):
    b.placed.append(L.part_geom(q['ref'],*q['at'][:3]))
UM=(36,3,72,28.5)
DG=[(47.8+i*(71.6-47.8)/10,30.6+i*(24.9-30.6)/10) for i in range(11)]
MO=[(49.5,39.5),(51.6,39.6),(30.1,35.1),(25.2,34.8)]
A={'M12_OUT':MO,'M12_DG':DG}
W={'M12_DX':6,'M12_DXA':6,'M12_DXB':6,'M12_OUT':2,'M12_DG':1,'SEQ_PD':3,'SEQ_G':3,'SEQ_Z':2,'SEQ_EN_N':2,'SEQ_RG':2}
order=sys.argv[1].split(',') if len(sys.argv)>1 else ['Q55','RXN3','RXN2','R76','C44','C45','D4','Q9','RSQ3','Q13','RSQ4','D5','RSQ2','Q8','RSQ1','Q7','R81','R82']
plan=[dict(ref=r,region=UM,attract=A|{'P12_OUT':[(64.3,29.8),(63.1,31)]},w=W) for r in order]
res=L.place(b,plan,step=0.5)
rm=set()
for r in res:
    if r[1]: rm|=set(r[2])
print('remove',[tuple(round(c,2) for c in b.gvias[i].centroid.coords[0]) for i in sorted(rm)])
L.dump(b,'tmp/d2/placed.json')
json.dump([q for q in json.load(open('tmp/d2/placed.json')) if q['ref'] in order],open('tmp/d2/placed_um.json','w'))
