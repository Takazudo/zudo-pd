import os
exec(open('/tmp/claude-0/plan_work/planner.py').read().replace('box(-1.19,-0.75,1.19,0.75)', os.environ.get('CYD','box(-1.19,-0.75,1.19,0.75)')))
import shapely, time, collections, os
from scipy import ndimage
G = 0.025
RAD = float(os.environ.get('RAD', '3.5'))
CLR = 0.2
M = 0.03          # raster safety margin
HOLE_CL = 0.25
VDRILL = 0.3
LAY = {L: layer_objs(L) for L in ('F.Cu', 'In2.Cu', 'B.Cu')}
holes = [(v['p'], VDRILL / 2) for v in vias]
PAD_HALF = (0.283, 0.27)
PAD_DX = 0.43
CY_HALF = tuple(map(float, os.environ.get('CYH', '1.19,0.75').split(',')))
ONLY = os.environ.get('ONLY')
def t_skip(div):
    return (ONLY and div not in ONLY.split(',')) or (os.environ.get('ORDER') and div not in os.environ['ORDER'].split(','))


def raster(geoms, x0, y0, nx, ny):
    xs = x0 + np.arange(nx) * G
    ys = y0 + np.arange(ny) * G
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    pts = shapely.points(XX.ravel(), YY.ravel())
    u = unary_union(geoms) if geoms else None
    if u is None or u.is_empty:
        return np.zeros((nx, ny), bool)
    shapely.prepare(u)
    return shapely.intersects(u, pts).reshape(nx, ny)


def rect_mask(cx, cy, hx, hy, x0, y0, nx, ny):
    i0 = max(0, int(np.floor((cx - hx - x0) / G))); i1 = min(nx, int(np.ceil((cx + hx - x0) / G)) + 1)
    j0 = max(0, int(np.floor((cy - hy - y0) / G))); j1 = min(ny, int(np.ceil((cy + hy - y0) / G)) + 1)
    return i0, i1, j0, j1


