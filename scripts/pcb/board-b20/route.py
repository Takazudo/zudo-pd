"""Phase 21 host-side grid router for the B20 placement draft (two layers, 45-degree moves, through vias).

usage: uv run --python 3.12 --with numpy --with scipy python route.py <geom.json> <routes.json>

geom.json comes from dump-geom.py. The router works on a 0.1 mm grid. Other copper is an obstacle when its distance
from a track centre is below the 0.2 mm clearance plus half the track width (plus a grid margin); the board edge keeps
0.5 mm. Order:
  1. the switching stages: each stage's hot-loop pairs (input capacitor to VIN pin, SW pin to catch diode, inductor and
     boot capacitor), then the INA301 Kelvin sense pairs as their own copper groups that may only touch their sense pad;
  2. the GND stubs of the stage power pads (pad -> short track -> via to the B.Cu GND plane);
  3. the remaining power nets (0.8 mm where the pads allow it, else 0.4 mm), then every signal net (0.25 mm);
  4. a GND stub for every other surface-mount GND pad.
GND is otherwise left to the F.Cu and B.Cu pours that apply-routes.py adds. A connection that finds no path is reported
as unrouted; there is no rip-up. Signals pay twice the F.Cu cost on B.Cu so B.Cu stays mostly plane.
"""
import heapq
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

G = 0.1
W, H = 110.0, 85.0
NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
CL, EDGE, MARGIN = 0.2, 0.5, 0.08
RASTER = 0.0707   # half a cell diagonal: copper is marked on every cell it touches
VIA_D, VIA_DRILL, HOLE_CL = 0.8, 0.3, 0.25
VIA_COST = 3.0
B_COST = {'power': 1.2, 'signal': float(os.environ.get('B20_BSIG', 0.7)), 'P5_SUP': 0.8, 'REF25': 0.8, 'EN_E': 0.8, 'FAULT_N': 0.8}
SUPPLY = ['P5_SUP', 'REF25', 'FAULT_N', 'EN_E']
W_POWER, W_POWER_MIN, W_SIG = 0.8, 0.4, 0.25
# 0.2 mm (the board minimum) is the fallback: on the 0.1 mm grid a 0.25 mm track cannot leave the middle pin of a
# 0.65 mm pitch row with the clearance margin, which left the INA301 sense pins and other fine-pitch pins open
W_FINE = 0.2
POWER_NETS = {'VIN', 'A_SW', 'B_SW', 'C_SW', 'P12_RAW', 'P5_RAW', 'M12_RAW', 'P12_PRE', 'P5_PRE', 'M12_PRE',
              'P12_SH', 'P5_SH', 'M12_SH', 'P12_CS', 'P5_CS', 'M12_CS', 'P12_OUT', 'P5_OUT', 'M12_OUT'}
POWER_FP = ('HSOP-8', 'VSON-8', 'ASPI-0630', 'SMA_', 'R2512', 'R1206_TA-I', 'C1210', 'CAP-SMD', 'HDR', 'IDC', 'WJ500V')
STAGES = {  # stage: (IC, input caps, diode, inductor, boot cap, output caps, IC ground net)
    'A': ('U1', ['C3'], 'D1', 'L1', 'C4', ['CAO1', 'CAO2'], 'GND'),
    'B': ('U2', ['C7'], 'D2', 'L3', 'C8', ['CBO1', 'CBO2'], 'GND'),
    'C': ('U3', ['CCIN1', 'CCIN2'], 'D3', 'L5', 'C11', ['CCO1', 'CCO2', 'CCO3', 'CCO4'], 'M12_RAW'),
}
KELVIN = [('U11', '8', 'RSH1'), ('U11', '7', 'RSH1'), ('U12', '8', 'RSH2'), ('U12', '7', 'RSH2'),
          ('U9', '3', 'RSH3'), ('U9', '4', 'RSH3')]
XS = np.arange(NX) * G
YS = np.arange(NY) * G
# phase 27: B20_LAYERS=4 adds the inner signal/power layer In2 (In1 is a GND plane that the router does not use; every
# via passes through it and a GND via lands on it)
FOUR = os.environ.get('B20_LAYERS', '4') == '4'
# phase 28: pins that get an escape via before the power and signal nets (4-layer default). The list is the pins earlier
# runs left boxed in, plus every fine-pitch signal pin of U5, U7, U8, U13 and U16; the best of the phase 28 fanout trials.
FANOUT_4L = (
    'U4.3', 'U2.3', 'U5.7', 'U1.3', 'Q4.4', 'RCEN2.1', 'Q5.4', 'U9.7', 'U16.2', 'U6.6', 'U5.1', 'U7.3', 'U8.7',
    'U7.7', 'U7.6', 'R73.2', 'Q34.4', 'Q48.1', 'U13.7', 'U16.6', 'U16.5', 'R28.1', 'U16.3', 'U13.6', 'U8.1', 'U16.7',
    'R37.1', 'Q11.1', 'U13.1', 'U13.2', 'U13.3', 'U13.5', 'U13.8', 'U16.1', 'U16.4', 'U16.8', 'U5.2', 'U5.4', 'U5.5',
    'U5.6', 'U5.8', 'U7.1', 'U7.2', 'U7.5', 'U7.8', 'U8.2', 'U8.4', 'U8.5', 'U8.8',
)
GND_FIRST = FOUR and os.environ.get('B20_GNDFIRST', '1') == '1'
STUB_REACH = float(os.environ.get('B20_STUBREACH', 6.0 if FOUR else 2.5))   # phase 27: a second, wider GND-stub window
LAYERS = ('F', 'In2', 'B') if FOUR else ('F', 'B')

