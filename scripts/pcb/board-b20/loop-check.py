"""Phase 21 desk self-check of the B20 switching-stage loops and shunt sense routing (no field solver, nothing measured).

usage: python3 loop-check.py <geom.json> <routes.json> <out.json>

Per stage it reports the hot-loop polygon through the pad centres (input capacitor VIN pad -> IC VIN pin -> IC SW pin ->
catch-diode cathode -> diode anode -> input capacitor return pad), the copper length and layer of each loop branch, and
whether the input-capacitor and diode returns share F.Cu copper or only meet through vias and the pours. Per INA301
sense pair it reports the trace lengths, the pad each trace lands on, the F.Cu length that runs within a 0.3 mm edge
gap of the partner trace (coupled) and the longest run that does not.
"""
import json
import math
import os
import sys

geom = json.load(open(sys.argv[1]))
routes = json.load(open(sys.argv[2]))
STAGES = {
    'A': ('U1', 'C3', 'D1', 'L1', 'GND'),
    'B': ('U2', 'C7', 'D2', 'L3', 'GND'),
    'C': ('U3', 'CCIN1', 'D3', 'L5', 'M12_RAW'),
}
# builder names -> annotated PCB references (board_b20_spec.BUILDER_REFS)
import importlib.util as _ilu
_s = _ilu.spec_from_file_location('board_b20_spec', __import__('pathlib').Path(__file__).resolve().parents[2] / 'schgen/board_b20_spec.py')
_m = _ilu.module_from_spec(_s)
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'schgen'))
_s.loader.exec_module(_m)
B20_REFS = _m.BUILDER_REFS
# shunt: (amplifier, + sense pin, - sense pin); a pin given as (ref, num) sits on another part. RSH3's M12_PRE sense
# is RL3C.2, the tie of the U9A - reference (U9.4 is the op-amp V- supply; PD20 independent review)
SENSE = {'RSH1': ('U11', '8', '7'), 'RSH2': ('U12', '8', '7'), 'RSH3': ('U9', (B20_REFS.get('RL3C', 'RL3C'), '2'), '3')}


def pad(ref, num, biggest=True):
    hits = [p for p in geom['pads'] if p['ref'] == ref and p['num'] == num]
    key = lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1])
    return max(hits, key=key) if biggest else min(hits, key=key)


def inside(pt, p, tol=0.1):  # a 0.2 mm track end may stop half its width short of the pad box
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
# PD20 layout review: the inverter's M12_RAW pour regions (route.py M12_POURS): which input-capacitor returns and
# output-bank pads sit inside them, and the M12_RAW vias that join the F.Cu regions to the B.Cu one
POURS = routes.get('m12_pours', {})
if POURS:
    def in_poly(pt, pts):
        hit = False
        for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]):
            if (ya > pt[1]) != (yb > pt[1]) and pt[0] < xa + (pt[1] - ya) * (xb - xa) / (yb - ya):
                hit = not hit
        return hit
    m12 = [p for p in geom['pads'] if p['net'] == 'M12_RAW' and not p['drill']]
    vias = [v['at'] for v in routes['vias'] if v['net'] == 'M12_RAW']
    out['m12_raw_pours'] = {
        name: {'layer': z['layer'],
               'pads': sorted({f"{p['ref']}.{p['num']}" for p in m12 if z['layer'] == 'F' and in_poly(p['center'], z['pts'])}),
               'vias_inside': sum(in_poly(v, z['pts']) for v in vias)}
        for name, z in POURS.items()}
    out['stages']['C']['input_cap_returns_in_one_pour'] = all(
        f'{c}.2' in out['m12_raw_pours']['M12_RAW_D3']['pads'] for c in ('CCIN1', 'CCIN2'))
for shunt, (ina, plus, minus) in SENSE.items():
    rows = {}
    for num in (plus, minus):
        ip = pad(*num) if isinstance(num, tuple) else pad(ina, num)
        num = '.'.join(num) if isinstance(num, tuple) else num
        group = [t for t in routes['tracks'] if t['net'] == ip['net']]
        kel = [p for p in geom['pads'] if p['ref'] == shunt and p['net'] == ip['net']]
        target = min(kel, key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))
        ts = branch(ip['net'], ip, target)
        rows[num] = dict(describe(ts), net=ip['net'], lands_on='sense pad' if len(kel) == 2 else 'current pad (no sense pad)')
        rows[num]['segs'] = [t for t in (ts or []) if t['layer'] == 'F']
    key = lambda n: '.'.join(n) if isinstance(n, tuple) else n
    pa, pb = rows[key(plus)].pop('segs'), rows[key(minus)].pop('segs')
    for me, other, num in ((pa, pb, key(plus)), (pb, pa, key(minus))):
        if not me or not other:
            continue
        coupled = run = longest = 0.0
        for t in me:
            L = math.dist(t['a'], t['b'])
            n = max(1, int(L / 0.05))
            for k in range(n):
                q = (t['a'][0] + (t['b'][0] - t['a'][0]) * (k + 0.5) / n, t['a'][1] + (t['b'][1] - t['a'][1]) * (k + 0.5) / n)
                gap = min(seg_dist(q, u['a'], u['b']) - (t['w'] + u['w']) / 2 for u in other)
                if gap <= 0.3 + 1e-6:
                    coupled += L / n
                    run = 0.0
                else:
                    run += L / n
                    longest = max(longest, run)
        rows[num]['coupled_mm'] = round(coupled, 2)       # F.Cu length within 0.3 mm edge gap of the partner trace
        rows[num]['longest_uncoupled_run_mm'] = round(longest, 2)
    out['sense'][shunt] = {'ina': ina, 'pins': rows}

