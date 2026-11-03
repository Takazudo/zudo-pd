"""Dump copper geometry of a board for the host-side router (phase 12).

usage: python3 dump-geom.py <board.kicad_pcb> > geom.json   (inside the pinned KiCad image)
Pads give net, layers (F, B or both), bounding box and drill; rule areas give their outline and flags;
existing tracks and vias are listed. Units are mm in KiCad board coordinates.
"""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
out = {'pads': [], 'rule_areas': [], 'tracks': [], 'vias': []}
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        layers = [l for l, lid in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)) if p.IsOnLayer(lid)]
        drill = mm(p.GetDrillSize().x) if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else 0
        out['pads'].append({'ref': fp.GetReference(), 'num': p.GetNumber(), 'net': p.GetNetname(), 'layers': layers,
                            'bbox': [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
                            'center': [mm(p.GetPosition().x), mm(p.GetPosition().y)], 'drill': drill})
for z in b.Zones():
    if z.GetIsRuleArea():
        ol = z.Outline().Outline(0)
        out['rule_areas'].append({'layer': 'F' if z.GetLayer() == pcbnew.F_Cu else 'B',
                                  'no_vias': z.GetDoNotAllowVias(), 'no_tracks': z.GetDoNotAllowTracks(),
                                  'points': [[mm(ol.CPoint(i).x), mm(ol.CPoint(i).y)] for i in range(ol.PointCount())]})
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        out['vias'].append({'net': t.GetNetname(), 'at': [mm(t.GetPosition().x), mm(t.GetPosition().y)], 'd': mm(t.GetWidth(pcbnew.F_Cu))})
    else:
        out['tracks'].append({'net': t.GetNetname(), 'layer': 'F' if t.GetLayer() == pcbnew.F_Cu else 'B', 'w': mm(t.GetWidth()),
                              'a': [mm(t.GetStart().x), mm(t.GetStart().y)], 'b': [mm(t.GetEnd().x), mm(t.GetEnd().y)]})
print(json.dumps(out))
