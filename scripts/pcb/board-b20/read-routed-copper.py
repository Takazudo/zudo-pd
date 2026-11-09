"""Derive desk-report copper from a saved native PCB, retaining named route metadata.

usage: read-routed-copper.py PCB ROUTES_OR_RECEIPT FINAL_GEOM FINAL_ROUTES RECEIPT
The receipt retains metadata so these inputs can be reproduced without rerouting.
This read does not replace native DRC, ERC or electrical acceptance.
"""
import hashlib
import json
from pathlib import Path
import sys
import pcbnew as p
from report_provenance import owner_hashes

pcb, template_path, geom_path, output, receipt_path = map(Path, sys.argv[1:])
board = p.LoadBoard(str(pcb))
if board.GetCopperLayerCount() != 4:
    raise SystemExit('B20 report inputs require the adopted four-layer stack')
raw = json.loads(template_path.read_text())
template = raw.get('routing_metadata', raw)
metadata = {key: template[key] for key in ('trunks', 'm12_pours', 'layers')}
if metadata['layers'] != ['F', 'In2', 'B']:
    raise SystemExit('Unexpected B20 router layer metadata')
geom = json.loads(geom_path.read_text())
# Independently bind every supplied pad field to this native PCB; a stale geometry
# file with unchanged net names must not acquire a fresh PCB hash in the receipt.
native_pads = []
for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
    for pad in fp.Pads():
        box = pad.GetBoundingBox()
        native_pads.append({'ref': fp.GetReference(), 'num': pad.GetNumber(), 'net': pad.GetNetname(),
                            'fp': str(fp.GetFPID().GetLibItemName()),
                            'layers': [name for name, layer in (('F', p.F_Cu), ('B', p.B_Cu)) if pad.IsOnLayer(layer)],
                            'round': pad.GetShape(p.F_Cu) in (p.PAD_SHAPE_CIRCLE, p.PAD_SHAPE_OVAL),
                            'bbox': [p.ToMM(box.GetLeft()), p.ToMM(box.GetTop()), p.ToMM(box.GetRight()), p.ToMM(box.GetBottom())],
                            'center': [p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y)],
                            'drill': p.ToMM(pad.GetDrillSize().x) if pad.GetAttribute() in (p.PAD_ATTRIB_PTH, p.PAD_ATTRIB_NPTH) else 0})
if geom['pads'] != native_pads:
    raise SystemExit('Supplied report pad geometry differs from current native PCB')
pads = {(pad['ref'], pad['num']): pad for pad in geom['pads']}
for trunk in metadata['trunks']:
    for end in ('from', 'to'):
        if pads[tuple(trunk[end].split('.'))]['net'] != trunk['net']:
            raise SystemExit('Named current-path endpoint no longer matches native geometry')
# The loop checker uses the named quiet-return pour outlines, so bind those to
# the actual native zones rather than accepting stale route metadata.
layer_ids = {'F': p.F_Cu, 'In2': p.In2_Cu, 'B': p.B_Cu}
for name, row in metadata['m12_pours'].items():
    matches = [z for z in board.Zones() if z.GetZoneName() == name and z.GetLayer() == layer_ids[row['layer']]]
    if len(matches) != 1 or matches[0].GetNetname() != 'M12_RAW':
        raise SystemExit('Missing or duplicate native quiet-return pour: ' + name)
    shape = matches[0].Outline()  # keep the SWIG parent alive through vertex extraction
    outline = shape.Outline(0)
    points = [[round(p.ToMM(outline.CPoint(i).x), 4), round(p.ToMM(outline.CPoint(i).y), 4)] for i in range(outline.PointCount())]
    expected = [[round(float(x), 4), round(float(y), 4)] for x, y in row['pts']]
    # Native KiCad may rotate/reverse a polygon's cyclic starting vertex.
    def edges(poly):
        return {tuple(sorted((tuple(a), tuple(b)))) for a, b in zip(poly, poly[1:] + poly[:1]) if a != b}
    if edges(points) != edges(expected):
        raise SystemExit('Quiet-return pour outline differs from route metadata: ' + name)
tracks, vias = [], []
for item in board.GetTracks():
    if isinstance(item, p.PCB_VIA):
        vias.append({'net': item.GetNetname(), 'at': [p.ToMM(item.GetPosition().x), p.ToMM(item.GetPosition().y)], 'd': p.ToMM(item.GetWidth(p.F_Cu))})
    else:
        if item.GetClass() != 'PCB_TRACK' or item.GetLayer() not in layer_ids.values():
            raise SystemExit('Unsupported routed primitive in B20 report input')
        tracks.append({'net': item.GetNetname(), 'layer': next(name for name, layer in layer_ids.items() if layer == item.GetLayer()),
                       'w': p.ToMM(item.GetWidth()), 'a': [p.ToMM(item.GetStart().x), p.ToMM(item.GetStart().y)],
                       'b': [p.ToMM(item.GetEnd().x), p.ToMM(item.GetEnd().y)]})
key = lambda row: json.dumps(row, sort_keys=True)
output.write_text(json.dumps({**metadata, 'tracks': sorted(tracks, key=key), 'vias': sorted(vias, key=key)}, indent=1)+'\n')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
root = Path(__file__).resolve().parents[3]
receipt = {'scope': 'Current/loop desk-report inputs extracted from actual native B20 copper; not electrical qualification',
           'pcb_sha256': sha(pcb), 'kicad_version': p.GetBuildVersion(), 'routing_metadata': metadata,
           'geom_sha256': sha(geom_path), 'routes_sha256': sha(output), 'native_track_count': len(tracks), 'native_via_count': len(vias),
           'owner_sha256': owner_hashes(root)}
receipt_path.write_text(json.dumps(receipt, indent=2)+'\n')
print(f'Native report inputs: {len(tracks)} tracks, {len(vias)} vias; quiet-return outlines and named path nets match')
