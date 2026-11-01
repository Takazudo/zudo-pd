"""Phase 14: closest same-layer distance from RESET copper to high-voltage nets on a Board P PCB (pcbnew, KiCad 10.0.6 image).
usage (in the pinned image, --cpus 1): python3 scripts/pcb/board-p-reset-clearance.py boards/board-p/board-p.kicad_pcb
The distances are compared with the LED Board P #144 record (0.222 mm between R13 pads, 0.326 mm from a VBUS_VS_DISCH via)."""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
HV = {'VBUS_IN','VBUS_VS_DISCH','DISCH','VBEN','VBUS_OUT','Q1_G'}
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
out = []
for r in reset:
    for h in hv:
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            if r.IsOnLayer(L) and h.IsOnLayer(L):
                d = dist(r, h, L)
                if d is not None:
                    def nm(i):
                        if isinstance(i, pcbnew.PAD): return i.GetParentFootprint().GetReference()+'.'+i.GetNumber()
                        return i.GetClass()
                    out.append((round(d,3), nm(r), nm(h), h.GetNetname(), b.GetLayerName(L)))
out.sort()
print(json.dumps(out[:12], indent=0))
