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


def stitch_islands(rounds=8):
    """Join GND pour fragments that the router left apart: union fragments through GND vias, plated GND holes and GND
    tracks; for every fragment outside the largest group, add one via where a 0.45 mm-eroded copy of that fragment and
    a fragment of another group on the other layer overlap, at least the hole-to-hole rule from every other hole.
    Rounds repeat until no via is added, so chains of small fragments reach the main group."""
    gnd = b.FindNet('GND').GetNetCode()
    zones = {zz.GetLayer(): zz for zz in b.Zones() if not zz.GetIsRuleArea() and zz.GetNetCode() == gnd}
    L = (pcbnew.F_Cu, pcbnew.B_Cu)
    total = 0
    for _ in range(rounds):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        polys = {l: zones[l].GetFilledPolysList(l) for l in L}
        eroded = {}
        for l in L:
            e = pcbnew.SHAPE_POLY_SET(polys[l])
            e.Deflate(mm(0.45), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.005))
            eroded[l] = e
        parent = {}

        def find(x):
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def frag(l, pt):
            for i in range(polys[l].OutlineCount()):
                if polys[l].Contains(pt, i):
                    return (l, i)
            return None

        holes = []
        for v in b.GetTracks():
            if isinstance(v, pcbnew.PCB_VIA):
                holes.append((v.GetPosition(), v.GetDrillValue()))
                if v.GetNetCode() == gnd:
                    a, c = frag(L[0], v.GetPosition()), frag(L[1], v.GetPosition())
                    if a and c:
                        parent[find(a)] = find(c)
            elif v.GetNetCode() == gnd and v.GetLayer() in L:
                a, c = frag(v.GetLayer(), v.GetStart()), frag(v.GetLayer(), v.GetEnd())
                if a and c:
                    parent[find(a)] = find(c)
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetDrillSize().x > 0:
                    holes.append((pad.GetPosition(), max(pad.GetDrillSize().x, pad.GetDrillSize().y)))
                    if pad.GetNetCode() == gnd:
                        a, c = frag(L[0], pad.GetPosition()), frag(L[1], pad.GetPosition())
                        if a and c:
                            parent[find(a)] = find(c)
        frags = [(l, i) for l in L for i in range(polys[l].OutlineCount())]
        area = {}
        for f in frags:
            area[find(f)] = area.get(find(f), 0) + abs(polys[f[0]].Outline(f[1]).Area())
        main = max(area, key=area.get)
        added = 0
        for l, i in frags:
            if find((l, i)) == main:
                continue
            other = L[1] if l == L[0] else L[0]
            bb = polys[l].Outline(i).BBox()
            step = mm(0.1)
            done = False
            y = bb.GetTop()
            while y <= bb.GetBottom() and not done:
                x = bb.GetLeft()
                while x <= bb.GetRight() and not done:
                    pt = pcbnew.VECTOR2I(x, y)
                    if (polys[l].Contains(pt, i) and eroded[l].Contains(pt) and eroded[other].Contains(pt)
                            and frag(other, pt) is not None and find(frag(other, pt)) != find((l, i))
                            and all((pt - h[0]).EuclideanNorm() >= mm(0.15 + 0.25) + h[1] // 2 for h in holes)):
                        v = pcbnew.PCB_VIA(b)
                        v.SetPosition(pt)
                        v.SetWidth(mm(0.8))
                        v.SetDrill(mm(0.3))
                        v.SetNetCode(gnd)
                        b.Add(v)
                        holes.append((pt, mm(0.3)))
                        added += 1
                        done = True
                    x += step
                y += step
            if done:
                parent[find((l, i))] = find(frag(other, pt))
        total += added
        if not added:
            break
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    return total


islands = stitch_islands()
pcbnew.SaveBoard(sys.argv[3], b)
rules.write_text(rules_text)
print(f"{len(r['tracks'])} tracks, {len(r['vias'])} vias, GND pours on F.Cu and B.Cu filled, {islands} island vias")
