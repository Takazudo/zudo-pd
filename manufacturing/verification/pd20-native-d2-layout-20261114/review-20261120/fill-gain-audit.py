"""Independent audit of out-of-region fill differences (B20 D2): per zone/layer, loss and gain pieces outside the
verifier's edit region (+2 mm, as fill-slit-check.py), island mapping before->after, and the smallest distance from
each gained piece to other-net copper on the same layer. usage: fill-gain-audit.py BEFORE AFTER edit-region.json out.json"""
import json, sys, math
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import pcbparse as pp
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.validation import make_valid

def fills(g):
    out = {}
    for z in g['zones']:
        for f in z['filled']:
            out.setdefault((z['net'], f['layer']), []).append(make_valid(Polygon(f['pts'])).buffer(0))
    return out

B, A = pp.load(sys.argv[1]), pp.load(sys.argv[2])
region = json.load(open(sys.argv[3]))
R = unary_union([LineString([r['a'], r['b']]).buffer(r['r'] + 2.0, 64) if r['a'] != r['b'] else Point(r['a']).buffer(r['r'] + 2.0, 64) for r in region])
fb, fa = fills(B), fills(A)
def other_copper(g, layer, net):
    geo = [LineString([s['a'], s['b']]).buffer(s['w'] / 2) for s in g['segs'] if s['layer'] == layer and s['net'] != net]
    geo += [Point(v['xy']).buffer(v['size'] / 2) for v in g['vias'] if v['net'] != net]
    for f in g['fps']:
        for p in f['pads']:
            if p['net'] != net and p['net'] is not None and (p['type'] in ('thru_hole', 'np_thru_hole') or f['layer'] == layer):
                geo.append(Point(p['xy']).buffer(min(p['size']) / 2))   # inscribed-circle proxy for the pad
    for (n, l), polys in fills(g).items():
        if l == layer and n != net:
            geo += polys
    return unary_union(geo)
res = {'scope': 'independent out-of-region fill audit, CALCULATED geometry', 'zones': {}}
for key in sorted(set(fb) | set(fa)):
    ub, ua = unary_union(fb.get(key, [])), unary_union(fa.get(key, []))
    loss = ub.difference(ua).difference(R); gain = ua.difference(ub).difference(R)
    if loss.area < 1e-9 and gain.area < 1e-9:
        continue
    gp = [g for g in getattr(gain, 'geoms', [gain]) if g.area > 1e-4]
    lp = [g for g in getattr(loss, 'geoms', [loss]) if g.area > 1e-4]
    # island mapping: every BEFORE island must lie (outside the region) inside one AFTER island
    unmapped = []
    for i, pb in enumerate(fb.get(key, [])):
        out_b = pb.difference(R)
        if out_b.area < 1e-6:
            continue
        cover = max((out_b.intersection(pa).area for pa in fa.get(key, [])), default=0)
        if cover < out_b.area - 1e-3:
            unmapped.append({'island': i, 'area_outside': out_b.area, 'largest_after_cover': cover})
    # gained pieces: attached to an AFTER island that also existed BEFORE (not a new isolated island)
    attached = []
    oc = other_copper(A, key[1], key[0])
    for g in gp:
        host = [pa for pa in fa.get(key, []) if pa.buffer(1e-4).intersects(g) and pa.intersects(ub)]
        attached.append({'area_mm2': round(g.area, 4), 'centroid': [round(g.centroid.x, 2), round(g.centroid.y, 2)],
                         'attached_to_pre_existing_island': bool(host),
                         'min_distance_to_other_net_copper_mm': round(g.distance(oc), 4)})
    res['zones'][f'{key[0]}/{key[1]}'] = {
        'loss_outside_mm2': loss.area, 'gain_outside_mm2': gain.area, 'loss_pieces_gt_1e-4mm2': len(lp),
        'gain_pieces': attached, 'islands_before': len(fb.get(key, [])), 'islands_after': len(fa.get(key, [])),
        'before_islands_not_preserved_outside_region': unmapped}
Path(sys.argv[4]).write_text(json.dumps(res, indent=1) + '\n')
print(json.dumps(res, indent=1))
