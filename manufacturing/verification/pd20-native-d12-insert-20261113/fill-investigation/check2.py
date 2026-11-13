import json,math,sys,collections
sys.path.insert(0,'scripts/schgen')
from sexp import parse,tokenize,atom
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
from shapely import affinity
from shapely.validation import make_valid
def rings(path):
    out={}
    for it in parse(tokenize(Path(path).read_text())):
        if isinstance(it,list) and it and atom(it[0])=='zone':
            uid=[atom(c[1]) for c in it if isinstance(c,list) and atom(c[0])=='uuid'][0]
            for fp in it:
                if isinstance(fp,list) and fp and atom(fp[0])=='filled_polygon':
                    layer=[atom(c[1]) for c in fp if isinstance(c,list) and atom(c[0])=='layer'][0]
                    pts=[c for c in fp if isinstance(c,list) and atom(c[0])=='pts'][0]
                    out.setdefault((uid,layer),[]).append([(atom(q[1]),atom(q[2])) for q in pts[1:] if atom(q[0])=='xy'])
    return out
B=rings('tmp/d12-before/board-b20-draft.kicad_pcb');A=rings('boards/board-b20-draft/board-b20-draft.kicad_pcb')
key=('b81109bf-72ac-5385-9d8f-bd5b62bf413f','F.Cu')
ver=json.load(open('manufacturing/verification/pd20-native-d12-insert-20261113/insert-verification-unfilled.json'))
items=[('removed',x) for x in ver['removed_copper']]+[('added',x) for x in ver['added_copper']]
def g(x):
    if x['kind']=='via': return Point(x['at']).buffer(x['d']/2)
    return LineString([x['a'],x['b']]).buffer(x['w']/2) if x['a']!=x['b'] else Point(x['a']).buffer(x['w']/2)
crt={'R77':(67.46,60.0,90),'R78':(70.61,57.16,0),'R79':(84.2,55.0,0),'R80':(69.02,48.18,0)}
cyd={r:affinity.rotate(box(x-1.19,y-0.75,x+1.19,y+0.75),rot,origin=(x,y)) for r,(x,y,rot) in crt.items()}
big=json.load(open('tmp/d12-final/check1.json'))
out={'i':[],'ii':{},'iii':{},'iv':{}}
fl=lambda v:(float(v[0]),float(v[1]))
for v in big:
    p=Point(fl(v['xy']))
    d,it=min(((g(x).distance(p),(k,x)) for k,x in items),key=lambda t:t[0])
    dc,rc=min(((c.distance(p),r) for r,c in cyd.items()))
    # all items on F.Cu only
    dF,itF=min(((g(x).distance(p),(k,x)) for k,x in items if x.get('layer','F.Cu')=='F.Cu' or x['kind']=='via'),key=lambda t:t[0])
    out['i'].append({'xy':v['xy'],'side':v['side'],'dist_um':v['dist_um'],'nearest_changed_item_mm':round(d,3),'item':it,'nearest_changed_FCu_or_via_mm':round(dF,3),'item_FCu':itF,'nearest_new_courtyard_mm':round(dc,3),'courtyard':rc})
# ii: ring windows
def window(R,xy,k=10):
    for ri,r in enumerate(R):
        n=len(r)
        for i,q in enumerate(r):
            if q==tuple(xy): return {'ring':ri,'index':i,'pts':[r[(i+j)%n] for j in range(-k,k+1)]}
for tag,xy in (('cluster_before',['92.390641','54.062582']),('cluster_after',['92.420007','54.077738']),('r62_before',['107.28748','49.258826'])):
    R=B[key] if 'before' in tag else A[key]
    out['ii'][tag]=window(R,xy)
# counterpart window in other board near the same point
def nearest_window(R,P,k=10):
    best=None
    for ri,r in enumerate(R):
        for i,q in enumerate(r):
            d=math.dist(fl(q),P)
            if best is None or d<best[0]: best=(d,ri,i)
    d,ri,i=best;r=R[ri];n=len(r);return {'ring':ri,'index':i,'dist':d,'pts':[r[(i+j)%n] for j in range(-k,k+1)]}
out['ii']['cluster_after_near_before_pt']=nearest_window(A[key],(92.390641,54.062582))
out['ii']['r62_after_near']=nearest_window(A[key],(107.28748,49.258826))
# iii: changed vertices inside region in same zone ring
region=json.load(open('manufacturing/verification/pd20-native-d12-insert-20261113/edit-region.json'))
def sd(p,a,b):
    ax,ay=a;bx,by=b;px,py=p;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy;t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));return math.hypot(px-ax-t*dx,py-ay-t*dy)
inside=lambda p:any(sd(p,r['a'],r['b'])<=r['r']+2.0 for r in region)
cb=collections.Counter(v for r in B[key] for v in r);ca=collections.Counter(v for r in A[key] for v in r)
ch=[v for v in (cb-ca)+(ca-cb)]
ins=[fl(v) for v in ch if inside(fl(v))]
for tag,P in (('cluster',(92.40,54.07)),('r62',(107.287,49.259))):
    dmin=min(math.dist(P,q) for q in ins)
    # same filled polygon? find polygon containing point in AFTER
    polys=[make_valid(Polygon([fl(q) for q in r])).buffer(0) for r in A[key]]
    pid=[i for i,pg in enumerate(polys) if pg.distance(Point(P))<0.01]
    same=[q for q in ins if any(polys[i].distance(Point(q))<0.01 for i in pid)]
    out['iii'][tag]={'changed_inside_region_total':len(ins),'nearest_inside_changed_vertex_euclid_mm':round(dmin,3),'polygon_ids_after':pid,'inside_changed_in_same_polygon':len(same),
       'nearest_same_polygon_inside_changed_mm':round(min(math.dist(P,q) for q in same),3) if same else None}
json.dump(out,open('tmp/d12-final/check2.json','w'),indent=1,default=str)
for x in out['i']: print(x['xy'],x['dist_um'],'near item',x['nearest_changed_item_mm'],x['item'][0],x['item'][1]['net'],x['item'][1].get('layer','via'),'| F/via',x['nearest_changed_FCu_or_via_mm'],x['item_FCu'][1]['net'],'| crtyd',x['nearest_new_courtyard_mm'],x['courtyard'])
print(json.dumps(out['iii'],indent=1))