geom = json.load(open(sys.argv[1]))
pads = sorted(geom['pads'], key=lambda p: (p['ref'], p['num'], p['center']))
for k, p in enumerate(pads):
    p['id'] = k
    if FOUR and p['drill'] and p['layers']:
        p['layers'] = list(LAYERS)
nets = sorted({p['net'] for p in pads if p['net']})
NET_ID = {n: i + 1 for i, n in enumerate(nets)}
next_group = [len(nets) + 1]
NONET = -2


def new_group():
    next_group[0] += 1
    return next_group[0]


def window(x0, y0, x1, y1, r=0.0):
    i0, i1 = max(0, int((x0 - r) / G)), min(NX, int(math.ceil((x1 + r) / G)) + 1)
    j0, j1 = max(0, int((y0 - r) / G)), min(NY, int(math.ceil((y1 + r) / G)) + 1)
    return i0, i1, j0, j1


def pad_mask(p, m, val):
    b = p['bbox']
    i0, i1, j0, j1 = window(*b, G)
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    # every cell whose square touches the pad is marked, so a cell-centre distance never exceeds the true distance
    # by more than half a cell diagonal (0.071 mm), which MARGIN covers; a centre-inside raster could miss 0.1 mm
    if p['round']:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        rx, ry = (b[2] - b[0]) / 2 + RASTER, (b[3] - b[1]) / 2 + RASTER
        sel = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0
    else:
        h = G / 2 + 1e-6
        sel = (x >= b[0] - h) & (x <= b[2] + h) & (y >= b[1] - h) & (y <= b[3] + h)
    if not sel.any():
        j, i = int(round((b[1] + b[3]) / 2 / G)), int(round((b[0] + b[2]) / 2 / G))
        m[j, i] = val
        return
    sub = m[j0:j1, i0:i1]
    sub[sel] = val


def seg_cells(a, b, r):
    i0, i1, j0, j1 = window(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]), r)
    x, y = XS[i0:i1][None, :], YS[j0:j1][:, None]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = np.clip(((x - a[0]) * dx + (y - a[1]) * dy) / L, 0, 1) if L > 0 else 0.0
    px, py = x - a[0] - t * dx, y - a[1] - t * dy
    return (j0, j1, i0, i1), px * px + py * py <= r * r


# copper group raster per layer: 0 empty, >0 copper group (net id, or a Kelvin group), NONET unconnected copper
lab = {l: np.zeros((NY, NX), np.int32) for l in LAYERS}
smd = np.zeros((NY, NX), bool)
holes = np.zeros((NY, NX), bool)
npth = np.zeros((NY, NX), bool)   # holes without copper; plated holes are covered by their pad copper
pad_group = {}
sense_pad = {}
for p in pads:
    pad_group[p['id']] = NET_ID.get(p['net'], NONET)
for ina, pin, shunt in KELVIN:
    cand = [p for p in pads if p['ref'] == shunt]
    ina_pad = next(p for p in pads if p['ref'] == ina and p['num'] == pin)
    net = ina_pad['net']
    same = [p for p in cand if p['net'] == net]
    if len(same) == 2:   # Kelvin footprint: the smaller pad of the terminal is the sense pad
        target = min(same, key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))
    else:                # two-terminal shunt: sense lands on the pad itself (not a Kelvin footprint)
        target = same[0]
    kelvin = len(same) == 2
    g = new_group() if kelvin else NET_ID[net]
    sense_pad[(ina, pin)] = (ina_pad, target, g, kelvin)
    if kelvin:
        pad_group[ina_pad['id']] = g
        pad_group[target['id']] = g
for p in pads:
    if p['ref'].startswith('FID'):
        # fiducials carry a 1.0 mm local clearance and a 2 mm mask opening: keep copper out of a 1.3 mm radius disc
        c = p['center']
        p['bbox'] = [c[0] - 1.3, c[1] - 1.3, c[0] + 1.3, c[1] + 1.3]
        p['round'] = True
for p in pads:
    for l in p['layers']:
        pad_mask(p, lab[l], pad_group[p['id']])
    if not p['drill'] and 'F' in p['layers']:
        pad_mask(p, smd, True)
    if p['drill']:
        (j0, j1, i0, i1), sel = seg_cells(p['center'], p['center'], p['drill'] / 2)
        holes[j0:j1, i0:i1] |= sel
        if not p['layers'] or not p['net']:
            npth[j0:j1, i0:i1] |= sel

