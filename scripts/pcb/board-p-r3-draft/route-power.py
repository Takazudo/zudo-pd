"""Phase 11: first routing pass on the Board P r3 placement draft (power path and ground only).

usage: python3 route-power.py <board.kicad_pcb> <report.json>   (inside the pinned KiCad image)
The power nets are copper pours on F.Cu shaped along the floorplan corridors (floorplan.json); GND is
a B.Cu pour plus an F.Cu fill, stitched with vias wherever both fills exist. Signal nets stay unrouted.
Widths: IPC-2221 external-layer chart, 1 oz (35 um, the board stackup), 5 A at a 20 C rise -> 1.81 mm
minimum (PA: rise and chart are design assumptions, not a measured thermal result).
"""
import json, math, sys
import pcbnew

pcb_path, rep_path = sys.argv[1:3]
board = pcbnew.LoadBoard(pcb_path)
mm = pcbnew.FromMM
I_A, DT_C, OZ_MIL = 5.0, 20.0, 1.378
area_mil2 = (I_A / (0.048 * DT_C ** 0.44)) ** (1 / 0.725)
W_MIN_MM = area_mil2 / OZ_MIL * 0.0254

# (net, layer, priority, outlines); an outline is a polygon given as (x, y) vertices in mm (KiCad board
# coordinates), shaped to floorplan.json v2: VBUS_IN joins J1.2/J1.5 to D5 and the Q3 sources; EF_IN joins the
# Q3 drain to U2 IN; VBUS_P leaves U2 OUT, rises on the left of U1 to C3.1 and drops to the Q1 sources;
# VBUS_OUT joins the Q1 drain to JOUT1.1/.2.
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


POURS = [
    ('VBUS_IN', 'F.Cu', 40, [[(7.2, 7.85), (11.45, 7.85), (11.45, 6.3), (12.5, 6.3), (12.5, 7.85), (14.5, 7.85),
                              (14.5, 6.3), (15.6, 6.3), (15.6, 10.55), (7.2, 10.55)]]),
    ('EF_IN', 'F.Cu', 40, [rect(5.3, 10.75, 9.3, 15.95)]),
    ('VBUS_P', 'F.Cu', 40, [[(9.5, 12.3), (16.8, 12.3), (16.8, 15.6), (11.5, 15.6), (11.5, 23.5), (9.3, 23.5),
                             (9.3, 26.45), (5.6, 26.45), (5.6, 22.0), (7.3, 22.0), (7.3, 19.9), (9.5, 19.9)]]),
    ('VBUS_OUT', 'F.Cu', 40, [rect(4.6, 26.75, 9.3, 38.9)]),
    ('GND', 'F.Cu', 0, [rect(0.3, 0.3, 26.7, 39.7)]),
    ('GND', 'B.Cu', 0, [rect(0.3, 0.3, 26.7, 39.7)]),
]

def add_zone(net, layer, prio, r):
    z = pcbnew.ZONE(board)
    z.SetLayer(board.GetLayerID(layer)); z.SetNet(board.FindNet(net)); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in r:
        ol.Append(mm(x), mm(y))
    board.Add(z)
    return z


zones = [add_zone(n, l, p, r) for n, l, p, rs in POURS for r in rs]
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

# stitching vias: grid points inside both GND fills, at least 0.8 mm from any pad or keep-out
gnd = board.FindNet('GND')
fz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.F_Cu]
bz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.B_Cu]
keep = [z for z in board.Zones() if z.GetIsRuleArea()]
pad_boxes = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox(); bb.Inflate(mm(0.8)); pad_boxes.append(bb)
VIA_D, VIA_DRILL, PITCH = 0.6, 0.3, 2.0
vias = []
y = 1.0
while y < 39.0:
    x = 1.0
    while x < 26.0:
        pt = pcbnew.VECTOR2I(mm(x), mm(y))
        ok = all(any(z.HitTestFilledArea(z.GetLayer(), pt, mm(VIA_D / 2 + 0.2)) for z in zs) for zs in (fz, bz))
        ok = ok and not any(k.Outline().Contains(pt) for k in keep)
        ok = ok and not any(bb.Contains(pt) for bb in pad_boxes)
        if ok:
            v = pcbnew.PCB_VIA(board); v.SetPosition(pt); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(gnd)
            board.Add(v); vias.append((round(x, 2), round(y, 2)))
        x += PITCH
    y += PITCH
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(pcb_path, board)

# filled-copper cross-sections across each corridor, sampled every 0.05 mm: the aggregate filled length and the
# largest single filled run along the cut (neither proves one continuous corridor nor a rated current)
CUTS = [('VBUS_IN', 'x', 10.0, 7.85, 10.55), ('VBUS_IN', 'x', 13.5, 7.85, 10.55), ('EF_IN', 'y', 14.05, 5.3, 9.3),
        ('VBUS_P', 'y', 17.5, 9.5, 11.5), ('VBUS_P', 'x', 13.5, 12.3, 15.6), ('VBUS_P', 'y', 24.5, 5.6, 9.3),
        ('VBUS_OUT', 'y', 33.0, 4.6, 9.3)]
cuts = []
for net, axis, at, a, b in CUTS:
    nz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net and z.GetLayer() == pcbnew.F_Cu]
    hits, run, best, t = 0, 0, 0, a
    while t <= b + 1e-9:
        pt = pcbnew.VECTOR2I(mm(at), mm(t)) if axis == 'x' else pcbnew.VECTOR2I(mm(t), mm(at))
        h = any(z.HitTestFilledArea(pcbnew.F_Cu, pt, 0) for z in nz)
        hits += h; run = run + 1 if h else 0; best = max(best, run); t += 0.05
    cuts.append({'net': net, 'cut': f'{axis}={at}', 'span_mm': [a, b], 'aggregate_filled_mm': round(hits * 0.05, 2),
                 'largest_run_mm': round(best * 0.05, 2), 'meets_min_width': best * 0.05 >= W_MIN_MM})
report = {'width_rule': {'current_a': I_A, 'temperature_rise_c': DT_C, 'copper': '35 um (1 oz) outer, board stackup',
                         'method': 'IPC-2221 external-layer chart (PA)', 'min_width_mm': round(W_MIN_MM, 2)},
          'pours': [{'net': n, 'layer': l, 'outlines_mm': rs} for n, l, p, rs in POURS],
          'cross_sections': cuts,
          'stitching_vias': {'count': len(vias), 'diameter_mm': VIA_D, 'drill_mm': VIA_DRILL, 'pitch_mm': PITCH}}
open(rep_path, 'w').write(json.dumps(report, indent=1) + '\n')
print(json.dumps({'min_width_mm': round(W_MIN_MM, 2), 'vias': len(vias), 'cuts': cuts}))