def bfs(free, starts, goals):
    nx, ny = free.shape
    prev = -np.ones(nx * ny, np.int64)
    seen = np.zeros(nx * ny, bool)
    q = collections.deque()
    for i, j in zip(*np.nonzero(starts & free)):
        k = i * ny + j; seen[k] = True; q.append(k)
    gl = (goals & free).ravel()
    if not q or not gl.any():
        return None
    fr = free.ravel()
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while q:
        k = q.popleft()
        if gl[k]:
            path = []
            while k != -1:
                path.append((k // ny, k % ny)); k = prev[k]
            return path[::-1]
        i, j = divmod(k, ny)
        for di, dj in steps:
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny:
                kk = a * ny + b
                if fr[kk] and not seen[kk]:
                    seen[kk] = True; prev[kk] = k; q.append(kk)
    return None


def los(path, free):
    out = [path[0]]; k = 0
    while k < len(path) - 1:
        best = k + 1
        for m in range(len(path) - 1, k, -1):
            (i0, j0), (i1, j1) = path[k], path[m]
            n = int(max(abs(i1 - i0), abs(j1 - j0)) * 2) + 1
            ok = all(free[int(round(i0 + (i1 - i0) * t / n)), int(round(j0 + (j1 - j0) * t / n))] for t in range(n + 1))
            if ok:
                best = m; break
        out.append(path[best]); k = best
    return out


def path_points(div, v0):
    ins = [s for s in segs if s['layer'] == 'In2.Cu' and s['net'] == div]
    out = [(0.0, v0, [], None)]; cur = v0; used = []; dist = 0
    while True:
        nxt = [s for s in ins if id(s) not in used and (math.dist(s['a'], cur) < 0.45 or math.dist(s['b'], cur) < 0.45)]
        if not nxt or dist > 6:
            break
        s = nxt[0]; used.append(id(s))
        a, b = (s['a'], s['b']) if math.dist(s['a'], cur) < math.dist(s['b'], cur) else (s['b'], s['a'])
        L = math.dist(a, b); n = max(1, int(L / 0.1))
        for k in range(1, n + 1):
            t = k / n; q = (round(a[0] + (b[0] - a[0]) * t, 2), round(a[1] + (b[1] - a[1]) * t, 2))
            out.append((dist + L * t, q, list(used[:-1]), (s, a, b, q)))
        dist += L; cur = b
    return out, ins


plans = {}
placed = []      # (geom, net)
newcourts = []
ORDER = os.environ.get('ORDER', '').split(',') if os.environ.get('ORDER') else [t[0] for t in TARGETS]
for div, new, ic, pin in sorted(TARGETS, key=lambda t: ORDER.index(t[0]) if t[0] in ORDER else 99):
    if t_skip(div):
        continue
    T0 = time.time()
    pad, chain, vend = stub_chain(div, ic, pin); v0 = vend[0]['p']
    chainkeys = {('seg', s['a'], s['b']) for s in chain}
    pinpoly = padpoly(pad); px, py = pad['c']
    W = 6.0
    x0, y0 = px - W, py - W
    nx = ny = int(2 * W / G) + 1
    LB = box(px - W - 1, py - W - 1, px + W + 1, py + W + 1)

    def objs(layer, skipnets, skipvia=True):
        g = [o for o, n, tag in LAY[layer] if n not in skipnets and tag not in chainkeys and o.intersects(LB)
             and not (tag[0] == 'pad' and tag[1] == ic and tag[2] == pin) and not (skipvia and tag == ('via', v0))]
        g += [o for o, n in placed if n not in skipnets]
        return g
    # copper of other nets on F (for DIV routing): excludes DIV-net copper
    F_notdiv = raster(objs('F.Cu', {div}), x0, y0, nx, ny)
    F_notin = raster(objs('F.Cu', {new}), x0, y0, nx, ny)     # includes DIV copper (remaining)
    pinmask = raster([pinpoly], x0, y0, nx, ny)
    dist_notdiv = ndimage.distance_transform_edt(~F_notdiv) * G
    cmask = raster([c for c, _ in courts] + newcourts, x0, y0, nx, ny)
    allotherF = objs('F.Cu', set())
    oIn2 = unary_union(objs('In2.Cu', {div})); oB = unary_union(objs('B.Cu', {div})); oFd = unary_union(objs('F.Cu', {div}))
    pts, ins = path_points(div, v0)
    if os.environ.get('EXTEND', '') and div in os.environ['EXTEND'].split(','):
        end = [e for s in ins for e in (s['a'], s['b']) if math.dist(e, v0) < 0.45][0]
        wdt = [s['w'] for s in ins if math.dist(s['a'], v0) < 0.45 or math.dist(s['b'], v0) < 0.45][0]
        ext = []
        for ex in np.arange(-2.5, 2.51, 0.1):
            for ey in np.arange(-2.5, 2.51, 0.1):
                q = (round(v0[0] + ex, 2), round(v0[1] + ey, 2))
                ext.append((math.hypot(ex, ey), q, [], ('extend', end, wdt)))
        ext.sort(key=lambda e: e[0])
        pts = [pts[0]] + ext
    best = None
    stats = collections.Counter()
    for d, vp, usedsegs, cut in pts:
        if d > 6:
            break
        if best and d > best[0]:
            break
        vpoly = Point(vp).buffer(VIA / 2)
        if any(vpoly.distance(o) < CLR - 1e-3 for o in (oIn2, oB, oFd) if not o.is_empty):
            continue
        if cut and cut[0] == 'extend':
            ext = LineString([cut[1], vp]).buffer(cut[2] / 2)
            if ext.distance(oIn2) < CLR - 1e-3:
                continue
        if any(math.dist(vp, h) < VDRILL / 2 + r + HOLE_CL for h, r in holes if math.dist(h, v0) > 1e-3):
            continue
        if vpoly.distance(pinpoly) < CLR - 1e-3:
            continue
        stats['via_ok'] += 1
        vmask = raster([vpoly], x0, y0, nx, ny)
        # IN-route obstacles: all non-IN copper incl. DIV via; distance field
        base_in = F_notin | vmask
        dist_in = ndimage.distance_transform_edt(~base_in) * G
        found = None
        for rot in (0, 90):
            for sx in np.arange(-RAD, RAD + 0.01, 0.1):
                for sy in np.arange(-RAD, RAD + 0.01, 0.1):
                    cx, cy = round(px + sx, 2), round(py + sy, 2)
                    hx, hy = (CY_HALF if rot == 0 else CY_HALF[::-1])
                    i0, i1, j0, j1 = rect_mask(cx, cy, hx - 0.01, hy - 0.01, x0, y0, nx, ny)
                    if cmask[i0:i1, j0:j1].any():
                        continue
                    for flip in (1, -1):
                        ax, ay = ((flip * PAD_DX, 0) if rot == 0 else (0, flip * PAD_DX))
                        p1c = (cx - ax, cy - ay); p2c = (cx + ax, cy + ay)   # p1 DIV, p2 IN
                        phx, phy = (PAD_HALF if rot == 0 else PAD_HALF[::-1])
                        a = rect_mask(*p1c, phx, phy, x0, y0, nx, ny); b = rect_mask(*p2c, phx, phy, x0, y0, nx, ny)
                        if dist_notdiv[a[0]:a[1], a[2]:a[3]].min() < CLR + M:
                            continue
                        if dist_in[b[0]:b[1], b[2]:b[3]].min() < CLR + M:
                            continue
                        p1 = box(p1c[0] - phx, p1c[1] - phy, p1c[0] + phx, p1c[1] + phy)
                        p2 = box(p2c[0] - phx, p2c[1] - phy, p2c[0] + phx, p2c[1] + phy)
                        if p1.distance(pinpoly) < CLR + M or p1.distance(vpoly) < CLR or p2.distance(vpoly) < CLR + M:
                            continue
                        stats['cand'] += 1
                        score = p2.distance(pinpoly) + p1.distance(vpoly)
                        cands_key = (score, cx, cy, rot, flip, p1c, p2c, p1, p2)
                        if found is None:
                            found = [cands_key]
                        else:
                            found.append(cands_key)
        if not found:
            continue
        found.sort(key=lambda c: c[0])
        for score, cx, cy, rot, flip, p1c, p2c, p1, p2 in found[:60]:
            p1m = raster([p1], x0, y0, nx, ny); p2m = raster([p2], x0, y0, nx, ny)
            # IN route: centre cells at >= CLR+TW/2 from non-IN copper and from the new DIV pad
            dist_in2 = ndimage.distance_transform_edt(~(base_in | p1m)) * G
            free_in = dist_in2 >= CLR + TW / 2 + M
            r_in = bfs(free_in, p2m, pinmask)
            if not r_in:
                stats['no_in'] += 1
                continue
            r_in = los(r_in, free_in); rin_pts = [(x0 + i * G, y0 + j * G) for i, j in r_in]
            rin_poly = (LineString(rin_pts) if len(rin_pts) > 1 else Point(rin_pts[0])).buffer(TW / 2)
            div_obs = F_notdiv | raster([rin_poly, p2, pinpoly], x0, y0, nx, ny)
            dist_div = ndimage.distance_transform_edt(~div_obs) * G
            free_div = dist_div >= CLR + TW / 2 + M
            r_div = bfs(free_div, p1m, vmask)
            if not r_div:
                stats['no_div'] += 1
                continue
            r_div = los(r_div, free_div); rdiv_pts = [(x0 + i * G, y0 + j * G) for i, j in r_div]
            L = (LineString(rin_pts).length if len(rin_pts) > 1 else 0) + (LineString(rdiv_pts).length if len(rdiv_pts) > 1 else 0) + 0.5 * d
            if best is None or L < best[0]:
                best = (L, d, vp, cut, usedsegs, cx, cy, rot, flip, p1c, p2c, rin_pts, rdiv_pts, p1, p2)
            break
    print(div, dict(stats), round(time.time() - T0, 1), flush=True)
    if not best:
        print(div, 'NO ROUTE', flush=True); continue
    L, d, vp, cut, usedsegs, cx, cy, rot, flip, p1c, p2c, rin, rdiv, p1, p2 = best
    rin_s = simplify([(round(a, 3), round(b, 3)) for a, b in rin]); rdiv_s = simplify([(round(a, 3), round(b, 3)) for a, b in rdiv])
    print(div, 'via d', round(d, 2), vp, 'R', cx, cy, rot, flip, 'L', round(L, 2), 'in', rin_s, 'div', rdiv_s, flush=True)
    cutd = None
    if cut and cut[0] == 'extend':
        cutd = dict(extend_from=list(cut[1]), width=cut[2])
    elif cut:
        s, a, b, q = cut; cutd = dict(seg=[s['a'], s['b']], width=s['w'], keep_from=list(q), keep_to=list(b))
    plans[div] = dict(new_net=new, ic=ic, pin=pin, pin_center=list(pad['c']), center=[cx, cy], rot=rot, flip=flip,
                      p1=list(p1c), p2=list(p2c), old_via=list(v0), new_via=list(vp),
                      remove_f=[[s['a'], s['b'], s['w']] for s in chain],
                      remove_in2=[[s['a'], s['b'], s['w']] for s in ins if id(s) in usedsegs], cut_in2=cutd,
                      route_in=rin_s, route_div=rdiv_s)
    placed += [(p1, div), (p2, new), (LineString(rin).buffer(TW / 2) if len(rin) > 1 else p2, new),
               (LineString(rdiv).buffer(TW / 2) if len(rdiv) > 1 else p1, div), (Point(vp).buffer(VIA / 2), div)]
    hx, hy = (CY_HALF if rot == 0 else CY_HALF[::-1])
    newcourts.append(box(cx - hx, cy - hy, cx + hx, cy + hy))
json.dump(plans, open(os.environ.get('PLAN_OUT', '/tmp/claude-0/plan_work/plan.json'), 'w'), indent=1)
print('done', flush=True)
