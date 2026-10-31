"""Host-side greedy placement search with perturbed restarts for the Board P r3 draft (courtyard rectangles, 90-degree rotations).

usage: python3 search-placement.py <repo> <fpsize.json> <asbuilt.json> <out.json> <mode: top|both> <restarts> [floorplan.json]
floorplan.json (phase 11): {"pre": {ref: [x, y, rot]}, "reserved": {name: [x0, y0, x1, y1]}} fixes the
power-path parts and keeps the power-routing corridors free of other footprints.
"""
import importlib.util, json, math, random, sys

repo, fpsize_p, asb_p, out_p, mode, restarts = sys.argv[1:7]
restarts = int(restarts)
s = importlib.util.spec_from_file_location('spec', f'{repo}/scripts/schgen/board_p_spec.py')
spec = importlib.util.module_from_spec(s); s.loader.exec_module(spec)
FP = json.load(open(fpsize_p))
ASB = {r['ref']: r for r in json.load(open(asb_p))}
W, H, EDGE, GAP, GRID = 27.0, 40.0, 0.25, 0.10, 0.25
pad_net = {pin: n for n, pins in spec.NETS.items() for pin in pins}
FIXED = {r: (ASB[r]['x'], ASB[r]['y'], ASB[r]['rot']) for r in ('J1', 'JOUT1', 'J2', 'J3', 'U1')}
FLOOR = json.load(open(sys.argv[7])) if len(sys.argv) > 7 else {'pre': {}, 'reserved': {}}
for _r in FLOOR['pre']:
    FIXED.pop(_r, None)
PIN_GROUP = [('R21', 'U1', '6', '1'), ('D9', 'U1', '24', '1'), ('D10', 'U1', '18', '1'),
             ('D11', 'U1', '16', '1'), ('D12', 'U1', '9', '1')]
BOTTOM_OK = {r for r, c in spec.COMPONENTS.items() if c[3].split(':')[1] in ('R0603', 'C0603', 'SOD-523_L1.2-W0.8-LS1.6-RD', 'SOD-123_L2.8-W1.8-LS3.7-RD', 'C1206')}


def fpn(ref):
    return spec.COMPONENTS[ref][3].split(':')[1]


