"""Add route.py's tracks and vias plus the F.Cu/B.Cu GND pours to the B20 draft, then fill (pinned KiCad 10.0.6 pcbnew).

usage: python3 apply-routes.py <placed.kicad_pcb> <routes.json> <out.kicad_pcb>

The design rules live in <out>.kicad_pro (copied from Board B). They are copied beside the placed board first, so the
zone fill uses them, and SaveBoard's rewrite of the project file is undone.
"""
import json
import pathlib
import sys

import pcbnew

rules = pathlib.Path(sys.argv[3]).with_suffix('.kicad_pro')
rules_text = rules.read_text()
pathlib.Path(sys.argv[1]).with_suffix('.kicad_pro').write_text(rules_text)
b = pcbnew.LoadBoard(sys.argv[1])
r = json.load(open(sys.argv[2]))
mm = pcbnew.FromMM
for t in r['tracks']:
    s = pcbnew.PCB_TRACK(b)
    s.SetStart(pcbnew.VECTOR2I(mm(t['a'][0]), mm(t['a'][1])))
    s.SetEnd(pcbnew.VECTOR2I(mm(t['b'][0]), mm(t['b'][1])))
    s.SetWidth(mm(t['w']))
    s.SetLayer(pcbnew.F_Cu if t['layer'] == 'F' else pcbnew.B_Cu)
    s.SetNet(b.FindNet(t['net']))
    b.Add(s)
for v in r['vias']:
    s = pcbnew.PCB_VIA(b)
    s.SetPosition(pcbnew.VECTOR2I(mm(v['at'][0]), mm(v['at'][1])))
    s.SetWidth(mm(v['d']))
    s.SetDrill(mm(0.3))
    s.SetNet(b.FindNet(v['net']))
    b.Add(s)
for d in b.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith('B20 DRAFT'):
        d.SetText('B20 DRAFT - PARTLY ROUTED - NOT FOR FABRICATION')
edge = b.GetBoardEdgesBoundingBox()
for layer, priority in ((pcbnew.F_Cu, 0), (pcbnew.B_Cu, 0)):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet('GND'))
    z.SetZoneName('GND_F' if layer == pcbnew.F_Cu else 'GND_B')
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid: the EP via pads and small GND pads join the pours directly
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((edge.GetLeft(), edge.GetTop()), (edge.GetRight(), edge.GetTop()),
                 (edge.GetRight(), edge.GetBottom()), (edge.GetLeft(), edge.GetBottom())):
        ol.Append(x, y)
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[3], b)
rules.write_text(rules_text)
print(f"{len(r['tracks'])} tracks, {len(r['vias'])} vias, GND pours on F.Cu and B.Cu filled")
