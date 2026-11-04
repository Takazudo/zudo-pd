#!/usr/bin/env python3
"""Check board-b20-draft against its schematic and the shared Board B mechanical contract.

usage: kicad-python verify-mechanics.py [pcb] [--output report.json]

B20 keeps the Board B outline, PD stack, corner supports, terminal blocks and bus sockets (boards/board-b/mechanical.json)
but carries its own nets. This mirrors scripts/pcb/verify-board-b.py and the shared parts of
scripts/pcb/verify-compact-mechanics.py with the B20 net names, without changing either Board B verifier (their hashes
bind the 15 V package's stack proof). The front/back rail labels follow the reviewed Board B contract and are checked
against the J6/J7 pin nets (PD20). The Board B top-edge pogo row (P1, TP3-TP5) keeps the contract positions with the
B20 nets of the 2026-11-04 owner decision: no ATT (P1.1 and P1.4 open), PDOK, the shared GND P1.3 and the three *_PRE nodes.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import wx
_KICAD_APP = wx.GetApp() or wx.App(False)
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/pcb'))
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from board_b_layout import WIDTH, HEIGHT, pd_to_board_b  # noqa: E402
from pcb_common import pcb_net_name  # noqa: E402
import board_b20_spec as spec  # noqa: E402

_compact = importlib.util.spec_from_file_location('compact_mechanics', ROOT / 'scripts/pcb/verify-compact-mechanics.py')
compact = importlib.util.module_from_spec(_compact)
_compact.loader.exec_module(compact)

CONTRACT = ROOT / 'boards/board-b/mechanical.json'
# Board P r3 contact roles on B20: VBUS_OUT feeds VIN directly; ATT is not used by the B20 draft (J5.3 no-connect).
PD_NETS = {'VBUS_OUT': 'VIN', 'ATT': None, 'PDOK': 'PDOK', 'GND': 'GND'}
TERMINAL_NETS = {'J6': {'1': 'GND', '2': 'M12_OUT'}, 'J7': {'1': 'P5_OUT', '2': 'P12_OUT'}}
# owner decision 2026-11-04: Board B's seven contacts left to right, carrying B20 nets (None: unconnected copper)
POGO_NETS = (None, 'PDOK', 'GND', None, 'P12_PRE', 'P5_PRE', 'M12_PRE')
SOCKET_NETS = {1: 'M12_OUT', 2: 'M12_OUT', **{n: 'GND' for n in range(3, 9)}, 9: 'P12_OUT', 10: 'P12_OUT',
               11: 'P5_OUT', 12: 'P5_OUT', 13: 'CV', 14: 'CV', 15: 'GATE', 16: 'GATE'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def xy(item):
    pos = item.GetPosition()
    return [p.ToMM(pos.x), p.ToMM(pos.y)]


def near(a, b, tol=.001):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def unconnected(pad):
    return pad.GetNetCode() == 0 or pad.GetNetname().startswith('unconnected-')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', nargs='?', type=Path, default=ROOT / 'boards/board-b20-draft/board-b20-draft.kicad_pcb')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    board = p.LoadBoard(str(args.pcb))
    fps = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        require(ref not in fps, 'Duplicate reference ' + ref)
        fps[ref] = fp
    contract = json.loads(CONTRACT.read_text())
    errors = []

    def check(name, fn):
        try:
            return fn()
        except (KeyError, ValueError, StopIteration) as error:
            errors.append(f'{name}: {error}')

    def identity():
        expected = {pin: pcb_net_name(net) for net, pins in spec.NETS.items() for pin in pins}
        seen = set()
        for ref, comp in spec.COMPONENTS.items():
            require(ref in fps, 'missing ' + ref)
            fp = fps[ref]
            require(fp.GetValue() == comp[1] and fp.GetFPIDAsString() == comp[3] and fp.IsDNP() == comp[4],
                    ref + ': identity/population mismatch')
            require(fp.GetFieldText('LCSC') == comp[2], ref + ': LCSC mismatch')
            for pad in fp.Pads():
                key = ref + '.' + pad.GetNumber()
                if pad.GetAttribute() == p.PAD_ATTRIB_NPTH:
                    continue
                if key in spec.NO_CONNECT:
                    require(unconnected(pad), key + ': no-connect was connected')
                else:
                    require(expected.get(key) == pad.GetNetname(), key + ': incorrect/missing net ' + pad.GetNetname())
                    seen.add(key)
        require(seen == set(expected), 'not all schematic pins have matching PCB pads')
        return 'PASS'

    def outline():
        x0, y0, x1, y1 = compact.outline_bounds(board)
        require(abs(x1 - x0 - WIDTH) < .01 and abs(y1 - y0 - HEIGHT) < .01, f'outline {x1-x0} x {y1-y0}')
        require(contract['size_mm'] == [WIDTH, HEIGHT], 'contract size differs')
        return [x0, y0, x1, y1]

    def pd_mating():
        board_p = json.loads((ROOT / 'boards/board-p/mechanical.json').read_text())
        stack = contract['pd_stack']
        require(stack['point_transform'] == 'P(x,y) -> B(y-0.5,x+12)' and stack['nominal_board_p_top_z_mm'] == 11.1,
                'unreviewed stack transform or spacing')
        header = fps['J5']
        pads = {pad.GetNumber(): pad for pad in header.Pads()}
        require(set(pads) == {str(i) for i in range(1, 7)}, 'J5 must have exactly six contacts')
        require(header.GetLayer() == p.F_Cu and abs(header.GetOrientationDegrees() % 360 - 270) < .001,
                'J5 must be front-side at rotation 270')
        rows = []
        for pin in board_p['interface']['pads']:
            pad = pads[str(pin['pin'])]
            target = pd_to_board_b(pin['center'])
            require(near(xy(pad), target), f'J5.{pin["pin"]}: mating pad position')
            locked = next(v for v in stack['pads'] if v['pin'] == pin['pin'])
            require(near(target, locked['center_mm']), 'contract pad differs from source Board P')
            want = PD_NETS[pin['net']]
            require(unconnected(pad) if want is None else pad.GetNetname() == pcb_net_name(want),
                    f'J5.{pin["pin"]}: net {pad.GetNetname()} for Board P {pin["net"]}')
            rows.append({'pin': pin['pin'], 'board_p_net': pin['net'], 'center_mm': xy(pad),
                         'board_b20_net': pad.GetNetname() or 'unconnected'})
        for i, hole in enumerate(board_p['mounting_holes'], 1):
            pad = list(fps['H' + str(i)].Pads())
            require(len(pad) == 1 and near(xy(pad[0]), pd_to_board_b(hole['center']))
                    and pad[0].GetAttribute() == p.PAD_ATTRIB_NPTH
                    and near([p.ToMM(pad[0].GetDrillSize().x)], [hole['drill']]), f'H{i}: PD mount mismatch')
        return rows

    def corners():
        support = contract['corner_supports']
        expected = {'H4': [WIDTH - 4, 4], 'H5': [4, HEIGHT - 4], 'H6': [WIDTH - 4, HEIGHT - 4], 'H7': [4, 4]}
        require(support['placements'] == expected and support['hole_diameter_mm'] == 3.0, 'corner contract')
        for ref, center in expected.items():
            fp = fps[ref]
            pads = list(fp.Pads())
            require(fp.GetFPIDAsString() == support['footprint'] and len(pads) == 1, ref + ': support footprint')
            q = pads[0]
            require(near(xy(q), center, .01) and q.GetAttribute() == p.PAD_ATTRIB_NPTH and q.GetNetCode() == 0
                    and abs(p.ToMM(q.GetDrillSize().x) - 3.0) < .001, ref + ': netless 3 mm NPTH at the corner')
        return 'PASS'

    def terminals():
        terminal = contract['terminal_blocks']
        positions = {item['reference']: item for item in terminal['placements']}
        rows = []
        for ref, nets in TERMINAL_NETS.items():
            fp = fps[ref]
            require(fp.GetLayer() == p.F_Cu and abs(fp.GetOrientationDegrees() % 360 - 90) < .001, ref + ': rotation')
            require(fp.GetFPIDAsString() == terminal['footprint'] and fp.GetFieldText('LCSC') == terminal['lcsc'],
                    ref + ': footprint or C8465 identity')
            fx, fy = xy(fp)
            require(near([fx, fy], positions[ref]['center_mm'], .01), ref + ': origin differs from the contract')
            for number, q in {q.GetNumber(): q for q in fp.Pads()}.items():
                lx, ly = terminal['pad_centers_local_mm'][number]
                require(near(xy(q), [fx + ly, fy - lx], .01) and q.GetNetname() == nets[number]
                        and q.GetAttribute() == p.PAD_ATTRIB_PTH, f'{ref}.{number}: position, net or plating')
            rows.append({'reference': ref, 'origin_mm': [fx, fy], 'pins': nets})
        return rows

    def sockets():
        for ref in ('J10', 'J11'):
            fp = fps[ref]
            require(fp.GetLayer() == p.F_Cu and abs(fp.GetOrientationDegrees()) < .001, ref + ': mating direction')
            require(abs(xy(fp)[1] + 12.23 - HEIGHT) < .001, ref + ': mating face not at the board edge')
            pads = {int(q.GetNumber()): q for q in fp.Pads()}
            require(set(pads) == set(SOCKET_NETS), ref + ': contacts')
            for number, net in SOCKET_NETS.items():
                require(pads[number].GetNetname() == net, f'{ref}.{number}: wrong rail {pads[number].GetNetname()}')
            require(pads[1].GetShape() == p.PAD_SHAPE_RECT, ref + ': no rectangular pin-1 marker')
        return 'PASS'

    def rail_labels():
        contract = json.loads(CONTRACT.read_text())['terminal_blocks']['rail_labels']
        require(contract == {'back_labels': compact.BACK_RAIL_LABELS, 'back_rotation_deg': 0, 'back_mirrored': True,
                             'front_x_mm': .8, 'front_size_mm': .8, 'front_rotation_deg': 90, 'front_mirrored': False},
                'unreviewed front/back rail-label contract')
        rows = []
        for text, (ref, pin) in compact.RAIL_LABEL_PINS.items():
            pad = next(q for q in fps[ref].Pads() if q.GetNumber() == pin)
            require(pad.GetNetname() == TERMINAL_NETS[ref][pin], f'{text}: {ref}.{pin} carries {pad.GetNetname()}')
            for side, layer in (('front', p.F_SilkS), ('back', p.B_SilkS)):
                found = [v for v in board.GetDrawings() if isinstance(v, p.PCB_TEXT) and v.GetLayer() == layer
                         and v.GetText() == text]
                require(len(found) == 1, f'{side} {text}: expected exactly one board text label')
                label = found[0]
                reviewed = contract['back_labels'][text] if side == 'back' else None
                target = reviewed['center_mm'] if reviewed else [contract['front_x_mm'], xy(pad)[1]]
                size = reviewed['size_mm'] if reviewed else contract['front_size_mm']
                require(near(xy(label), target, .01), f'{side} {text}: position differs from the contract')
                require(label.IsMirrored() == contract[side + '_mirrored']
                        and abs(label.GetTextAngle().AsDegrees() % 360 - contract[side + '_rotation_deg']) < .001
                        and all(abs(p.ToMM(v) - size) < .001 for v in (label.GetTextSize().x, label.GetTextSize().y)),
                        f'{side} {text}: wrong mirror, orientation or size')
                if reviewed:
                    require(label.IsBold() == reviewed['bold']
                            and abs(p.ToMM(label.GetTextThickness()) - reviewed['thickness_mm']) < .001,
                            f'{side} {text}: bold weight or stroke differs')
                rows.append({'side': side, 'text': text, 'pin': f'{ref}.{pin}', 'net': pad.GetNetname(),
                             'center_mm': xy(label), 'mirrored': label.IsMirrored()})
        return rows

    def pogo_row():
        row = json.loads(CONTRACT.read_text())['edge_pogo']
        refs = row['references']
        require(refs == ['P1', 'TP3', 'TP4', 'TP5'] and row['contact_count'] == len(POGO_NETS), 'pogo contract changed')
        require(near(xy(fps['P1']), row['origin_mm'], .01), 'P1: origin differs from the contract')
        pads = []
        for ref in refs:
            fp = fps[ref]
            require(fp.GetLayer() == p.F_Cu and abs(fp.GetOrientationDegrees()) < .001, ref + ': side or rotation')
            require(not fp.GetFieldText('LCSC') and fp.GetAttributes() & p.FP_EXCLUDE_FROM_BOM
                    and fp.GetAttributes() & p.FP_EXCLUDE_FROM_POS_FILES, ref + ': bare copper must stay out of BOM/CPL')
            pads += sorted(fp.Pads(), key=lambda q: xy(q)[0])
        require(len(pads) == len(POGO_NETS), 'pogo contact count')
        x0 = xy(pads[0])[0]
        rows = []
        for i, (q, net) in enumerate(zip(pads, POGO_NETS)):
            cx, cy = xy(q)
            require(abs(cx - x0 - i * row['pitch_mm']) < .01 and abs(cy - row['center_y_mm']) < .01,
                    f'contact {i + 1}: off the {row["pitch_mm"]} mm row')
            require(abs(cy - p.ToMM(q.GetSize().y) / 2 - row['copper_to_top_edge_mm']) < .01, f'contact {i + 1}: edge gap')
            layers = q.GetLayerSet()
            require(layers.Contains(p.F_Cu) and layers.Contains(p.F_Mask) and not layers.Contains(p.F_Paste)
                    and layers.CuStack().size() == 1, f'contact {i + 1}: must be F.Cu/F.Mask only')
            got = q.GetNetname()
            require(got == net if net else (not got or got.startswith('unconnected-')), f'contact {i + 1}: carries {got}')
            rows.append({'pad': f'{q.GetParentFootprint().GetReference()}.{q.GetNumber()}', 'center_mm': [cx, cy],
                         'net': net})
        require(rows[2]['pad'] == row['shared_ground'], 'shared probe ground moved')
        labels = sorted((t for t in fps['P1'].GraphicalItems() if isinstance(t, p.PCB_TEXT) and t.GetLayer() == p.F_SilkS),
                        key=lambda t: xy(t)[0])
        require([t.GetText() for t in labels] == ['NC', 'PDOK', 'GND', 'NC'], 'P1 silk labels differ from the B20 pin nets')
        return rows

    result = {'board': 'board-b20-draft', 'size_mm': [WIDTH, HEIGHT], 'component_count': len(spec.COMPONENTS),
              'schematic_pad_identity': check('identity', identity),
              'outline_mm': check('outline', outline),
              'pd_mating': check('pd_mating', pd_mating),
              'corner_supports': check('corner_supports', corners),
              'terminal_blocks': check('terminals', terminals),
              'eurorack_pin_contract': check('sockets', sockets),
              'pogo_row': check('pogo_row', pogo_row),
              'rail_labels': check('rail_labels', rail_labels),
              'physical_stack_and_cable_fit': 'NOT MEASURED',
              'errors': errors}
    result['status'] = 'FAIL' if errors else 'PASS'
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
