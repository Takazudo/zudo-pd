"""Phase 12: host-side grid router for the Board P r3 draft (two layers, 45-degree moves, through vias).

usage: python3 route-signals.py <geom.json> <pours.json> <out.json> [passes]
geom.json comes from dump-geom.py on the placed board. Every net except GND is routed pad by pad onto a growing
tree of its own copper (pads, routed tracks and, for the power nets, their own F.Cu pour outline). Other nets'
pads, tracks, vias and power pours are obstacles inflated by the 0.2 mm Default clearance plus half the track
width; the 0.5 mm copper-to-edge rule and the rule-area via bans are kept. GND is left to the pours. There is no
rip-up inside a pass: a connection that finds no path (window, then whole board) is reported as unrouted, and the next
pass routes the failed nets first; the pass with the fewest unrouted connections is kept. Widths: 0.2 mm signals (Default netclass),
0.4 mm on the power-net branches (decoupling, divider and sense pins; the 5 A path is the pour).
"""
import heapq, json, math, random, sys

import numpy as np

geom = json.load(open(sys.argv[1]))
POUR_DOC = json.load(open(sys.argv[2]))
pours = [p for p in POUR_DOC['pours'] if p['net'] != 'GND']
FIXED_TRACKS = POUR_DOC.get('tracks', [])
geom['tracks'] += FIXED_TRACKS
G, W, H = 0.05, 27.0, 40.0
NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
CL, EDGE, VIA_DRILL, HOLE_CL, MARGIN = 0.2, 0.5, 0.3, 0.25, 0.03
VIA_D = 0.6   # set per net in run(): 0.6 mm power branches (netclass), 0.5 mm signals (0.1 mm annular, the board minimum)
POWER = {p['net'] for p in pours}
VIA_COST, WINDOW = 30.0, 4.0
XS = np.arange(NX) * G
YS = np.arange(NY) * G
LAYERS = ('F', 'B')


def width(net):
    return 0.4 if net in POWER else 0.2


def window(x0, y0, x1, y1, r):
    i0, i1 = max(0, int((x0 - r) / G)), min(NX, int(math.ceil((x1 + r) / G)) + 1)
    j0, j1 = max(0, int((y0 - r) / G)), min(NY, int(math.ceil((y1 + r) / G)) + 1)
    return i0, i1, j0, j1


def mark_rect(m, b, r):
    i0, i1, j0, j1 = window(*b, r)
    if i0 >= i1 or j0 >= j1:
        return
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    dx = np.maximum(np.maximum(b[0] - x, x - b[2]), 0)
    dy = np.maximum(np.maximum(b[1] - y, y - b[3]), 0)
    m[j0:j1, i0:i1] |= dx * dx + dy * dy <= r * r


def mark_seg(m, a, b, r):
    i0, i1, j0, j1 = window(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]), r)
    if i0 >= i1 or j0 >= j1:
        return
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = np.clip(((x - a[0]) * dx + (y - a[1]) * dy) / L, 0, 1) if L > 0 else 0.0
    px, py = x - a[0] - t * dx, y - a[1] - t * dy
    m[j0:j1, i0:i1] |= px * px + py * py <= r * r


def inside_poly(pts, x, y):
    ins = np.zeros(np.broadcast(x, y).shape, bool)
    n = len(pts)
    for k in range(n):
        (xa, ya), (xb, yb) = pts[k], pts[(k + 1) % n]
        cond = (ya > y) != (yb > y)
        with np.errstate(divide='ignore', invalid='ignore'):
            xc = xa + (y - ya) * (xb - xa) / (yb - ya)
        ins ^= cond & (x < xc)
    return ins


def mark_poly(m, pts, r, shrink=False):
    xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
    i0, i1, j0, j1 = window(min(xs_), min(ys_), max(xs_), max(ys_), max(r, 0))
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    ins = inside_poly(pts, x, y)
    edge = np.zeros_like(ins)
    for k in range(len(pts)):
        sub = np.zeros((NY, NX), bool)
        mark_seg(sub, pts[k], pts[(k + 1) % len(pts)], abs(r))
        edge |= sub[j0:j1, i0:i1]
    m[j0:j1, i0:i1] |= (ins & ~edge) if shrink else (ins | edge)


def base_edge(hw):
    m = np.zeros((NY, NX), bool)
    lim = EDGE + hw
    m[:, XS < lim] = True; m[:, XS > W - lim] = True
    m[YS < lim, :] = True; m[YS > H - lim, :] = True
    return m


routed_tracks, routed_vias = [], []