# Pickup estimate (desk arithmetic, order of magnitude; no field solver, nothing measured).
# SW edge: TI SLVSBN0C eq. 55 note, trise = VIN x 0.16 ns/V + 3 ns, at VIN = 20 V. Switched current per stage:
# A and B carry their +12 V / +5 V rail currents; C (inverting) carries Iout x (1 + |Vout| / VIN). The currents are the
# load_cases.py let-through maximum, the largest contract case, so the estimate bounds every contract case (pickup is
# linear in the switched current).
# INA301A3 (SBOS713A): CMR 110 dB min at DC; Figure 9 (typical) falls to about 85 dB at 100 kHz and 65 dB at 1 MHz;
# gain 100 V/V; bandwidth 450 kHz.
MU0, EPS0, EPS_EFF = 4e-7 * math.pi, 8.854e-12, 2.7
VIN = 20.0
T_RISE = (VIN * 0.16 + 3) * 1e-9
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from load_cases import CASES  # noqa: E402
PICKUP_CASE = 'let_through_max'
_L = CASES[PICKUP_CASE]['loads']
SWITCHED_A = {'A': _L['+12'], 'B': _L['+5'], 'C': _L['-12'] * (1 + 12.0 / VIN)}
F_EDGE = 1 / (math.pi * T_RISE)
# 4-layer draft: height (mm) of the F.Cu loops above a solid GND plane; 0 keeps the free-space model of the 2-layer draft.
# An ideal plane adds an image of each loop with opposite current 2h below it (dipole term), and terminates the field
# between two traces (two-microstrip crosstalk rule of thumb, coupling x 1 / (1 + (d / h)^2)).
# 0.2175 mm = the JLC7628 4-layer stackup's 0.2 mm prepreg + half the 0.035 mm F.Cu, used when the routes are 4-layer.
PLANE_H = float(os.environ.get('B20_PLANE_H', 0.2175 if 'In2' in routes.get('layers', []) else 0))


def plane_factor(r_mm):
    if PLANE_H <= 0:
        return 1.0
    big = math.hypot(r_mm, 2 * PLANE_H)
    cos2 = (2 * PLANE_H / big) ** 2
    return abs(1 + (3 * cos2 - 1) * (r_mm / big) ** 3)
INA_GAIN, INA_BW, INA_CMRR_1MHZ_DB = 100.0, 450e3, 65.0


def chain(ts, start):
    """Order a branch's segments into a point list starting at the end nearest `start`."""
    segs = [(tuple(t['a']), tuple(t['b'])) for t in ts]
    pts, cur = [start], start
    while segs:
        k, flip = min(((k, f) for k in range(len(segs)) for f in (0, 1)), key=lambda kf: math.dist(cur, segs[kf[0]][kf[1]]))
        a, b = segs.pop(k)
        a, b = (a, b) if flip == 0 else (b, a)
        pts += [a, b]
        cur = b
    return pts


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


sw_copper = {name: [t for t in routes['tracks'] if t['net'] == pad(ic, '8')['net']] for name, (ic, *_r) in STAGES.items()}
hot = {}
for name, (ic, cin, diode, ind, ground) in STAGES.items():
    cg = next(p for p in geom['pads'] if p['ref'] == cin and p['net'] == ground)
    poly = [pad(cin, '1')['center'], pad(ic, '2')['center'], pad(ic, '8')['center'], pad(diode, '1')['center'], pad(diode, '2')['center'], cg['center']]
    hot[name] = (shoelace(poly) * 1e-6, centroid(poly))
