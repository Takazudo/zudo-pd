"""Dump the copper geometry of the B20 draft for the host-side router (pinned KiCad 10.0.6 pcbnew, --cpus 1).

usage: python3 dump-geom.py <board.kicad_pcb> > geom.json
Pads carry net, footprint, layers, bounding box, size and drill; rule areas their outline and flags. Units are mm.
"""
import json
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
out = {'pads': [], 'rule_areas': [], 'tracks': [], 'vias': []}
# footprints in reference order: the board's own order follows the builder's set iteration, and the router's result
# depends on pad order
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    name = str(fp.GetFPID().GetLibItemName())
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        layers = [l for l, lid in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)) if p.IsOnLayer(lid)]
        drill = mm(p.GetDrillSize().x) if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else 0
        out['pads'].append({'ref': fp.GetReference(), 'num': p.GetNumber(), 'net': p.GetNetname(), 'fp': name,
                            'layers': layers, 'round': p.GetShape(pcbnew.F_Cu) in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL),
                            'bbox': [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
                            'center': [mm(p.GetPosition().x), mm(p.GetPosition().y)], 'drill': drill})
for z in b.Zones():
    if z.GetIsRuleArea():
        ol = z.Outline().Outline(0)
        out['rule_areas'].append({'name': z.GetZoneName(), 'no_vias': z.GetDoNotAllowVias(), 'no_tracks': z.GetDoNotAllowTracks(),
                                  'points': [[mm(ol.CPoint(i).x), mm(ol.CPoint(i).y)] for i in range(ol.PointCount())]})
print(json.dumps(out))