edge_dist = np.minimum.reduce([XS[None, :].repeat(NY, 0), (W - XS)[None, :].repeat(NY, 0),
                               YS[:, None].repeat(NX, 1), (H - YS)[:, None].repeat(NX, 1)])
smd_dist = ndimage.distance_transform_edt(~smd) * G
hole_dist = ndimage.distance_transform_edt(~npth) * G
tracks, vias, unrouted, notes = [], [], [], []
trk = {l: np.zeros((NY, NX), np.int32) for l in LAYERS}   # routed track and via copper only
fail_by_net = {}


CROP = 15   # cells of margin around a search window for the clearance transforms (1.5 mm)


def foreign_dist(group, l, box):
    i0, i1, j0, j1 = box
    a0, a1, b0, b1 = max(0, i0 - CROP), min(NX, i1 + CROP), max(0, j0 - CROP), min(NY, j1 + CROP)
    m = lab[l][b0:b1, a0:a1]
    foreign = (m != 0) & (m != group)
    d = ndimage.distance_transform_edt(~foreign) * G
    return d[j0 - b0:j1 - b0, i0 - a0:i1 - a0]


def crop(a, box):
    i0, i1, j0, j1 = box
    return a[j0:j1, i0:i1]


def free_masks(group, hw, box):
    out = {}
    for l in LAYERS:
        out[l] = ((foreign_dist(group, l, box) >= CL + hw + MARGIN) & (crop(edge_dist, box) >= EDGE + hw)
                  & (crop(hole_dist, box) >= HOLE_CL + hw + MARGIN))
    return out


def via_mask(group, box):
    vr = VIA_D / 2
    ok = np.ones((box[3] - box[2], box[1] - box[0]), bool)
    for l in LAYERS:
        ok &= foreign_dist(group, l, box) >= CL + vr + MARGIN
    ok &= crop(edge_dist, box) >= EDGE + vr
    i0, i1, j0, j1 = box
    a0, a1, b0, b1 = max(0, i0 - CROP), min(NX, i1 + CROP), max(0, j0 - CROP), min(NY, j1 + CROP)
    hd = ndimage.distance_transform_edt(~holes[b0:b1, a0:a1]) * G
    ok &= hd[j0 - b0:j1 - b0, i0 - a0:i1 - a0] >= HOLE_CL + VIA_DRILL / 2 + 0.15
    ok &= crop(smd_dist, box) >= vr + 0.1
    return ok


def add_track(a, b, w, l, net, group):
    tracks.append({'net': net, 'layer': l, 'w': w, 'a': [round(a[0], 4), round(a[1], 4)], 'b': [round(b[0], 4), round(b[1], 4)]})
    (j0, j1, i0, i1), sel = seg_cells(a, b, w / 2 + RASTER)
    sub = lab[l][j0:j1, i0:i1]
    sub[sel & (sub == 0)] = group
    trk[l][j0:j1, i0:i1][sel] = group


def add_via(c, net, group):
    vias.append({'net': net, 'at': [round(c[0], 4), round(c[1], 4)], 'd': VIA_D})
    (j0, j1, i0, i1), sel = seg_cells(c, c, VIA_D / 2 + RASTER)
    for l in LAYERS:
        sub = lab[l][j0:j1, i0:i1]
        sub[sel & (sub == 0)] = group
        trk[l][j0:j1, i0:i1][sel] = group
    (j0, j1, i0, i1), sel = seg_cells(c, c, VIA_DRILL / 2)
    holes[j0:j1, i0:i1] |= sel


def _load_astar():
    """Compile astar.c once per source hash into the system temp directory and bind it with ctypes."""
    import ctypes
    import hashlib
    import subprocess
    import tempfile
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'astar.c')
    tag = hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16]
    lib = os.path.join(tempfile.gettempdir(), f'b20-astar-{tag}.so')
    if not os.path.exists(lib):
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', '-o', lib + '.tmp', src, '-lm'], check=True)
        os.replace(lib + '.tmp', lib)
    so = ctypes.CDLL(lib)
    u8 = np.ctypeslib.ndpointer(np.uint8, flags='C_CONTIGUOUS')
    f32 = ctypes.c_void_p
    so.astar.restype = ctypes.c_int
    pp = ctypes.POINTER(ctypes.c_void_p)
    so.astar.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, pp, u8, pp, pp, pp,
                         np.ctypeslib.ndpointer(np.float64, flags='C_CONTIGUOUS'), ctypes.c_double,
                         np.ctypeslib.ndpointer(np.int32, flags='C_CONTIGUOUS'), ctypes.c_int]
    return so


_SO = _load_astar()