for shunt, (ina, plus, minus) in SENSE.items():
    rows = out['sense'][shunt]['pins']
    ip, im = [pad(*n) if isinstance(n, tuple) else pad(ina, n) for n in (plus, minus)]
    kp = min((p for p in geom['pads'] if p['ref'] == shunt and p['net'] == ip['net']), key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))
    km = min((p for p in geom['pads'] if p['ref'] == shunt and p['net'] == im['net']), key=lambda p: (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]))
    tp, tm = branch(ip['net'], ip, kp), branch(im['net'], im, km)
    pitch = math.dist(ip['center'], im['center'])
    geo = {'amplifier_pin_pitch_mm': round(pitch, 3), 'start_edge_gap_0p2mm_tracks_mm': round(pitch - 0.2, 3),
           'sense_pad_separation_mm': round(math.dist(kp['center'], km['center']), 2)}
    if tp and tm:
        loop = chain(tp, tuple(ip['center'])) + [tuple(kp['center']), tuple(km['center'])] + chain(tm, tuple(im['center']))[::-1]
        area = shoelace(loop) * 1e-6
        c = centroid(loop)
        v_dm = 0.0
        for name, (a_h, ch) in hot.items():
            r = max(math.dist(c, ch), 1.0) * 1e-3
            v_dm += MU0 * a_h * area * (SWITCHED_A[name] / T_RISE) / (4 * math.pi * r ** 3) * plane_factor(r * 1e3)
        # capacitive injection from the nearest SW copper into each trace
        cm = []
        for ts in (tp, tm):
            best = None
            for name, sws in sw_copper.items():
                for t in ts:
                    for u in sws:
                        n = max(1, int(math.dist(t['a'], t['b']) / 0.1))
                        for k in range(n + 1):
                            q = (t['a'][0] + (t['b'][0] - t['a'][0]) * k / n, t['a'][1] + (t['b'][1] - t['a'][1]) * k / n)
                            d = seg_dist(q, u['a'], u['b'])
                            if best is None or d < best[0]:
                                best = (d, u['w'], name)
            length = sum(math.dist(t['a'], t['b']) for t in ts)
            if best:
                d, wu, name = best
                a_eff = (0.2 + wu) / 4
                c_f = math.pi * EPS0 * EPS_EFF * length * 1e-3 / math.acosh(max(d / (2 * a_eff), 1.0001))
                if PLANE_H > 0:
                    c_f /= 1 + (d / PLANE_H) ** 2
                i_inj = c_f * VIN / T_RISE
                v_cm = i_inj * 2 * math.pi * F_EDGE * (length * 1e-9)
                cm.append({'nearest_sw_stage': name, 'centre_distance_mm': round(d, 2), 'trace_mm': round(length, 2),
                           'coupling_pf_upper': round(c_f * 1e12, 4), 'injected_ma_peak': round(i_inj * 1e3, 3), 'v_cm_mv_peak': round(v_cm * 1e3, 3),
                           **({'v_cm_uv_peak': round(v_cm * 1e6, 4)} if PLANE_H > 0 else {})})
        geo.update({'sense_loop_area_mm2': round(area * 1e6, 2), 'differential_pickup_mv_peak_at_input': round(v_dm * 1e3, 3),
                    'capacitive_common_mode': cm, **({'differential_pickup_uv_peak_at_input': round(v_dm * 1e6, 3)} if PLANE_H > 0 else {})})
        worst_cm = max((x['v_cm_mv_peak'] for x in cm), default=0.0)
        if ina.startswith('U1'):
            bw = INA_BW / F_EDGE
            geo['ina301_output_mv_peak'] = {
                'differential_bandwidth_limited': round(v_dm * INA_GAIN * bw * 1e3, 3),
                'common_mode_through_cmrr_1mhz': round(worst_cm * INA_GAIN * 10 ** (-INA_CMRR_1MHZ_DB / 20), 4)}
    out['sense'][shunt]['geometry_and_pickup'] = geo
out['pickup_assumptions'] = {'vin_v': VIN, 'sw_rise_ns': round(T_RISE * 1e9, 2), 'edge_frequency_mhz': round(F_EDGE / 1e6, 1),
                             'switched_current_case': PICKUP_CASE, 'switched_current_source': CASES[PICKUP_CASE]['source'],
                             'switched_current_a': {k: round(v, 3) for k, v in SWITCHED_A.items()},
                             'ina301a3': 'gain 100 V/V, BW 450 kHz, CMRR 65 dB at 1 MHz (SBOS713A Figure 9, typical)',
                             'model': 'magnetic dipole between pad-centre loops; two-wire capacitance to the nearest SW track; 1 nH/mm trace inductance'
                             + (f'; ideal GND plane {PLANE_H} mm below F.Cu: image dipole, coupling x 1/(1+(d/h)^2)' if PLANE_H > 0 else '')}
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print(json.dumps(out, indent=1))
