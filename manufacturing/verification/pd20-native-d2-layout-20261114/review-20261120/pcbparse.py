"""Minimal KiCad 10 .kicad_pcb reader for the D2 review (footprints/pads, segments, vias, zones). Read-only."""
import math, re

def sexp(text):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
    stack = [[]]
    for m in tok.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]

def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def one(node, name):
    k = kids(node, name); return k[0] if k else None

def load(path):
    root = sexp(open(path).read())
    fps, segs, vias, zones = [], [], [], []
    for fp in kids(root, 'footprint'):
        at = one(fp, 'at'); x, y = float(at[1]), float(at[2]); rot = float(at[3]) if len(at) > 3 else 0.0
        ref = next((p[2] for p in kids(fp, 'property') if p[1] == 'Reference'), '?')
        props = {p[1]: p[2] for p in kids(fp, 'property')}
        layer = one(fp, 'layer')[1]
        pads = []
        for p in kids(fp, 'pad'):
            pat = one(p, 'at'); px, py = float(pat[1]), float(pat[2])
            r = math.radians(-rot)
            gx = x + px * math.cos(r) - py * math.sin(r); gy = y + px * math.sin(r) + py * math.cos(r)
            net = one(p, 'net'); size = one(p, 'size'); drill = one(p, 'drill')
            pads.append({'num': p[1], 'type': p[2], 'xy': (gx, gy), 'net': net[-1] if net else None,
                         'size': (float(size[1]), float(size[2])), 'drill': float(drill[1]) if drill and len(drill) > 1 and drill[1] != 'oval' else None})
        fps.append({'ref': ref, 'lib': fp[1], 'xy': (x, y), 'rot': rot, 'layer': layer, 'props': props, 'pads': pads})
    for s in kids(root, 'segment'):
        segs.append({'a': tuple(map(float, one(s, 'start')[1:3])), 'b': tuple(map(float, one(s, 'end')[1:3])),
                     'w': float(one(s, 'width')[1]), 'layer': one(s, 'layer')[1], 'net': one(s, 'net')[1]})
    for v in kids(root, 'via'):
        vias.append({'xy': tuple(map(float, one(v, 'at')[1:3])), 'size': float(one(v, 'size')[1]),
                     'drill': float(one(v, 'drill')[1]), 'net': one(v, 'net')[1]})
    for z in kids(root, 'zone'):
        net = one(z, 'net'); lay = one(z, 'layer') or one(z, 'layers')
        polys = []
        for fp_ in kids(z, 'filled_polygon'):
            pts = [(float(p[1]), float(p[2])) for p in one(fp_, 'pts') if p[0] == 'xy']
            polys.append({'layer': one(fp_, 'layer')[1], 'pts': pts})
        zones.append({'net': net[1] if net else None, 'layer': lay[1:] if lay else None, 'filled': polys})
    return {'fps': fps, 'segs': segs, 'vias': vias, 'zones': zones}

def area(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2