def rot_pt(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def local_rect(ref, deg):
    b = FP[fpn(ref)]['bbox']
    pts = [rot_pt(x, y, deg) for x in (b[0], b[2]) for y in (b[1], b[3])]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def pad_abs(ref, num, x, y, deg):
    px, py = FP[fpn(ref)]['pads'][num]
    dx, dy = rot_pt(px, py, deg)
    return x + dx, y + dy


def run(order, rng):
    occ = {'F': [], 'B': []}
    for r in ASB:
        if r.startswith('MH'):
            b = ASB[r]['bbox']; occ['F'].append((*b, r)); occ['B'].append((*b, r))
    pos = {}
    for r, (x, y, d) in FIXED.items():
        lr = local_rect(r, d); rect = (lr[0] + x, lr[1] + y, lr[2] + x, lr[3] + y, r)
        occ['F'].append(rect)
        if FP[fpn(r)]['th']:
            occ['B'].append(rect)
        pos[r] = (x, y, d, 'F')
    for r, (x, y, d) in FLOOR['pre'].items():
        lr = local_rect(r, d); occ['F'].append((lr[0] + x, lr[1] + y, lr[2] + x, lr[3] + y, r)); pos[r] = (x, y, d, 'F')
    for name, rr in FLOOR['reserved'].items():
        occ['F'].append((*rr, name))
    keep = []

    def free(rect, side):
        if any(rect[0] < o[2] + GAP and rect[2] > o[0] - GAP and rect[1] < o[3] + GAP and rect[3] > o[1] - GAP for o in occ[side]):
            return False
        return not (side == 'F' and any(rect[0] < k[2] and rect[2] > k[0] and rect[1] < k[3] and rect[3] > k[1] for k in keep))

    def best(ref, target, pin=None, sides=('F',)):
        cands = []
        for side in sides:
            for d in (0, 90, 180, 270):
                lr = local_rect(ref, d)
                off = pad_abs(ref, pin, 0, 0, d) if pin else (0, 0)
                x = math.ceil((EDGE - lr[0]) / GRID) * GRID
                while x <= W - EDGE - lr[2] + 1e-9:
                    y = math.ceil((EDGE - lr[1]) / GRID) * GRID
                    while y <= H - EDGE - lr[3] + 1e-9:
                        dist = math.hypot(x + off[0] - target[0], y + off[1] - target[1]) + (3.0 if side == 'B' else 0.0)
                        cands.append((dist, x, y, d, side, lr))
                        y += GRID
                    x += GRID
        cands.sort(key=lambda c: c[0])
        for dist, x, y, d, side, lr in cands:
            rect = (lr[0] + x, lr[1] + y, lr[2] + x, lr[3] + y, ref)
            if free(rect, side):
                occ[side].append(rect); pos[ref] = (x, y, d, side)
                return dist
        return None

    def target(ref):
        pts = []
        for num in FP[fpn(ref)]['pads']:
            n = pad_net.get(f'{ref}.{num}')
            if not n or n == 'GND':
                continue
            for o, (x, y, d, _s) in pos.items():
                for q in FP[fpn(o)]['pads']:
                    if pad_net.get(f'{o}.{q}') == n:
                        pts.append(pad_abs(o, q, x, y, d))
        if not pts:
            return (W / 2, H / 2)
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    pin_d = {}
    for ref, ic, ip, pp in PIN_GROUP:
        x, y, d, _ = pos[ic]
        pin_d[ref] = best(ref, pad_abs(ic, ip, x, y, d), pp)
        if pin_d[ref] is not None:
            a = pad_abs(ic, ip, x, y, d); b = pad_abs(ref, pp, *pos[ref][:3])
            keep.append((min(a[0], b[0]) - 0.3, min(a[1], b[1]) - 0.3, max(a[0], b[0]) + 0.3, max(a[1], b[1]) + 0.3))
    unplaced = []
    for ref in order:
        sides = ('F', 'B') if mode == 'both' and ref in BOTTOM_OK else ('F',)
        if best(ref, target(ref), None, sides) is None:
            unplaced.append(ref)
    wire = 0.0
    for n, pins in spec.NETS.items():
        if n == 'GND':
            continue
        pts = [pad_abs(p.split('.')[0], p.split('.')[1], *pos[p.split('.')[0]][:3]) for p in pins if p.split('.')[0] in pos]
        if len(pts) > 1:
            wire += (max(p[0] for p in pts) - min(p[0] for p in pts)) + (max(p[1] for p in pts) - min(p[1] for p in pts))
    return {'unplaced': unplaced, 'pos': pos, 'pin_d': pin_d, 'keepouts': keep, 'hpwl_mm': round(wire, 2),
            'bottom': sorted(r for r, p in pos.items() if p[3] == 'B')}


rng = random.Random(10)
rest = [r for r in spec.COMPONENTS if r not in FIXED and r not in FLOOR['pre'] and r not in {g[0] for g in PIN_GROUP}]
area = lambda r: (lambda b: (b[2] - b[0]) * (b[3] - b[1]))(FP[fpn(r)]['bbox'])
base = sorted(rest, key=lambda r: -area(r))
best_run = None
for k in range(restarts):
    order = list(base)
    if k:
        for i in range(len(order)):          # perturb the big-first order
            j = min(len(order) - 1, max(0, i + rng.randint(-4, 4)))
            order[i], order[j] = order[j], order[i]
    res = run(order, rng); res['order'] = order
    print(k, res['unplaced'], len(res['bottom']), res['hpwl_mm'], file=sys.stderr)
    key = (len(res['unplaced']), len(res['bottom']), res['hpwl_mm'])
    if best_run is None or key < best_run[0]:
        best_run = (key, res)
    if not res['unplaced'] and mode == 'top' and k > 20:
        pass
res = best_run[1]
res['mode'] = mode; res['restarts'] = restarts
res['floorplan'] = FLOOR
json.dump(res, open(out_p, 'w'), indent=1)
print(json.dumps({'mode': mode, 'unplaced': res['unplaced'], 'bottom': res['bottom'], 'hpwl': res['hpwl_mm'], 'pin_d': res['pin_d']}))
