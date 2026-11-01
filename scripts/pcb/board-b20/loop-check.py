"""Phase 21 desk self-check of the B20 switching-stage loops and shunt sense routing (no field solver, nothing measured).

usage: python3 loop-check.py <geom.json> <routes.json> <out.json>

Per stage it reports the hot-loop polygon through the pad centres (input capacitor VIN pad -> IC VIN pin -> IC SW pin ->
catch-diode cathode -> diode anode -> input capacitor return pad), the copper length and layer of each loop branch, and
whether the input-capacitor and diode returns share F.Cu copper or only meet through vias and the pours. Per INA301
sense pair it reports the trace lengths, vias, the pad each trace lands on and the largest gap between the two traces.
"""
import json
import math
import sys

geom = json.load(open(sys.argv[1]))
routes = json.load(open(sys.argv[2]))
STAGES = {
    'A': ('U1', 'C3', 'D1', 'L1', 'GND'),
    'B': ('U2', 'C7', 'D2', 'L3', 'GND'),
    'C': ('U3', 'CCIN1', 'D3', 'L5', 'M12_RAW'),
}
SENSE = {'RSH1': ('U11', '8', '7'), 'RSH2': ('U12', '8', '7'), 'RSH3': ('U9', '4', '3')}


def pad(ref, num, biggest=True):
    hits = [p for p in geom['pads'] if p['ref'] == ref and p['num'] == num]
    key = lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1])
    return max(hits, key=key) if biggest else min(hits, key=key)


def inside(pt, p, tol=0.05):
    b = p['bbox']
    return b[0] - tol <= pt[0] <= b[2] + tol and b[1] - tol <= pt[1] <= b[3] + tol


def shoelace(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def net_tracks(net):
    return [t for t in routes['tracks'] if t['net'] == net]


def length(ts):
    return sum(math.dist(t['a'], t['b']) for t in ts)


def branch(net, p, q):
    """Tracks of net forming the path between pads p and q (walk the track graph)."""
    ts = net_tracks(net)
    vs = [tuple(v['at']) for v in routes['vias'] if v['net'] == net]
    nodes = {}

    def key(pt):
        return (round(pt[0], 3), round(pt[1], 3))
    adj = {}
    for k, t in enumerate(ts):
        a, b = key(t['a']), key(t['b'])
        adj.setdefault(a, []).append((b, k))
        adj.setdefault(b, []).append((a, k))
    starts = [n for n in adj if inside(n, p)]
    goals = {n for n in adj if inside(n, q)}
    # endpoints that touch another track's body are joined to that track's ends
    for k, t in enumerate(ts):
        for e in (key(t['a']), key(t['b'])):
            for m, u in enumerate(ts):
                if m == k:
                    continue
                if seg_dist(e, u['a'], u['b']) < u['w'] / 2 and u['layer'] == t['layer']:
                    for f in (key(u['a']), key(u['b'])):
                        adj.setdefault(e, []).append((f, m))
    for v in vs:
        vk = key(v)
        near = [n for n in adj if math.dist(n, vk) < 0.05]
        for a in near:
            for b in near:
                if a != b:
                    adj[a].append((b, None))
    import heapq
    dist, prev, heap = {}, {}, [(0.0, s) for s in starts]
    for s in starts:
        dist[s] = 0.0
    while heap:
        d, n = heapq.heappop(heap)
        if n in goals:
            used = []
            while n in prev:
                n, k = prev[n]
                if k is not None:
                    used.append(ts[k])
            return used
        for m, k in adj.get(n, []):
            nd = d + math.dist(n, m)
            if nd < dist.get(m, 1e9):
                dist[m] = nd
                prev[m] = (n, k)
                heapq.heappush(heap, (nd, m))
    return None


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def describe(ts):
    if ts is None:
        return {'routed': False}
    return {'routed': True, 'length_mm': round(length(ts), 2), 'layers': sorted({t['layer'] for t in ts}),
            'min_width_mm': min((t['w'] for t in ts), default=None)}


out = {'_comment': __doc__.strip().splitlines()[0], 'stages': {}, 'sense': {}}
for name, (ic, cin, diode, ind, ground) in STAGES.items():
    cv, cg = pad(cin, '1'), next(p for p in geom['pads'] if p['ref'] == cin and p['net'] == ground)
    vin, sw = pad(ic, '2'), pad(ic, '8')
    dk, da = pad(diode, '1'), pad(diode, '2')
    poly = [cv['center'], vin['center'], sw['center'], dk['center'], da['center'], cg['center']]
    ret = branch(ground, da, cg)
    out['stages'][name] = {
        'ic': ic, 'input_cap': cin, 'diode': diode,
        'hot_loop_polygon_mm2': round(shoelace(poly), 1),
        'hot_loop_perimeter_mm': round(sum(math.dist(a, b) for a, b in zip(poly, poly[1:] + poly[:1])), 1),
        'vin_branch': describe(branch('VIN', cv, vin)),
        'sw_branch': describe(branch(sw['net'], sw, dk)),
        'return_branch_diode_to_cin': describe(ret) if ret else {'routed': False, 'via': 'pour and vias only' if ground == 'GND' else 'no copper path'},
        'inductor_branch': describe(branch(sw['net'], dk, pad(ind, '1'))),
    }
for shunt, (ina, plus, minus) in SENSE.items():
    rows = {}
    for num in (plus, minus):
        ip = pad(ina, num)
        group = [t for t in routes['tracks'] if t['net'] == ip['net']]
        kel = [p for p in geom['pads'] if p['ref'] == shunt and p['net'] == ip['net']]
        target = min(kel, key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))
        ts = branch(ip['net'], ip, target)
        rows[num] = dict(describe(ts), net=ip['net'], lands_on='sense pad' if len(kel) == 2 else 'current pad (no sense pad)')
        rows[num]['pts'] = [pt for t in (ts or []) for pt in (t['a'], t['b'])]
    a, b = rows[plus].pop('pts'), rows[minus].pop('pts')
    gap = max((min(math.dist(p, q) for q in b) for p in a), default=None) if a and b else None
    out['sense'][shunt] = {'ina': ina, 'pins': rows, 'largest_pair_gap_mm': round(gap, 2) if gap is not None else None}
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print(json.dumps(out, indent=1))
