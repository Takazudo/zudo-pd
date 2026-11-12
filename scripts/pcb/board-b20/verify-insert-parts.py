"""Prove a B20 PCB edit only added parts and changed copper on their nets (plus explicitly allowed nets).

usage: verify-insert-parts.py BEFORE.kicad_pcb AFTER.kicad_pcb --refs R77,R78 [--repin U7.6=UV5_IN ...]
       [--extra-net NET ...] [--reach-mm 10] --output OUT.json

Each board's project is read from beside it (BEFORE.kicad_pro, AFTER.kicad_pro, and any .kicad_dru).

Pure Python (sexp), no third-party dependency. Built for an insertion done in native KiCad, where the
exact copper is only known afterwards. Filled polygons are set aside and:
- every footprint of BEFORE is in AFTER with an identical tree, and AFTER adds exactly --refs. The only exception
  is each --repin pad: a series part splits a net, so that existing pad moves from one new-part net to another
  (for example U7.6 from UV5_DIV to UV5_IN). Its old and new net must be on two pads of one new part, the new
  net must not exist anywhere in BEFORE, and the pad must change; nothing else in that footprint may;
- the allowed nets are the nets on the new footprints' pads plus each --extra-net; every segment and via on any
  other net is unchanged as a whole tree (identity included);
- every removed or added segment or via lies, along its whole length, within --reach-mm of a new courtyard or a repinned
  footprint, so copper on an allowed net cannot change elsewhere on the board;
- every other top-level node (setup, layers, outline and legend graphics, zone definitions) is identical;
- the project's design rules (board.design_settings and net_settings in .kicad_pro, plus any sibling .kicad_dru)
  are identical, so no rule is relaxed outside the PCB file;
- filled copper may differ only inside the edit region: each new courtyard and each removed or added copper item,
  grown by FILL_MARGIN_MM. Every filled-area corner of each zone (by uuid and layer) that appears or disappears
  must lie in that region, so a fill change anywhere else fails. KiCad's zero-width fracture slits are removed first,
  because a hole that changes inside the region can move a slit that ends far outside it.
This is a vertex screen, not a connectivity proof: a far island that loses its connection without any vertex moving,
or a long new fill edge from a vertex inside the region, is left to DRC (unconnected items, isolated copper).
The output records every removed and added copper item, so the delta can be reviewed item by item.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

import math

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, parse, tokenize  # noqa: E402

FILL_MARGIN_MM = 2.0
REACH_MM = 10.0
# KiCad stores 1 nm units; a slit foot rounded onto an outline edge sits within a few nm of it.
SLIT_FOOT_MM = 1e-5


def child(node, name):
    for item in node:
        if isinstance(item, list) and item and atom(item[0]) == name:
            return item
    return None


def strip(node):
    if not isinstance(node, list):
        return node
    return [strip(item) for item in node if not (isinstance(item, list) and item and atom(item[0]) == 'filled_polygon')]


def key(node):
    return json.dumps(node, default=str)


def xy(node, name):
    found = child(node, name)
    return [float(atom(found[1])), float(atom(found[2]))]


def describe(node):
    net = atom(child(node, 'net')[1])
    if atom(node[0]) == 'segment':
        return {'kind': 'segment', 'layer': atom(child(node, 'layer')[1]), 'net': net, 'a': xy(node, 'start'),
                'b': xy(node, 'end'), 'w': float(atom(child(node, 'width')[1]))}
    return {'kind': 'via', 'net': net, 'at': xy(node, 'at'), 'd': float(atom(child(node, 'size')[1])),
            'drill': float(atom(child(node, 'drill')[1]))}


def seg_distance(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def reach(item):
    """(a, b, radius): a capsule covering the item."""
    if item['kind'] == 'segment':
        return item['a'], item['b'], item['w'] / 2
    return item['at'], item['at'], item['d'] / 2


def footprint_refs(tree):
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'footprint':
            for q in item:
                if isinstance(q, list) and q and atom(q[0]) == 'property' and atom(q[1]) == 'Reference':
                    yield atom(q[2])


def footprints(tree):
    found = {}
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'footprint':
            props = {atom(q[1]): q for q in item if isinstance(q, list) and q and atom(q[0]) == 'property'}
            found[atom(props['Reference'][2])] = item
    return found


def pad_nets(fp_node):
    nets = set()
    for pad in fp_node:
        if isinstance(pad, list) and pad and atom(pad[0]) == 'pad' and child(pad, 'net'):
            nets.add(atom(child(pad, 'net')[1]))
    return nets


def pads(fp_node):
    return {atom(p[1]): p for p in fp_node if isinstance(p, list) and p and atom(p[0]) == 'pad'}


def set_pad_net(fp_node, number, net_node):
    for i, item in enumerate(fp_node):
        if isinstance(item, list) and item and atom(item[0]) == 'pad' and atom(item[1]) == number:
            fp_node[i] = [net_node if isinstance(q, list) and q and atom(q[0]) == 'net' else q for q in item]


def footprint_reach(fp_node):
    """(a, b, radius): a circle about the footprint centre covering every pad centre."""
    at = child(fp_node, 'at')
    centre = [float(atom(at[1])), float(atom(at[2]))]
    return centre, centre, max(math.hypot(*xy(p, 'at')) for p in pads(fp_node).values())


def courtyard(fp_node):
    at = child(fp_node, 'at')
    centre = [float(atom(at[1])), float(atom(at[2]))]
    corners = []
    for g in fp_node:
        if isinstance(g, list) and g and atom(g[0]) in ('fp_line', 'fp_rect') and atom(child(g, 'layer')[1]).endswith('CrtYd'):
            corners += [xy(g, 'start'), xy(g, 'end')]
    if not corners:
        raise SystemExit('New footprint has no courtyard')
    # Conservative for any rotation: the circle through the farthest courtyard corner.
    return centre, centre, max(math.hypot(px, py) for px, py in corners)


def ring_corners(pts):
    """Corner vertices of one KiCad filled polygon with its fracture slits removed.

    KiCad stores each filled area as one outline joined to its holes by zero-width slits: an edge that the outline
    also traverses in reverse. A slit's position depends on the holes' order and can land far from an edit. Dropping
    every reverse-edge pair, zero-length edge and straight-through (collinear) vertex leaves the outline and hole
    corners, which do not depend on how the area was fractured.
    """
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    present = collections.Counter(edges)
    keep = [i for i, (a, b) in enumerate(edges) if a != b and not present[(b, a)]]
    by_start = collections.defaultdict(list)
    for i in keep:
        by_start[edges[i][0]].append(i)
    corners = collections.Counter()
    for i in keep:
        u, v = edges[i]
        following = by_start[v]
        if not following:
            corners[v] += 1
            continue
        j = min(following, key=lambda k: (k - i - 1) % n)
        w = edges[j][1]
        (ux, uy), (vx, vy), (wx, wy) = ((float(x), float(y)) for x, y in (u, v, w))
        cross = (vx - ux) * (wy - vy) - (vy - uy) * (wx - vx)
        off_line = abs(cross) > SLIT_FOOT_MM * max(math.hypot(wx - ux, wy - uy), 1e-9)
        if off_line or (vx - ux) * (wx - vx) + (vy - uy) * (wy - vy) < 0:
            corners[v] += 1
    return corners


def fills(tree):
    """Filled-area corners per (zone uuid, layer), as a multiset of exact coordinate strings, fracture slits removed."""
    zones = {}
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'zone':
            name = atom(child(item, 'uuid')[1])
            for fp in item:
                if isinstance(fp, list) and fp and atom(fp[0]) == 'filled_polygon':
                    layer = atom(child(fp, 'layer')[1])
                    pts = [(atom(q[1]), atom(q[2])) for q in child(fp, 'pts')[1:] if atom(q[0]) == 'xy']
                    zones.setdefault((name, layer), collections.Counter()).update(ring_corners(pts))
    return zones


def rules(pcb_path):
    """Design rules from the project beside the board, and the sha256 of each file read."""
    pro = Path(pcb_path).with_suffix('.kicad_pro')
    if not pro.exists():
        raise SystemExit(f'{pro} is missing; the project must sit beside its board to prove no rule changed')
    dru = pro.with_suffix('.kicad_dru')
    project = json.loads(pro.read_text())
    shas = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (pro, dru) if f.exists()}
    return {'design_settings': project['board']['design_settings'], 'net_settings': project['net_settings'],
            'kicad_dru': dru.read_text() if dru.exists() else None}, shas


def all_nets(tree):
    found = set()

    def walk(node):
        if isinstance(node, list) and node:
            if atom(node[0]) == 'net' and len(node) > 1:
                found.add(atom(node[1]))
            for item in node:
                walk(item)
    walk(tree)
    return found


def verify(before_path, after_path, refs, extra_nets, repins=None, reach_mm=REACH_MM):
    repins = dict(repins or {})
    if Path(before_path).resolve() == Path(after_path).resolve():
        raise SystemExit('BEFORE and AFTER are the same file')
    rules_before, project_before = rules(before_path)
    rules_after, project_after = rules(after_path)
    if rules_before != rules_after:
        raise SystemExit('Project design rules changed (design_settings, net_settings or .kicad_dru)')
    raw_before, raw_after = Path(before_path).read_bytes(), Path(after_path).read_bytes()
    before, after = parse(tokenize(raw_before.decode())), parse(tokenize(raw_after.decode()))
    for tree, label in ((before, 'BEFORE'), (after, 'AFTER')):
        refs_seen = list(footprint_refs(tree))
        if len(refs_seen) != len(set(refs_seen)):
            raise SystemExit(f'{label} has duplicate references')
    old, new = footprints(before), footprints(after)
    if set(old) - set(new):
        raise SystemExit(f'Footprints removed: {sorted(set(old) - set(new))}')
    if set(new) - set(old) != refs:
        raise SystemExit(f'Footprints added {sorted(set(new) - set(old))} differ from expected {sorted(refs)}')
    part_nets = set().union(*(pad_nets(new[r]) for r in refs)) if refs else set()
    before_nets = all_nets(before)
    repinned = []
    for spec, net_to in sorted(repins.items()):
        ref, number = spec.split('.', 1)
        pad = pads(old[ref]).get(number) if ref in old else None
        if pad is None:
            raise SystemExit(f'Repinned pad {spec} does not exist')
        net_from = atom(child(pad, 'net')[1])
        if net_from == net_to or not any({net_from, net_to} <= pad_nets(new[r]) for r in refs):
            raise SystemExit(f'Repin {spec} {net_from} -> {net_to} must move between two pads of one new part')
        if net_to in before_nets:
            raise SystemExit(f'Repin {spec} target {net_to} already exists in BEFORE; a split must create a new net')
        after_pad = pads(new[ref]).get(number) if ref in new else None
        if after_pad is None or not child(after_pad, 'net') or atom(child(after_pad, 'net')[1]) != net_to:
            raise SystemExit(f'Repinned pad {spec} is not on {net_to} in AFTER')
        set_pad_net(old[ref], number, child(after_pad, 'net'))
        repinned.append({'pad': spec, 'from': net_from, 'to': net_to})
    for ref in sorted(old):
        if key(strip(old[ref])) != key(strip(new[ref])):
            raise SystemExit(f'Existing footprint {ref} changed' + (' beyond its repinned pad' if any(
                r['pad'].split('.')[0] == ref for r in repinned) else ''))
    allowed = part_nets | set(extra_nets)

    def copper(tree):
        return [i for i in tree if isinstance(i, list) and i and atom(i[0]) in ('segment', 'via')]

    def net(node):
        return atom(child(node, 'net')[1])

    fixed_before = sorted(key(i) for i in copper(before) if net(i) not in allowed)
    fixed_after = sorted(key(i) for i in copper(after) if net(i) not in allowed)
    if fixed_before != fixed_after:
        raise SystemExit('Copper on a net outside the allowed set changed')
    others_before = [key(strip(i)) for i in before if isinstance(i, list) and i and atom(i[0]) not in ('segment', 'via', 'footprint')]
    others_after = [key(strip(i)) for i in after if isinstance(i, list) and i and atom(i[0]) not in ('segment', 'via', 'footprint')]
    if others_before != others_after:
        raise SystemExit('Non-copper board content changed')

    kept = {key(i) for i in copper(before)} & {key(i) for i in copper(after)}
    removed = [describe(i) for i in copper(before) if net(i) in allowed and key(i) not in kept]
    added = [describe(i) for i in copper(after) if net(i) in allowed and key(i) not in kept]
    touched = {item['net'] for item in removed + added}
    if touched - allowed:
        raise SystemExit(f'Changed nets {sorted(touched - allowed)} are not allowed')
    unused = set(extra_nets) - touched
    if unused:
        raise SystemExit(f'Extra nets {sorted(unused)} were allowed but not changed; drop them from the allowance')

    anchors = [courtyard(new[r]) for r in refs] + [footprint_reach(new[r['pad'].split('.')[0]]) for r in repinned]

    def near(point):
        return any(seg_distance(point, a, b) <= r + reach_mm for a, b, r in anchors)

    for item in removed + added:
        a, b, _r = reach(item)
        steps = max(1, math.ceil(math.dist(a, b) / 0.5))
        if not all(near([a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps]) for k in range(steps + 1)):
            raise SystemExit(f'Copper change on {item["net"]} lies beyond {reach_mm} mm of the new parts: {item}')

    region = [courtyard(new[r]) for r in refs] + [reach(item) for item in removed + added]

    def inside(point):
        p = (float(point[0]), float(point[1]))
        return any(seg_distance(p, a, b) <= r + FILL_MARGIN_MM for a, b, r in region)

    f_old, f_new = fills(before), fills(after)
    if set(f_old) != set(f_new):
        raise SystemExit(f'Filled zone set changed: {sorted(set(f_old) ^ set(f_new))}')
    deltas = {}
    for zone in sorted(f_old):
        changed = (f_old[zone] - f_new[zone]) + (f_new[zone] - f_old[zone])
        outside = [pt for pt in changed if not inside(pt)]
        if outside:
            raise SystemExit(f'Fill of {"/".join(zone)} changed outside the edit region, e.g. at {outside[0]}')
        if changed:
            deltas['/'.join(zone)] = sum(changed.values())
    return {'scope': 'B20 part insertion: existing footprints, copper on other nets and non-copper content unchanged; '
                     'fill changes confined to the edit region; not electrical acceptance',
            'before_sha256': hashlib.sha256(raw_before).hexdigest(), 'after_sha256': hashlib.sha256(raw_after).hexdigest(),
            'added_parts': sorted(refs), 'part_nets': sorted(part_nets), 'extra_nets': sorted(extra_nets),
            'repinned_pads': repinned, 'reach_mm': reach_mm, 'project_rules_identical': True,
            'project_before_sha256': project_before, 'project_after_sha256': project_after,
            'removed_copper': removed, 'added_copper': added,
            'existing_footprints_identical': len(old), 'other_net_copper_identical': len(fixed_before),
            'fill_margin_mm': FILL_MARGIN_MM, 'fill_vertices_changed_inside_region': deltas}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--refs', required=True)
    parser.add_argument('--repin', action='append', default=[], help='REF.PAD=NEW_NET')
    parser.add_argument('--extra-net', action='append', default=[])
    parser.add_argument('--reach-mm', type=float, default=REACH_MM)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    repins = dict(r.split('=', 1) for r in args.repin)
    result = verify(args.before, args.after, set(filter(None, args.refs.split(','))), args.extra_net, repins,
                    args.reach_mm)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('removed_copper', 'added_copper')}, indent=2))


if __name__ == '__main__':
    main()
