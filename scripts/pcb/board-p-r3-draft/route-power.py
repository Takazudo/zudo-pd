"""Phase 11/12: power-path pours and ground on the Board P r3 draft (runs after route-signals.py in phase 12).

usage: python3 route-power.py <board.kicad_pcb> <report.json> <pours.json>   (inside the pinned KiCad image)
The power nets are copper pours on F.Cu shaped along the floorplan corridors (floorplan.json); GND is
a B.Cu pour plus an F.Cu fill, stitched with vias wherever both fills exist. Signal routing is supplied
by route-signals.py/apply-tracks.py; this stage fills copper and checks ground connectivity.
Widths: IPC-2221 external-layer chart, 1 oz (35 um, the board stackup), 5 A at a 20 C rise -> 1.82 mm
minimum (PA: rise and chart are design assumptions, not a measured thermal result).
"""
import json, math, sys, uuid
import pcbnew
from native_connectivity import pad_polygon_contacts

pcb_path, rep_path = sys.argv[1:3]
board = pcbnew.LoadBoard(pcb_path)
mm = pcbnew.FromMM
I_A, DT_C, OZ_MIL = 5.0, 20.0, 1.378
area_mil2 = (I_A / (0.048 * DT_C ** 0.44)) ** (1 / 0.725)
W_MIN_MM = area_mil2 / OZ_MIL * 0.0254


POURS = [(p['net'], p['layer'], p['priority'], [[tuple(v) for v in o] for o in p['outlines']])
         for p in json.load(open(sys.argv[3]))['pours']]


def add_zone(net, layer, prio, r):
    z = pcbnew.ZONE(board)
    z.SetLayer(board.GetLayerID(layer)); z.SetNet(board.FindNet(net)); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in r:
        ol.Append(mm(x), mm(y))
    z.m_Uuid.Clone(pcbnew.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, 'zudo-pd/r3/zone/'+json.dumps([net,layer,prio,r])))))
    board.Add(z)
    return z


zones = [add_zone(n, l, p, r) for n, l, p, rs in POURS for r in rs]
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

# stitching vias: grid points inside both GND fills, at least 0.8 mm from any pad or keep-out
gnd = board.FindNet('GND')
fz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.F_Cu]
bz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.B_Cu]
keep = [z for z in board.Zones() if z.GetIsRuleArea()]
pad_boxes = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox(); bb.Inflate(mm(0.8)); pad_boxes.append(bb)
VIA_D, VIA_DRILL, PITCH = 0.6, 0.3, 2.0
segs = [(pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y), pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y),
         pcbnew.ToMM(t.GetWidth()) if t.GetClass() != 'PCB_VIA' else pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)))
        for t in board.GetTracks()]


def seg_dist(x, y, s):
    ax, ay, bx, by, _w = s
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


vias = []
y = 1.0
while y < 39.0:
    x = 1.0
    while x < 26.0:
        pt = pcbnew.VECTOR2I(mm(x), mm(y))
        ok = all(any(z.HitTestFilledArea(z.GetLayer(), pt, mm(VIA_D / 2 + 0.2)) for z in zs) for zs in (fz, bz))
        ok = ok and not any(k.Outline().Contains(pt) for k in keep)
        ok = ok and not any(bb.Contains(pt) for bb in pad_boxes)
        ok = ok and all(seg_dist(x, y, sg) > VIA_D / 2 + 0.2 + sg[4] / 2 + 0.05 for sg in segs)
        if ok:
            v = pcbnew.PCB_VIA(board); v.SetPosition(pt); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(gnd)
            v.m_Uuid.Clone(pcbnew.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, 'zudo-pd/r3/stitch/'+str(v.GetPosition().x)+'/'+str(v.GetPosition().y))))); board.Add(v); vias.append((round(x, 2), round(y, 2))); segs.append((x, y, x, y, VIA_D))
        x += PITCH
    y += PITCH
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())


# phase 12: every GND fill island on either layer needs a via or a GND PTH pad inside, or it floats; place one on a
# 0.1 mm grid where both layers are filled, clear of pads and tracks
def via_point_ok(x, y):
    pt = pcbnew.VECTOR2I(mm(x), mm(y))
    # phase 13: the via centre must lie in both fills; the refill then connects the zone around the via
    for zs in (fz, bz):
        if not any(z.HitTestFilledArea(z.GetLayer(), pt, 0) for z in zs):
            return False
    if any(k.Outline().Contains(pt) for k in keep) or any(bb.Contains(pt) for bb in island_pad_boxes):
        return False
    return all(seg_dist(x, y, sg) > ISL_VIA_D / 2 + 0.2 + sg[4] / 2 + 0.05 for sg in segs)


