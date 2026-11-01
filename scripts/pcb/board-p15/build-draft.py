"""Build the 15 V Board P draft PCB from the as-built routed module (pcbnew, pinned KiCad 10.0.6 image, --cpus 1).

usage: python3 build-draft.py <as-built board-p.kicad_pcb> <out board-p15-draft.kicad_pcb>

The as-built file is only read. The draft keeps every as-built placement and track except the edits of
dec-p15-reset-subset (scripts/schgen/board_p15_spec.py):
  - R15/R16 (I2C pull-ups to VREG_2V7) and their branch copper are removed;
  - J2.4 loses the RESET net and its silk label reads NC;
  - R21 becomes an R0603 0 Ohm strap beside U1.6 on F.Cu, with its GND end on a via into the B.Cu GND pour;
  - VBUS_VS_DISCH leaves the two vias beside the U1 RESET corner and runs on B.Cu only.
Every removed segment is named by its exact as-built end points, so an unexpected as-built change fails loudly.
Zones are refilled before saving.
"""
import sys
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu


def pt(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def close(p, x, y):
    return abs(pcbnew.ToMM(p.x) - x) < 0.002 and abs(pcbnew.ToMM(p.y) - y) < 0.002


TRACKS = list(b.GetTracks())   # one snapshot: the SWIG track list does not survive a Remove in this build
DOOMED = []


def remove_track(net, layer, a, c):
    hits = [t for t in TRACKS if t not in DOOMED and t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net and t.GetLayer() == layer
            and ((close(t.GetStart(), *a) and close(t.GetEnd(), *c)) or (close(t.GetStart(), *c) and close(t.GetEnd(), *a)))]
    if len(hits) != 1:
        raise SystemExit(f'expected one {net} track {a}-{c} on {b.GetLayerName(layer)}, found {len(hits)}')
    DOOMED.append(hits[0])


def remove_via(net, x, y):
    hits = [t for t in TRACKS if t not in DOOMED and t.GetClass() == 'PCB_VIA' and t.GetNetname() == net and close(t.GetPosition(), x, y)]
    if len(hits) != 1:
        raise SystemExit(f'expected one {net} via at ({x}, {y}), found {len(hits)}')
    DOOMED.append(hits[0])


def add_track(net, layer, pts, width=0.25):
    n = b.FindNet(net)
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pt(*a)); t.SetEnd(pt(*c)); t.SetWidth(MM(width)); t.SetLayer(layer); t.SetNet(n)
        b.Add(t)


def add_via(net, x, y, drill=0.3, size=0.5):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pt(x, y)); v.SetDrill(MM(drill)); v.SetWidth(MM(size)); v.SetNet(b.FindNet(net))
    v.SetLayerPair(F, B)
    b.Add(v)


fp = {f.GetReference(): f for f in b.GetFootprints()}

# 1. R15/R16 pull-ups and their branch copper (SCL, SDA, VREG_2V7)
for a, c in [((8.117, 21.718), (7.955, 21.556)), ((7.955, 21.556), (7.955, 19.98)), ((7.955, 19.98), (8.517, 19.418)),
             ((8.517, 19.418), (8.73, 19.418)), ((8.73, 19.418), (10.43, 21.118)), ((10.43, 21.118), (13.848, 21.118)),
             ((13.848, 21.118), (19.13, 26.4)), ((19.13, 26.4), (19.13, 26.418))]:
    remove_track('SCL', B, a, c)
remove_via('SCL', 19.13, 26.418)
for a, c in [((19.13, 26.418), (18.3, 26.418)), ((18.3, 26.418), (18.128, 26.59))]:
    remove_track('SCL', F, a, c)
for a, c in [((7.13, 25.918), (9.03, 27.818)), ((9.03, 27.818), (18.543, 27.818)), ((18.543, 27.818), (19.705, 26.656)),
             ((19.705, 26.656), (19.705, 25.193)), ((19.705, 25.193), (19.33, 24.818))]:
    remove_track('SDA', B, a, c)
remove_via('SDA', 19.33, 24.818)
for a, c in [((19.33, 24.818), (18.134, 24.818)), ((18.134, 24.818), (18.128, 24.812))]:
    remove_track('SDA', F, a, c)
