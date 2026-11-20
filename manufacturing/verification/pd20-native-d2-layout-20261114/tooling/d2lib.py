"""Host-side helpers for the D2 back-side placement (tmp working copy)."""
import json, math, re, sys
from pathlib import Path
from shapely.geometry import box as sbox, Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / 'footprints/kicad/zudo-power.pretty'
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import board_b20_spec as spec

def parse_fp(name):
    t = (LIB / f'{name}.kicad_mod').read_text()
    pads = []
    for m in re.finditer(r'\(pad "?([^"\s]*)"? (\w+) (\w+)\s*\(at ([-\d. ]+)\)\s*\(size ([\d. ]+)\)', t):
        num, kind, shape, at, size = m.groups()
        at = [float(v) for v in at.split()]; size = [float(v) for v in size.split()]
        rot = at[2] if len(at) > 2 else 0
        w, h = (size[1], size[0]) if round(rot) % 180 == 90 else size
        pads.append({'num': num, 'x': at[0], 'y': at[1], 'w': w, 'h': h})
    xs, ys = [], []
    for m in re.finditer(r'\(fp_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)[^\n]*?(?:\n[^\n]*?){0,3}\(layer "?F.CrtYd"?\)', t):
        a, b, c, d = map(float, m.groups()); xs += [a, c]; ys += [b, d]
    return {'pads': pads, 'cy': (min(xs), min(ys), max(xs), max(ys))}

FP = {}
def fp(name):
    if name not in FP: FP[name] = parse_fp(name)
    return FP[name]

def xform(x, y, X, Y, rot, side):
    if side == 'B': y = -y
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return X + x * c + y * s, Y - x * s + y * c

def rect_poly(cx, cy, w, h, X, Y, rot, side):
    pts = [xform(cx + dx, cy + dy, X, Y, rot, side) for dx, dy in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2))]
    return Polygon(pts)

