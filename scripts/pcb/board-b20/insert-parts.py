"""Insert new parts and their local copper into the saved B20 PCB (pinned KiCad 10.0.6 pcbnew).

usage: insert-parts.py IN.kicad_pcb OUT.kicad_pcb PLAN.json

PLAN.json is the committed, reviewed geometry for one incremental change. It lists the parts to add,
the existing tracks and vias to remove, and the tracks and vias to add. Every new part must be in
board_b20_components.py and absent from IN. Every removed or added copper item must be on a net that
a new part's pad uses. The script fails without saving when:
- the footprint set after insertion differs from the components projection;
- a new part's footprint, value, LCSC or pad nets differ from the spec;
- a removed item does not match exactly one existing item (layer, net, geometry, width);
- an added or removed item is on a net that no new part touches.
It never moves an existing footprint and never touches other nets. Fills are redone by
finalize_refill.py, and verify-insert-parts.py proves the rest of the board is unchanged.
"""
import json
from pathlib import Path
import sys

import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
sys.path.insert(0, str(ROOT / 'scripts/pcb'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_b20_components import COMPONENTS  # noqa: E402
import board_b20_spec as spec  # noqa: E402
from deterministic_ids import drawing_key, stable_id  # noqa: E402
from pcb_common import pcb_net_name  # noqa: E402
from schgen_core import new_uuid  # noqa: E402

LIB = str(ROOT / 'footprints/kicad/zudo-power.pretty')
LAYERS = {'F.Cu': p.F_Cu, 'In2.Cu': p.In2_Cu, 'B.Cu': p.B_Cu}
NM = 1e-6  # plan coordinates are mm; pcbnew is nm


def nm(v):
    return int(round(v * 1e6))


def vec(xy):
    return p.VECTOR2I(nm(xy[0]), nm(xy[1]))


def same_point(a, xy):
    return a.x == nm(xy[0]) and a.y == nm(xy[1])


def pad_nets(ref):
    nets = {}
    for name, pins in spec.NETS.items():
        for pin in pins:
            r, num = pin.rsplit('.', 1)
            if r == ref:
                nets[num] = name
    return nets


def part_ids(fp, ref):
    # Same identity scheme as deterministic_ids.builder_ids, applied to the new footprint only.
    import collections
    stable_id(fp, 'footprint', ref)
    for field in fp.GetFields():
        stable_id(field, 'footprint-field', ref, field.GetName())
    counts = collections.Counter()
    for pad in fp.Pads():
        key = [pad.GetNumber(), [int(pad.GetPosition().x), int(pad.GetPosition().y)],
               [int(pad.GetSize().x), int(pad.GetSize().y)], [int(pad.GetDrillSize().x), int(pad.GetDrillSize().y)],
               pad.GetLayerSet().FmtHex(), int(pad.GetAttribute()), int(pad.GetShape(p.F_Cu))]
        text = json.dumps(key, sort_keys=True)
        stable_id(pad, 'pad', ref, key, counts[text])
        counts[text] += 1
    counts = collections.Counter()
    for item in fp.GraphicalItems():
        key = drawing_key(item)
        text = json.dumps(key, sort_keys=True)
        stable_id(item, 'footprint-graphic', ref, key, counts[text])
        counts[text] += 1


def main():
    source, output, plan_path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    plan = json.loads(plan_path.read_text())
    board = p.LoadBoard(source)
    existing = {fp.GetReference() for fp in board.GetFootprints()}
    parts = plan['parts']
    refs = [part['ref'] for part in parts]
    allowed_nets = set()
    for ref in refs:
        if ref in existing:
            raise SystemExit(f'{ref} is already on the PCB')
        if ref not in COMPONENTS:
            raise SystemExit(f'{ref} is not in the B20 components projection')
        allowed_nets |= set(pad_nets(ref).values())
    if set(COMPONENTS) - existing != set(refs):
        raise SystemExit(f'Projection adds {sorted(set(COMPONENTS) - existing)}, plan adds {sorted(refs)}')

    nets = {}
    for name in sorted(allowed_nets):
        net = board.FindNet(pcb_net_name(name))
        if net is None:
            net = p.NETINFO_ITEM(board, pcb_net_name(name))
            board.Add(net)
        nets[name] = net

    for part in parts:
        ref = part['ref']
        symbol, value, lcsc, footprint, dnp, _ = COMPONENTS[ref]
        if footprint != part['footprint']:
            raise SystemExit(f'{ref}: plan footprint {part["footprint"]} differs from projection {footprint}')
        fp = p.FootprintLoad(LIB, footprint.split(':')[1])
        if not fp:
            raise SystemExit(f'missing footprint {footprint}')
        board.Add(fp)
        fp.SetFPID(p.LIB_ID(*footprint.split(':', 1)))
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetField('LCSC', lcsc)
        fp.GetField('LCSC').SetVisible(False)
        fp.SetPath(p.KIID_PATH('/' + new_uuid('board-b20-draft:root') + '/' + new_uuid('board-b20-draft:' + ref + ':instance')))
        fp.SetDNP(dnp)
        fp.Value().SetVisible(False)
        fp.Reference().SetLayer(p.F_Fab)
        fp.Reference().SetTextSize(p.VECTOR2I(p.FromMM(0.5), p.FromMM(0.5)))
        fp.Reference().SetTextThickness(p.FromMM(0.08))
        want = pad_nets(ref)
        if {pad.GetNumber() for pad in fp.Pads()} != set(want):
            raise SystemExit(f'{ref}: pads {sorted(pad.GetNumber() for pad in fp.Pads())} differ from spec {sorted(want)}')
        for pad in fp.Pads():
            pad.SetNet(nets[want[pad.GetNumber()]])
        fp.SetPosition(vec(part['at']))
        fp.SetOrientationDegrees(part['rot'])
        for pad in fp.Pads():
            want_xy = part['pads'][pad.GetNumber()]
            got = pad.GetPosition()
            if abs(got.x - nm(want_xy[0])) > 1 or abs(got.y - nm(want_xy[1])) > 1:
                raise SystemExit(f'{ref}.{pad.GetNumber()} lands at {got.x / 1e6}, {got.y / 1e6}; plan says {want_xy}')
        part_ids(fp, ref)

    tracks = list(board.GetTracks())
    removed = []
    for item in plan['remove_tracks']:
        if item['net'] not in allowed_nets:
            raise SystemExit(f'remove on unrelated net {item["net"]}')
        hits = [t for t in tracks if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == pcb_net_name(item['net'])
                and t.GetLayer() == LAYERS[item['layer']] and t.GetWidth() == nm(item['w'])
                and ((same_point(t.GetStart(), item['a']) and same_point(t.GetEnd(), item['b']))
                     or (same_point(t.GetStart(), item['b']) and same_point(t.GetEnd(), item['a'])))]
        if len(hits) != 1:
            raise SystemExit(f'track to remove matched {len(hits)} items: {item}')
        removed.append(hits[0])
    for item in plan['remove_vias']:
        if item['net'] not in allowed_nets:
            raise SystemExit(f'remove on unrelated net {item["net"]}')
        hits = [t for t in tracks if t.GetClass() == 'PCB_VIA' and t.GetNetname() == pcb_net_name(item['net'])
                and same_point(t.GetPosition(), item['at'])]
        if len(hits) != 1:
            raise SystemExit(f'via to remove matched {len(hits)} items: {item}')
        removed.append(hits[0])
    if len({id(t) for t in removed}) != len(removed):
        raise SystemExit('plan removes one item twice')
    for t in removed:
        board.Remove(t)

    for index, item in enumerate(plan['add_tracks']):
        if item['net'] not in allowed_nets:
            raise SystemExit(f'add on unrelated net {item["net"]}')
        t = p.PCB_TRACK(board)
        t.SetStart(vec(item['a']))
        t.SetEnd(vec(item['b']))
        t.SetWidth(nm(item['w']))
        t.SetLayer(LAYERS[item['layer']])
        t.SetNet(nets[item['net']])
        stable_id(t, 'inserted-track', plan['id'], index, item)
        board.Add(t)
    for index, item in enumerate(plan['add_vias']):
        if item['net'] not in allowed_nets:
            raise SystemExit(f'add on unrelated net {item["net"]}')
        v = p.PCB_VIA(board)
        v.SetPosition(vec(item['at']))
        v.SetWidth(nm(item['d']))
        v.SetDrill(nm(item['drill']))
        v.SetNet(nets[item['net']])
        stable_id(v, 'inserted-via', plan['id'], index, item)
        board.Add(v)

    after = {fp.GetReference() for fp in board.GetFootprints()}
    if after - {r for r in after if r not in COMPONENTS} != set(COMPONENTS):
        raise SystemExit(f'Footprint set differs from the projection: missing {sorted(set(COMPONENTS) - after)}')
    board.Save(output)
    print(json.dumps({'plan': plan['id'], 'added_parts': refs, 'removed_items': len(removed),
                      'added_tracks': len(plan['add_tracks']), 'added_vias': len(plan['add_vias']),
                      'nets': sorted(allowed_nets)}, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
