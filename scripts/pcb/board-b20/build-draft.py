"""Build the first B20 draft PCB placement from board_b20_spec (pcbnew, pinned KiCad 10.0.6 image, --cpus 1).

usage: python3 build-draft.py <out board-b20-draft.kicad_pcb>

This is an unrouted, unvalidated placement draft. It is generated, never hand-edited:
  - The outline, mounting holes, fiducials and the fixed hardware J5, J6, J7, J10 and J11 come from
    scripts/pcb/board_b_layout.py, so B20 keeps the Board B mechanical positions.
  - A footprint keep-out rule area covers x 7.74-17.25, y 24.54-35.77 mm on both sides. Board P r3's C3
    (8.3 x 8.3 mm base, 10.2 mm tall) projects there across the 11.1 mm plane gap
    (boards/board-p/r3-draft/README.md, stack conflict).
  - Every other part is packed greedily, top side only, around the anchor of its functional block.
    A part joins the block of the nearest seed part through signal nets (nets with more than
    MAX_SIGNAL_PINS pins, and the supply nets in SUPPLY_NETS, do not link parts); a part reached only
    through supply nets joins the block of a part on its smallest shared supply net other than GND.
  - Reference designators sit on F.Fab, so the placement draft carries no silkscreen text yet.
Courtyards keep at least CLEARANCE mm apart and BOARD_MARGIN mm inside the board edge.
"""
import math
import sys
from pathlib import Path

import wx
_APP = wx.App(False)
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
sys.path.insert(0, str(ROOT / 'scripts/pcb'))
import board_b20_spec as spec  # noqa: E402
from schgen_core import new_uuid  # noqa: E402
from pcb_common import pcb_net_name  # noqa: E402
from sexp import atom, find_all, load  # noqa: E402
from board_b_layout import WIDTH, HEIGHT, PLACEMENTS, MOUNTING_HOLES, FIDUCIALS, SUPPORT_REFS, edge_primitives  # noqa: E402

LIB = str(ROOT / 'footprints/kicad/zudo-power.pretty')
FIXED = ('J5', 'J6', 'J7', 'J10', 'J11')
C3_KEEPOUT = (7.74, 24.54, 17.25, 35.77)
CLEARANCE = 0.8          # phase 21: routing channels between greedily packed parts
TEMPLATE_CLEARANCE = 0.3 # stage templates are packed tight on purpose (hot loops)
BOARD_MARGIN = 0.5
CELL = 0.1
MAX_SIGNAL_PINS = 6
MAX_SUPPLY_PINS = 24
SUPPLY_NETS = {'GND', 'VIN', 'P5_SUP', 'REF25', 'M12_PRE', 'M12_RAW', 'FAULT_N', 'EN_E',
               'P12_OUT', 'P5_OUT', 'M12_OUT'}
# Block anchors (mm). Power stages run along the top, rail switches and shunts toward the
# J6/J7 terminals and the J10/J11 headers, supervision and servo logic on the right.
ANCHORS = {
    'U14': (31, 7), 'U1': (50, 11), 'U2': (78, 11), 'U3': (30, 48),
    'Q1': (60, 30), 'Q3': (88, 30), 'Q5': (60, 54), 'U9': (52, 58),
    'U11': (44.5, 30), 'U12': (72.5, 30), 'U10': (100, 24), 'U4': (100, 34),
    'U13': (74, 46), 'U15': (84, 42), 'U16': (96, 44), 'U5': (104, 56),
    'U6': (72, 60), 'U7': (84, 58), 'U8': (96, 62),
}
# Phase 21: the switching stages and their shunt/INA pairs are placed as fixed templates before the greedy fill.
# Offsets (dx, dy, rotation) are relative to the stage IC at its anchor (rotation 0). The input capacitor, catch
# diode and IC ground pad sit side by side so the hot loop (CIN -> VIN pin -> SW -> diode -> CIN return) closes
# over about 10 x 6 mm; the inductor and output capacitors follow on the SW side.
BUCK = (('ic', 0, 0, 0), ('boot', 0, -4.6, 0), ('cin', -3.4, -8.2, 0), ('diode', 3.6, -8.2, 180),
        ('ind', 11.6, -5.2, 270), ('cout1', 11.6, 2.4, 0), ('cout2', 11.6, 6.6, 0))
