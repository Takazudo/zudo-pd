"""Phase 14: closest same-layer distance from RESET copper to high-voltage nets on a Board P PCB (pcbnew, KiCad 10.0.6 image).
usage (in the pinned image, --cpus 1): python3 scripts/pcb/board-p-reset-clearance.py boards/board-p/board-p.kicad_pcb
The distances are compared with the LED Board P #144 record (0.222 mm between R13 pads, 0.326 mm from a VBUS_VS_DISCH via)."""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
HV = {'VBUS_IN','VBUS_VS_DISCH','DISCH','VBEN','VBUS_OUT','Q1_G','VDD_LOC','VDD_MID'}   # VDD_LOC/VDD_MID: board-p15 VDD feed (phase 17)
def items():
    for t in b.GetTracks(): yield t
    for f in b.GetFootprints():
        for p in f.Pads(): yield p
reset = [i for i in items() if i.GetNetname()=='RESET']
hv = [i for i in items() if i.GetNetname() in HV]
def dist(a, b2, layer):
    sa = a.GetEffectiveShape(layer); sb = b2.GetEffectiveShape(layer)
    if sa.Collide(sb, 0): return 0.0
    lo, hi = 0, pcbnew.FromMM(5)
    if not sa.Collide(sb, hi): return None
    while hi - lo > 1000:
        m = (lo+hi)//2
        if sa.Collide(sb, m): hi = m
        else: lo = m
    return pcbnew.ToMM(hi)
def scan(cross):
    rows = []
    for r in reset:
        for h in hv:
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not r.IsOnLayer(L):
                    continue
                for M in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if (M == L) == cross or not h.IsOnLayer(M):
                        continue
                    sa, sb = r.GetEffectiveShape(L), h.GetEffectiveShape(M)
                    d = 0.0 if sa.Collide(sb, 0) else None
                    if d is None:
                        lo, hi = 0, pcbnew.FromMM(5)
                        if sa.Collide(sb, hi):
                            while hi - lo > 1000:
                                m = (lo + hi) // 2
                                if sa.Collide(sb, m): hi = m
                                else: lo = m
                            d = pcbnew.ToMM(hi)
                    if d is not None:
                        rows.append((round(d, 3), nm(r), nm(h), h.GetNetname(), b.GetLayerName(L) + ('/' + b.GetLayerName(M) if cross else '')))
    return sorted(rows)[:12]


def nm(i):
    if isinstance(i, pcbnew.PAD): return i.GetParentFootprint().GetReference() + '.' + i.GetNumber()
    return i.GetClass()


if '--cross-layer' in sys.argv:
    # in-plane distance from RESET copper to VBUS-class copper on the other copper layer (through the board)
    print(json.dumps(scan(True), indent=0))
else:
    print(json.dumps(scan(False), indent=0))