def obstacles(net, hw):
    ob = {l: base_edge(hw) for l in LAYERS}
    for p in geom['pads']:
        if p['net'] == net and net:
            continue
        for l in p['layers']:
            mark_rect(ob[l], p['bbox'], CL + hw + MARGIN)
    for t in geom['tracks'] + routed_tracks:
        if t['net'] != net:
            mark_seg(ob[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
    for v in geom['vias'] + routed_vias:
        if v['net'] != net:
            for l in LAYERS:
                mark_seg(ob[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
    for z in pours:
        if z['net'] != net:
            for o in z['outlines']:
                mark_poly(ob[z['layer'][0]], o, 0.25 + hw + MARGIN)
    return ob


def via_ok(net):
    ob = obstacles(net, VIA_D / 2)
    m = ~(ob['F'] | ob['B'])
    bad = np.zeros((NY, NX), bool)
    for a in geom['rule_areas']:
        if a['no_vias']:
            mark_poly(bad, a['points'], VIA_D / 2)
    for p in geom['pads']:
        if p['drill'] and p['net'] != net:
            mark_seg(bad, p['center'], p['center'], HOLE_CL + VIA_DRILL / 2 + p['drill'] / 2)
    for v in geom['vias'] + routed_vias:
        mark_seg(bad, v['at'], v['at'], HOLE_CL + VIA_DRILL)
    return m & ~bad


def pad_cells(p):
    """Cells inside the ellipse inscribed in the pad box (round PTH pads lose their box corners), shrunk by one cell."""
    m = np.zeros((NY, NX), bool)
    b = p['bbox']
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    rx, ry = max((b[2] - b[0]) / 2 - G, G / 2), max((b[3] - b[1]) / 2 - G, G / 2)
    i0, i1, j0, j1 = window(*b, 0)
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    m[j0:j1, i0:i1] = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0
    if not m.any():
        mark_rect(m, b, 0)
    return m


def route(net, src, tree, ob, vok, hw, win=None):
    """Dijkstra from src cells to tree cells (dicts layer -> mask) inside a window; returns [(l, j, i), ...]."""
    ys_, xs_ = [], []
    for msk in list(src.values()):
        j, i = np.nonzero(msk); ys_ += list(j); xs_ += list(i)
    tj, ti = [], []
    for msk in tree.values():
        j, i = np.nonzero(msk); tj += list(j); ti += list(i)
    if not ys_ or not tj:
        return None
    sy, sx = np.mean(ys_), np.mean(xs_)
    d2 = (np.array(tj) - sy) ** 2 + (np.array(ti) - sx) ** 2
    k = int(np.argmin(d2))
    w = int((win or WINDOW) / G)
    j0, j1 = max(0, min(min(ys_), tj[k]) - w), min(NY, max(max(ys_), tj[k]) + w + 1)
    i0, i1 = max(0, min(min(xs_), ti[k]) - w), min(NX, max(max(xs_), ti[k]) + w + 1)
    li = {'F': 0, 'B': 1}
    free = np.stack([~ob[l][j0:j1, i0:i1] | src.get(l, np.zeros((NY, NX), bool))[j0:j1, i0:i1]
                     | tree.get(l, np.zeros((NY, NX), bool))[j0:j1, i0:i1] for l in LAYERS])
    tgt = np.stack([tree.get(l, np.zeros((NY, NX), bool))[j0:j1, i0:i1] for l in LAYERS])
    vv = vok[j0:j1, i0:i1]
    dist = np.full(free.shape, np.inf)
    prev = {}
    pq = []
    for l, msk in src.items():
        jj, ii = np.nonzero(msk[j0:j1, i0:i1])
        for a, b in zip(jj, ii):
            dist[li[l], a, b] = 0.0
            heapq.heappush(pq, (0.0, li[l], int(a), int(b)))
    moves = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    hj, hi = free.shape[1], free.shape[2]
    end = None
    while pq:
        d, l, a, b = heapq.heappop(pq)
        if d > dist[l, a, b]:
            continue
        if tgt[l, a, b]:
            end = (l, a, b); break
        for da, db, c in moves:
            na, nb = a + da, b + db
            if 0 <= na < hj and 0 <= nb < hi and free[l, na, nb]:
                if da and db and not (free[l, a + da, b] and free[l, a, b + db]):
                    continue
                nd = d + c
                if nd < dist[l, na, nb]:
                    dist[l, na, nb] = nd; prev[(l, na, nb)] = (l, a, b); heapq.heappush(pq, (nd, l, na, nb))
        if vv[a, b]:
            ol = 1 - l
            if free[ol, a, b]:
                nd = d + VIA_COST
                if nd < dist[ol, a, b]:
                    dist[ol, a, b] = nd; prev[(ol, a, b)] = (l, a, b); heapq.heappush(pq, (nd, ol, a, b))
    if end is None:
        return None
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    return [(LAYERS[l], a + j0, b + i0) for l, a, b in reversed(path)]


def emit(net, path, hw):
    tracks, vias = [], []
    pts = [(l, i * G, j * G) for l, j, i in path]
    k = 0
    while k < len(pts) - 1:
        l, x0, y0 = pts[k]
        if pts[k + 1][0] != l:
            vias.append({'net': net, 'at': [round(float(x0), 3), round(float(y0), 3)], 'd': VIA_D})
            k += 1; continue
        dirn = (round((pts[k + 1][1] - x0) / G), round((pts[k + 1][2] - y0) / G))
        m = k + 1
        while m + 1 < len(pts) and pts[m + 1][0] == l and (round((pts[m + 1][1] - pts[m][1]) / G), round((pts[m + 1][2] - pts[m][2]) / G)) == dirn:
            m += 1
        tracks.append({'net': net, 'layer': l, 'w': round(2 * hw, 3), 'a': [round(float(x0), 3), round(float(y0), 3)],
                       'b': [round(float(pts[m][1]), 3), round(float(pts[m][2]), 3)]})
        k = m
    return tracks, vias


nets = {}
for p in geom['pads']:
    if p['net'] and p['net'] != 'GND' and not p['net'].startswith('unconnected'):
        nets.setdefault(p['net'], []).append(p)
nets = {n: ps for n, ps in nets.items() if len(ps) > 1}


def hpwl(ps):
    return (max(p['center'][0] for p in ps) - min(p['center'][0] for p in ps)) + (max(p['center'][1] for p in ps) - min(p['center'][1] for p in ps))


def run(order):
    routed_tracks.clear(); routed_vias.clear()
    report = {'routed': [], 'unrouted': []}
    global VIA_D
    for net in order:
        VIA_D = 0.6 if net in POWER else 0.5
        hw = width(net) / 2
        ob = obstacles(net, hw)
        vok = via_ok(net)
        thin = None
        tree = {l: np.zeros((NY, NX), bool) for l in LAYERS}
        pending = list(nets[net])
        for z in pours:
            if z['net'] == net:
                for o in z['outlines']:
                    mark_poly(tree[z['layer'][0]], o, 0.3, shrink=True)
        for ft in FIXED_TRACKS:
            if ft['net'] == net:
                mark_seg(tree[ft['layer']], ft['a'], ft['b'], ft['w'] / 2)
        if tree['F'].any():
            for p in list(pending):
                c = pad_cells(p)
                if any((tree[l] & c).any() for l in p['layers']):
                    pending.remove(p)
                    for l in p['layers']:
                        tree[l] |= c
        else:
            p = pending.pop(0)
            for l in p['layers']:
                tree[l] |= pad_cells(p)
        while pending:
            cy = np.mean([np.nonzero(tree[l])[0].mean() for l in LAYERS if tree[l].any()]) * G
            cx = np.mean([np.nonzero(tree[l])[1].mean() for l in LAYERS if tree[l].any()]) * G
            pending.sort(key=lambda p: math.hypot(p['center'][0] - cx, p['center'][1] - cy))
            p = pending.pop(0)
            src = {l: pad_cells(p) for l in p['layers']}
            path = route(net, src, tree, ob, vok, hw) or route(net, src, tree, ob, vok, hw, W + H)
            used = hw
            if path is None and hw > 0.1:
                # a power-net pin that cannot escape at 0.4 mm (sense or supply pin between fine-pitch neighbours) gets 0.2 mm
                if thin is None:
                    thin = (obstacles(net, 0.1), via_ok(net))
                path = route(net, src, tree, thin[0], thin[1], 0.1, W + H); used = 0.1
            if path is None:
                report['unrouted'].append(f"{net}: {p['ref']}.{p['num']}")
                continue
            t, v = emit(net, path, used)
            routed_tracks.extend(t); routed_vias.extend(v)
            for l in LAYERS:
                for tr in t:
                    if tr['layer'] == l:
                        mark_seg(tree[l], tr['a'], tr['b'], used)
            for vi in v:
                for l in LAYERS:
                    mark_seg(tree[l], vi['at'], vi['at'], VIA_D / 2)
            for l in p['layers']:
                tree[l] |= src[l]
            report['routed'].append(f"{net}: {p['ref']}.{p['num']}")
    return list(routed_tracks), list(routed_vias), report


# passes: the first pass routes the power branches first; later passes move the nets that failed to the front (odd
# passes shuffle the rest with a fixed seed); the pass with the fewest power-net, then total, unrouted connections is kept
order = sorted(nets, key=lambda n: (n not in POWER, hpwl(nets[n])))
best = None
rng = random.Random(12)


def score(rep):
    return (sum(u.split(':')[0] in POWER for u in rep['unrouted']), len(rep['unrouted']))


for k in range(int(sys.argv[4]) if len(sys.argv) > 4 else 6):
    t, v, rep = run(order)
    t = FIXED_TRACKS + t
    print(k, score(rep), rep['unrouted'], file=sys.stderr, flush=True)
    if best is None or score(rep) < score(best[2]):
        best = (t, v, rep, list(order))
    if not rep['unrouted']:
        break
    failed = []
    for u in rep['unrouted']:
        n = u.split(':')[0]
        if n not in failed:
            failed.append(n)
    rest = [n for n in order if n not in failed]
    if k % 2:
        rng.shuffle(rest)
    order = failed + rest
t, v, rep, order = best
rep['net_order'] = order
json.dump({'tracks': t, 'vias': v, 'report': rep}, open(sys.argv[3], 'w'), indent=1)
print(json.dumps({'tracks': len(t), 'vias': len(v), 'routed': len(rep['routed']), 'unrouted': rep['unrouted']}))