def part_geom(ref, X, Y, rot, side='B'):
    name = spec.COMPONENTS[ref][3].split(':')[1]
    f = fp(name)
    x0, y0, x1, y1 = f['cy']
    cy = rect_poly((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, X, Y, rot, side)
    nets = {}
    for n, pins in spec.NETS.items():
        for p in pins:
            r, num = p.split('.')
            if r == ref: nets[num] = n
    pads = [{'num': p['num'], 'net': nets.get(p['num'], ''), 'poly': rect_poly(p['x'], p['y'], p['w'], p['h'], X, Y, rot, side),
             'c': xform(p['x'], p['y'], X, Y, rot, side)} for p in f['pads']]
    return {'ref': ref, 'fp': name, 'at': (X, Y, rot, side), 'cy': cy, 'pads': pads}

REMOVED = {'Q51', 'Q52', 'Q55', 'RX12', 'RX5', 'R76'}

class Board:
    def __init__(self, geom='tmp/d2/geom.json'):
        g = json.load(open(ROOT / geom)); self.g = g
        self.hard = []      # (geom, net, kind) on B: non-GND copper, THT keep, holes
        self.gvias = []     # GND vias (removable)
        for t in g['tracks']:
            if t['l'] == 'B.Cu':
                self.hard.append((LineString([t['a'], t['b']]).buffer(t['w'] / 2), t['net'], 'track'))
        for v in g['vias']:
            geo = Point(v['c']).buffer(v['d'] / 2)
            (self.gvias if v['net'] == 'GND' else self.hard).append((geo, v['net'], 'via') if v['net'] != 'GND' else geo)
        for f in g['fps']:
            if f['ref'] in REMOVED: continue
            for p in f['pads']:
                if p['drill'] > 0:
                    b = sbox(*p['bbox'])
                    keep = 0.9 if (p['drill'] > 0.9 and not f['ref'].startswith('H')) else 0.0
                    self.hard.append((b.buffer(keep), p['net'] if not keep else '#THT', 'tht'))
            if f['ref'].startswith('H'):
                self.hard.append((sbox(*f['cy']), '#H', 'hole'))
        for z in g['zones']:
            if 'B.Cu' in z['layers'] and (z['rule'] or z['net'] not in ('GND',)):
                self.hard.append((Polygon(z['pts']), '#RULE' if z['rule'] else z['net'], 'zone'))
        # B.SilkS rail labels (approximate text boxes)
        for x, y in ((11.8, 63.8), (11.6, 50.5), (12.2, 46), (12.2, 58.4)):
            self.hard.append((sbox(x - 2.6, y - 1.0, x + 2.6, y + 1.0), '#SILK', 'silk'))
        self.edge = sbox(0.5, 0.5, 109.5, 84.5)
        self.tree = STRtree([h[0] for h in self.hard]); self.vtree = STRtree(self.gvias)
        self.placed = []

    def check(self, part, gap=0.1):
        cy = part['cy']
        if not self.edge.contains(cy): return None
        for i in self.tree.query(cy.buffer(0.2)):
            geo, net, kind = self.hard[i]
            if geo.distance(cy) < {'silk': 0.0, 'hole': 0.1}.get(kind, 0.2):
                return None
        for q in self.placed:
            if q['cy'].distance(cy) < gap: return None
        remove = []
        for p in part['pads']:
            for i in self.vtree.query(p['poly'].buffer(0.25)):
                if self.gvias[i].distance(p['poly']) < 0.2: remove.append(i)
        return sorted(set(remove))

def place(board, plan, step=0.25):
    """plan: list of dicts ref, region (x0,y0,x1,y1), attract {net: [(x,y),...]}, rots"""
    out = []
    for item in plan:
        ref = item['ref']; x0, y0, x1, y1 = item['region']
        best = None
        rots = item.get('rots', (0, 90, 180, 270))
        X = x0
        while X <= x1:
            Y = y0
            while Y <= y1:
                for rot in rots:
                    part = part_geom(ref, X, Y, rot)
                    if not all(Polygon(sbox(x0 - 0.01, y0 - 0.01, x1 + 0.01, y1 + 0.01)).contains(Point(p['c'])) for p in part['pads'][:1]):
                        pass
                    rem = board.check(part)
                    if rem is None: continue
                    score = 2.0 * len(rem)
                    for p in part['pads']:
                        tg = list(item.get('attract', {}).get(p['net'], []))
                        tg += [q['c'] for o in board.placed for q in o['pads'] if q['net'] == p['net'] and q['net'] != 'GND']
                        if tg: score += min(math.dist(p['c'], t) for t in tg) * item.get('w', {}).get(p['net'], 1.0)
                    if best is None or score < best[0]: best = (score, part, rem)
                Y += step
            X += step
        if best is None:
            print('NO SITE', ref); out.append((ref, None)); continue
        board.placed.append(best[1]); out.append((ref, best[1]['at'], best[2], round(best[0], 2)))
        print(ref, [round(v, 2) if isinstance(v, float) else v for v in best[1]['at']], 'rm', len(best[2]), 'score', round(best[0], 2))
    return out

def dump(board, path):
    json.dump([{'ref': p['ref'], 'at': p['at'], 'cy': list(p['cy'].exterior.coords),
                'pads': [{'num': q['num'], 'net': q['net'], 'c': q['c'], 'poly': list(q['poly'].exterior.coords)} for q in p['pads']]}
               for p in board.placed], open(path, 'w'))

def why(board, part, gap=0.15):
    cy = part['cy']; out = []
    if not board.edge.contains(cy): out.append('edge')
    for i in board.tree.query(cy.buffer(0.2)):
        geo, net, kind = board.hard[i]
        d = geo.distance(cy)
        if d < (0.2 if kind != 'silk' else 0.0): out.append((kind, net, round(d, 2), [round(v, 2) for v in geo.bounds]))
    for q in board.placed:
        if q['cy'].distance(cy) < gap: out.append(('part', q['ref'], round(q['cy'].distance(cy), 2)))
    return out
