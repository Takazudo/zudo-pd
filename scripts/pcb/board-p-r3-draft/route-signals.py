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
import heapq, json, math, os, random, sys

import numpy as np

geom = json.load(open(sys.argv[1]))
# pcbnew lists footprints in load order, which differs between a fresh build and a saved board; route from a canonical order
geom['pads'].sort(key=lambda p: (p['ref'], p['num'], p['center']))
geom['rule_areas'].sort(key=lambda a: (a['layer'], a['points']))
POUR_DOC = json.load(open(sys.argv[2]))
pours = [p for p in POUR_DOC['pours'] if p['net'] != 'GND']
FIXED_TRACKS = POUR_DOC.get('tracks', [])
FIXED_VIAS = POUR_DOC.get('vias', [])
geom['tracks'] += FIXED_TRACKS
geom['vias'] += FIXED_VIAS
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
# phase 13 negotiated-congestion history: cells where a rip-up pushed one net through another cost more for every net
HIST = {l: np.zeros((NY, NX)) for l in LAYERS}
HIST_W = float(__import__('os').environ.get('R3_HIST_W', 2.0))


def obstacles(net, hw, routed=True):
    ob = {l: base_edge(hw) for l in LAYERS}
    for p in geom['pads']:
        if p['net'] == net and net:
            continue
        for l in p['layers']:
            mark_rect(ob[l], p['bbox'], CL + hw + MARGIN)
    for t in geom['tracks'] + (routed_tracks if routed else []):
        if t['net'] != net:
            mark_seg(ob[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
    for v in geom['vias'] + (routed_vias if routed else []):
        if v['net'] != net:
            for l in LAYERS:
                mark_seg(ob[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
    for z in pours:
        if z['net'] != net:
            for o in z['outlines']:
                mark_poly(ob[z['layer'][0]], o, 0.25 + hw + MARGIN)
    return ob


def via_ok_static(net, rippable):
    """via_ok ignoring the routed copper of the rippable nets only (rip-up mode for the GND fallback and joins)."""
    ob = obstacles(net, VIA_D / 2, routed=False)
    for t in routed_tracks:
        if t['net'] != net and t['net'] not in rippable:
            mark_seg(ob[t['layer']], t['a'], t['b'], CL + VIA_D / 2 + t['w'] / 2 + MARGIN)
    for v in routed_vias:
        if v['net'] != net and v['net'] not in rippable:
            for l in LAYERS:
                mark_seg(ob[l], v['at'], v['at'], CL + VIA_D / 2 + v['d'] / 2 + MARGIN)
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


GND_UNROUTED = {}


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


def route(net, src, tree, ob, vok, hw, win=None, soft=None, pen=0.0):
    """Dijkstra from src cells to tree cells (dicts layer -> mask) inside a window; returns [(l, j, i), ...].
    soft (layer -> mask) marks other nets' rippable copper: passable at pen per cell (rip-up mode)."""
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
    sc = (np.stack([soft[l][j0:j1, i0:i1] for l in LAYERS]) * pen) if soft is not None else np.zeros(free.shape)
    sc = sc + HIST_W * np.stack([HIST[l][j0:j1, i0:i1] for l in LAYERS])
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
                nd = d + c + sc[l, na, nb]
                if nd < dist[l, na, nb]:
                    dist[l, na, nb] = nd; prev[(l, na, nb)] = (l, a, b); heapq.heappush(pq, (nd, l, na, nb))
        if vv[a, b]:
            ol = 1 - l
            if free[ol, a, b]:
                nd = d + VIA_COST + sc[ol, a, b]
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



def copper_mask(net, hw):
    """Cells where a track of half-width hw on another net would violate clearance to net's routed copper."""
    m = {l: np.zeros((NY, NX), bool) for l in LAYERS}
    for t in routed_tracks:
        if t['net'] == net:
            mark_seg(m[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
    for v in routed_vias:
        if v['net'] == net:
            for l in LAYERS:
                mark_seg(m[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
    return m


def path_cells(path):
    """Path cells per layer; a layer change is a via, which occupies the cell on both layers (inflated by the via)."""
    cells = set(path)
    r = int(math.ceil((VIA_D / 2) / G))
    for (la, ja, ia), (lb, jb, ib) in zip(path, path[1:]):
        if la != lb:
            for l in LAYERS:
                for dj in range(-r, r + 1):
                    for di in range(-r, r + 1):
                        if dj * dj + di * di <= r * r and 0 <= ja + dj < NY and 0 <= ia + di < NX:
                            cells.add((l, ja + dj, ia + di))
    return cells


def rip(net):
    routed_tracks[:] = [t for t in routed_tracks if t['net'] != net]
    routed_vias[:] = [v for v in routed_vias if v['net'] != net]


def route_net(net, soft_mode=False, frozen=()):
    """Route every pad of net onto one tree. Returns (failed pads, victim nets). In soft mode a connection that finds
    no hard path may cross other signal nets' routed copper at a per-cell penalty; those nets become victims. Nets in
    frozen (just routed in this rip-up round) stay hard obstacles, so two nets cannot keep ripping each other."""
    global VIA_D
    VIA_D = 0.6 if net in POWER else 0.5
    hw = width(net) / 2
    ob = obstacles(net, hw)
    vok = via_ok(net)
    thin, softctx = None, None
    victims, failed = set(), []
    tree = {l: np.zeros((NY, NX), bool) for l in LAYERS}
    pending = list(nets[net])
    for z in pours:
        if z['net'] == net:
            for o in z['outlines']:
                mark_poly(tree[z['layer'][0]], o, 0.3, shrink=True)
    has_pour = tree['F'].any()
    groups = fixed_groups(net)
    side = []   # phase 14: with a pour, a fixed group that does not touch it joins the tree only through a routed pad
    for g in groups:
        if not has_pour or any((g[l] & tree[l]).any() for l in LAYERS):
            for l in LAYERS:
                tree[l] |= g[l]
        else:
            side.append(g)
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
        src = {l: pad_cells(p) if l in p['layers'] else np.zeros((NY, NX), bool) for l in LAYERS}
        for g in [g for g in side if any((g[l] & src[l]).any() for l in LAYERS)]:
            side.remove(g)
            for l in LAYERS:
                src[l] |= g[l]
            for q in list(pending):
                if any((g[l] & pad_cells(q)).any() for l in q['layers']):
                    pending.remove(q)
                    for l in q['layers']:
                        src[l] |= pad_cells(q)
        path = route(net, src, tree, ob, vok, hw) or route(net, src, tree, ob, vok, hw, W + H)
        used = hw
        if path is None and hw > 0.1:
            # a power-net pin that cannot escape at 0.4 mm (sense or supply pin between fine-pitch neighbours) gets 0.2 mm
            if thin is None:
                thin = (obstacles(net, 0.1), via_ok(net))
            path = route(net, src, tree, thin[0], thin[1], 0.1, W + H); used = 0.1
        if path is None and soft_mode:
            # rip-up: other signal nets' copper is passable at a cost; power-net branches stay hard obstacles
            if softctx is None:
                others = sorted({t['net'] for t in routed_tracks + routed_vias
                                 if t['net'] != net and (GND_TREE or t['net'] != 'GND') and (RIP_POWER or t['net'] not in POWER)
                                 and t['net'] not in frozen})
                masks = {o: copper_mask(o, hw) for o in others}
                hard = obstacles(net, hw, routed=False)
                for t in routed_tracks:
                    if t['net'] != net and t['net'] not in others:
                        mark_seg(hard[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
                for v in routed_vias:
                    if v['net'] != net and v['net'] not in others:
                        for l in LAYERS:
                            mark_seg(hard[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
                soft = {l: np.zeros((NY, NX), bool) for l in LAYERS}
                for o in others:
                    for l in LAYERS:
                        soft[l] |= masks[o][l]
                softctx = (masks, hard, soft)
            masks, hard, soft = softctx
            path = route(net, src, tree, hard, vok, hw, W + H, soft=soft, pen=RIP_PEN)
            if path is not None:
                cells = path_cells(path)
                for o, m in masks.items():
                    hit = [(l, j, i) for l, j, i in cells if m[l][j, i]]
                    if hit:
                        victims.add(o)
                        for l, j, i in hit:
                            HIST[l][j, i] += 1.0
        if path is None:
            failed.append(f"{net}: {p['ref']}.{p['num']}")
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
        for l in LAYERS:
            tree[l] |= src[l]
    return failed, victims


def fixed_groups(net):
    """Connected groups of the net's fixed tracks and vias (shared end points), as per-layer cell masks."""
    items = [('t', t) for t in FIXED_TRACKS if t['net'] == net] + [('v', v) for v in FIXED_VIAS if v['net'] == net]
    pts = [[tuple(x['a']), tuple(x['b'])] if k == 't' else [tuple(x['at'])] for k, x in items]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(len(items)):
        for j in range(i):
            if any(math.hypot(a[0] - b[0], a[1] - b[1]) < 0.01 for a in pts[i] for b in pts[j]):
                parent[find(i)] = find(j)
    out = {}
    for i, (k, x) in enumerate(items):
        g = out.setdefault(find(i), {l: np.zeros((NY, NX), bool) for l in LAYERS})
        if k == 't':
            mark_seg(g[x['layer']], x['a'], x['b'], x['w'] / 2)
        else:
            for l in LAYERS:
                mark_seg(g[l], x['at'], x['at'], x['d'] / 2 - G)
    return list(out.values())


def run(order):
    routed_tracks.clear(); routed_vias.clear()
    unrouted = {}
    if GND_TREE:
        f, _ = route_net('GND')
        if f:
            unrouted['GND'] = f
    elif GND_FIRST:
        ESC[:] = gnd_escapes()
    for net in order:
        if net == 'GND':
            continue
        f, _ = route_net(net)
        if f:
            unrouted[net] = f
    return unrouted


def score(unr):
    flat = [u for fs in unr.values() for u in fs]
    return (sum(u.split(':')[0] in POWER for u in flat), len(flat))


def settle(victims, frozen, depth, unrouted):
    """Reroute ripped victims: hard first, then soft with the nets already placed this round frozen (cascade)."""
    for o in sorted(victims, key=lambda n: (hpwl(nets[n]), n)):
        fo, _ = route_net(o)
        if fo and depth > 0:
            rip(o)
            fo, vv = route_net(o, soft_mode=True, frozen=frozen | {o})
            for x in vv:
                rip(x); unrouted.pop(x, None)
            settle(vv, frozen | {o}, depth - 1, unrouted)
        if fo:
            unrouted[o] = fo
        else:
            unrouted.pop(o, None)


def rip_up(unrouted, rounds):
    """Phase 13 rip-up and reroute: a failed net is ripped and rerouted in soft mode; every signal net it crosses is
    ripped and rerouted after it (hard first, then soft with the nets placed in this round frozen, three levels deep).
    The best state seen is kept."""
    best = (score(unrouted), list(routed_tracks), list(routed_vias), dict(unrouted))
    hist = {}
    queue = list(unrouted)
    tabu = {}   # net -> nets that ripped it; it may not rip them back
    for k in range(rounds):
        if not unrouted:
            break
        net = queue.pop(0) if queue else next(iter(unrouted))
        if net not in unrouted:
            continue
        hist[net] = hist.get(net, 0) + 1
        rip(net); unrouted.pop(net, None)
        f, victims = route_net(net, soft_mode=True, frozen=tabu.get(net, set()))
        for o in victims:
            rip(o); unrouted.pop(o, None)
            if TABU:
                tabu.setdefault(o, set()).add(net)
        if f:
            unrouted[net] = f
        settle(victims, {net} | tabu.get(net, set()), 3, unrouted)
        print('rip', k, net, sorted(victims), score(unrouted), file=sys.stderr, flush=True)
        if score(unrouted) < best[0]:
            best = (score(unrouted), list(routed_tracks), list(routed_vias), dict(unrouted))
        queue = [n for n in queue if n in unrouted] + [n for n in unrouted if n not in queue and hist.get(n, 0) < 6]
        if not queue:
            break
    _, t, v, u = best
    routed_tracks[:] = t; routed_vias[:] = v
    return u


def gnd_escapes():
    """Phase 13: every GND SMD pad without a GND via or PTH within 1.2 mm gets a short 0.2 mm track to a 0.5 mm via
    (the fills alone left four F.Cu islands floating in phase 12); the via search widens from 1.5 to 3 mm. Runs after the signals, so it never blocks them."""
    global VIA_D
    VIA_D, hw = 0.5, 0.1
    out, misses = [], []
    anchors = [v['at'] for v in geom['vias'] + routed_vias if v['net'] == 'GND']
    anchors += [p['center'] for p in geom['pads'] if p['net'] == 'GND' and p['drill']]
    for p in geom['pads']:
        if p['net'] != 'GND' or p['drill'] or p['ref'] == 'U1' and p['num'] == '25':
            continue
        if any(math.hypot(a[0] - p['center'][0], a[1] - p['center'][1]) <= 1.2 for a in anchors):
            continue
        ob = obstacles('GND', hw)
        vok = via_ok('GND')
        src = {l: pad_cells(p) for l in p['layers']}
        tgt = {l: vok & ~ob[l] for l in LAYERS if l in p['layers']}
        path = None
        for r in (1.5, 3.0):
            i0, i1, j0, j1 = window(p['center'][0], p['center'][1], p['center'][0], p['center'][1], r)
            near = np.zeros((NY, NX), bool); near[j0:j1, i0:i1] = True
            tr = {l: m & near & ~src[l] for l, m in tgt.items()}
            path = route('GND', src, tr, ob, np.zeros((NY, NX), bool), hw, r)
            if path is not None:
                break
        if path is None:
            misses.append(p)
            continue
        l, j, i = path[-1]
        t, _ = emit('GND', path, hw)
        v = {'net': 'GND', 'at': [round(i * G, 3), round(j * G, 3)], 'd': VIA_D}
        routed_tracks.extend(t); routed_vias.append(v); anchors.append(v['at'])
        out.append({'pad': f"{p['ref']}.{p['num']}", 'via': v['at']})
    # a pad with no via site nearby (under the F.Cu power pours, or between fine-pitch pins) gets a track on either
    # layer, with vias, to the nearest GND escape via or GND PTH pad
    for p in misses:
        VIA_D = 0.5
        ob = obstacles('GND', hw)
        vok = via_ok('GND')
        src = {l: pad_cells(p) for l in p['layers']}
        tree = {l: np.zeros((NY, NX), bool) for l in LAYERS}
        for v in routed_vias:
            if v['net'] == 'GND':
                for l in LAYERS:
                    mark_seg(tree[l], v['at'], v['at'], 0.2)
        for q in geom['pads']:
            if q['net'] == 'GND' and q['drill']:
                for l in q['layers']:
                    tree[l] |= pad_cells(q)
        path = route('GND', src, tree, ob, vok, hw, W + H)
        victims = set()
        if path is None:
            # rip-up: signal copper is passable at a cost; crossed nets are rerouted afterwards
            others = sorted({t['net'] for t in routed_tracks + routed_vias if t['net'] not in POWER and t['net'] != 'GND'})
            masks = {o: copper_mask(o, hw) for o in others}
            hard = obstacles('GND', hw, routed=False)
            for t in routed_tracks:
                if t['net'] not in others:
                    mark_seg(hard[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
            for v in routed_vias:
                if v['net'] not in others:
                    for l in LAYERS:
                        mark_seg(hard[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
            soft = {l: np.zeros((NY, NX), bool) for l in LAYERS}
            for o in others:
                for l in LAYERS:
                    soft[l] |= masks[o][l]
            vok_soft = via_ok_static('GND', set(others))
            path = route('GND', src, tree, hard, vok_soft, hw, W + H, soft=soft, pen=RIP_PEN)
            if path is not None:
                cells = path_cells(path)
                for o, m in masks.items():
                    if any(m[l][j, i] for l, j, i in cells):
                        victims.add(o)
        if path is None:
            out.append({'pad': f"{p['ref']}.{p['num']}", 'via': None, 'track_to_anchor': False})
            continue
        for o in victims:
            rip(o)
        t, vs = emit('GND', path, hw)
        routed_tracks.extend(t); routed_vias.extend(vs)
        end = path[-1]
        out.append({'pad': f"{p['ref']}.{p['num']}", 'via': None, 'track_to_anchor': True,
                    'anchor_cell_mm': [round(end[2] * G, 3), round(end[1] * G, 3)], 'vias': [v['at'] for v in vs],
                    'rerouted_nets': sorted(victims)})
        if victims:
            unr = {}
            settle(victims, {'GND'}, 3, unr)
            for n, fs in unr.items():
                GND_UNROUTED.setdefault(n, []).extend(fs)
    return out


def gnd_join(detached):
    """Phase 13: join each GND cluster that the fills left detached (route-power.py report) to the main GND with a
    0.2 mm track, from its pads and vias to any GND via or pad outside the detached clusters. Signal copper may be
    ripped and is rerouted afterwards; when a ripped net cannot be rerouted, the join is undone and retried with that
    net held fixed (up to eight tries)."""
    global VIA_D
    out = []
    bad_pads = {p for d in detached for p in d['pads']}
    bad_vias = [tuple(v) for d in detached for v in d['vias']]
    for d in detached:
        keep = set()
        for attempt in range(8):
            VIA_D, hw = 0.5, 0.1
            snap = (list(routed_tracks), list(routed_vias))
            src = {l: np.zeros((NY, NX), bool) for l in LAYERS}
            for p in geom['pads']:
                if f"{p['ref']}.{p['num']}" in d['pads']:
                    for l in p['layers']:
                        src[l] |= pad_cells(p)
            for v in d['vias']:
                for l in LAYERS:
                    mark_seg(src[l], v, v, 0.2)
            tree = {l: np.zeros((NY, NX), bool) for l in LAYERS}
            for v in routed_vias + geom['vias']:
                if v['net'] == 'GND' and not any(math.hypot(v['at'][0] - b[0], v['at'][1] - b[1]) < 0.05 for b in bad_vias):
                    for l in LAYERS:
                        mark_seg(tree[l], v['at'], v['at'], 0.2)
            for p in geom['pads']:
                if p['net'] == 'GND' and f"{p['ref']}.{p['num']}" not in bad_pads:
                    for l in p['layers']:
                        tree[l] |= pad_cells(p)
            path = route('GND', src, tree, obstacles('GND', hw), via_ok('GND'), hw, W + H)
            victims = set()
            if path is None:
                # power-net branch tracks may be ripped here too (the pours stay fixed)
                others = sorted({t['net'] for t in routed_tracks + routed_vias
                                 if t['net'] != 'GND' and t['net'] not in keep})
                masks = {o: copper_mask(o, hw) for o in others}
                hard = obstacles('GND', hw, routed=False)
                for t in routed_tracks:
                    if t['net'] not in others:
                        mark_seg(hard[t['layer']], t['a'], t['b'], CL + hw + t['w'] / 2 + MARGIN)
                for v in routed_vias:
                    if v['net'] not in others:
                        for l in LAYERS:
                            mark_seg(hard[l], v['at'], v['at'], CL + hw + v['d'] / 2 + MARGIN)
                soft = {l: np.zeros((NY, NX), bool) for l in LAYERS}
                for o in others:
                    for l in LAYERS:
                        soft[l] |= masks[o][l]
                path = route('GND', src, tree, hard, via_ok_static('GND', set(others)), hw, W + H, soft=soft, pen=RIP_PEN)
                if path is not None:
                    cells = path_cells(path)
                    victims = {o for o, m in masks.items() if any(m[l][j, i] for l, j, i in cells)}
            if path is None:
                break
            for o in victims:
                rip(o)
            t, vs = emit('GND', path, hw)
            routed_tracks.extend(t); routed_vias.extend(vs)
            unr = {}
            if victims:
                settle(victims, {'GND'}, 3, unr)
            if not unr:
                out.append({'cluster_pads': d['pads'], 'joined': True, 'rerouted_nets': sorted(victims), 'tries': attempt + 1})
                break
            if JOIN_FORCE and attempt == 7:
                # phase 14: keep the last join and hand the nets it displaced to the closing rip-up
                JOIN_PENDING.update(unr)
                out.append({'cluster_pads': d['pads'], 'joined': True, 'rerouted_nets': sorted(victims), 'tries': attempt + 1,
                            'displaced': sorted(unr)})
                break
            routed_tracks[:], routed_vias[:] = snap
            keep |= set(unr)
            path = None
        if path is None:
            out.append({'cluster_pads': d['pads'], 'joined': False, 'held_fixed': sorted(keep)})
    return out


# passes: the first pass routes the power branches first; later passes move the nets that failed to the front (odd
# passes shuffle the rest with a fixed seed); the pass with the fewest power-net, then total, unrouted connections is
# kept, then rip-up and reroute works on what is left
RIP_PEN = float(os.environ.get('R3_RIP_PEN', 6.0))
TABU = os.environ.get('R3_TABU', '1') == '1'
GND_FIRST = os.environ.get('R3_GND_FIRST', '1') == '1'   # GND pad escapes before the signals (phase 13 default)
GND_TREE = os.environ.get('R3_GND_TREE', '0') == '1'
RIP_POWER = os.environ.get('R3_RIP_POWER', '1') == '1'   # phase 14: power-net branch tracks (not pours) may be ripped too
JOIN_FORCE = os.environ.get('R3_JOIN_FORCE', '1') == '1'   # phase 14: a join that displaces signals is kept, then rip-up
JOIN_PENDING = {}
JOIN = os.environ.get('R3_JOIN_REPORT')   # second run.sh pass: join the GND clusters route-power.py left detached
if GND_TREE:
    nets['GND'] = [p for p in geom['pads'] if p['net'] == 'GND']
ESC = []
order = sorted(nets, key=lambda n: (n not in POWER, hpwl(nets[n]), n))
best = None
rng = random.Random(int(os.environ.get('R3_SEED', 12)))   # run.sh steps the seed when a run leaves connections open
CACHE = sys.argv[6] if len(sys.argv) > 6 else None
for k in range(0 if JOIN or CACHE and os.path.exists(CACHE) else (int(sys.argv[4]) if len(sys.argv) > 4 else 6)):
    unr = run(order)
    print(k, score(unr), unr, file=sys.stderr, flush=True)
    if best is None or score(unr) < best[0]:
        best = (score(unr), list(routed_tracks), list(routed_vias), dict(unr), list(order))
    if not unr:
        break
    failed = list(unr)
    rest = [n for n in order if n not in failed]
    if k % 2:
        rng.shuffle(rest)
    order = failed + rest
if JOIN:
    c = json.load(open(os.environ['R3_JOIN_ROUTES']))
    best = (None, [], [], {}, c['report']['net_order'])
elif best is None:
    c = json.load(open(CACHE))
    best = (None, c['tracks'], c['vias'], c['unrouted'], c['order'])
_, t, v, unr, order = best
routed_tracks[:] = t; routed_vias[:] = v
if CACHE and not os.path.exists(CACHE):
    # development cache of the pass stage (same geometry and pours only); run.sh does not use it
    json.dump({'tracks': t, 'vias': v, 'unrouted': unr, 'order': order}, open(sys.argv[6], 'w'))
if not JOIN:
    unr = rip_up(unr, int(sys.argv[5]) if len(sys.argv) > 5 else 60)
if JOIN:
    prev = json.load(open(os.environ['R3_JOIN_ROUTES']))
    routed_tracks[:] = [t for t in prev['tracks'] if t not in FIXED_TRACKS]
    routed_vias[:] = [v for v in prev['vias'] if v not in FIXED_VIAS]
    esc = prev['report'].get('gnd_escapes', [])
    joins = gnd_join(json.load(open(JOIN))['gnd_clusters_detached'])
    unr = {}
    for u in prev['report']['unrouted']:
        unr.setdefault(u.split(':')[0], []).append(u)
    if JOIN_FORCE:
        for n in list(unr) + list(JOIN_PENDING):
            rip(n)
        unr = {n: unr.get(n, JOIN_PENDING.get(n)) for n in set(unr) | set(JOIN_PENDING)}
        for n in sorted(unr):
            f, _ = route_net(n)
            if f:
                unr[n] = f
            else:
                unr.pop(n)
        if unr:
            unr = rip_up(unr, int(sys.argv[5]) if len(sys.argv) > 5 else 60)
else:
    joins = []
    esc = [] if GND_TREE else (ESC if GND_FIRST else gnd_escapes())
if GND_UNROUTED:
    unr = rip_up({**unr, **GND_UNROUTED}, 30)
flat = [u for fs in unr.values() for u in fs]
rep = {'unrouted': flat, 'net_order': order, 'gnd_escapes': esc, 'gnd_joins': prev['report'].get('gnd_joins', []) + joins if JOIN else [],
       'routed_nets': sorted(n for n in nets if n not in unr)}
t = FIXED_TRACKS + routed_tracks
json.dump({'tracks': t, 'vias': FIXED_VIAS + routed_vias, 'report': rep}, open(sys.argv[3], 'w'), indent=1)
print(json.dumps({'tracks': len(t), 'vias': len(FIXED_VIAS) + len(routed_vias), 'unrouted': flat,
                  'gnd_escapes': sum(e['via'] is not None for e in esc), 'gnd_tracks_to_anchor': [e['pad'] for e in esc if e.get('track_to_anchor')],
                  'gnd_escape_misses': [e['pad'] for e in esc if e['via'] is None and not e.get('track_to_anchor')]}))
