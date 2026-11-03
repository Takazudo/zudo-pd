"""Build the Board P r3 placement draft from board_p_spec.py (run inside the pinned KiCad image; see run.sh).

usage: python3 build-draft.py <repo> <out.kicad_pcb> <report.json> <asbuilt-stripped.kicad_pcb> <asbuilt-pos.json> <search.json>
Starts from the as-built outline and mounting holes only (strip-asbuilt.py); every component footprint is
loaded from the shared library named in the spec and given the spec nets. J1, JOUT1, J2, J3, MH1-MH3 and U1
stay at their as-built coordinates; the other positions come from search-placement.py. The RESET-strap and
STUSB local-clamp pin corridors become via keep-out rule areas; footprint intrusion is asserted here. Floorplan 'pre' parts (phase 11)
override the as-built position, which moves U1 (not a connector). Power routing is route-power.py.
"""
import importlib.util, json, math, sys
import pcbnew

repo, out_pcb, out_rep = sys.argv[1:4]
spec_path = f'{repo}/scripts/schgen/board_p_spec.py'
s = importlib.util.spec_from_file_location('board_p_spec', spec_path)
spec = importlib.util.module_from_spec(s); s.loader.exec_module(spec)
LIB = f'{repo}/footprints/kicad/zudo-power.pretty'
W, H = 27.0, 40.0
EDGE = 0.25          # courtyard-to-edge clearance (PA) for parts not fixed on the edge
GAP = 0.10           # courtyard-to-courtyard spacing (PA); KiCad DRC requires only no overlap
GRID = 0.25
mm = pcbnew.FromMM

board = pcbnew.LoadBoard(sys.argv[4])   # as-built board with tracks, vias and zones stripped (strip.py)
asbuilt = json.load(open(sys.argv[5]))
_unused = {fp.GetReference(): (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y), fp.GetOrientationDegrees())
           for fp in board.GetFootprints()}

def pin_names():
    """(symbol, pin number) -> pin name, so no-connect nets carry KiCad's schematic names (as board-b20 build-draft)."""
    sys.path.insert(0, f'{repo}/scripts/schgen')
    from sexp import atom, find_all, load
    names = {}
    for sym in find_all(load(f'{repo}/symbols/zudo-pd.kicad_sym'), 'symbol'):
        top = atom(sym[1])
        for unit in [sym] + find_all(sym, 'symbol'):
            for pin in find_all(unit, 'pin'):
                number = [atom(n[1]) for n in find_all(pin, 'number')]
                name = [atom(n[1]) for n in find_all(pin, 'name')]
                if number and name:
                    names[(top, number[0])] = name[0]
    return names


PIN_NAMES = pin_names()
nets = {}
for name in spec.NETS:
    ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
pad_net = {pin: n for n, pins in spec.NETS.items() for pin in pins}

FIXED = {r: asbuilt[r] for r in ('J1', 'JOUT1', 'J2', 'J3', 'U1')}
rects = []           # (x0, y0, x1, y1, owner)
for fp in board.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
    rects.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()), fp.GetReference()))

fps, missing_pads = {}, []
for ref, (sym, value, lcsc, fpname, dnp, _pos) in spec.COMPONENTS.items():
    fp = pcbnew.FootprintLoad(LIB, fpname.split(':', 1)[1])
    assert fp is not None, fpname
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetFPID(pcbnew.LIB_ID('zudo-pd', fpname.split(':', 1)[1]))
    # exact supplier identity from the spec, as the exporter's identity gate and schematic-parity DRC require
    # library footprints may carry a supplier alias field from another part (the shared SOD-123 has C92321); the
    # exporter rejects any alias that differs from LCSC, so every alias present takes the spec's LCSC (pcbnew 10 has
    # no field removal)
    for alias in ('LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
        if fp.HasField(alias):
            fp.SetField(alias, lcsc or '')
    if lcsc:
        fp.SetField('LCSC', lcsc)
        fp.GetField('LCSC').SetVisible(False)
    else:
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    if dnp:
        fp.SetDNP(True)
    for pad in fp.Pads():
        key = f'{ref}.{pad.GetNumber()}'
        if key in pad_net:
            pad.SetNet(nets[pad_net[key]])
        elif key in spec.NO_CONNECT:
            pin = PIN_NAMES.get((sym, pad.GetNumber()), '~')
            label = f'{ref}-Pad{pad.GetNumber()}' if pin in ('~', '', pad.GetNumber()) else f'{ref}-{pin}-Pad{pad.GetNumber()}'
            ni = pcbnew.NETINFO_ITEM(board, f'unconnected-({label})'); board.Add(ni)
            pad.SetNet(ni)
    have = {p.GetNumber() for p in fp.Pads()}
    missing_pads += [p for p in pad_net if p.split('.')[0] == ref and p.split('.', 1)[1] not in have]
    board.Add(fp); fps[ref] = fp


def courtyard(fp):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


def put(fp, x, y, rot):
    fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def pad_xy(ref, num):
    p = next(p for p in fps[ref].Pads() if p.GetNumber() == num)
    return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)


def overlaps(r, gap=GAP):
    return [o[4] for o in rects if r[0] < o[2] + gap and r[2] > o[0] - gap and r[1] < o[3] + gap and r[3] > o[1] - gap]


for ref, (x, y, rot) in FIXED.items():
    put(fps[ref], x, y, rot)
    c = courtyard(fps[ref]); rects.append((*c, ref))

placed = dict(FIXED)
keepouts = []