def astar(src, dst, free, vok, box, b_cost, extra=None):
    """src/dst: dict layer -> bool mask (full board); free/vok/extra: box windows. Returns [(l, j, i), ...] or None."""
    import ctypes
    i0, i1, j0, j1 = box
    w, h = i1 - i0, j1 - j0
    keep = []

    def ptrs(arrays, dtype):
        out = (ctypes.c_void_p * len(LAYERS))()
        for n, a in enumerate(arrays):
            if a is None:
                out[n] = None
                continue
            a = np.ascontiguousarray(a, dtype=dtype)
            keep.append(a)
            out[n] = a.ctypes.data
        return ctypes.cast(out, ctypes.POINTER(ctypes.c_void_p))
    fr = ptrs([free[l] for l in LAYERS], np.uint8)
    sr = ptrs([src[l][j0:j1, i0:i1] for l in LAYERS], np.uint8)
    dt = ptrs([dst[l][j0:j1, i0:i1] for l in LAYERS], np.uint8)
    ex = ptrs([extra[l] if extra is not None else None for l in LAYERS], np.float32)
    lc = np.array([1.0] + [float(b_cost)] * (len(LAYERS) - 1), np.float64)
    cap = len(LAYERS) * w * h
    out = np.zeros(cap, np.int32)
    n = _SO.astar(w, h, len(LAYERS), fr, np.ascontiguousarray(vok, dtype=np.uint8), sr, dt, ex, lc, VIA_COST / G, out, cap)
    if n <= 0:
        return None
    N = w * h
    return [(LAYERS[v // N], (v % N) // w + j0, (v % N) % w + i0) for v in out[:n].tolist()]


def emit(path, w, net, group, allowed, box):
    """Write the path as tracks and vias, pulling each same-layer run taut where the straight line stays in allowed cells."""
    pts = [(l, i * G, j * G) for l, j, i in path]
    run = [pts[0]]
    for q in pts[1:]:
        if q[0] != run[-1][0]:
            flush(run, w, net, group, allowed, box)
            add_via((q[1], q[2]), net, group)
            run = [q]
        else:
            run.append(q)
    flush(run, w, net, group, allowed, box)


def line_ok(a, b, m, box):
    i0, i1, j0, j1 = box
    n = max(2, int(math.hypot(b[1] - a[1], b[2] - a[2]) / (G / 2)) + 1)
    for k in range(n + 1):
        x = a[1] + (b[1] - a[1]) * k / n
        y = a[2] + (b[2] - a[2]) * k / n
        for i in (int(math.floor(x / G + 1e-9)), int(math.ceil(x / G - 1e-9))):
            for j in (int(math.floor(y / G + 1e-9)), int(math.ceil(y / G - 1e-9))):
                if not (i0 <= i < i1 and j0 <= j < j1) or not m[j - j0, i - i0]:
                    return False
    return True


def flush(run, w, net, group, allowed, box):
    if len(run) < 2:
        return
    m = allowed[run[0][0]]
    corners = [run[0]]
    k = 0
    while k < len(run) - 1:
        far = k + 1
        stride = max(1, (len(run) - 1 - k) // 40)
        for e in range(len(run) - 1, k + 1, -stride):
            if line_ok(run[k], run[e], m, box):
                far = e
                break
        corners.append(run[far])
        k = far
    for a, b in zip(corners, corners[1:]):
        add_track((a[1], a[2]), (b[1], b[2]), w, a[0], net, group)


def mask_of_pad(p):
    m = np.zeros((NY, NX), bool)
    pad_mask(p, m, True)
    return {l: (m if l in p['layers'] else np.zeros_like(m)) for l in LAYERS}


def group_mask(group):
    return {l: lab[l] == group for l in LAYERS}


def bbox_of(masks):
    js, is_ = [], []
    for m in masks:
        for l in LAYERS:
            jj, ii = np.nonzero(m[l])
            if len(jj):
                js += [jj.min(), jj.max()]; is_ += [ii.min(), ii.max()]
    return min(is_) * G, min(js) * G, max(is_) * G, max(js) * G


LAST_PATH = []


def connect(src, dst, net, group, widths, b_cost, label, quiet_fail=False, extra_fn=None):
    x0, y0, x1, y1 = bbox_of([src, dst])
    tries = [(w, grow) for w in widths for grow in (4.0, 12.0)] + [(widths[-1], 200.0)]
    for w, grow in tries:
        box = window(x0, y0, x1, y1, grow)
        free = free_masks(group, w / 2, box)
        vok = via_mask(group, box)
        s_src, s_dst = seat(src, group, w, box), seat(dst, group, w, box)
        if not (s_src.ok and s_dst.ok) and (w, grow) != tries[-1]:
            continue
        path = astar(s_src, s_dst, free, vok, box, b_cost, extra_fn(box) if extra_fn else None)
        if path:
            LAST_PATH[:] = path
            # taut pulling may cross only free cells and the seat cells, never the rest of a pad near a foreign pad
            emit(path, w, net, group, {l: free[l] | crop(s_src[l], box) | crop(s_dst[l], box) for l in LAYERS}, box)
            log(f'{label}: {w} mm')
            return w
    if not quiet_fail:
        unrouted.append(label)
        log(f'{label}: UNROUTED')
    return None


def seat(mask, group, w, box):
    """End cells where a track of width w stays inside the group's own copper. When the pad is narrower than w, the one
    cell farthest from foreign copper; .ok is False when even that cell leaves less than the clearance for width w."""
    i0, i1, j0, j1 = box
    out = Seat()
    for l in LAYERS:
        m = np.zeros((NY, NX), bool)
        own = lab[l][j0:j1, i0:i1] == group
        deep = ndimage.distance_transform_edt(own) * G >= w / 2
        sub = mask[l][j0:j1, i0:i1]
        m[j0:j1, i0:i1] = sub & deep
        if sub.any() and not m[j0:j1, i0:i1].any():
            fd = np.where(sub, foreign_dist(group, l, box), -1.0)
            j, i = np.unravel_index(int(np.argmax(fd)), fd.shape)
            m[j0 + j, i0 + i] = True
            if fd[j, i] < CL + w / 2 + MARGIN:
                out.ok = False
        out[l] = m
    return out


class Seat(dict):
    ok = True


def stitch(pitch=3.0, keep=1.0):
    """GND stitching vias on a grid wherever both pours have room, tying F.Cu and B.Cu GND together."""
    group = NET_ID['GND']
    box = (0, NX, 0, NY)
    vok = via_mask(group, box)
    far = np.ones((NY, NX), bool)
    for l in LAYERS:
        far &= foreign_dist(group, l, box) >= keep
    step = int(round(pitch / G))
    n = 0
    for j in range(step // 2, NY, step):
        for i in range(step // 2, NX, step):
            if vok[j, i] and far[j, i] and not any(math.dist((i * G, j * G), v['at']) < pitch / 2 for v in vias if v['net'] == 'GND'):
                add_via((i * G, j * G), 'GND', group)
                n += 1
    log(f'GND stitching vias: {n}')


def near_part(mask, c, r):
    """The part of a layer mask within r mm of point c."""
    i0, i1, j0, j1 = window(c[0], c[1], c[0], c[1], r)
    out = {}
    for l in LAYERS:
        m = np.zeros((NY, NX), bool)
        m[j0:j1, i0:i1] = mask[l][j0:j1, i0:i1]
        out[l] = m
    return out


def log(msg):
    print(msg, flush=True)


def pin(ref, num):
    hits = [p for p in pads if p['ref'] == ref and p['num'] == num]
    if not hits:
        raise SystemExit(f'no pad {ref}.{num}')
    return max(hits, key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))


def is_power_pad(p):
    return p['net'] in POWER_NETS and p['fp'].startswith(POWER_FP)


def widths_for(p, q):
    if is_power_pad(p) and is_power_pad(q):
        return (W_POWER, W_POWER_MIN, W_SIG)
    if p['net'] in POWER_NETS:
        return (W_POWER_MIN, W_SIG, W_FINE)
    return (W_SIG, W_FINE)


def route_pair(p, q, label, widths=None):
    group = pad_group[p['id']]
    kind = 'power' if p['net'] in POWER_NETS else 'signal'
    return connect(mask_of_pad(p), mask_of_pad(q), p['net'], group, widths or widths_for(p, q), B_COST[kind], label)


def components(group):
    """Connected copper of one group, each layer labelled separately and joined where a hole carries several layers."""
    labels, offset = {}, 0
    for l in LAYERS:
        lab_l, n = ndimage.label(lab[l] == group)
        labels[l] = np.where(lab_l > 0, lab_l + offset, 0)
        offset += n
    parent = list(range(offset + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for la, lb in zip(LAYERS, LAYERS[1:]):
        both = holes & (labels[la] > 0) & (labels[lb] > 0)
        for a, b in set(zip(labels[la][both].tolist(), labels[lb][both].tolist())):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    roots = np.array([find(a) for a in range(offset + 1)])
    return {l: roots[labels[l]] for l in LAYERS}


def comp_of(p, comps):
    j, i = int(round(p['center'][1] / G)), int(round(p['center'][0] / G))
    for l in p['layers']:
        if comps[l][j, i]:
            return comps[l][j, i]
    return 0


def route_net(net, root_ref=None):
    """Grow from the root pad's copper to the nearest unconnected pad; a pad that cannot reach the root joins any other
    copper of the net, so the net ends as few pieces as the board allows."""
    group = NET_ID[net]
    members = [p for p in pads if p['net'] == net and pad_group[p['id']] == group]
    if len(members) < 2:
        return
    kind = 'power' if net in POWER_NETS else 'signal'
    root = next((p for p in members if p['ref'] == root_ref), members[0])
    failed = []
    fail_by_net[net] = []
    while True:
        comps = components(group)
        rc = comp_of(root, comps)
        dead = {comp_of(p, comps) for p in failed}
        todo = [p for p in members if comp_of(p, comps) != rc and comp_of(p, comps) not in dead]
        if not todo:
            return
        tree = {l: comps[l] == rc for l in LAYERS}
        tj, ti = np.nonzero(np.logical_or.reduce([tree[l] for l in LAYERS]))
        pts = np.stack([ti * G, tj * G], 1)
        best = min(todo, key=lambda p: float(np.min((pts[:, 0] - p['center'][0]) ** 2 + (pts[:, 1] - p['center'][1]) ** 2)))
        bc = comp_of(best, comps)
        src = {l: comps[l] == bc for l in LAYERS}
        near = pts[int(np.argmin((pts[:, 0] - best['center'][0]) ** 2 + (pts[:, 1] - best['center'][1]) ** 2))]
        nearest_pad = min((p for p in members if p is not best), key=lambda p: (p['center'][0] - near[0]) ** 2 + (p['center'][1] - near[1]) ** 2)
        ws = widths_for(best, nearest_pad)
        label = f'{net}:{best["ref"]}.{best["num"]}'
        local = near_part(tree, best['center'], 12.0)
        if any(local[l].any() for l in LAYERS) and connect(src, local, net, group, ws, B_COST.get(net, B_COST[kind]), label, quiet_fail=True):
            continue
        if connect(src, tree, net, group, ws[-1:], B_COST.get(net, B_COST[kind]), label, quiet_fail=True):
            continue
        others = {l: (comps[l] > 0) & (comps[l] != bc) & (comps[l] != rc) for l in LAYERS}
        if any(others[l].any() for l in LAYERS) and connect(src, near_part(others, best['center'], 12.0), net, group, ws[-1:], B_COST.get(net, B_COST[kind]), label + ' (to a fragment)', quiet_fail=True):
            continue
        failed.append(best)
        fail_by_net[net].append(label)
        log(f'{label}: UNROUTED')


def gnd_stub(p):
    """Short F.Cu stub from a GND surface pad to a via that reaches the B.Cu GND plane."""
    group = NET_ID['GND']
    src = mask_of_pad(p)
    for reach in (2.5,) + ((STUB_REACH,) if STUB_REACH > 2.5 else ()):
        if gnd_stub_at(p, group, src, reach):
            return True
    unrouted.append(f'GND stub {p["ref"]}.{p["num"]}')
    log(f'GND stub {p["ref"]}.{p["num"]}: UNROUTED')


def fanout(p):
    """Pin escape: a short F.Cu stub from a signal pad to its own via, laid before the nets that would box it in."""
    group = pad_group[p['id']]
    for reach in (2.5, max(STUB_REACH, 4.0)):
        nt, nv = len(tracks), len(vias)
        if gnd_stub_at(p, group, mask_of_pad(p), reach, net=p['net']):
            for x in tracks[nt:] + vias[nv:]:
                x['fan'] = True   # rip-up keeps the escape
            log(f'fanout {p["ref"]}.{p["num"]}')
            return True
    log(f'fanout {p["ref"]}.{p["num"]}: no via site')
    return False


def gnd_stub_at(p, group, src, reach, net='GND'):
    box = window(*p['bbox'], reach)
    vok = via_mask(group, box)
    for w in (0.5, W_SIG, W_FINE):
        free = free_masks(group, w / 2, box)
        dst = vok & np.logical_and.reduce([free[l] for l in LAYERS])
        if not dst.any():
            continue
        i0, i1, j0, j1 = box
        full = np.zeros((NY, NX), bool)
        full[j0:j1, i0:i1] = dst
        s_src = seat(src, group, w, box)
        if not s_src.ok and w != W_FINE:
            continue
        path = astar(s_src, {l: full if l == 'F' else np.zeros_like(full) for l in LAYERS}, free, np.zeros_like(dst), box, 9.0)
        if path:
            emit(path, w, net, group, {l: free[l] | crop(s_src[l], box) if l == 'F' else free[l] for l in LAYERS}, box)
            _, j, i = path[-1]
            add_via((i * G, j * G), net, group)
            return True
    return False


RIPPABLE = None


def rippable(net):
    return net in NET_ID and net not in POWER_NETS and net not in SUPPLY and net != 'GND' and not net.startswith('unconnected')


def snapshot():
    return ({l: lab[l].copy() for l in LAYERS}, {l: trk[l].copy() for l in LAYERS}, holes.copy(), list(tracks), list(vias),
            {k: list(v) for k, v in fail_by_net.items()})


def restore(s):
    for l in LAYERS:
        lab[l][:] = s[0][l]
        trk[l][:] = s[1][l]
    holes[:] = s[2]
    tracks[:] = s[3]
    vias[:] = s[4]
    fail_by_net.clear()
    fail_by_net.update({k: list(v) for k, v in s[5].items()})


def rip(net):
    group = NET_ID[net]
    kept_t = [x for x in tracks if x['net'] == net and x.get('fan')]
    kept_v = [v for v in vias if v['net'] == net and v.get('fan')]
    tracks[:] = [x for x in tracks if x['net'] != net]
    gone = [v for v in vias if v['net'] == net and not v.get('fan')]
    vias[:] = [v for v in vias if v['net'] != net]
    for l in LAYERS:
        lab[l][lab[l] == group] = 0
        trk[l][trk[l] == group] = 0
    for x in kept_t:
        add_track(x['a'], x['b'], x['w'], x['layer'], net, group)
        tracks[-1]['fan'] = True
    for v in kept_v:
        add_via(v['at'], net, group)
        vias[-1]['fan'] = True
    for p in pads:
        if pad_group[p['id']] == group:
            for l in p['layers']:
                pad_mask(p, lab[l], group)
    for v in gone:
        (j0, j1, i0, i1), sel = seg_cells(v['at'], v['at'], VIA_DRILL / 2)
        holes[j0:j1, i0:i1][sel] = False
    for p in pads:
        if p['drill']:
            (j0, j1, i0, i1), sel = seg_cells(p['center'], p['center'], p['drill'] / 2)
            holes[j0:j1, i0:i1] |= sel
    fail_by_net[net] = []


def blockers(net):
    """Nets whose routed signal copper stands in the way of net's failed pads: path search with that copper ignored."""
    group = NET_ID[net]
    soft_groups = [NET_ID[n] for n in NET_ID if rippable(n) and n != net]
    soft = {l: np.isin(trk[l], soft_groups) for l in LAYERS}
    comps = components(group)
    found = set()
    members = [p for p in pads if p['net'] == net and pad_group[p['id']] == group]
    cids = {comp_of(p, comps) for p in members}
    if len(cids) < 2:
        return found
    pieces = sorted(cids)
    src = {l: comps[l] == pieces[0] for l in LAYERS}
    dst = {l: (comps[l] > 0) & (comps[l] != pieces[0]) for l in LAYERS}
    x0, y0, x1, y1 = bbox_of([src, dst])
    box = window(x0, y0, x1, y1, 6.0)
    saved = {l: lab[l].copy() for l in LAYERS}
    for l in LAYERS:
        lab[l][soft[l] & (lab[l] != group)] = 0
    free = free_masks(group, W_SIG / 2, box)
    vok = via_mask(group, box)
    for l in LAYERS:
        lab[l][:] = saved[l]
    path = astar(src, dst, free, vok, box, B_COST['signal'])
    if not path:
        return found
    reach = int(math.ceil((CL + W_SIG + MARGIN) / G)) + 1
    for l, j, i in path:
        sub = trk[l][max(0, j - reach):j + reach + 1, max(0, i - reach):i + reach + 1]
        for g in np.unique(sub):
            if g and g != group and g in soft_groups:
                found.add(nets[g - 1])
    return found


def total_fail():
    return sum(len(v) for v in fail_by_net.values())


def ripup(rounds=int(os.environ.get("B20_RIPUP", 6))):
    for r in range(rounds):
        todo = [n for n, v in fail_by_net.items() if v and rippable(n)]
        if not todo:
            return
        improved = 0
        for net in todo:
            if not fail_by_net.get(net):
                continue
            before = total_fail()
            s = snapshot()
            hit = blockers(net)
            if not hit:
                continue
            for b in hit:
                rip(b)
            route_net(net)
            for b in sorted(hit):
                route_net(b)
            after = total_fail()
            if after < before:
                improved += 1
                log(f'rip-up {net}: ripped {sorted(hit)}, failures {before} -> {after}')
            else:
                restore(s)
        log(f'rip-up round {r + 1}: {improved} nets improved, {total_fail()} failed connections')
        if not improved:
            return


def coupling(path, pitch=0.5, weight=2.0, cap=3.0):
    """Step-cost windows that keep a Kelvin trace beside its partner's centre line: free within `pitch` mm (0.2 mm tracks
    at 0.5 mm centres leave a 0.3 mm gap), then `weight` per mm of extra distance, capped."""
    def fn(box):
        i0, i1, j0, j1 = box
        out = {}
        for l in LAYERS:
            m = np.zeros((j1 - j0, i1 - i0), bool)
            for pl, j, i in path:
                if pl == l and j0 <= j < j1 and i0 <= i < i1:
                    m[j - j0, i - i0] = True
            if not m.any():
                out[l] = np.full(m.shape, weight * cap, np.float32)
                continue
            d = ndimage.distance_transform_edt(~m) * G
            out[l] = (weight * np.clip(d - pitch, 0, cap)).astype(np.float32)
        return out
    return fn


def main():
    # 1. stage hot loops: VIN pin to input capacitor, SW pin to diode, inductor and boot capacitor, inductor to output
    for name, (ic, cins, diode, ind, boot, couts, ground) in STAGES.items():
        vin = pin(ic, '2')
        route_pair(pin(cins[0], '1'), vin, f'{name}: CIN-VIN')
        for extra in cins[1:]:
            route_pair(pin(extra, '1'), pin(cins[0], '1'), f'{name}: CIN2')
        sw = pin(ic, '8')
        route_pair(pin(diode, '1'), sw, f'{name}: SW-diode')
        route_pair(pin(ind, '1'), pin(diode, '1'), f'{name}: diode-L')
        # hot-loop return on F.Cu (TI SLVSBN0C 10.1): diode anode to the input-capacitor return pad, and that pad to the
        # exposed pad under the IC, before anything else crosses the top-side ground area
        route_pair(pin(diode, '2'), pin(cins[0], '2'), f'{name}: diode-CIN return', (W_POWER, W_POWER_MIN, W_SIG))
        route_pair(pin(cins[0], '2'), pin(ic, '9'), f'{name}: CIN-EP ground', (W_POWER, W_POWER_MIN, W_SIG))
        route_pair(pin(diode, '2'), pin(ic, '9'), f'{name}: diode-EP ground', (W_POWER, W_POWER_MIN, W_SIG))
        route_pair(pin(boot, '2'), sw, f'{name}: boot-SW')
        # the BOOT trace runs on B.Cu (Figure 58) so it does not cut the top-side ground area
        bp, ip = pin(boot, '1'), pin(ic, '1')
        connect(mask_of_pad(bp), mask_of_pad(ip), bp['net'], pad_group[bp['id']], (W_SIG, W_FINE), 0.3,
                f'{name}: boot-BOOT')
        outnet = next(p['net'] for p in pads if p['ref'] == ind and p['num'] == '2')
        for c in couts:
            cp = next(p for p in pads if p['ref'] == c and p['net'] == outnet)
            route_pair(cp, pin(ind, '2'), f'{name}: L-COUT {c}', (W_POWER, W_POWER_MIN, W_SIG))
    # 1b. Kelvin sense pairs, both traces of a shunt together; the second order is tried when the first leaves one open
    pairs = {}
    for (ina, num), row in sense_pad.items():
        pairs.setdefault(row[1]['ref'], []).append(((ina, num), row))
    for shunt, rows in pairs.items():
        best = None
        for order in (rows, rows[::-1]):
            s = snapshot()
            before = len(unrouted)
            partner = None
            for (ina, num), (ip, target, g, kelvin) in order:
                ok = connect(mask_of_pad(ip), mask_of_pad(target), ip['net'], g, (W_FINE,), B_COST['signal'],
                             f'Kelvin {ina}.{num}', extra_fn=coupling(partner) if partner else None)
                if ok and partner is None:
                    partner = list(LAST_PATH)
            misses = len(unrouted) - before
            if best is None or misses < best[0]:
                best = (misses, snapshot(), list(unrouted))
            restore(s)
            del unrouted[before:]
            if misses == 0:
                break
        restore(best[1])
        unrouted[:] = best[2]
        for (ina, num), (ip, target, g, kelvin) in rows:
            if not kelvin:
                notes.append(f'{ina}.{num}: {target["ref"]} has no sense pads; the sense trace lands on its current pad')
    # 2. GND stubs of the stage power pads
    stage_refs = set()
    for ic, cins, diode, ind, boot, couts, ground in STAGES.values():
        stage_refs |= {ic, diode, ind, *cins, *couts}
    for p in pads:
        if p['net'] == 'GND' and not p['drill'] and p['ref'] in stage_refs and p['layers'] == ['F']:
            gnd_stub(p)
    # 4-layer: every GND surface pad takes its own via to the In1.Cu plane before the signals claim the via sites
    if GND_FIRST:
        for p in pads:
            if p['net'] == 'GND' and not p['drill'] and p['ref'] not in stage_refs and p['layers'] == ['F']:
                gnd_stub(p)
    # pin escapes named in B20_FANOUT (ref.pin list), e.g. the pins a previous run left boxed in
    for key in [k for k in os.environ.get('B20_FANOUT', ','.join(FANOUT_4L) if FOUR else '').split(',') if k]:
        ref, num = key.split('.')
        fp = next((p for p in pads if p['ref'] == ref and p['num'] == num and not p['drill']), None)
        if fp and fp['net'] in NET_ID and rippable(fp['net']):
            fanout(fp)
    # 3. remaining power nets, then signals by span
    for net in sorted(POWER_NETS & set(NET_ID)):
        route_net(net, root_ref={'VIN': 'J5'}.get(net))
    def span(n):
        ps = [p['center'] for p in pads if p['net'] == n]
        return (max(q[0] for q in ps) - min(q[0] for q in ps)) + (max(q[1] for q in ps) - min(q[1] for q in ps))
    for net in SUPPLY:
        route_net(net)
    signals = sorted((n for n in NET_ID if n not in POWER_NETS and n not in SUPPLY and n != 'GND' and not n.startswith('unconnected')), key=span)
    first = [n for n in os.environ.get('B20_FIRST', '').split(',') if n in signals]
    for net in first + [n for n in signals if n not in first]:
        route_net(net)
    ripup()
    stitch()
    # 4. every other GND surface pad
    for p in pads if not GND_FIRST else ():
        if p['net'] == 'GND' and not p['drill'] and p['ref'] not in stage_refs and p['layers'] == ['F']:
            gnd_stub(p)
    for v in fail_by_net.values():
        unrouted.extend(v)
    failed_nets = sorted({u.split(':')[0] for u in unrouted if not u.startswith('GND stub')})
    json.dump({'tracks': tracks, 'vias': vias, 'unrouted': unrouted, 'failed_nets': failed_nets, 'first': first, 'notes': notes,
               **({'layers': list(LAYERS)} if FOUR else {})},
              open(sys.argv[2], 'w'), indent=0)
    print(f'{len(tracks)} tracks, {len(vias)} vias, {len(unrouted)} unrouted')


if __name__ == '__main__':
    main()
