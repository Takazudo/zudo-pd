#!/usr/bin/env python3
"""Move only colliding reference labels into nearby readable silkscreen space.

Run with KiCad's Python. The input PCB is never saved. A native DRC identifies
reference fields needing repair; functional labels and package artwork remain
unchanged. The output contains only reference-position/angle/visibility edits.
A second native DRC and a structural fingerprint enforce that limited scope.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import wx
_KICAD_APP = wx.GetApp() or wx.App(False)
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load

KICAD_CLI = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
SILK_TYPES = {'silk_overlap', 'silk_over_copper', 'silk_edge_clearance'}


def serialize(node):
    if isinstance(node, list):
        return '(' + ' '.join(serialize(v) for v in node) + ')'
    return json.dumps(node[1], ensure_ascii=False) if node[0] == 'str' else node[1]


def reference_nodes(tree):
    result = {}
    for fp in find_all(tree, 'footprint'):
        nodes = [v for v in find_all(fp, 'property') if atom(v[1]) == 'Reference']
        if len(nodes) != 1:
            raise ValueError('Each footprint must have one Reference property')
        ref = atom(nodes[0][2])
        if ref in result:
            raise ValueError('Duplicate footprint reference: ' + ref)
        result[ref] = nodes[0]
    return result


def immutable_hash(tree):
    """Exclude only position/angle and visibility of reference fields."""
    tree = copy.deepcopy(tree)
    for field in reference_nodes(tree).values():
        for at in find_all(field, 'at'):
            field.remove(at)
        for effects in find_all(field, 'effects'):
            effects[:] = [x for x in effects if x != ('atom', 'hide')]
        field[:] = [x for x in field if x != ('atom', 'hide')]
        for hidden in find_all(field, 'hide'):
            field.remove(hidden)
    return hashlib.sha256(serialize(tree).encode()).hexdigest()


def bounds(item):
    b = item.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))


def expand(box, gap):
    return box[0] - gap, box[1] - gap, box[2] + gap, box[3] + gap


def overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def point(item):
    q = item.GetPosition()
    return p.ToMM(q.x), p.ToMM(q.y)


class Obstacles:
    """Conservative box collision index, separated by board side."""
    def __init__(self):
        self.cells = {}
        self.boxes = []

    def keys(self, layer, box):
        for x in range(math.floor(box[0] / 5), math.floor(box[2] / 5) + 1):
            for y in range(math.floor(box[1] / 5), math.floor(box[3] / 5) + 1):
                yield layer, x, y

    def add(self, layer, box):
        index = len(self.boxes)
        self.boxes.append(box)
        for key in self.keys(layer, box):
            self.cells.setdefault(key, []).append(index)

    def blocked(self, layer, box):
        ids = set(i for key in self.keys(layer, box) for i in self.cells.get(key, []))
        return any(overlap(box, self.boxes[i]) for i in ids)


def drc(pcb, project_file, scratch, cli, label):
    # A disposable sibling project supplies the actual rule settings. No project
    # file beside either the input or output board is created or overwritten.
    destination = scratch / (label + '.kicad_pcb')
    shutil.copyfile(pcb, destination)
    source_base = project_file
    if not source_base.is_file():
        raise ValueError('DRC project settings not found: ' + str(source_base))
    shutil.copyfile(source_base, destination.with_suffix('.kicad_pro'))
    rules = source_base.with_suffix('.kicad_dru')
    if rules.is_file():
        shutil.copyfile(rules, destination.with_suffix('.kicad_dru'))
    report = scratch / (label + '-drc.json')
    command = [str(cli), 'pcb', 'drc', '--format', 'json', '--output', str(report), str(destination)]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode or not report.is_file():
        raise RuntimeError('Native DRC failed: ' + result.stdout + result.stderr)
    return json.loads(report.read_text())


def reference_violations(report, ids):
    result = {}
    for violation in report['violations']:
        if violation['type'] not in SILK_TYPES:
            continue
        for item in violation['items']:
            if item['uuid'] in ids:
                result.setdefault(ids[item['uuid']], []).append(violation['type'])
    return result


def build_obstacles(board, moving, clearance):
    index = Obstacles()
    for fp in board.GetFootprints():
        graphics = [fp.Reference(), fp.Value(), *list(fp.GraphicalItems())]
        for item in graphics:
            if item.GetLayer() not in (p.F_SilkS, p.B_SilkS):
                continue
            if hasattr(item, 'IsVisible') and not item.IsVisible():
                continue
            if item.m_Uuid.AsString() in moving:
                continue
            index.add(item.GetLayer(), expand(bounds(item), clearance))
        # Keep references outside package courtyards so they remain readable
        # after assembly, rather than printing underneath a component body.
        for courtyard, silk in [(p.F_CrtYd, p.F_SilkS), (p.B_CrtYd, p.B_SilkS)]:
            boxes = [bounds(v) for v in fp.GraphicalItems() if v.GetLayer() == courtyard]
            if boxes:
                index.add(silk, (min(v[0] for v in boxes), min(v[1] for v in boxes),
                                 max(v[2] for v in boxes), max(v[3] for v in boxes)))
        for pad in fp.Pads():
            for mask, silk in [(p.F_Mask, p.F_SilkS), (p.B_Mask, p.B_SilkS)]:
                if pad.GetLayerSet().Contains(mask):
                    margin = max(0, p.ToMM(pad.GetSolderMaskExpansion(mask))) + clearance
                    index.add(silk, expand(bounds(pad), margin))
    for item in board.GetDrawings():
        if item.GetLayer() in (p.F_SilkS, p.B_SilkS):
            index.add(item.GetLayer(), expand(bounds(item), clearance))
    return index


def place(board, bad, clearance, radius):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    moving = {fps[ref].Reference().m_Uuid.AsString() for ref in bad}
    obstacles = build_obstacles(board, moving, clearance)
    edges = [bounds(x) for x in board.GetDrawings() if x.GetLayer() == p.Edge_Cuts]
    if not edges:
        raise ValueError('Missing Edge.Cuts')
    edge = (min(v[0] for v in edges) + .35, min(v[1] for v in edges) + .35,
            max(v[2] for v in edges) - .35, max(v[3] for v in edges) - .35)
    changes = []
    # Larger fields are harder to fit; reserve their nearby spaces first.
    for ref in sorted(bad, key=lambda name: (-len(name), name)):
        fp = fps[ref]; field = fp.Reference()
        old = point(field); old_angle = field.GetTextAngleDegrees()
        candidates = []
        body_parts = [bounds(v) for v in fp.GraphicalItems()
                      if v.GetLayer() in (p.F_CrtYd, p.B_CrtYd)] or [bounds(v) for v in fp.Pads()]
        body = (min(v[0] for v in body_parts), min(v[1] for v in body_parts),
                max(v[2] for v in body_parts), max(v[3] for v in body_parts))
        # The other side of a large capacitor is still nearby the same part,
        # even when it is more than radius away from its original label.
        reach = min(radius, 2.0)
        xs = range(math.floor(min(old[0]-radius, body[0]-reach)*4),
                   math.ceil(max(old[0]+radius, body[2]+reach)*4)+1)
        ys = range(math.floor(min(old[1]-radius, body[1]-reach)*4),
                   math.ceil(max(old[1]+radius, body[3]+reach)*4)+1)
        for angle in dict.fromkeys([old_angle, 0.0, 90.0]):
            field.SetTextAngleDegrees(angle)
            box = bounds(field)
            local = (box[0] - old[0], box[1] - old[1], box[2] - old[0], box[3] - old[1])
            for ix in xs:
                for iy in ys:
                    x, y = ix / 4, iy / 4
                    distance2 = (x-old[0])**2 + (y-old[1])**2
                    body_distance2 = max(body[0]-x, 0, x-body[2])**2 + max(body[1]-y, 0, y-body[3])**2
                    if distance2 > radius**2 and body_distance2 > reach**2:
                        continue
                    moved = (x + local[0], y + local[1], x + local[2], y + local[3])
                    if moved[0] < edge[0] or moved[1] < edge[1] or moved[2] > edge[2] or moved[3] > edge[3]:
                        continue
                    if obstacles.blocked(field.GetLayer(), moved):
                        continue
                    score = distance2 + (.3 if angle != old_angle else 0)
                    candidates.append((score, angle, x, y, moved))
        if candidates:
            _, angle, x, y, box = min(candidates)
            field.SetTextAngleDegrees(angle)
            field.SetPosition(p.VECTOR2I(p.FromMM(x), p.FromMM(y)))
            obstacles.add(field.GetLayer(), expand(box, clearance))
            changes.append({'reference': ref, 'from_mm': old, 'to_mm': [x, y],
                            'angle_before_deg': old_angle, 'angle_after_deg': angle,
                            'hidden': False, 'reason': sorted(set(bad[ref]))})
        else:
            field.SetTextAngleDegrees(old_angle)
            field.SetVisible(False)
            changes.append({'reference': ref, 'from_mm': old, 'to_mm': old,
                            'angle_before_deg': old_angle, 'angle_after_deg': old_angle,
                            'hidden': True, 'reason': f'No free location within {radius:g} mm of old label or {reach:g} mm of own courtyard'})
    return changes


def apply_fields(original, native, refs):
    before = reference_nodes(original); after = reference_nodes(native)
    for ref in refs:
        target, source = before[ref], after[ref]
        for at in find_all(target, 'at'):
            target.remove(at)
        target.append(copy.deepcopy(find_all(source, 'at')[0]))
        # KiCad versions encode field visibility in either effects or property.
        for node in [target, *find_all(target, 'effects')]:
            node[:] = [v for v in node if v != ('atom', 'hide')]
            for hidden in find_all(node, 'hide'):
                node.remove(hidden)
        for hidden in find_all(source, 'hide'):
            target.append(copy.deepcopy(hidden))
        if ('atom', 'hide') in source:
            target.append(('atom', 'hide'))
        for effects in find_all(source, 'effects'):
            if ('atom', 'hide') in effects:
                find_all(target, 'effects')[0].append(('atom', 'hide'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--project-dir', type=Path, help='Actual KiCad project directory for temporary inputs')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--radius', type=float, default=6.0)
    parser.add_argument('--clearance', type=float, default=.20)
    parser.add_argument('--kicad-cli', type=Path, default=KICAD_CLI)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Refusing to overwrite; use a new output path')
    if args.radius <= 0 or args.clearance < .15:
        parser.error('radius must be positive and silkscreen clearance must be at least 0.15 mm')
    args.input = args.input.resolve()
    project_file = (args.project_dir / (args.project_dir.name + ".kicad_pro")) if args.project_dir else args.input.with_suffix(".kicad_pro")
    original = load(args.input); invariant = immutable_hash(original)
    board = p.LoadBoard(str(args.input))
    ids = {f.Reference().m_Uuid.AsString(): f.GetReference() for f in board.GetFootprints()
           if f.Reference().IsVisible() and f.Reference().GetLayer() in (p.F_SilkS, p.B_SilkS)}
    with tempfile.TemporaryDirectory(prefix='zudo-pd-labels-') as temporary:
        scratch = Path(temporary)
        before = drc(args.input, project_file, scratch, args.kicad_cli, 'before')
        bad = reference_violations(before, ids)
        changes = place(board, bad, args.clearance, args.radius)
        native = scratch / 'native.kicad_pcb'
        p.SaveBoard(str(native), board)
        apply_fields(original, load(native), [x['reference'] for x in changes])
        if immutable_hash(original) != invariant:
            raise AssertionError('A non-reference or protected reference field changed')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialize(original) + '\n')
        if immutable_hash(load(args.output)) != invariant:
            raise AssertionError('Output round-trip changed protected content')
        after = drc(args.output.resolve(), project_file, scratch, args.kicad_cli, 'after')
        remaining = reference_violations(after, ids)
        report = {'status': 'FAIL' if remaining else 'PASS', 'input': str(args.input),
                  'output': str(args.output.resolve()), 'reference_violations_before': bad,
                  'reference_violations_after': remaining, 'changes': changes,
                  'moved': sum(not x['hidden'] for x in changes),
                  'hidden': sum(x['hidden'] for x in changes),
                  'protected_content_sha256': invariant,
                  'protected_content_unchanged': True,
                  'remaining_silkscreen_violations': [v for v in after['violations'] if v['type'] in SILK_TYPES],
                  'limits': ['Functional labels and package artwork are preserved, including any pre-existing DRC warnings.',
                             'Clearance search uses conservative boxes and does not shrink reference text.']}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'remaining_silkscreen_violations'}, indent=2))
        return 1 if remaining else 0


if __name__ == '__main__':
    sys.exit(main())
