"""Phase 12: add the tracks and vias from route-signals.py to the Board P r3 draft.

usage: python3 apply-tracks.py <board.kicad_pcb> <routes.json>   (inside the pinned KiCad image)
"""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
r = json.load(open(sys.argv[2]))
mm = pcbnew.FromMM
for t in r['tracks']:
    s = pcbnew.PCB_TRACK(b)
    s.SetStart(pcbnew.VECTOR2I(mm(t['a'][0]), mm(t['a'][1]))); s.SetEnd(pcbnew.VECTOR2I(mm(t['b'][0]), mm(t['b'][1])))
    s.SetWidth(mm(t['w'])); s.SetLayer(pcbnew.F_Cu if t['layer'] == 'F' else pcbnew.B_Cu); s.SetNet(b.FindNet(t['net']))
    b.Add(s)
for v in r['vias']:
    s = pcbnew.PCB_VIA(b)
    s.SetPosition(pcbnew.VECTOR2I(mm(v['at'][0]), mm(v['at'][1]))); s.SetWidth(mm(v['d'])); s.SetDrill(mm(0.3))
    s.SetNet(b.FindNet(v['net']))
    b.Add(s)
pcbnew.SaveBoard(sys.argv[1], b)
print(len(r['tracks']), len(r['vias']))
