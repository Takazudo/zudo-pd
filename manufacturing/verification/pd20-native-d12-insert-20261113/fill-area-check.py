import sys,re,math,json
sys.path.insert(0,'/Users/takazudo/repos/circuits/zudo-pd-review-234/scripts/schgen')
from sexp import parse,tokenize,atom
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
from shapely.validation import make_valid
def load(path):
    t=parse(tokenize(open(path).read())); z={}
    for it in t:
        if isinstance(it,list) and it and atom(it[0])=='zone':
            uid=[atom(c[1]) for c in it if isinstance(c,list) and atom(c[0])=='uuid'][0]
            for fp in it:
                if isinstance(fp,list) and fp and atom(fp[0])=='filled_polygon':
                    layer=[atom(c[1]) for c in fp if isinstance(c,list) and atom(c[0])=='layer'][0]
                    pts=[c for c in fp if isinstance(c,list) and atom(c[0])=='pts'][0]
                    xy=[(float(atom(q[1])),float(atom(q[2]))) for q in pts[1:] if atom(q[0])=='xy']
                    z.setdefault((uid,layer),[]).append(make_valid(Polygon(xy)).buffer(0))
    return {k:unary_union(v) for k,v in z.items()}
A=load(sys.argv[1]);B=load(sys.argv[2])
ver=None
# edit region from verifier style: rebuild from added/removed copper & courtyards approximated
reg=json.load(open(sys.argv[4])) if len(sys.argv)>4 else []
R=unary_union([LineString([r['a'],r['b']]).buffer(r['r']+2.0) if r['a']!=r['b'] else Point(r['a']).buffer(r['r']+2.0) for r in reg]) if reg else None
res={}
for k in sorted(set(A)|set(B)):
    d=A[k].symmetric_difference(B[k])
    if d.area<1e-9: continue
    out=d.difference(R) if R is not None else d
    res['/'.join(k)]={'sym_diff_mm2':round(d.area,6),'outside_region_mm2':round(out.area,9),'outside_bounds':[round(v,3) for v in out.bounds] if not out.is_empty else None}
print(json.dumps(res,indent=1))