def best_spot(ref, target, pin=None):
    """Nearest legal grid position to target (or the position putting pad `pin` nearest to target)."""
    fp = fps[ref]
    tx, ty = target
    cands = []
    for rot in (0, 90, 180, 270):
        put(fp, 0, 0, rot)
        c = courtyard(fp)
        off = pad_xy(ref, pin) if pin else (0.0, 0.0)
        x = math.ceil((EDGE - c[0]) / GRID) * GRID
        while x <= W - EDGE - c[2]:
            y = math.ceil((EDGE - c[1]) / GRID) * GRID
            while y <= H - EDGE - c[3]:
                cands.append((math.hypot(x + off[0] - tx, y + off[1] - ty), x, y, rot, c))
                y += GRID
            x += GRID
    cands.sort(key=lambda k: k[0])
    for d, x, y, rot, c in cands:
        r = (c[0] + x, c[1] + y, c[2] + x, c[3] + y)
        if overlaps(r) or any(r[0] < k[2] and r[2] > k[0] and r[1] < k[3] and r[3] > k[1] for k in keepouts):
            continue
        return (d, x, y, rot)
    return None


def place(ref, target, pin=None):
    b = best_spot(ref, target, pin)
    if not b:
        return None
    _, x, y, rot = b
    put(fps[ref], x, y, rot)
    c = courtyard(fps[ref]); rects.append((*c, ref)); placed[ref] = (x, y, rot)
    return b[0]


def net_target(ref):
    pts = []
    for pad in fps[ref].Pads():
        n = pad.GetNetname()
        if not n or n == 'GND':
            continue
        for other, fp in fps.items():
            if other == ref or other not in placed:
                continue
            for q in fp.Pads():
                if q.GetNetname() == n:
                    pts.append((pcbnew.ToMM(q.GetPosition().x), pcbnew.ToMM(q.GetPosition().y)))
    if not pts:
        return (W / 2, H / 2)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


# Placement comes from search.py (host-side courtyard search); applied here and re-measured by pcbnew.
SEARCH = json.load(open(sys.argv[6]))
keepouts = [tuple(k) for k in SEARCH['keepouts']]
pin_dist = SEARCH['pin_d']
unplaced = list(SEARCH['unplaced'])
PRE = SEARCH.get('floorplan', {}).get('pre', {})
for ref, (x, y, rot, side) in SEARCH['pos'].items():
    if ref in FIXED and ref not in PRE:
        continue
    fp = fps[ref]
    put(fp, x, y, rot)
    if side == 'B':
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
    placed[ref] = (x, y, rot)
for ref in unplaced:
    put(fps[ref], W + 8, 5 + 6 * unplaced.index(ref), 0)

# Each corridor runs from a protected STUSB4500 pin to its owner's pad, so the owner and U1 necessarily touch it.
# A footprint-disallow rule area therefore flagged exactly those owners (5 items_not_allowed). The corridor stays a
# via keep-out for DRC, and the footprint rule is checked here instead: only U1 and the protected owners may touch one
# (a neighbouring owner's courtyard may clip a corridor; the report lists every touching footprint).
CORRIDOR_OWNERS = {'U1', *pin_dist}
corridor_touch = []
for k in keepouts:
    touching = sorted(r for r in spec.COMPONENTS if fps[r].GetLayer() == pcbnew.F_Cu
                      and (lambda c: c[0] < k[2] and c[2] > k[0] and c[1] < k[3] and c[3] > k[1])(courtyard(fps[r])))
    assert set(touching) <= CORRIDOR_OWNERS, f'corridor {k} intruded by {touching}'
    corridor_touch.append(touching)
for k in keepouts:
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowFootprints(False)
    z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowZoneFills(False)
    z.SetLayer(pcbnew.F_Cu)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])):
        ol.Append(mm(x), mm(y))
    board.Add(z)

area_board = W * H
area_parts = sum((c[2] - c[0]) * (c[3] - c[1]) for c in (courtyard(fps[r]) for r in spec.COMPONENTS))
area_holes = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects if r[4].startswith('MH'))
pcbnew.SaveBoard(out_pcb, board)
report = {
    'board_mm': [W, H], 'grid_mm': GRID, 'edge_clearance_mm': EDGE, 'courtyard_gap_mm': GAP, 'side': 'top and bottom' if any(p[3] == 'B' for p in SEARCH['pos'].values()) else 'top only', 'bottom': sorted(r for r, p in SEARCH['pos'].items() if p[3] == 'B'),
    'fixed': {r: placed[r] for r in FIXED if r not in PRE}, 'floorplan_pre': PRE, 'mounting_holes': {r: asbuilt[r] for r in asbuilt if r.startswith('MH')},
    'placed': {r: [round(v, 3) for v in placed[r]] for r in placed if r not in FIXED},
    'unplaced': unplaced, 'missing_pads': missing_pads,
    'pin_to_part_pad_mm': {r: (round(d, 3) if d is not None else None) for r, d in pin_dist.items()},
    'keepouts_mm': [[round(v, 3) for v in k] for k in keepouts],
    'keepout_rule': 'vias not allowed; footprints checked by build-draft.py: only U1 and protected owners touch a corridor',
    'keepout_footprints': corridor_touch,
    'area_mm2': {'board': area_board, 'mounting_hole_courtyards': round(area_holes, 1),
                 'component_courtyards_library': round(area_parts, 1),
                 'utilisation_of_board_less_holes': round(area_parts / (area_board - area_holes), 3)},
}
open(out_rep, 'w').write(json.dumps(report, indent=1) + '\n')
print(json.dumps({'unplaced': unplaced, 'missing_pads': missing_pads, 'area': report['area_mm2'], 'pin': report['pin_to_part_pad_mm']}))
