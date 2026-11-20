#!/usr/bin/env python3
"""Check Board L's rear controls against the schematic spec and a KiCad DRC report."""
import argparse
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import board_l_spec as spec
from sexp import atom, find_all, load


def field(node, name):
    return atom(find_all(node, name)[0][1])


def check_board(path):
    board = load(str(path))
    footprints = {}
    nets = {}
    for fp in find_all(board, 'footprint'):
        properties = {atom(p[1]): atom(p[2]) for p in find_all(fp, 'property')}
        ref = properties['Reference']
        if ref not in spec.COMPONENTS:
            continue
        assert ref not in footprints, f'Duplicate footprint {ref}'
        footprints[ref] = fp
        assert atom(fp[1]) == spec.COMPONENTS[ref][3], f'Wrong footprint for {ref}'
        for pad in find_all(fp, 'pad'):
            net = find_all(pad, 'net')
            if net:
                nets[f'{ref}.{atom(pad[1])}'] = atom(net[0][-1])
    assert set(footprints) == set(spec.COMPONENTS) - set(spec.EXTERNAL_COMPONENTS)
    for name, pins in spec.NETS.items():
        for pin in pins:
            if pin.split('.')[0] not in spec.EXTERNAL_COMPONENTS:
                assert nets.get(pin) == name, f'{pin}: {nets.get(pin)} != {name}'
    assert {p for p, net in nets.items() if net == 'V15_FUSED'} == {'F1.2', 'SW2.2'}
    assert field(footprints['RV1'], 'layer') == 'B.Cu'
    assert field(footprints['SW2'], 'layer') == 'B.Cu'
    assert all(field(footprints[f'LED{i}'], 'layer') == 'F.Cu' for i in range(1, 25))
    attrs = {atom(a) for a in find_all(footprints['SW2'], 'attr')[0][1:]}
    assert 'through_hole' in attrs
    assert not {'exclude_from_bom', 'exclude_from_pos_files'} & attrs
    assert not any(any(atom(p[1]) == 'Reference' and atom(p[2]) == 'J5'
                       for p in find_all(f, 'property')) for f in find_all(board, 'footprint'))
    properties = {atom(p[1]): atom(p[2]) for p in find_all(footprints['SW2'], 'property')}
    assert properties['LCSC'] == properties['LCSC Part'] == 'C5446803'
    for pad in find_all(footprints['SW2'], 'pad'):
        assert xy(find_all(pad,'size')[0]) == (2.25,2.25)
        assert abs(float(atom(find_all(pad,'drill')[0][1]))-1.6)<.001
    for ref,value,lcsc in [('RV1','RK10J11E0034','C470643'),('R22','100k','C25803'),('R27','100R','C22775')]:
        properties={atom(p[1]):atom(p[2]) for p in find_all(footprints[ref],'property')}
        assert properties['LCSC']==lcsc, f'{ref} wrong assembly part'
    assert 'SW2.3' in spec.NO_CONNECT
    assert nets['SW2.3'] == 'unconnected-(SW2-Pad3)'
    assert [pin for pin, net in nets.items() if net == nets['SW2.3']] == ['SW2.3']
    # OFF connects the fused supply to throw 3 inside the switch; it has no board copper connection.
    for kind in ['segment', 'via', 'zone']:
        for item in find_all(board, kind):
            net = find_all(item, 'net')
            assert not net or atom(net[0][-1]) != nets['SW2.3'], 'OFF throw must stay isolated'
    for ref, name, expected in [
        ('SW2', 'SW-TH_SS-12D01-G020', [(-4.4,4.4),(-1.95,1.95),(-4.3,6.0)]),
        ('RV1', 'POT-TH_RK10J11E0034_family', [(-7,7),(-5.124958,9.525),(-2.100072,1.970024)]),
    ]:
        models = find_all(footprints[ref], 'model')
        assert len(models) == 1
        assert atom(models[0][1]) == '${KIPRJMOD}/../../footprints/kicad/zudo-led-lamp.3dshapes/' + name + '.wrl'
        for kind, transform_value in [('offset',(0,0,0)),('rotate',(0,0,0)),('scale',(1,1,1))]:
            assert tuple(float(atom(v)) for v in find_all(find_all(models[0],kind)[0],'xyz')[0][1:]) == transform_value
        model_path = ROOT / 'footprints/kicad/zudo-led-lamp.3dshapes' / (name+'.wrl')
        assert model_path.with_suffix('.step').is_file()
        points=[]
        for block in re.findall(r'point\s*\[([^]]+)\]',model_path.read_text()):
            values=list(map(float,re.findall(r'[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?',block)))
            points.extend(zip(values[::3],values[1::3],values[2::3]))
        bounds=[(min(p[i] for p in points)*2.54,max(p[i] for p in points)*2.54) for i in range(3)]
        assert all(math.dist(a,e)<.001 for a,e in zip(bounds,expected)), f'Recheck {ref} model bounds'
    assert abs(float(field(find_all(board,'general')[0],'thickness'))-1.6)<.001
    assert set(nets[p] for p in ['RV1.1','RV1.2','RV1.3']) == {'GND','BRIGHT_WIPER','V3P3'}
    for number in ['MP1','MP2','MP3','MP4']:
        assert nets['RV1.'+number].startswith('unconnected-')
    assert nets['U3.8'].startswith('unconnected-')
    assert set(nets[p] for p in ['R27.2','R22.1','C22.1','U3.7']) == {'BRIGHT_ADC'}
    # The shared supplier footprint had a dual-gang pin map. Check actual single-gang rows.
    for number, point in [('1',(-4,-5)),('2',(0,-5)),('3',(4,-5)),
                          ('MP1',(-2,-5)),('MP2',(2,-5)),('MP3',(5,5)),('MP4',(-5,5))]:
        pad=next(p for p in find_all(footprints['RV1'],'pad') if atom(p[1])==number)
        assert math.dist(xy(find_all(pad,'at')[0]),point)<.001, f'Wrong single-gang pad {number}'
    return len(footprints)


