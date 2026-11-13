import json,math,sys
sys.argv=['x','tmp/d12-before/board-b20-draft.kicad_pcb','boards/board-b20-draft/board-b20-draft.kicad_pcb','manufacturing/verification/pd20-native-d12-insert-20261113/edit-region.json','/dev/null']
src=open('manufacturing/verification/pd20-native-d12-insert-20261113/fill-slit-check.py').read().split('result={')[0]
g={'__file__':'/Users/takazudo/repos/circuits/zudo-pd-review-234/manufacturing/verification/pd20-native-d12-insert-20261113/fill-slit-check.py','__name__':'x'};exec(src,g)
before,after=g['before'],g['after']
res=json.load(open('manufacturing/verification/pd20-native-d12-insert-20261113/fill-slit-check.json'))
G=json.load(open('/private/tmp/claude-501/-Users-takazudo-repos-circuits-zudo-pd/e62b3ee4-aecb-420c-90bc-550343ad2567/scratchpad/geom.json'))
centres=[('via '+it['net'],it['c']) for it in G if it['k']=='via' and it['layer']=='F.Cu']+[('hole '+it['ref'],it['c']) for it in G if it['k']=='hole']
for it in G:
    if it['k']=='pad' and it['layer']=='F.Cu':
        xs=[p[0] for p in it['poly'][0]];ys=[p[1] for p in it['poly'][0]];centres.append(('pad '+it['ref']+'.'+it['num'],[(min(xs)+max(xs))/2,(min(ys)+max(ys))/2]))
big=[v for v in res['non_slit_vertices'] if v['distance_to_other_fill_boundary_mm']>1e-4]
out=[]
for v in big:
    key=tuple(v['zone'].split('/'));side=v['side'];xy=tuple(v['xy'])
    mine=(before if side=='before' else after)[key];other=(after if side=='before' else before)[key]
    sl_m=g['slit_vertices'](mine);sl_o=g['slit_vertices'](other)
    oset=set(x for r in other for x in r)
    a=False;near=[]
    for r in mine:
        n=len(r)
        for i,p in enumerate(r):
            if p==xy:
                nb=[r[(i+k)%n] for k in range(-2,3)]
                near=nb
                for q in nb:
                    if q in sl_m and q not in oset: a=True
    # also: does the other board have a slit vertex within 0.1 mm that is not in mine? (slit moved)
    mset=set(x for r in mine for x in r)
    moved=[q for q in sl_o if q not in mset and math.dist((float(q[0]),float(q[1])),(float(xy[0]),float(xy[1])))<0.15]
    fx=(float(xy[0]),float(xy[1]))
    best=None
    for name,c in centres:
        ds=[math.dist((float(q[0]),float(q[1])),c) for q in near]
        if max(ds)<1.5 and max(ds)-min(ds)<0.002:
            if best is None or abs(ds[2]-0.4)<abs(best[1]-0.4): best=(name,round(ds[2],5),round(max(ds)-min(ds),6))
    out.append({'zone':v['zone'].split('/')[1],'side':side,'xy':v['xy'],'dist_um':round(v['distance_to_other_fill_boundary_mm']*1000,3),
                'a_slit_change_within_2_steps':a or bool(moved),'a_detail':{'own_ring_new_slit_vertex_within_2':a,'other_board_slit_vertex_within_0.15mm_absent_here':len(moved)},
                'b_on_arc':best})
json.dump(out,open('tmp/d12-final/check1.json','w'),indent=1)
for o in out: print(o['zone'],o['side'],o['xy'],o['dist_um'],'a=',o['a_slit_change_within_2_steps'],o['a_detail'],'b=',o['b_on_arc'])
import numpy as np
def fit(pts):
    A=np.array([[2*x,2*y,1] for x,y in pts]);b=np.array([x*x+y*y for x,y in pts]);c=np.linalg.lstsq(A,b,rcond=None)[0];r=math.sqrt(c[2]+c[0]**2+c[1]**2)
    res=[abs(math.dist((x,y),(c[0],c[1]))-r) for x,y in pts];return (round(c[0],4),round(c[1],4)),round(r,4),round(max(res)*1000,3)
print('--- arc fits (window of +-3 ring steps)')
for o in out:
    key=('b81109bf-72ac-5385-9d8f-bd5b62bf413f','F.Cu') if o['zone']=='F.Cu' else None
    mine=(before if o['side']=='before' else after)[key]
    for r in mine:
        n=len(r)
        for i,p in enumerate(r):
            if p==tuple(o['xy']):
                w=[(float(r[(i+k)%n][0]),float(r[(i+k)%n][1])) for k in range(-3,4)]
                print(o['side'],o['xy'],o['dist_um'],'fit centre,radius,max resid um:',fit(w),'chord mm',[round(math.dist(w[k],w[k+1]),4) for k in range(6)])
