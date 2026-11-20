"""Grid router for the D2 back-side insert, reusing scripts/pcb/board-b20/astar.c (tmp working copy)."""
import ctypes, hashlib, json, math, os, subprocess, sys, tempfile
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__)); import d2lib as L
G = 0.05
W, H = 110.0, 85.0
NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
LAYERS = ['F.Cu', 'In2.Cu', 'B.Cu']
CL = 0.2; VIA_D = 0.8; VIA_DRILL = 0.3

def _so():
    src = L.ROOT / 'scripts/pcb/board-b20/astar.c'
    lib = os.path.join(tempfile.gettempdir(), 'd2-astar.so')
    if not os.path.exists(lib):
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', '-o', lib, str(src), '-lm'], check=True)
    so = ctypes.CDLL(lib); pp = ctypes.POINTER(ctypes.c_void_p)
    so.astar.restype = ctypes.c_int
    so.astar.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, pp, np.ctypeslib.ndpointer(np.uint8, flags='C_CONTIGUOUS'), pp, pp, pp,
                         np.ctypeslib.ndpointer(np.float64, flags='C_CONTIGUOUS'), ctypes.c_double,
                         np.ctypeslib.ndpointer(np.int32, flags='C_CONTIGUOUS'), ctypes.c_int]
    return so
SO = _so()

def cells_poly(poly):
    x0, y0, x1, y1 = poly.bounds
    i0, i1 = max(0, int(x0 / G) - 1), min(NX - 1, int(x1 / G) + 2)
    j0, j1 = max(0, int(y0 / G) - 1), min(NY - 1, int(y1 / G) + 2)
    from shapely import vectorized
    xs, ys = np.meshgrid(np.arange(i0, i1) * G, np.arange(j0, j1) * G)
    m = vectorized.contains(poly, xs, ys)
    return j0, i0, m

