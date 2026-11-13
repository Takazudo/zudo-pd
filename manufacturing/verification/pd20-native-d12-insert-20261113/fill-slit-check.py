"""D12 fill-screen replacement evidence: (a) per-zone fill area outside the edit region before/after,
(b) every out-of-region changed fill vertex lies on a zero-width fracture slit (an edge the ring also
traverses in reverse). usage: fill-slit-check.py BEFORE.kicad_pcb AFTER.kicad_pcb edit-region.json out.json
Requires shapely. The edit region is the verifier's own (courtyard circles + changed copper, grown by 2 mm)."""
import collections,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import parse,tokenize,atom
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely.validation import make_valid
MARGIN=2.0
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
def seg_distance(p,a,b):
    ax,ay=a;bx,by=b;px,py=p;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));return math.hypot(px-ax-t*dx,py-ay-t*dy)
before,after=rings(sys.argv[1]),rings(sys.argv[2]);region=json.load(open(sys.argv[3]))
inside=lambda p:any(seg_distance((float(p[0]),float(p[1])),r['a'],r['b'])<=r['r']+MARGIN for r in region)
R=unary_union([LineString([r['a'],r['b']]).buffer(r['r']+MARGIN,64) if r['a']!=r['b'] else Point(r['a']).buffer(r['r']+MARGIN,64) for r in region])
def area(rs):return unary_union([make_valid(Polygon([(float(x),float(y)) for x,y in r])).buffer(0) for r in rs])
def slit_vertices(rs):
    on=set()
    for r in rs:
        n=len(r);edges=[(r[i],r[(i+1)%n]) for i in range(n)];es=set(edges)
        rev=[(a,b) for a,b in edges if (b,a) in es and a!=b]
        for a,b in rev:on.update([a,b])
        segs=[((float(a[0]),float(a[1])),(float(b[0]),float(b[1]))) for a,b in rev]
        for v in r:
            if v in on:continue
            fv=(float(v[0]),float(v[1]))
            if any(seg_distance(fv,a,b)<1e-6 for a,b in segs):on.add(v)
    return on
result={'scope':'Replacement for the verify-insert-parts fill-vertex screen only (D12, #283); CALCULATED geometry','margin_mm':MARGIN,'zones':{},'non_slit_vertices':[]}
for key in sorted(set(before)|set(after)):
    cb=collections.Counter(v for r in before.get(key,[]) for v in r);ca=collections.Counter(v for r in after.get(key,[]) for v in r)
    changed=(cb-ca)+(ca-cb);outside=[v for v in changed if not inside(v)]
    A,B=area(before.get(key,[])),area(after.get(key,[]))
    ab,aa=A.difference(R).area,B.difference(R).area
    entry={'vertices_changed':sum(changed.values()),'vertices_changed_outside_region':len(outside),
           'area_outside_region_before_mm2':round(ab,6),'area_outside_region_after_mm2':round(aa,6),'area_outside_delta_mm2':round(aa-ab,9),
           'symmetric_difference_outside_region_mm2':round(A.symmetric_difference(B).difference(R).area,9)}
    if outside:
        sb,sa=slit_vertices(before.get(key,[])),slit_vertices(after.get(key,[]))
        bad=[v for v in outside if not ((v in cb and v in sb) or (v in ca and v in sa))]
        entry['outside_vertices_on_slits']=len(outside)-len(bad)
        # distance from each non-slit vertex to the other board's fill boundary (numeric refill jitter vs real change)
        for v in bad:
            other=B if v in cb else A
            d=other.boundary.distance(Point(float(v[0]),float(v[1])))
            result['non_slit_vertices'].append({'zone':'/'.join(key),'xy':v,'side':'before' if v in cb else 'after','distance_to_other_fill_boundary_mm':round(d,6)})
    if changed:result['zones']['/'.join(key)]=entry
result['non_slit_max_distance_mm']=max([v['distance_to_other_fill_boundary_mm'] for v in result['non_slit_vertices']],default=0)
result['non_slit_count']=len(result['non_slit_vertices'])
result['status']='PASS' if not result['non_slit_vertices'] else 'FAIL (non-slit vertices present; see distances)'
Path(sys.argv[4]).write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='non_slit_vertices'},indent=1))
