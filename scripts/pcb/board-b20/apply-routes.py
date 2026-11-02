"""Add route.py's tracks and vias plus the F.Cu/B.Cu GND pours to the B20 draft, then fill (pinned KiCad 10.0.6 pcbnew).

usage: python3 apply-routes.py <placed.kicad_pcb> <routes.json> <out.kicad_pcb>

The design rules live in <out>.kicad_pro (copied from Board B). They are copied beside the placed board first, so the
zone fill uses them, and SaveBoard's rewrite of the project file is undone.
"""
import json
import math
import pathlib
import sys

import pcbnew

rules = pathlib.Path(sys.argv[3]).with_suffix('.kicad_pro')
rules_text = rules.read_text()
pathlib.Path(sys.argv[1]).with_suffix('.kicad_pro').write_text(rules_text)
b = pcbnew.LoadBoard(sys.argv[1])
r = json.load(open(sys.argv[2]))
mm = pcbnew.FromMM
# phase 27: a four-layer route (an In2 signal/power layer from route.py B20_LAYERS=4) gets a 4-layer stackup with an
# In1.Cu GND plane over the whole board
FOUR = 'In2' in r.get('layers', []) or any(t['layer'] == 'In2' for t in r['tracks'])
CU = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In2': pcbnew.In2_Cu}
if FOUR:
    b.SetCopperLayerCount(4)
    b.GetDesignSettings().SetCopperLayerCount(4)
for t in r['tracks']:
    s = pcbnew.PCB_TRACK(b)
    s.SetStart(pcbnew.VECTOR2I(mm(t['a'][0]), mm(t['a'][1])))
    s.SetEnd(pcbnew.VECTOR2I(mm(t['b'][0]), mm(t['b'][1])))
    s.SetWidth(mm(t['w']))
    s.SetLayer(CU[t['layer']])
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
for layer, priority in ((pcbnew.F_Cu, 0), (pcbnew.B_Cu, 0)) + (((pcbnew.In1_Cu, 0),) if FOUR else ()):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet('GND'))
    z.SetZoneName({pcbnew.F_Cu: 'GND_F', pcbnew.B_Cu: 'GND_B', pcbnew.In1_Cu: 'GND_IN1'}[layer])
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
        # the pours stop at F/B copper, but a through via also crosses In2: keep it a clearance away from In2 tracks
        inner = [(s.GetStart(), s.GetEnd(), s.GetWidth()) for s in b.GetTracks()
                 if not isinstance(s, pcbnew.PCB_VIA) and s.GetLayer() == pcbnew.In2_Cu and s.GetNetCode() != gnd]

        def clear_of_inner(pt):
            for a, c, w in inner:
                d = c - a
                n2 = d.x * d.x + d.y * d.y
                t = 0.0 if n2 == 0 else max(0.0, min(1.0, ((pt.x - a.x) * d.x + (pt.y - a.y) * d.y) / n2))
                if math.hypot(pt.x - a.x - t * d.x, pt.y - a.y - t * d.y) < mm(0.4 + 0.25) + w // 2:
                    return False
            return True
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
                            and all((pt - h[0]).EuclideanNorm() >= mm(0.15 + 0.25) + h[1] // 2 for h in holes)
                            and clear_of_inner(pt)):
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
if FOUR:
    # a 1.6 mm 4-layer build in the shape of JLC's common prepreg/core/prepreg stack, B20's 2 oz outer copper kept;
    # the dielectric thicknesses are placeholders (they do not enter DRC) until a stackup is chosen
    out = pathlib.Path(sys.argv[3])
    text = out.read_text()
    i = text.index('(stackup')
    depth, k = 0, i
    while True:
        if text[k] == '(':
            depth += 1
        elif text[k] == ')':
            depth -= 1
            if depth == 0:
                break
        k += 1
    out.write_text(text[:i] + '\n'.join([
        '    (stackup',
        '      (layer "F.SilkS" (type "Top Silk Screen"))',
        '      (layer "F.Paste" (type "Top Solder Paste"))',
        '      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))',
        '      (layer "F.Cu" (type "copper") (thickness 0.07))',
        '      (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        '      (layer "In1.Cu" (type "copper") (thickness 0.0152))',
        '      (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))',
        '      (layer "In2.Cu" (type "copper") (thickness 0.0152))',
        '      (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        '      (layer "B.Cu" (type "copper") (thickness 0.07))',
        '      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))',
        '      (layer "B.Paste" (type "Bottom Solder Paste"))',
        '      (layer "B.SilkS" (type "Bottom Silk Screen"))',
        '      (copper_finish "None") (dielectric_constraints no)',
        '    )']) + text[k + 1:])
print(f"{len(r['tracks'])} tracks, {len(r['vias'])} vias, GND pours on F.Cu and B.Cu filled, {islands} island vias")
