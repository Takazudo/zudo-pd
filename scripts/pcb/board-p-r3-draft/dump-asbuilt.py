import pcbnew, json, sys
b = pcbnew.LoadBoard(sys.argv[1])
out = []
for fp in b.GetFootprints():
    p = fp.GetPosition(); bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
    out.append({'ref': fp.GetReference(), 'fpid': str(fp.GetFPID().GetLibItemName()), 'x': pcbnew.ToMM(p.x), 'y': pcbnew.ToMM(p.y),
                'rot': fp.GetOrientationDegrees(), 'side': 'B' if fp.IsFlipped() else 'F',
                'bbox': [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())]})
print(json.dumps(sorted(out, key=lambda r: r['ref']), indent=0))
