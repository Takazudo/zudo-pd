"""Prove a finalized B20 PCB differs from its predecessor only by one reviewed insertion plan.

usage: verify-insert-parts.py BEFORE.kicad_pcb AFTER.kicad_pcb PLAN.json OUT.json

Pure Python (sexp) plus shapely for the fill comparison. Filled polygons are set aside and:
- every footprint of BEFORE is in AFTER with an identical tree; AFTER adds exactly the plan parts,
  at the plan position and rotation;
- the segments and vias of BEFORE, less exactly the plan removals, equal those of AFTER less exactly
  the plan additions, as whole trees (identity included);
- every other top-level node (setup, layers, outline and legend graphics, zone definitions) is identical;
- filled copper may differ only inside the plan region: each new footprint courtyard and each removed
  or added copper item, grown by FILL_MARGIN_MM. Any fill change outside it fails.
"""
import hashlib
import json
from pathlib import Path
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, parse, tokenize  # noqa: E402

FILL_MARGIN_MM = 2.0
AREA_EPS_MM2 = 1e-6


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
    return (float(atom(found[1])), float(atom(found[2])))


def copper(node):
    kind = atom(node[0])
    net = atom(child(node, 'net')[1])
    if kind == 'segment':
        return ('segment', atom(child(node, 'layer')[1]), net, xy(node, 'start'), xy(node, 'end'), float(atom(child(node, 'width')[1])))
    return ('via', net, xy(node, 'at'), float(atom(child(node, 'size')[1])), float(atom(child(node, 'drill')[1])))


def plan_track(item):
    a, b = tuple(item['a']), tuple(item['b'])
    return [('segment', item['layer'], item['net'], a, b, item['w']), ('segment', item['layer'], item['net'], b, a, item['w'])]


def take(items, wanted, label):
    """Remove exactly one match per wanted entry (each entry lists equivalent spellings)."""
    left = list(items)
    for options in wanted:
        hits = [i for i, (sig, _node) in enumerate(left) if sig in options]
        if len(hits) != 1:
            raise SystemExit(f'{label}: {options[0]} matched {len(hits)} items')
        left.pop(hits[0])
    return left


def fills(tree):
    zones = {}
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'zone':
            name = atom(child(item, 'name')[1]) if child(item, 'name') else ''
            for fp in item:
                if isinstance(fp, list) and fp and atom(fp[0]) == 'filled_polygon':
                    layer = atom(child(fp, 'layer')[1])
                    pts = [(float(atom(q[1])), float(atom(q[2]))) for q in child(fp, 'pts')[1:] if atom(q[0]) == 'xy']
                    zones.setdefault((name, layer), []).append(Polygon(pts).buffer(0))
    return {k: unary_union(v) for k, v in zones.items()}


def courtyard(fp_node):
    at = child(fp_node, 'at')
    x, y = float(atom(at[1])), float(atom(at[2]))
    xs, ys = [], []
    for g in fp_node:
        if isinstance(g, list) and g and atom(g[0]) in ('fp_line', 'fp_rect') and atom(child(g, 'layer')[1]).endswith('CrtYd'):
            for name in ('start', 'end'):
                px, py = xy(g, name)
                xs.append(px)
                ys.append(py)
    # A rotated rectangle is enclosed by the circle through its corners; use that conservative bound.
    r = max((px ** 2 + py ** 2) ** 0.5 for px in xs for py in ys)
    return Point(x, y).buffer(r)


def main():
    before_path, after_path, plan_path, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    plan = json.loads(plan_path.read_text())
    raw_before, raw_after = Path(before_path).read_bytes(), Path(after_path).read_bytes()
    before, after = parse(tokenize(raw_before.decode())), parse(tokenize(raw_after.decode()))

    def footprints(tree):
        found = {}
        for item in tree:
            if isinstance(item, list) and item and atom(item[0]) == 'footprint':
                props = {atom(q[1]): q for q in item if isinstance(q, list) and q and atom(q[0]) == 'property'}
                found[atom(props['Reference'][2])] = item
        return found

    old, new = footprints(before), footprints(after)
    refs = {part['ref'] for part in plan['parts']}
    if set(new) - set(old) != refs or set(old) - set(new):
        raise SystemExit(f'Footprint set change {sorted(set(new) ^ set(old))} differs from plan {sorted(refs)}')
    for ref in old:
        if key(strip(old[ref])) != key(strip(new[ref])):
            raise SystemExit(f'Existing footprint {ref} changed')
    for part in plan['parts']:
        at = child(new[part['ref']], 'at')
        got = (float(atom(at[1])), float(atom(at[2])), float(atom(at[3])) if len(at) > 3 else 0.0)
        if got != (part['at'][0], part['at'][1], float(part['rot'])):
            raise SystemExit(f'{part["ref"]} placed at {got}, plan {part["at"]} rot {part["rot"]}')

    def copper_items(tree):
        return [(copper(i), i) for i in tree if isinstance(i, list) and i and atom(i[0]) in ('segment', 'via')]

    def others(tree):
        return [key(strip(i)) for i in tree if isinstance(i, list) and i and atom(i[0]) not in ('segment', 'via', 'footprint')]

    removals = [plan_track(t) for t in plan['remove_tracks']]
    removals += [[('via', v['net'], tuple(v['at']), v['d'], v['drill'])] for v in plan['remove_vias']]
    additions = [plan_track(t) for t in plan['add_tracks']]
    additions += [[('via', v['net'], tuple(v['at']), v['d'], v['drill'])] for v in plan['add_vias']]
    kept_before = take(copper_items(before), removals, 'plan removal')
    kept_after = take(copper_items(after), additions, 'plan addition')
    if sorted(key(n) for _s, n in kept_before) != sorted(key(n) for _s, n in kept_after):
        raise SystemExit('Copper outside the plan changed')
    if others(before) != others(after):
        raise SystemExit('Non-copper board content changed')

    region = [courtyard(new[r]) for r in refs]
    for t in plan['remove_tracks'] + plan['add_tracks']:
        region.append(LineString([t['a'], t['b']]).buffer(t['w'] / 2))
    for v in plan['remove_vias'] + plan['add_vias']:
        region.append(Point(v['at']).buffer(0.4))
    region = unary_union(region).buffer(FILL_MARGIN_MM)
    f_old, f_new = fills(before), fills(after)
    if set(f_old) != set(f_new):
        raise SystemExit(f'Filled zone set changed: {sorted(set(f_old) ^ set(f_new))}')
    deltas = {}
    for zone in sorted(f_old):
        diff = f_old[zone].symmetric_difference(f_new[zone])
        outside = diff.difference(region).area
        if outside > AREA_EPS_MM2:
            raise SystemExit(f'Fill of {zone} changed outside the plan region by {outside:.6f} mm2')
        if diff.area > AREA_EPS_MM2:
            deltas['/'.join(zone)] = round(diff.area, 4)
    result = {'scope': 'Incremental B20 insertion: existing footprints, other copper and non-copper content unchanged; '
                       'fill changes confined to the plan region; not electrical acceptance',
              'plan': plan['id'], 'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
              'before_sha256': hashlib.sha256(raw_before).hexdigest(), 'after_sha256': hashlib.sha256(raw_after).hexdigest(),
              'added_parts': sorted(refs), 'removed_copper': len(removals), 'added_copper': len(additions),
              'fill_margin_mm': FILL_MARGIN_MM, 'fill_delta_mm2_inside_region': deltas,
              'existing_footprints_identical': len(old), 'other_copper_identical': len(kept_before)}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
