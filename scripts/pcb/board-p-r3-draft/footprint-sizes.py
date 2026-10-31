import pcbnew, sys, json
lib = sys.argv[1]
names = sys.argv[2:]
out = {}
for n in names:
    fp = pcbnew.FootprintLoad(lib, n)
    if fp is None: out[n] = None; continue
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    pads = {p.GetNumber(): [pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)] for p in fp.Pads()}
    out[n] = {'bbox': [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())],
              'has_cy': bool(cy.OutlineCount()), 'pads': pads, 'th': any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())}
print(json.dumps(out))
