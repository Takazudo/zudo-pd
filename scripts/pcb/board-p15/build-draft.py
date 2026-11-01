"""Build the 15 V Board P draft PCB from the as-built routed module (pcbnew, pinned KiCad 10.0.6 image, --cpus 1).

usage: python3 build-draft.py <as-built board-p.kicad_pcb> <out board-p15-draft.kicad_pcb>

The as-built file is only read. The draft keeps every as-built placement and track except the edits of
dec-p15-reset-subset (scripts/schgen/board_p15_spec.py):
  - R15/R16 (I2C pull-ups to VREG_2V7) and their branch copper are removed;
  - J2.4 loses the RESET net and its silk label reads NC;
  - R21 becomes an R0603 0 Ohm strap beside U1.6 on F.Cu, with its GND end on a via into the B.Cu GND pour;
  - VBUS_VS_DISCH leaves the two vias beside the U1 RESET corner and runs on B.Cu only.
Phase 17 (dec-p15-i2c-pulldowns, dec-p15-vdd-local-clamp; no as-built part moves):
  - J2.4 carries the schematic's no-connect net, so schematic-parity DRC sees no net conflict;
  - R21 is a copy of the as-built R19 0 Ohm R0603 (same lands and silk as the ordered board) with LCSC Part;
  - R22/R23 100k pull SCL/SDA to GND beside the J2 pogo row (copies of the as-built R11);
  - U1.24 and C2.2 leave VBUS_IN for VDD_LOC: the C2 riser from VBUS_IN is removed, R29 1k + R30 470R and
    D9 BZT52C18 sit between VREG_2V7 and C34, R29 is fed from the existing VBUS_IN via, and VDD_LOC returns
    to the C2/U1.24 track through two vias on B.Cu.
Phase 18 (dec-p15-vdd-local-clamp amended): C38 1 uF decouples VDD_LOC; the supplier fields of every
added part are hidden on F.Fab, and the J2 SCL/SDA, J3 VBUS and U1 reference texts move (text only) off the
new pads. No part moves.
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
nc = pcbnew.NETINFO_ITEM(b, 'unconnected-(J2-Pad4)')
b.Add(nc)
for pad in j2.Pads():
    if pad.GetNumber() == '4':
        pad.SetNet(nc)
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

lib = sys.argv[3] if len(sys.argv) > 3 else 'footprints/kicad/zudo-power.pretty'

# 4. R21: copy of the as-built R19 0 Ohm R0603 beside U1.6, GND end on a via into the B.Cu pour
for name in ('VDD_LOC', 'VDD_MID'):
    b.Add(pcbnew.NETINFO_ITEM(b, name))


def set_fields(f, lcsc, mpn):
    # supplier fields stay hidden on F.Fab: a new visible field lands on F.SilkS at the footprint origin
    for key, val in (('LCSC', lcsc), ('LCSC Part', lcsc), ('MPN', mpn)):
        f.SetField(key, val)
        field = f.GetField(key)
        field.SetLayer(pcbnew.F_Fab)
        field.SetVisible(False)


def move_text(f, text, dx, dy):
    hits = [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == text]
    if len(hits) != 1:
        raise SystemExit(f'expected one {f.GetReference()} silk text {text!r}, found {len(hits)}')
    hits[0].Move(pt(dx, dy))


def clone(src, ref, value, lcsc, mpn, x, y, rot, nets):
    f = pcbnew.Cast_to_FOOTPRINT(fp[src].Duplicate(False))
    f.SetReference(ref); f.SetValue(value)
    set_fields(f, lcsc, mpn)
    b.Add(f)
    f.SetOrientationDegrees(rot)
    f.SetPosition(pt(x, y))
    f.Reference().SetLayer(pcbnew.F_Fab)   # assembly reference on F.Fab
    for g in list(f.GraphicalItems()):
        if g.GetLayer() == pcbnew.F_SilkS:
            g.SetLayer(pcbnew.F_Fab)       # the copied R0603 silk box is wider than the new spacing; resistors need no polarity mark
    for pad in f.Pads():
        pad.SetNet(b.FindNet(nets[pad.GetNumber()]))
    return f


def pad_xy(f, n):
    p = [q for q in f.Pads() if q.GetNumber() == n][0].GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


old = fp.pop('R21')
pos_note = (pcbnew.ToMM(old.GetPosition().x), pcbnew.ToMM(old.GetPosition().y))
r21 = clone('R19', 'R21', '0R', 'C21189', '0603WAF0000T5E', 8.6, 20.0, 180, {'1': 'RESET', '2': 'GND'})
x1, y1 = pad_xy(r21, '1')
x2, y2 = pad_xy(r21, '2')
add_track('RESET', F, [(10.478, 21.288), (10.478, 20.9), (9.95, 20.372), (x1, y1)])
add_via('GND', x2 - 0.75, y2)
add_track('GND', F, [(x2, y2), (x2 - 0.75, y2)])

# 5. SCL/SDA 100k pull-downs beside the J2 pogo row (pad 1 on the signal, pad 2 on GND)
r22 = clone('R11', 'R22', '100k', 'C25803', '0603WAF1003T5E', 4.54, 33.05, 180, {'1': 'SCL', '2': 'GND'})
add_track('SCL', F, [pad_xy(r22, '1'), (5.378, 34.972)])
gx, gy = pad_xy(r22, '2')
add_via('GND', gx, gy + 0.85)
add_track('GND', F, [(gx, gy), (gx, gy + 0.85)])
r23 = clone('R11', 'R23', '100k', 'C25803', '0603WAF1003T5E', 5.04, 30.55, 0, {'1': 'SDA', '2': 'GND'})
add_track('SDA', F, [pad_xy(r23, '1'), (3.726, 31.288)])
gx, gy = pad_xy(r23, '2')
add_track('GND', F, [(gx, gy), (gx, 29.638)])

# 6. VDD local feed and clamp: U1.24 and C2.2 move to VDD_LOC
remove_track('VBUS_IN', F, (16.678, 17.328), (16.678, 21.002))
for t in TRACKS:
    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'VBUS_IN' and t.GetLayer() == F and any(
            close(e, *q) for e in (t.GetStart(), t.GetEnd()) for q in ((14.724, 21.002), (13.728, 21.998))):
        t.SetNet(b.FindNet('VDD_LOC'))
for ref, n in (('U1', '24'), ('C2', '2')):
    [q for q in fp[ref].Pads() if q.GetNumber() == n][0].SetNet(b.FindNet('VDD_LOC'))
r29 = clone('R11', 'R29', '1k', 'C21190', '0603WAF1001T5E', 20.6, 26.7, 180, {'1': 'VBUS_IN', '2': 'VDD_MID'})
r30 = clone('R13', 'R30', '470R', 'C23179', '0603WAF4700T5E', 18.15, 26.7, 180, {'1': 'VDD_MID', '2': 'VDD_LOC'})
d9 = pcbnew.FootprintLoad(lib, 'SOD-123_L2.8-W1.8-LS3.7-RD')
d9.SetParent(b)
d9.SetReference('D9'); d9.SetValue('BZT52C18-7-F')
set_fields(d9, 'C192739', 'BZT52C18-7-F')
d9.SetFPIDAsString('zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD')
b.Add(d9)
d9.SetPosition(pt(18.9, 24.95))
d9.Reference().SetLayer(pcbnew.F_Fab)
for pad in d9.Pads():
    pad.SetNet(b.FindNet('VDD_LOC' if pad.GetNumber() == '1' else 'GND'))
add_track('VBUS_IN', F, [(21.634, 25.066), (21.634, 26.416), pad_xy(r29, '1')])
add_track('VDD_MID', F, [pad_xy(r30, '1'), pad_xy(r29, '2')])
k = pad_xy(d9, '1')
add_track('VDD_LOC', F, [pad_xy(r30, '2'), k])
add_via('VDD_LOC', 16.6, k[1])
add_track('VDD_LOC', F, [k, (16.6, k[1])])
add_track('VDD_LOC', B, [(16.6, k[1]), (16.6, 22.878), (14.724, 21.002)])
add_via('VDD_LOC', 14.724, 21.002)
a = pad_xy(d9, '2')
add_via('GND', 19.3, a[1])
add_track('GND', F, [a, (19.3, a[1])])

# 7. C38 1 uF VDD_LOC decoupler (r3 C38, C15849 as C30/C34) in the free top-side slot right of C2/C30,
#    pad 1 on a VDD_LOC track to C2.2 through the C2/C30 gap, pad 2 on the existing GND via right of C30
c38 = clone('C30', 'C38', '1uF/50V', 'C15849', 'CL10A105KB8NNNC', 19.85, 22.05, 0, {'1': 'VDD_LOC', '2': 'GND'})
c1x, c1y = pad_xy(c38, '1')
c2x, c2y = pad_xy(c38, '2')
add_track('VDD_LOC', F, [(c1x, c1y), (16.95, c1y), (16.678, c1y - 0.272), (16.678, 21.002)])
add_track('GND', F, [(c2x, c2y), (c2x, 23.03), (19.35, 23.03)])

# 8. silk: move text only (no part moves) so no label clips a new pad
move_text(fp['J2'], 'SCL', 0, 1.25)      # below R22, still beside J2.1
move_text(fp['J2'], 'SDA', 0, 0.73)      # in the gap between R23 and R22, beside J2.2
move_text(fp['J3'], 'VBUS', 0.2, -0.5)   # above R29 pad 1, beside J3.4
fp['U1'].Reference().Move(pt(1.5, 0))    # clear of the R21 RESET pad
fp['C30'].Reference().SetLayer(pcbnew.F_Fab)   # its as-built spot right of C30 is now C38; no free silk spot beside C30

for gone in DOOMED + [old, fp.pop('R15'), fp.pop('R16')]:
    b.Remove(gone)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(OUT)
print(f'R21 moved from ({pos_note[0]:.3f}, {pos_note[1]:.3f}) to pads RESET ({x1:.3f}, {y1:.3f}) GND ({x2:.3f}, {y2:.3f}); saved {OUT}')