FILTER = (('lf', 3, 12.5, 0), ('cpoly', 13.2, 13.0, 0), ('shunt', 8, 20.2, 0), ('ina', -1, 20.2, 0))
STAGES = {
    'U1': dict(ic='U1', boot='C4', cin='C3', diode='D1', ind='L1', cout1='CAO1', cout2='CAO2',
               lf='L2', cpoly='CAF1', shunt='RSH1', ina='U11'),
    'U2': dict(ic='U2', boot='C8', cin='C7', diode='D2', ind='L3', cout1='CBO1', cout2='CBO2',
               lf='L4', cpoly='CBF1', shunt='RSH2', ina='U12'),
    'U3': dict(ic='U3', boot='C11', cin='CCIN1', cin2='CCIN2', diode='D3', ind='L5', cout1='CCO1', cout2='CCO2',
               cout3='CCO3', cout4='CCO4', shunt='RSH3', ina='U9'),
}
EXTRA = {'U3': (('cin2', -3.4, -12.5, 0), ('cout3', 11.6, 11.0, 0), ('cout4', 11.6, 15.4, 0),
                ('shunt', 22, 4, 0), ('ina', 22, 10.5, 180))}
DEFAULT_ANCHOR = (100, 62)


def pin_names():
    """(symbol, pin number) -> pin name, so no-connect nets carry KiCad's schematic names."""
    names = {}
    for sym in find_all(load(ROOT / 'symbols/zudo-pd.kicad_sym'), 'symbol'):
        top = atom(sym[1])
        for unit in [sym] + find_all(sym, 'symbol'):
            for pin in find_all(unit, 'pin'):
                number = [atom(n[1]) for n in find_all(pin, 'number')]
                name = [atom(n[1]) for n in find_all(pin, 'name')]
                if number and name:
                    names[(top, number[0])] = name[0]
    return names


def mm(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def courtyard_box(fp):
    boxes = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() in (p.F_CrtYd, p.B_CrtYd)]
    if not boxes:
        boxes = [fp.GetBoundingBox(False, False)]
    x0 = min(p.ToMM(b.GetLeft()) for b in boxes)
    y0 = min(p.ToMM(b.GetTop()) for b in boxes)
    x1 = max(p.ToMM(b.GetRight()) for b in boxes)
    y1 = max(p.ToMM(b.GetBottom()) for b in boxes)
    return x0, y0, x1, y1


class Grid:
    def __init__(self):
        self.nx, self.ny = int(WIDTH / CELL) + 1, int(HEIGHT / CELL) + 1
        self.used = bytearray(self.nx * self.ny)

    def _range(self, box, pad):
        x0, y0, x1, y1 = box
        return (max(0, int((x0 - pad) / CELL)), max(0, int((y0 - pad) / CELL)),
                min(self.nx - 1, int((x1 + pad) / CELL) + 1), min(self.ny - 1, int((y1 + pad) / CELL) + 1))

    def mark(self, box, pad=0.0):
        i0, j0, i1, j1 = self._range(box, pad)
        for j in range(j0, j1 + 1):
            row = j * self.nx
            self.used[row + i0:row + i1 + 1] = b'\x01' * (i1 - i0 + 1)

    def free(self, box, clearance=None):
        x0, y0, x1, y1 = box
        if x0 < BOARD_MARGIN or y0 < BOARD_MARGIN or x1 > WIDTH - BOARD_MARGIN or y1 > HEIGHT - BOARD_MARGIN:
            return False
        i0, j0, i1, j1 = self._range(box, CLEARANCE if clearance is None else clearance)
        for j in range(j0, j1 + 1):
            row = j * self.nx
            if any(self.used[row + i0:row + i1 + 1]):
                return False
        return True


def blocks():
    adjacency = {ref: set() for ref in spec.COMPONENTS}
    for net, pins in spec.NETS.items():
        if net in SUPPLY_NETS or len(pins) > MAX_SIGNAL_PINS:
            continue
        refs = {pin.split('.')[0] for pin in pins}
        for ref in refs:
            adjacency[ref] |= refs - {ref}
    owner, depth, frontier = {}, {}, []
    for seed in ANCHORS:
        owner[seed], depth[seed] = seed, 0
        frontier.append(seed)
    while frontier:
        nxt = []
        for ref in frontier:
            for other in sorted(adjacency[ref]):
                if other not in owner and other not in FIXED:
                    owner[other], depth[other] = owner[ref], depth[ref] + 1
                    nxt.append(other)
        frontier = nxt
    # Parts tied to the blocks only through supply nets (input and output capacitors, decoupling)
    # join the block of the first already-assigned part on their smallest shared supply net.
    for ref in spec.COMPONENTS:
        if ref in owner or ref in FIXED:
            continue
        shared = sorted((len(pins), net) for net, pins in spec.NETS.items()
                        if net != 'GND' and len(pins) <= MAX_SUPPLY_PINS and any(pin.split('.')[0] == ref for pin in pins))
        for _, net in shared:
            mates = sorted(pin.split('.')[0] for pin in spec.NETS[net] if pin.split('.')[0] in owner)
            if mates:
                owner[ref], depth[ref] = owner[mates[0]], depth[mates[0]] + 1
                break
    return owner, depth