add_track('SDA', B, [(7.13, 25.918), (8.33, 27.118), (8.63, 27.118)])
for a, c in [((16.678, 23.034), (16.678, 26.54)), ((16.678, 26.54), (16.628, 26.59))]:
    remove_track('VREG_2V7', F, a, c)

# 2. RESET: drop every as-built RESET track, J2.4 leaves the net, R21 old GND stub and via go
for a, c in [((7.24, 20.918), (10.108, 20.918)), ((5.632, 26.082), (5.632, 22.526)), ((2.018, 26.208), (5.506, 26.208)),
             ((5.362, 22.256), (5.362, 20.494)), ((5.362, 20.494), (6.816, 20.494)), ((5.632, 22.526), (5.362, 22.256)),
             ((1.8, 25.99), (2.018, 26.208)), ((6.816, 20.494), (7.24, 20.918)), ((10.108, 20.918), (10.478, 21.288)),
             ((5.506, 26.208), (5.632, 26.082))]:
    remove_track('RESET', F, a, c)
for a, c in [((3.362, 20.494), (3.362, 21.748)), ((3.362, 21.748), (2.838, 22.272))]:
    remove_track('GND', F, a, c)
remove_via('GND', 2.838, 22.272)
j2 = fp['J2']
for pad in j2.Pads():
    if pad.GetNumber() == '4':
        pad.SetNetCode(0)
for item in j2.GraphicalItems():
    if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == 'RST':
        item.SetText('NC')

# 3. VBUS_VS_DISCH: B.Cu only on the U1 left side (the two vias beside the RESET corner go)
for a, c in [((9.73, 17.218), (7.53, 19.418)), ((8.63, 20.218), (8.63, 21.243))]:
    remove_track('VBUS_VS_DISCH', B, a, c)
for a, c in [((7.53, 19.418), (7.83, 19.418)), ((7.83, 19.418), (8.63, 20.218))]:
    remove_track('VBUS_VS_DISCH', F, a, c)
remove_via('VBUS_VS_DISCH', 7.53, 19.418)
remove_via('VBUS_VS_DISCH', 8.63, 20.218)
add_track('VBUS_VS_DISCH', B, [(9.73, 17.218), (7.9, 19.048), (7.9, 20.9), (8.243, 21.243), (8.63, 21.243)])

# 4. R21: R0603 0 Ohm strap beside U1.6, GND end on a via into the B.Cu pour
old = fp.pop('R21')
pos_note = (pcbnew.ToMM(old.GetPosition().x), pcbnew.ToMM(old.GetPosition().y))
for gone in DOOMED + [old, fp.pop('R15'), fp.pop('R16')]:
    b.Remove(gone)
lib = sys.argv[3] if len(sys.argv) > 3 else 'footprints/kicad/zudo-power.pretty'
r21 = pcbnew.FootprintLoad(lib, 'R0603')
r21.SetParent(b)
r21.SetReference('R21'); r21.SetValue('0R')
for key, value in (('LCSC', 'C21189'), ('MPN', '0603WAF0000T5E')):
    r21.SetField(key, value)
r21.SetFPIDAsString('zudo-pd:R0603')
b.Add(r21)
r21.SetOrientationDegrees(180)          # pad 1 (RESET) at +x, toward U1.6
r21.SetPosition(pt(8.6, 20.0))
r21.Reference().SetVisible(False)
for pad in r21.Pads():
    pad.SetNet(b.FindNet('RESET' if pad.GetNumber() == '1' else 'GND'))
p1 = [p for p in r21.Pads() if p.GetNumber() == '1'][0].GetPosition()
p2 = [p for p in r21.Pads() if p.GetNumber() == '2'][0].GetPosition()
x1, y1 = pcbnew.ToMM(p1.x), pcbnew.ToMM(p1.y)
x2, y2 = pcbnew.ToMM(p2.x), pcbnew.ToMM(p2.y)
add_track('RESET', F, [(10.478, 21.288), (10.478, 20.9), (9.95, 20.372), (x1, y1)])
add_via('GND', x2 - 0.75, y2)
add_track('GND', F, [(x2, y2), (x2 - 0.75, y2)])

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(OUT)
print(f'R21 moved from ({pos_note[0]:.3f}, {pos_note[1]:.3f}) to pads RESET ({x1:.3f}, {y1:.3f}) GND ({x2:.3f}, {y2:.3f}); saved {OUT}')