ISL_VIA_D = 0.5   # island vias use the 0.5 mm board-minimum via (0.1 mm annular ring)
island_pad_boxes = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox(); bb.Inflate(mm(0.3 if p.GetNetname() == 'GND' else ISL_VIA_D / 2 + 0.25)); island_pad_boxes.append(bb)
gnd_th = [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
# phase 13: GND vias placed by route-signals.py (pad escapes) anchor islands too
gnd_th += [t.GetPosition() for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
island_vias = []


def gnd_clusters():
    """Phase 13: GND connectivity clusters of fill polygons, vias, pads and tracks (union-find). A fill island with a via
    can still float when the via lands in an island on the other layer, so islands are judged by cluster, not by via."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent.setdefault(parent[a], parent[a]); a = parent[a]
        return a

    def union(a, b):
        parent[find(a)] = find(b)
    polys, polysets = [], []
    for z in fz + bz:
        pl = z.GetFilledPolysList(z.GetLayer())
        for i in range(pl.OutlineCount()):
            ps = pcbnew.SHAPE_POLY_SET(); ps.AddOutline(pl.Outline(i))
            for j in range(pl.HoleCount(i)):
                ps.AddHole(pl.Hole(i, j))
            polysets.append(ps)
            polys.append((z.GetLayer(), ps.Outline(0)))
    vias_ = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    tracks_ = [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == 'GND']
    pads_ = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == 'GND']

    def at(pt, layer):
        # Retain holes for point contacts too; an outer-outline hit alone is not copper.
        hits = [('P', k) for k, (l, _ch) in enumerate(polys) if l == layer and polysets[k].Contains(pt)]
        hits += [('V', k) for k, v in enumerate(vias_) if v.HitTest(pt)]
        hits += [('D', k) for k, p in enumerate(pads_) if p.IsOnLayer(layer) and p.HitTest(pt)]
        # phase 15: a track end on another track's copper joins it (track-to-track joints, T-junctions), as KiCad counts it
        hits += [('T', k) for k, t in enumerate(tracks_) if t.GetLayer() == layer and t.HitTest(pt)]
        return hits
    for k, v in enumerate(vias_):
        for l in (pcbnew.F_Cu, pcbnew.B_Cu):
            for h in at(v.GetPosition(), l):
                union(('V', k), h)
    for k, p in enumerate(pads_):
        for l in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(l):
                for h in at(p.GetPosition(), l):
                    union(('D', k), h)
    # A filled polygon may touch the edge of a pad without containing its center.
    for pad_index, polygon_index in pad_polygon_contacts(pads_, polys, polysets):
        union(('D', pad_index), ('P', polygon_index))
    for k, t in enumerate(tracks_):
        for pt in (t.GetStart(), t.GetEnd()):
            for h in at(pt, t.GetLayer()):
                union(('T', k), h)
        # phase 15: a track whose body crosses a fill touches it, not only at its end points
        shape = t.GetEffectiveShape(t.GetLayer())
        for j, (l, _ch) in enumerate(polys):
            if l == t.GetLayer() and polysets[j].Collide(shape, 0):
                union(('T', k), ('P', j))
    groups = {}
    for k in range(len(polys)):
        groups.setdefault(find(('P', k)), []).append(k)
    for kind, n in (('V', len(vias_)), ('D', len(pads_)), ('T', len(tracks_))):
        for k in range(n):
            groups.setdefault(find((kind, k)), [])
    area = {g: sum(polys[k][1].Area() for k in ks) for g, ks in groups.items()}
    main = max(area, key=area.get)
    detached = []
    for g, ks in groups.items():
        if g == main:
            continue
        members = [m for m in parent if find(m) == g]
        detached.append({'polys': ks, 'pads': [f"{pads_[m[1]].GetParentFootprint().GetReference()}.{pads_[m[1]].GetNumber()}"
                                                for m in members if m[0] == 'D'],
                         'vias': [[round(pcbnew.ToMM(vias_[m[1]].GetPosition().x), 2), round(pcbnew.ToMM(vias_[m[1]].GetPosition().y), 2)]
                                  for m in members if m[0] == 'V']})
    return polys, [polys[k] for k in groups[main]], detached, polysets


for _round in range(4):
    added = 0
    polys, main_polys, detached, polygon_owners = gnd_clusters()
    for d in detached:
        done = False
        for k in d['polys']:
            layer, ch = polys[k]
            other = [c for l, c in main_polys if l != layer]
            bb = ch.BBox()
            x0, y0, x1, y1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
            yy = y0 + 0.05
            while yy < y1 and not done:
                xx = x0 + 0.05
                while xx < x1 and not done:
                    q = pcbnew.VECTOR2I(mm(xx), mm(yy))
                    if ch.PointInside(q) and any(c.PointInside(q) for c in other) and via_point_ok(xx, yy):
                        v = pcbnew.PCB_VIA(board); v.SetPosition(q); v.SetWidth(mm(ISL_VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(gnd)
                        v.m_Uuid.Clone(pcbnew.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, 'zudo-pd/r3/stitch/'+str(v.GetPosition().x)+'/'+str(v.GetPosition().y))))); board.Add(v); island_vias.append((round(xx, 2), round(yy, 2))); segs.append((xx, yy, xx, yy, ISL_VIA_D))
                        done = True; added += 1
                    xx += 0.05
                yy += 0.05
            if done:
                break
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    if not added:
        break
polys, main_polys, detached, polygon_owners = gnd_clusters()
floating = []
for d in detached:
    bbs = [polys[k][1].BBox() for k in d['polys']]
    floating.append({'layers': sorted({'F.Cu' if polys[k][0] == pcbnew.F_Cu else 'B.Cu' for k in d['polys']}),
                     'bbox_mm': [round(pcbnew.ToMM(min(b.GetLeft() for b in bbs)), 2), round(pcbnew.ToMM(min(b.GetTop() for b in bbs)), 2),
                                 round(pcbnew.ToMM(max(b.GetRight() for b in bbs)), 2), round(pcbnew.ToMM(max(b.GetBottom() for b in bbs)), 2)] if bbs else None,
                     'pads': d['pads'], 'vias': d['vias']})
pcbnew.SaveBoard(pcb_path, board)

# filled-copper cross-sections across each corridor, sampled every 0.05 mm: the aggregate filled length and the
# largest single filled run along the cut (neither proves one continuous corridor nor a rated current)
CUTS = [('VBUS_IN', 'x', 10.0, 7.85, 10.55), ('VBUS_IN', 'x', 13.5, 7.85, 10.55), ('EF_IN', 'y', 14.05, 5.75, 9.3),
        ('VBUS_P', 'y', 17.5, 9.3, 11.2), ('VBUS_P', 'x', 13.5, 12.3, 15.6), ('VBUS_P', 'y', 24.5, 5.6, 9.3),
        ('VBUS_OUT', 'y', 33.0, 4.6, 9.3)]
cuts = []
for net, axis, at, a, b in CUTS:
    nz = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net and z.GetLayer() == pcbnew.F_Cu]
    hits, run, best, t = 0, 0, 0, a
    while t <= b + 1e-9:
        pt = pcbnew.VECTOR2I(mm(at), mm(t)) if axis == 'x' else pcbnew.VECTOR2I(mm(t), mm(at))
        h = any(z.HitTestFilledArea(pcbnew.F_Cu, pt, 0) for z in nz)
        hits += h; run = run + 1 if h else 0; best = max(best, run); t += 0.05
    cuts.append({'net': net, 'cut': f'{axis}={at}', 'span_mm': [a, b], 'aggregate_filled_mm': round(hits * 0.05, 2),
                 'largest_run_mm': round(best * 0.05, 2), 'meets_min_width': best * 0.05 >= W_MIN_MM})
report = {'width_rule': {'current_a': I_A, 'temperature_rise_c': DT_C, 'copper': '35 um (1 oz) outer, board stackup',
                         'method': 'IPC-2221 external-layer chart (PA)', 'min_width_mm': round(W_MIN_MM, 2)},
          'pours': [{'net': n, 'layer': l, 'outlines_mm': rs} for n, l, p, rs in POURS],
          'cross_sections': cuts,
          'island_vias': island_vias, 'gnd_clusters_detached': floating,
          'stitching_vias': {'count': len(vias), 'diameter_mm': VIA_D, 'drill_mm': VIA_DRILL, 'pitch_mm': PITCH}}
open(rep_path, 'w').write(json.dumps(report, indent=1) + '\n')
print(json.dumps({'min_width_mm': round(W_MIN_MM, 2), 'vias': len(vias), 'island_vias': len(island_vias), 'cuts': cuts}))