class Router:
    def __init__(self, geom, placed, drop_nets=(), drop_refs=(), drop_vias=()):
        self.nets = {'': 0}
        self.cu = {l: np.zeros((NY, NX), np.int32) for l in LAYERS}   # net id + 1 ; -1 = hard (all nets)
        self.items = []  # new copper
        g = geom
        dv = [tuple(x) for x in drop_vias]
        g = dict(g); g['vias'] = [v for v in g['vias'] if not any(abs(v['c'][0]-a) < 0.02 and abs(v['c'][1]-b) < 0.02 for a, b in dv)]
        from shapely.geometry import LineString, Point, Polygon, box
        def nid(n):
            if n not in self.nets: self.nets[n] = len(self.nets)
            return self.nets[n]
        def paint(layer, poly, net):
            j0, i0, m = cells_poly(poly)
            sub = self.cu[layer][j0:j0 + m.shape[0], i0:i0 + m.shape[1]]
            sub[m] = nid(net) if net is not None else -1
        self.paint = paint
        self.holes = [tuple(v['c']) for v in g['vias'] if v['net'] not in drop_nets] + [tuple(p['c']) for f in g['fps'] if f['ref'] not in drop_refs for p in f['pads'] if p['drill'] > 0]
        for t in g['tracks']:
            if t['net'] in drop_nets: continue
            if t['l'] in LAYERS: paint(t['l'], LineString([t['a'], t['b']]).buffer(t['w'] / 2, cap_style=1) if t['a'] != t['b'] else Point(t['a']).buffer(t['w'] / 2), t['net'])
        for v in g['vias']:
            if v['net'] in drop_nets: continue
            for l in LAYERS: paint(l, Point(v['c']).buffer(v['d'] / 2), v['net'])
        for f in g['fps']:
            if f['ref'] in drop_refs: continue
            for p in f['pads']:
                lay = [l for l in LAYERS if (l[0] if l != 'In2.Cu' else 'In2') in p['layers']] if p['drill'] == 0 else LAYERS
                if p['drill'] > 0 and not p['net']:   # NPTH / mounting hole
                    for l in LAYERS: paint(l, box(*p['bbox']).buffer(0.25), None)
                    continue
                for l in lay: paint(l, box(*p['bbox']), p['net'] if p['net'] else '#NC')
            if f['ref'].startswith('H'):
                paint('B.Cu', Point(f['at']).buffer(3.0), None)    # screw head / collar on the back (Fab circle)
        for z in g['zones']:
            if z['rule'] or z['net'] in ('GND', ''): continue
            for l in z['layers']:
                if l in LAYERS: paint(l, Polygon(z['pts']), z['net'])
        for q in placed:
            for p in q['pads']:
                paint('B.Cu', Polygon(p['poly']), p['net'] or '#NC')
        for l in LAYERS:   # board edge
            c = self.cu[l]; e = int(0.5 / G)
            c[:e, :] = -1; c[-e:, :] = -1; c[:, :e] = -1; c[:, -e:] = -1

    def via_ok(self, net):
        vr = self.free(net, VIA_D / 2)
        ok = vr['F.Cu'] & vr['In2.Cu'] & vr['B.Cu']
        hm = np.zeros((NY, NX), bool)
        for x, y in self.holes:
            hm[int(round(y / G)), int(round(x / G))] = True
        d = ndimage.distance_transform_edt(~hm) * G
        return ok & (d >= 0.65)

    def free(self, net, hw, layers=LAYERS, box=None):
        n = self.nets.get(net, -99)
        out = {}
        for l in layers:
            foreign = (self.cu[l] != 0) & (self.cu[l] != n)
            d = ndimage.distance_transform_edt(~foreign) * G
            out[l] = d >= hw + CL + 0.07
        return out

    def route(self, net, src, dst, w, layers=LAYERS, lc=None, vcost=1.5, allow_via=True, label=''):
        """src/dst: list of (layer, shapely polygon). Returns path or None."""
        hw = w / 2
        fr = self.free(net, hw)
        vok = self.via_ok(net)
        if not allow_via: vok[:] = False
        S = {l: np.zeros((NY, NX), np.uint8) for l in LAYERS}; D = {l: np.zeros((NY, NX), np.uint8) for l in LAYERS}
        for arr, items in ((S, src), (D, dst)):
            for l, poly in items:
                j0, i0, m = cells_poly(poly)
                arr[l][j0:j0 + m.shape[0], i0:i0 + m.shape[1]] |= m.astype(np.uint8)
        for l in LAYERS:
            if l not in layers: fr[l][:] = False
            fr[l] |= (S[l] | D[l]).astype(bool) & (self.cu[l] == self.nets.get(net, -99))
            fr[l] |= (S[l] | D[l]).astype(bool)
        keep = []
        def ptrs(arrs, dt):
            o = (ctypes.c_void_p * 3)()
            for k, a in enumerate(arrs):
                if a is None: o[k] = None; continue
                a = np.ascontiguousarray(a, dtype=dt); keep.append(a); o[k] = a.ctypes.data
            return ctypes.cast(o, ctypes.POINTER(ctypes.c_void_p))
        lcv = np.array(lc or [3.0, 1.5, 1.0], np.float64)
        cap = 3 * NX * NY; out = np.zeros(cap, np.int32)
        n = SO.astar(NX, NY, 3, ptrs([fr[l] for l in LAYERS], np.uint8), np.ascontiguousarray(vok, np.uint8),
                     ptrs([S[l] for l in LAYERS], np.uint8), ptrs([D[l] for l in LAYERS], np.uint8), ptrs([None] * 3, np.float32),
                     lcv, vcost / G, out, cap)
        if n <= 0:
            print('FAIL', label, net); return None
        N = NX * NY
        path = [(LAYERS[v // N], ((v % N) % NX) * G, ((v % N) // NX) * G) for v in out[:n].tolist()]
        segs = self.emit(path, net, w, fr)
        print('OK', label, net, 'len %.1f' % sum(math.dist(s[1], s[2]) for s in segs if s[0] == 't'), 'vias', sum(1 for s in segs if s[0] == 'v'))
        return segs

    def emit(self, path, net, w, fr):
        from shapely.geometry import LineString, Point
        segs = []; run = [path[0]]
        def flush(run):
            pts = [(x, y) for _, x, y in run]
            l = run[0][0]
            # taut pull: greedy furthest visible point
            k = 0; out = [pts[0]]
            while k < len(pts) - 1:
                best = k + 1
                for m in range(len(pts) - 1, k + 1, -1):
                    if self.line_ok(pts[k], pts[m], fr[l]): best = m; break
                out.append(pts[best]); k = best
            for a, b in zip(out, out[1:]):
                if a != b: segs.append(('t', a, b, l, w))
        for q in path[1:]:
            if q[0] != run[-1][0]:
                flush(run); segs.append(('v', (q[1], q[2])))
                run = [q]
            else: run.append(q)
        flush(run)
        self.commit(net, segs)
        return segs

    def line_ok(self, a, b, m):
        n = int(math.dist(a, b) / (G / 2)) + 1
        for k in range(n + 1):
            t = k / n; x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
            i, j = int(round(x / G)), int(round(y / G))
            if not m[j, i]: return False
        return True

    def commit(self, net, segs):
        from shapely.geometry import LineString, Point
        for s in segs:
            if s[0] == 't':
                self.paint(s[3], LineString([s[1], s[2]]).buffer(s[4] / 2), net)
            else:
                for l in LAYERS: self.paint(l, Point(s[1]).buffer(VIA_D / 2), net)
                self.holes.append(tuple(s[1]))
            self.items.append((net,) + s)

def mask_of(items):
    """items: list of (layer, polygon) -> dict layer->bool mask"""
    M = {l: np.zeros((NY, NX), bool) for l in LAYERS}
    for l, poly in items:
        j0, i0, m = cells_poly(poly)
        M[l][j0:j0 + m.shape[0], i0:i0 + m.shape[1]] |= m
    return M

def seg_items(segs):
    from shapely.geometry import LineString, Point
    out = []
    for s in segs or []:
        if s[0] == 't': out.append((s[3], LineString([s[1], s[2]]).buffer(s[4] / 2)))
        else: out += [(l, Point(s[1]).buffer(VIA_D / 2)) for l in LAYERS]
    return out

def tree(r, net, terms, w, root=None, **kw):
    """terms: list of [(layer, poly)] per terminal. root: [(layer, poly)] existing copper to join. Returns ok flag."""
    conn = list(root) if root else list(terms[0])
    rest = terms if root else terms[1:]
    ok = True
    for k, t in enumerate(rest):
        segs = r.route(net, t, conn, w, label=f'{net}#{k}', **kw)
        if segs is None and w > 0.25:
            segs = r.route(net, t, conn, max(0.25, w / 2), label=f'{net}#{k} narrow', **kw)
        if segs is None: ok = False; continue
        conn += t + seg_items(segs)
    return ok

def stitch(r, net, poly, n=2, reach=2.5, w=0.6, layer='B.Cu'):
    """Add up to n vias near a pad polygon, each joined by a straight track."""
    from shapely.geometry import Point, LineString
    tr = r.free(net, w / 2)
    vok = r.via_ok(net)
    c = poly.centroid
    cand = []
    x0, y0, x1, y1 = poly.buffer(reach).bounds
    for j in range(int(y0 / G), int(y1 / G)):
        for i in range(int(x0 / G), int(x1 / G)):
            if vok[j, i]:
                p = Point(i * G, j * G); d = poly.distance(p)
                if 0.45 <= d <= reach: cand.append((d, i * G, j * G))
    cand.sort(); got = []
    for d, x, y in cand:
        if any(math.dist((x, y), g) < 1.1 for g in got): continue
        q = poly.exterior.interpolate(poly.exterior.project(Point(x, y)))
        a = (q.x, q.y)
        if not r.line_ok(a, (x, y), tr[layer]): continue
        segs = [('t', a, (x, y), layer, w), ('v', (x, y))]
        r.commit(net, segs); got.append((x, y))
        tr = r.free(net, w / 2); vok = r.via_ok(net)
        if len(got) >= n: break
    print('stitch', net, len(got), [tuple(round(v, 2) for v in g) for g in got])
    return got

def twins(r, net, segs, n=2, w=0.8):
    """For each via in segs, add up to n extra vias joined to it on the two layers it connects."""
    from shapely.geometry import Point
    out = []
    for k, s in enumerate(segs or []):
        if s[0] != 'v': continue
        la = next((t[3] for t in reversed(segs[:k]) if t[0] == 't'), None)
        lb = next((t[3] for t in segs[k + 1:] if t[0] == 't'), None)
        lays = [l for l in (la, lb) if l]
        tr = {l: r.free(net, w / 2, layers=[l])[l] for l in lays}
        vok = r.via_ok(net)
        x, y = s[1]; got = []
        for ang in range(0, 360, 15):
            for d in (1.05, 1.3, 1.6):
                px, py = x + d * math.cos(math.radians(ang)), y + d * math.sin(math.radians(ang))
                i, j = int(round(px / G)), int(round(py / G))
                if not vok[j, i] or any(math.dist((px, py), q) < 1.05 for q in got): continue
                if all(r.line_ok((x, y), (px, py), tr[l]) for l in lays):
                    sg = [('v', (px, py))] + [('t', (x, y), (px, py), l, w) for l in lays]
                    r.commit(net, sg); got.append((px, py))
                    vok = r.via_ok(net)
                    tr = {l: r.free(net, w / 2, layers=[l])[l] for l in lays}
                    break
            if len(got) >= n: break
        out.append(((x, y), got))
    print('twins', net, [(tuple(round(v, 2) for v in a), len(b)) for a, b in out])
    return out