def footprints(path):
    return {next(atom(p[2]) for p in find_all(f, 'property') if atom(p[1]) == 'Reference'): f
            for f in find_all(load(str(path)), 'footprint')}


def xy(node):
    return tuple(float(atom(v)) for v in node[1:3])


def transform(fp, point):
    at = find_all(fp, 'at')[0]
    x, y = xy(at)
    angle = math.radians(float(atom(at[3])) if len(at) > 3 else 0)
    px, py = point
    return x + px * math.cos(angle) + py * math.sin(angle), y - px * math.sin(angle) + py * math.cos(angle)


def pad_position(fp, number):
    pad = next(p for p in find_all(fp, 'pad') if atom(p[1]) == number)
    return transform(fp, xy(find_all(pad, 'at')[0]))


def check_stack(board_path, power_path):
    lamp, power = footprints(board_path), footprints(power_path)
    for path, expected in [(board_path, (0, 0, 60, 60)), (power_path, (0, 0, 27, 40))]:
        edges = [item for item in load(str(path)) if isinstance(item, list)
                 and find_all(item, 'layer') and field(item, 'layer') == 'Edge.Cuts']
        assert len(edges) == 1 and atom(edges[0][0]) == 'gr_rect', \
            'Recheck stack occupancy after changing the rectangular board outline'
        points = [xy(find_all(line, end)[0]) for line in edges for end in ['start', 'end']]
        bounds = (min(x for x, y in points), min(y for x, y in points),
                  max(x for x, y in points), max(y for x, y in points))
        assert bounds == expected, 'Recheck stack occupancy after resizing a board'
    # The two shared pillar pairs lock the translation, independently of connector pin order.
    for path, targets in [(power_path, [(4, 4), (23, 4)]),
                          (board_path, [(20.5, 4), (39.5, 4)])]:
        holes = [xy(find_all(f, 'at')[0]) for f in find_all(load(str(path)), 'footprint')
                 if 'MountingHole' in atom(f[1])]
        assert all(any(math.dist(target, hole) < .001 for hole in holes) for target in targets)
    assert field(lamp['J2'], 'layer') == 'B.Cu' and field(power['JOUT1'], 'layer') == 'F.Cu'
    expected_power = ['VBUS_OUT', 'VBUS_OUT', 'ATT', 'PDOK', 'GND', 'GND']
    for number in map(str, range(1, 7)):
        ppad = next(p for p in find_all(power['JOUT1'], 'pad') if atom(p[1]) == number)
        assert atom(find_all(ppad, 'net')[0][-1]) == expected_power[int(number)-1]
        px, py = pad_position(power['JOUT1'], number)
        assert math.dist(pad_position(lamp['J2'], number), (px + 16.5, py)) < .001, \
            f'Pin {number} does not mate at the pillar-aligned position'
    for ref, expected in [('RV1',(51.9,9.5)),('SW2',(9.1,27.75))]:
        assert math.dist(xy(find_all(lamp[ref],'at')[0]),expected)<.001
    # Transform the entire placed courtyard, including the off-origin 14.2 mm wheel.
    for ref in ['RV1','SW2']:
        fp=lamp[ref]
        points=[]
        for kind in ['fp_rect','fp_line']:
            for graphic in find_all(fp,kind):
                if field(graphic,'layer') == 'B.CrtYd':
                    points.extend(transform(fp,xy(find_all(graphic,end)[0])) for end in ['start','end'])
        assert points, f'{ref} courtyard missing'
        left,top,right,bottom=min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)
        assert left>=.5 and top>=.5 and right<=59.5 and bottom<=59.5
        assert right<=15.5 or left>=44.5 or top>=41, f'{ref} intrudes into Board P plus 1mm margin'


def check_drc(path, baseline=None):
    report = json.loads(path.read_text())
    assert not report['unconnected_items'], 'Unrouted connections remain'
    assert not report['schematic_parity'], 'PCB differs from schematic'
    unexpected = [v for v in report['violations']
                  if v['severity'] == 'error' or v['type'] not in {'silk_overlap', 'silk_over_copper'}]
    assert not unexpected, f'Electrical/layout violations: {unexpected}'
    if baseline:
        old = json.loads(baseline.read_text())
        signature = lambda v: (v['type'], tuple(sorted(i['uuid'] for i in v['items'])))
        previous = {signature(v) for v in old['violations']}
        assert all(signature(v) in previous for v in report['violations']), 'New DRC warnings introduced'
    return len(report['violations'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT / 'boards/board-l/board-l.kicad_pcb')
    parser.add_argument('--drc-report', type=Path, required=True,
                        help='Fresh kicad-cli pcb drc --format json --schematic-parity --refill-zones report')
    parser.add_argument('--baseline-drc', type=Path, help='Optional prior report; reject every new warning signature')
    args = parser.parse_args()
    count = check_board(args.board)
    check_stack(args.board, ROOT / 'boards/board-p/board-p.kicad_pcb')
    warnings = check_drc(args.drc_report, args.baseline_drc)
    print(f'PASS: {count} schematic footprints, rear controls, LED orientation and switch nets; '
          f'pillar-aligned 6-pin mating and Board P clearance; 0 electrical errors, 0 unrouted, 0 parity issues; {warnings} silkscreen warnings')
    print('DRC validates copper; enclosure fit, assembled OFF isolation and knob direction require hardware.')


if __name__ == '__main__':
    main()