def clip_header_silk(footprints, limit=11.73):
    """Clip J10/J11 F.SilkS segments at local y=11.73 mm, as finish-board-b.py does for the as-built Board B."""
    for ref in ('J10', 'J11'):
        fp = footprints[ref]
        assert fp.GetOrientationDegrees() == 0, ref
        edge = fp.GetPosition().y + p.FromMM(limit)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() != p.F_SilkS or item.GetClass() != 'PCB_SHAPE' or item.GetShape() != p.SHAPE_T_SEGMENT:
                continue
            a, b = item.GetStart(), item.GetEnd()
            if a.y >= edge and b.y >= edge:
                fp.Remove(item)
                continue
            if a.y > edge:
                a = p.VECTOR2I(int(b.x + (a.x - b.x) * (edge - b.y) / (a.y - b.y)), edge)
            if b.y > edge:
                b = p.VECTOR2I(int(a.x + (b.x - a.x) * (edge - a.y) / (b.y - a.y)), edge)
            item.SetStart(a)
            item.SetEnd(b)


def main():
    out = Path(sys.argv[1])
    board = p.BOARD()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(p.FromMM(1.6))
    ds.SetAuxOrigin(mm(0, HEIGHT))
    nets = {}
    for code, name in enumerate(spec.NETS, 1):
        net = p.NETINFO_ITEM(board, pcb_net_name(name), code)
        board.Add(net)
        nets[name] = net
    pin_nets = {pin: nets[name] for name, pins in spec.NETS.items() for pin in pins}
    nc_code = len(spec.NETS) + 1
    grid = Grid()
    footprints = {}
    names = pin_names()
    for ref, comp in spec.COMPONENTS.items():
        symbol, value, lcsc, footprint, dnp, _ = comp
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
        if not lcsc:
            fp.SetAttributes(fp.GetAttributes() | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.Value().SetVisible(False)
        fp.Reference().SetLayer(p.F_Fab)
        fp.Reference().SetTextSize(mm(0.5, 0.5))
        fp.Reference().SetTextThickness(p.FromMM(0.08))
        for pad in fp.Pads():
            key = f'{ref}.{pad.GetNumber()}'
            if key in pin_nets:
                pad.SetNet(pin_nets[key])
            elif key in spec.NO_CONNECT:
                pin = names.get((symbol, pad.GetNumber()), '~')
                label = f'{ref}-Pad{pad.GetNumber()}' if pin in ('~', '', pad.GetNumber()) else f'{ref}-{pin}-Pad{pad.GetNumber()}'
                net = p.NETINFO_ITEM(board, f'unconnected-({label})', nc_code)
                nc_code += 1
                board.Add(net)
                pad.SetNet(net)
            elif pad.GetAttribute() != p.PAD_ATTRIB_NPTH:
                raise SystemExit(f'unassigned pad {key}')
        footprints[ref] = fp

    def put(fp, x, y, rot):
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(mm(x, y))
        fp.Reference().SetPosition(mm(x, y))
        fp.Reference().SetTextAngle(p.EDA_ANGLE(0, p.DEGREES_T))

    for ref in FIXED:
        x, y, rot = PLACEMENTS[ref][:3]
        put(footprints[ref], x, y, rot)
        grid.mark(courtyard_box(footprints[ref]))
    clip_header_silk(footprints)
    for i, (x, y) in enumerate(MOUNTING_HOLES, 1):
        name = 'MountingHole_HC11_3mm' if f'H{i}' in SUPPORT_REFS else 'MountingHole_M3'
        fp = p.FootprintLoad(LIB, name)
        fp.SetFPID(p.LIB_ID('zudo-pd', name))
        fp.SetReference(f'H{i}')
        fp.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x, y))
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        board.Add(fp)
        grid.mark(courtyard_box(fp))
    for i, (x, y) in enumerate(FIDUCIALS, 1):
        fp = p.FootprintLoad(LIB, 'Fiducial_1mm_Mask2mm')
        fp.SetFPID(p.LIB_ID('zudo-pd', 'Fiducial_1mm_Mask2mm'))
        fp.SetReference(f'FID{i}')
        fp.SetAttributes(p.FP_SMD | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x, y))
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        board.Add(fp)
        grid.mark(courtyard_box(fp))
    grid.mark(C3_KEEPOUT)

    templated = {}
    for ic, roles in STAGES.items():
        ax, ay = ANCHORS[ic]
        rows = dict((r[0], r[1:]) for r in (BUCK + (() if ic == 'U3' else FILTER)))
        rows.update((r[0], r[1:]) for r in EXTRA.get(ic, ()))
        for role, (dx, dy, rot) in rows.items():
            ref = roles[role]
            put(footprints[ref], ax + dx, ay + dy, rot)
            box = courtyard_box(footprints[ref])
            if not grid.free(box, TEMPLATE_CLEARANCE):
                raise SystemExit(f'stage template {ic}:{role} ({ref}) collides at {ax + dx}, {ay + dy}')
            grid.mark(box)
            templated[ref] = (ax + dx, ay + dy)

    owner, depth = blocks()

    def area(ref):
        x0, y0, x1, y1 = courtyard_box(footprints[ref])
        return (x1 - x0) * (y1 - y0)

    order = sorted((r for r in spec.COMPONENTS if r not in FIXED and r not in templated),
                   key=lambda r: (r not in ANCHORS, list(ANCHORS).index(owner.get(r)) if owner.get(r) in ANCHORS else 99,
                                  depth.get(r, 99), -area(r), r))
    placed_at = dict(templated)
    unplaced = []
    for ref in order:
        fp = footprints[ref]
        ax, ay = ANCHORS[ref] if ref in ANCHORS else placed_at.get(owner.get(ref), DEFAULT_ANCHOR)
        done = False
        for radius in range(0, 400):
            r = radius * 0.5
            ring = [(0.0, 0.0)] if radius == 0 else []
            if radius:
                steps = max(8, int(2 * math.pi * r / 0.5))
                for k in range(steps):
                    t = 2 * math.pi * k / steps
                    ring.append((r * math.cos(t), r * math.sin(t)))
            for dx, dy in ring:
                for rot in (0, 90):
                    x, y = round((ax + dx) / 0.05) * 0.05, round((ay + dy) / 0.05) * 0.05
                    put(fp, x, y, rot)
                    box = courtyard_box(fp)
                    if grid.free(box):
                        grid.mark(box)
                        placed_at[ref] = (x, y)
                        done = True
                        break
                if done:
                    break
            if done:
                break
        if not done:
            unplaced.append(ref)
    if unplaced:
        raise SystemExit(f'no room for {unplaced}')

    zone = p.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowFootprints(True)
    zone.SetDoNotAllowTracks(False)
    zone.SetDoNotAllowVias(False)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowZoneFills(False)
    ls = p.LSET()
    ls.AddLayer(p.F_Cu)
    ls.AddLayer(p.B_Cu)
    zone.SetLayerSet(ls)
    zone.SetZoneName('BOARD_P_R3_C3_KEEPOUT')
    x0, y0, x1, y1 = C3_KEEPOUT
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        outline.Append(p.FromMM(x), p.FromMM(y))
    board.Add(zone)

    for edge in edge_primitives():
        item = p.PCB_SHAPE(board)
        item.SetShape(p.SHAPE_T_SEGMENT)
        item.SetStart(mm(*edge['start']))
        item.SetEnd(mm(*edge['end']))
        item.SetLayer(p.Edge_Cuts)
        item.SetWidth(p.FromMM(.05))
        board.Add(item)
    note = p.PCB_TEXT(board)
    note.SetText('B20 DRAFT - UNROUTED PLACEMENT - NOT FOR FABRICATION')
    note.SetPosition(mm(WIDTH / 2, HEIGHT - 1.5))
    note.SetTextSize(mm(0.8, 0.8))
    note.SetTextThickness(p.FromMM(0.12))
    note.SetLayer(p.F_Fab)
    board.Add(note)

    p.SaveBoard(str(out), board)
    stackup = '\n'.join([
        '    (stackup',
        '      (layer "F.SilkS" (type "Top Silk Screen"))',
        '      (layer "F.Paste" (type "Top Solder Paste"))',
        '      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))',
        '      (layer "F.Cu" (type "copper") (thickness 0.07))',
        '      (layer "dielectric 1" (type "core") (thickness 1.44) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))',
        '      (layer "B.Cu" (type "copper") (thickness 0.07))',
        '      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))',
        '      (layer "B.Paste" (type "Bottom Solder Paste"))',
        '      (layer "B.SilkS" (type "Bottom Silk Screen"))',
        '      (copper_finish "None") (dielectric_constraints no)',
        '    )',
    ])
    content = out.read_text()
    assert '(stackup' not in content
    out.write_text(content.replace('(setup\n', '(setup\n' + stackup + '\n', 1))
    blocks_used = {}
    for ref in placed_at:
        blocks_used.setdefault(owner.get(ref, 'default'), []).append(ref)
    print(f'placed {len(placed_at)} + {len(FIXED)} fixed parts on {WIDTH} x {HEIGHT} mm; '
          + ', '.join(f'{k}:{len(v)}' for k, v in sorted(blocks_used.items())))


if __name__ == '__main__':
    main()
