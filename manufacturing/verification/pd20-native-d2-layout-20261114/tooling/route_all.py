import sys, json, time; sys.path.insert(0,'tmp/d2'); import d2route as R, d2lib as L
from shapely.geometry import Polygon, Point, box, LineString
g=json.load(open('tmp/d2/geom.json'))
placed=json.load(open('tmp/d2/placed_bl.json'))+json.load(open('tmp/d2/placed_um.json'))
bb=L.Board(); RM=set()
for q in placed:
    gg=L.part_geom(q['ref'],*q['at'][:3]); RM|=set(bb.check(gg) or []); bb.placed.append(gg)
DV=[bb.gvias[i].centroid.coords[0] for i in RM]
r=R.Router(g,placed,drop_nets={'P12_DX','P5_DX','M12_DX'},drop_refs=L.REMOVED,drop_vias=DV)
pads={(q['ref'],p['num']):Polygon(p['poly']) for q in placed for p in q['pads']}
B='B.Cu'
def P(ref,*nums): return [(B,pads[(ref,n)]) for n in nums]
def netcopper(net):
    out=[]
    for t in g['tracks']:
        if t['net']==net and t['l'] in R.LAYERS: out.append((t['l'],LineString([t['a'],t['b']]).buffer(t['w']/2)))
    for v in g['vias']:
        if v['net']==net: out+=[(l,Point(v['c']).buffer(v['d']/2)) for l in R.LAYERS]
    for f in g['fps']:
        if f['ref'] in L.REMOVED: continue
        for p in f['pads']:
            if p['net']==net: out+=[(l,box(*p['bbox'])) for l in (R.LAYERS if p['drill']>0 else ['F.Cu'])]
    return out
EX={n:netcopper(n) for n in ('P12_OUT','P5_OUT','M12_OUT','M12_DG','DIS_P')}
Bonly=dict(layers=[B],allow_via=False)
log={}
# --- pulse loops (B only, wide)
for net,a,b in [('P12_DX',P('RX12','1'),P('Q51','9','5','6','7','8')),('P5_DX',P('RX5','1'),P('Q52','9','5','6','7','8')),
                ('M12_DX',P('RXN3','2'),P('Q55','9','5','6','7','8')),('M12_DXB',P('RXN3','1'),P('RXN2','2')),('M12_DXA',P('RXN2','1'),P('R76','2'))]:
    log[net]=r.route(net,a,b,1.2,label=net,**Bonly) or r.route(net,a,b,0.8,label=net+' 0.8',**Bonly)
# FET source pins joined to each other and the drain pins to pad 9 by short bars
for ref,net in (('Q51','GND'),('Q52','GND'),('Q55','M12_OUT'),('Q8','DIS_P')):
    R.tree(r,net,[P(ref,'1'),P(ref,'2'),P(ref,'3')],0.3,**Bonly)
for ref,net in (('Q51','P12_DX'),('Q52','P5_DX'),('Q55','M12_DX')):
    pass
# --- rails
log['P12_OUT']=r.route('P12_OUT',P('RX12','2'),EX['P12_OUT'],1.2,label='RX12->P12_OUT',**Bonly)
log['P5_OUT']=r.route('P5_OUT',P('RX5','2'),EX['P5_OUT'],1.2,label='RX5->P5_OUT',**Bonly)
mo=r.route('M12_OUT',P('Q55','1','2','3'),EX['M12_OUT'],1.0,lc=[3.0,1.2,1.0],label='Q55->M12_OUT')
log['M12_OUT']=mo; R.twins(r,'M12_OUT',mo,n=2)
# --- GND stitching at pulse returns and GND pads
for ref,num,n in (('Q51','2',3),('Q52','2',3),('R76','1',4),('CDG12','2',1),('CDG5','2',1),('D5','1',1),('Q7','2',1),('R82','2',1)):
    R.stitch(r,'GND',pads[(ref,num)],n=n)
# --- local gate / sequencer nets
R.tree(r,'P12_DG',[P('Q51','4'),P('RDG12','2'),P('CDG12','1')],0.3)
R.tree(r,'P5_DG',[P('Q52','4'),P('RDG5','2'),P('CDG5','1')],0.3)
R.tree(r,'M12_OUT',[P('C44','2'),P('C45','2'),P('D4','2'),P('Q9','2'),P('Q13','2'),P('RSQ3','2'),P('RSQ4','2')],0.4,root=P('Q55','1','2','3'))
R.tree(r,'M12_DG',[P('C44','1'),P('C45','1'),P('D4','1'),P('Q9','3')],0.3,root=P('Q55','4'))
R.tree(r,'SEQ_G',[P('RSQ2','2'),P('RSQ3','1'),P('Q9','1'),P('Q13','3')],0.25)
R.tree(r,'SEQ_Z',[P('D5','2'),P('RSQ4','1'),P('Q13','1')],0.25)
R.tree(r,'SEQ_PD',[P('Q8','9','5','6','7','8'),P('RSQ2','1')],0.3)
R.tree(r,'SEQ_EN_N',[P('Q7','3'),P('RSQ1','2'),P('Q8','4')],0.25)
R.tree(r,'SEQ_RG',[P('R81','2'),P('R82','1'),P('Q7','1')],0.25)
R.tree(r,'DIS_P',[P('Q8','1','2','3'),P('RSQ1','1')],0.25)
R.tree(r,'DIS_P',[P('RDG12','1'),P('RDG5','1')],0.25)
# --- long feeds
ok=R.tree(r,'M12_DG',[P('Q55','4')],0.25,root=EX['M12_DG'],lc=[4.0,1.0,1.2])
ok=R.tree(r,'P12_OUT',[P('R81','1')],0.25,root=EX['P12_OUT'],lc=[4.0,1.0,1.2])
ok=R.tree(r,'DIS_P',[P('RDG12','1')],0.25,root=EX['DIS_P'],lc=[4.0,1.0,1.2])
ok=R.tree(r,'DIS_P',[P('RSQ1','1')],0.25,root=EX['DIS_P']+P('RDG12','1'),lc=[4.0,1.0,1.2])
json.dump(r.items,open('tmp/d2/routes_all.json','w'))
print('items',len(r.items))
