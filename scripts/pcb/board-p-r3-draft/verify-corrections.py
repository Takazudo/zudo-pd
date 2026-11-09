"""Native local R1-R4 geometry checks; not a thermal rating or supplier process approval.

Usage: python verify-corrections.py <report.json> [--baseline-pcb PATH --execution-revision SHA]
Run with pinned pcbnew after the complete rebuild and DRC, under the native lock.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import subprocess
import pcbnew
import argparse
from correction_contract import validate_coverage
def xy(point):
    return (point.x, point.y)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output')
parser.add_argument('--baseline-pcb', type=Path)
parser.add_argument('--pcb', type=Path)
parser.add_argument('--execution-revision')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[3]
PCB = args.pcb or ROOT / 'boards/board-p/board-p.kicad_pcb'
OWNER = ROOT / 'boards/board-p/r3-draft'
if pcbnew.GetBuildVersion() != '10.0.6':
    raise ValueError('Native correction proof requires pinned KiCad 10.0.6')
board = pcbnew.LoadBoard(str(PCB))
mm = pcbnew.FromMM
pads = {f'{fp.GetReference()}.{p.GetNumber()}': p for fp in board.GetFootprints() for p in fp.Pads()}
vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
expected = json.loads((OWNER / 'pours.json').read_text())
via_fabrication = []
for via in vias:
    diameter, drill = via.GetWidth(pcbnew.F_Cu), via.GetDrillValue()
    if drill < mm(0.2) or diameter-drill < mm(0.2):
        raise ValueError('Via violates the reviewed 0.20 mm drill / 0.10 mm radial ring floor')
    via_fabrication.append({'diameter_mm': diameter/1e6, 'drill_mm': drill/1e6, 'radial_ring_mm': (diameter-drill)/2e6})
via_fabrication_summary = {'via_count': len(vias),
                           'minimum_drill_mm': min(v['drill_mm'] for v in via_fabrication),
                           'minimum_radial_ring_mm': min(v['radial_ring_mm'] for v in via_fabrication),
                           'scope': 'Local geometry floor; native hole/clearance checks and supplier process approval remain separate.'}

constraints = json.loads((OWNER / 'search-two-sided.json').read_text())['local_decoupling_constraints']
validate_coverage(expected, constraints)
thermal = []
for spec in expected['vias']:
    if 'thermal_owner' not in spec:
        continue
    point = pcbnew.VECTOR2I(*(mm(x) for x in spec['at']))
    matches = [v for v in vias if v.GetPosition() == point and v.GetNetname() == spec['net']]
    if not len(matches) == 1:
        raise ValueError(f'Missing/duplicate thermal via: {spec}')
    via = matches[0]
    if not (via.GetDrillValue() == mm(spec['drill']) and via.GetWidth(pcbnew.F_Cu) == mm(spec['d'])):
        raise ValueError(spec)
    pad = pads[spec['thermal_owner']]
    if not (pad.GetNetname() == spec['net'] and pad.HitTest(point)):
        raise ValueError(spec)
    # These adopted EPs are axis-aligned rectangles. Explicitly reject any
    # future rounded/custom/rotated shape before using rectangle containment.
    if pad.GetShape() != pcbnew.PAD_SHAPE_RECT or abs(pad.GetOrientation().AsDegrees() % 90) > 1e-6:
        raise ValueError(f'Thermal annulus containment needs a new exact shape proof: {spec}')
    box = pad.GetBoundingBox()
    radius = mm(spec['d'] / 2)
    if not box.Contains(pcbnew.VECTOR2I(point.x - radius, point.y - radius)):
        raise ValueError(spec)
    if not box.Contains(pcbnew.VECTOR2I(point.x + radius, point.y + radius)):
        raise ValueError(spec)
    back = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == spec['net'] and (z.GetLayer() == pcbnew.B_Cu) and z.HitTestFilledArea(pcbnew.B_Cu, point, 0)]
    if not back:
        raise ValueError(f'Thermal via lacks connected B.Cu fill: {spec}')
    thermal.append({**spec, 'annular_ring_mm': (spec['d'] - spec['drill']) / 2, 'inside_exposed_pad': True, 'containment_method': 'full via bounding square inside verified axis-aligned rectangular pad', 'back_fill_contact': True})
# Do not omit an unexpected additional hole from exposed-pad assembly review.
for owner in ['U2.21', 'Q1.9', 'Q3.9']:
    actual_centers = {xy(v.GetPosition()) for v in vias if pads[owner].HitTest(v.GetPosition())}
    expected_centers = {tuple(mm(value) for value in v['at']) for v in thermal if v['thermal_owner'] == owner}
    if actual_centers != expected_centers:
        raise ValueError(f'Unreviewed exposed-pad via coverage: {owner}, {actual_centers ^ expected_centers}')
# Conservatively bound each actual mask/paste opening by the native pad box
# expanded with its resolved layer-specific margin. A positive hole gap to this
# superset proves separation even for rotated/rounded pads.
local_via_openings = []
for spec in expected['vias']:
    if 'minimum_hole_to_opening_mm' not in spec:
        continue
    point = pcbnew.VECTOR2I(*(mm(value) for value in spec['at']))
    matches = [v for v in vias if v.GetPosition() == point and v.GetNetname() == spec['net']]
    if len(matches) != 1 or matches[0].GetDrillValue() != mm(spec['drill']) or matches[0].GetWidth(pcbnew.F_Cu) != mm(spec['d']):
        raise ValueError(f'Missing or changed local via: {spec}')
    via = matches[0]
    # Even a tented via is screened as if its resolved mask opening were open.
    # This avoids relying on tenting to prevent a shared component opening.
    via_opening_radius = via.GetWidth(pcbnew.F_Cu)/2e6 + max(0, via.GetSolderMaskExpansion())/1e6
    nearest = None
    for key, pad in pads.items():
        for layer in [pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.F_Paste, pcbnew.B_Paste]:
            if not pad.IsOnLayer(layer):
                continue
            box = pad.GetBoundingBox()
            if layer in [pcbnew.F_Mask, pcbnew.B_Mask]:
                mx = my = max(0, pad.GetSolderMaskExpansion(layer))
            else:
                margin = pad.GetSolderPasteMargin(layer)
                mx, my = max(0, margin.x), max(0, margin.y)
            dx = max(box.GetLeft()-mx-point.x, 0, point.x-box.GetRight()-mx)
            dy = max(box.GetTop()-my-point.y, 0, point.y-box.GetBottom()-my)
            gap = math.hypot(dx, dy)/1000000 - spec['drill']/2
            if nearest is None or gap < nearest['hole_to_opening_mm']:
                nearest = {'pad': key, 'layer': board.GetLayerName(layer), 'hole_to_opening_mm': gap,
                           'via_opening_to_pad_opening_mm': gap + spec['drill']/2 - via_opening_radius}
    if nearest is None or nearest['hole_to_opening_mm'] < spec['minimum_hole_to_opening_mm']-1e-6:
        raise ValueError(f'Local via too close to pad mask/paste opening: {spec}, {nearest}')
    if nearest['via_opening_to_pad_opening_mm'] < spec['minimum_via_opening_to_pad_opening_mm']-1e-6:
        raise ValueError(f'Local via and component mask/paste openings too close: {spec}, {nearest}')
    local_via_openings.append({'at': spec['at'], 'net': spec['net'], 'nearest_conservative_opening': nearest,
                               'minimum_hole_gap_mm': spec['minimum_hole_to_opening_mm'],
                               'minimum_opening_gap_mm': spec['minimum_via_opening_to_pad_opening_mm'],
                               'via_opening_radius_mm': via_opening_radius,
                               'front_tenting_mode': str(via.GetFrontTentingMode()), 'back_tenting_mode': str(via.GetBackTentingMode())})
decoupling = {}
for ref, spec in constraints.items():
    a, b = (pads[spec['ic_pad']], pads[f"{ref}.{spec['capacitor_pad']}"])
    if not a.GetNetname() == b.GetNetname():
        raise ValueError('Geometry check failed')
    distance = math.hypot(a.GetPosition().x - b.GetPosition().x, a.GetPosition().y - b.GetPosition().y) / 1000000.0
    if not distance <= spec['max_distance_mm']:
        raise ValueError((ref, distance))
    decoupling[ref] = {**spec, 'actual_distance_mm': distance}
local_returns = {}
for ref, pin, layer in [('C30', '1', pcbnew.F_Cu), ('C34', '2', pcbnew.B_Cu)]:
    pad = pads[f'{ref}.{pin}']
    return_spec = next(v for v in expected['vias'] if v.get('local_return_owner') == f'{ref}.{pin}')
    return_point = pcbnew.VECTOR2I(*(mm(value) for value in return_spec['at']))
    return_via = next(v for v in vias if v.GetNetname() == 'GND' and v.GetPosition() == return_point)
    matching = [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetLayer() == layer and t.GetNetname() == 'GND' and {xy(t.GetStart()), xy(t.GetEnd())} == {xy(pad.GetPosition()), xy(return_point)}]
    if len(matching) != 1:
        raise ValueError(f'{ref}: missing direct local GND return')
    length = matching[0].GetLength()/1e6
    if length > 1.0:
        raise ValueError((ref, length))
    if not any(z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.B_Cu and not z.GetIsRuleArea() and z.HitTestFilledArea(pcbnew.B_Cu, return_point, 0) for z in board.Zones()):
        raise ValueError(f'{ref}: local return via lacks B.Cu GND contact')
    local_returns[ref] = {'direct_return_length_mm': length, 'via': return_spec['at'], 'scope': 'Direct capacitor pad-center to via-center track; via barrel and connected B.Cu plane are separate.'}


def supply_path(start, end):
    """Shortest existing copper centerline route, including pad contact and via transitions."""
    import heapq
    net = start.GetNetname()
    graph = {}

    def edge(a, b, length, transitions=0):
        graph.setdefault(a, []).append((b, length, transitions))
        graph.setdefault(b, []).append((a, length, transitions))
    segments, vertices = [], set()
    for track in board.GetTracks():
        if track.GetNetname() != net:
            continue
        if track.GetClass() == 'PCB_VIA':
            x, y = xy(track.GetPosition())
            front, back = (x, y, pcbnew.F_Cu), (x, y, pcbnew.B_Cu)
            vertices.update([front, back])
            edge(front, back, 0, 1)
        else:
            a = (*xy(track.GetStart()), track.GetLayer())
            b = (*xy(track.GetEnd()), track.GetLayer())
            vertices.update([a, b])
            segments.append((a, b))
    # Split at all collinear branch/via endpoints; a T-junction need not be a
    # segment endpoint in the PCB serialization. One IU is 1 nm, not a gap bridge.
    for a, b in segments:
        dx, dy = b[0]-a[0], b[1]-a[1]
        squared = dx*dx+dy*dy
        if not squared:
            continue
        on_segment = []
        for point in vertices:
            if point[2] != a[2]:
                continue
            fraction = ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/squared
            if 0 <= fraction <= 1 and abs((point[0]-a[0])*dy-(point[1]-a[1])*dx) <= math.sqrt(squared):
                on_segment.append((fraction, point))
        on_segment.sort()
        for (_, first), (_, second) in zip(on_segment, on_segment[1:]):
            edge(first, second, math.hypot(second[0]-first[0], second[1]-first[1])/1e6)
    for pad, label in [(start, 'start'), (end, 'end')]:
        for node in list(graph):
            if isinstance(node, tuple) and pad.IsOnLayer(node[2]) and pad.HitTest(pcbnew.VECTOR2I(node[0], node[1])):
                edge(label, node, math.hypot(node[0] - pad.GetPosition().x, node[1] - pad.GetPosition().y) / 1000000.0)
    heap = [(0.0, 0, 0, 'start')]
    seen, serial = (set(), 0)
    while heap:
        length, transitions, _, node = heapq.heappop(heap)
        if (node, transitions) in seen or transitions > 2:
            continue
        seen.add((node, transitions))
        if node == 'end':
            if length > 4.5:
                raise ValueError(f'Local supply path detours: {length:.3f} mm')
            return {'routed_centerline_mm': length, 'via_transitions': transitions, 'limit_mm': 4.5, 'limit_via_transitions': 2, 'length_scope': 'Planar copper centerlines plus pad-center connections; via barrel length is excluded and transitions are bounded separately.'}
        for other, delta, vias_used in graph.get(node, []):
            serial += 1
            heapq.heappush(heap, (length + delta, transitions + vias_used, serial, other))
    raise ValueError(f'No short local supply path: {net}')
connected_back = {}
for owner in sorted({v['thermal_owner'] for v in thermal}):
    owner_vias = [v for v in thermal if v['thermal_owner'] == owner]
    touched = []
    for zone_index, zone in enumerate(board.Zones()):
        if zone.GetIsRuleArea() or zone.GetLayer() != pcbnew.B_Cu or zone.GetNetname() != owner_vias[0]['net']:
            continue
        filled = zone.GetFilledPolysList(pcbnew.B_Cu)
        for index in range(filled.OutlineCount()):
            outline = filled.Outline(index)
            holes = [filled.Hole(index, h) for h in range(filled.HoleCount(index))]
            contacts = [v['at'] for v in owner_vias
                        if outline.PointInside(pcbnew.VECTOR2I(*(mm(a) for a in v['at'])))
                        and not any(hole.PointInside(pcbnew.VECTOR2I(*(mm(a) for a in v['at']))) for hole in holes)]
            if not contacts:
                continue
            area = abs(outline.Area())
            for hole in range(filled.HoleCount(index)):
                area -= abs(filled.Hole(index, hole).Area())
            touched.append({'zone_index': zone_index, 'outline_index': index, 'area_mm2': area / 1000000000000.0, 'via_contacts_mm': contacts})
    if not touched:
        raise ValueError(f'{owner}: no connected B.Cu polygon')
    connected_back[owner] = {'connected_polygons': touched, 'connected_area_mm2': sum((p['area_mm2'] for p in touched)), 'continuity': 'Each listed filled polygon contacts an owner via inside the same continuous exposed F.Cu pad; separate polygons join through that pad.'}
for ref, spec in constraints.items():
    decoupling[ref]['routed_path'] = supply_path(pads[spec['ic_pad']], pads[f"{ref}.{spec['capacitor_pad']}"])
# The 2.96 mm square is the exposed solderable pad; the TI drawing's
# 3.4 x 6.5 mm rectangle is additional masked PCB metal, not the package pad.
u2_pad = pads['U2.21']
u2_points = [pcbnew.VECTOR2I(*(mm(a) for a in via['at'])) for via in thermal if via['thermal_owner'] == 'U2.21']
front_polygons = []
front_polysets = []  # Own SWIG polygon sets while borrowed outlines/holes are sampled.
for zone in board.Zones():
    if zone.GetIsRuleArea() or zone.GetLayer() != pcbnew.F_Cu or zone.GetNetname() != 'GND':
        continue
    filled = zone.GetFilledPolysList(pcbnew.F_Cu)
    front_polysets.append(filled)
    for index in range(filled.OutlineCount()):
        outline = filled.Outline(index)
        if any(outline.PointInside(point) and zone.HitTestFilledArea(pcbnew.F_Cu, point, 0) for point in u2_points):
            holes = [filled.Hole(index, h) for h in range(filled.HoleCount(index))]
            front_polygons.append((outline, holes))
center_x, center_y = (u2_pad.GetPosition().x/1e6, u2_pad.GetPosition().y/1e6)
hits, step = 0, 0.05
for column in range(130):
    for row in range(68):
        point = pcbnew.VECTOR2I(mm(center_x-3.25+(column+.5)*step), mm(center_y-1.7+(row+.5)*step))
        if u2_pad.HitTest(point) or any(outline.PointInside(point) and not any(hole.PointInside(point) for hole in holes) for outline, holes in front_polygons):
            hits += 1
u2_front_spreading = {
    'exposed_pad_mm': [2.96, 2.96], 'reference_masked_metal_mm': [6.5, 3.4],
    'reference_note': 'SLVSET9G PWP0020T example board layout, rotated with U2; note 9 permits metal size variation for creepage. The reference is not a guaranteed installed thermal condition.',
    'connected_filled_polygon_count': len(front_polygons),
    'connected_filled_polygon_area_mm2': sum((abs(outline.Area())-sum(abs(hole.Area()) for hole in holes))/1e12 for outline, holes in front_polygons),
    'sampled_pad_and_connected_fill_within_reference_rectangle_mm2': hits*step*step,
    'sample_pitch_mm': step,
    'scope': 'Filled-polygon continuity is established through the U2 pad/vias. Local union area is sampled geometry; neither area nor continuity establishes thermal resistance or a current rating.'}

# Dissipation is conditioned arithmetic, not an installed thermal rating.
evidence = {}
for name in ['tps16630pwpr', 'diodes-dmp3036sfg-7', 'csd18543q3a']:
    path = ROOT / '.claude/skills' / ('component-'+name) / 'facts.json'
    data = json.loads(path.read_text())
    rows = data if isinstance(data, list) else data['facts']
    evidence.update({row['fact_id']: row for row in rows})
ron = evidence['fact-c1849461-ron']['value']
if ron != '19 / 30.44 / 53 (min/typ/max)':
    raise ValueError('TPS16630 RON evidence changed; review conditioned loss inputs')
q1 = evidence['fact-c461081-rdson-10v-max']
q3 = evidence['fact-c840100-rdson-4v5-max']
if any(fact['unit'] != 'mOhm' for fact in [evidence['fact-c1849461-ron'], q1, q3]):
    raise ValueError('Resistance evidence units changed')
loss_cases = []
for case, current in [('nominal_20v_80percent_efficiency_at_osc_let_through', 51.7/(20*.8)), ('5a_contract_ceiling', 5.0)]:
    loss_cases.append({'case': case, 'input_current_a': current,
                      'u2_loss_w': current**2*.053,
                      'q1_loss_w_hot_assumption': current**2*float(q1['value'])/1000*1.5,
                      'q3_loss_w_hot_assumption': current**2*float(q3['value'])/1000*1.5})
conditioned_loss = {'method': 'I squared times resistance; 51.7 W is 12*2.1 + 12*2.0 + 5*0.5. The 80 percent efficiency and 1.5 hot-resistance factors are project assumptions, not guaranteed bounds.',
                    'cases': loss_cases,
                    'u2_condition': evidence['fact-c1849461-ron']['conditions'],
                    'q1_condition': q1['conditions'], 'q3_condition': q3['conditions'],
                    'reference_thermal_conditions': 'Q1 datasheet 55 C/W requires 1 in2 of 2 oz copper; 137 C/W is minimum-pad 2 oz. Neither is established by this 1 oz PCB. U2 JEDEC theta is likewise not an installed-board bound.',
                    'installed_thermal_resistance': 'UNKNOWN', 'bench_thermal_result': 'NOT RUN',
                    'acceptance': 'Preserved 5 A contract; these calculations and added copper do not establish 5 A thermal acceptance.'}

# Preserve the historical independent-review baseline, not the moving HEAD.
import tempfile
baseline_revision = '6b08236a30331659756ca6a9af492e59f3fc6061'
baseline_bytes = args.baseline_pcb.read_bytes() if args.baseline_pcb else subprocess.check_output(['git', 'show', baseline_revision+':boards/board-p/board-p.kicad_pcb'], cwd=ROOT)
if hashlib.sha256(baseline_bytes).hexdigest() != '67b0e0960c8d5590dec0efc6de22218d3f7a21fa098abcaffdd57433f3e0058d':
    raise ValueError('Baseline bytes do not match the historical independent review')
with tempfile.NamedTemporaryFile(suffix='.kicad_pcb') as temporary:
    temporary.write(baseline_bytes); temporary.flush()
    baseline_board = pcbnew.LoadBoard(temporary.name)

def placement_identity(value):
    return {fp.GetReference(): {'position_mm': [fp.GetPosition().x/1e6, fp.GetPosition().y/1e6],
                               'rotation_deg': fp.GetOrientation().AsDegrees(),
                               'layer': value.GetLayerName(fp.GetLayer()),
                               'footprint': str(fp.GetFPID().GetUniStringLibId())}
            for fp in value.GetFootprints()}

before, after = placement_identity(baseline_board), placement_identity(board)
if before.keys() != after.keys():
    raise ValueError('Footprint population changed during bounded layout correction')
changed = {ref: {'before': before[ref], 'after': after[ref]} for ref in before if before[ref] != after[ref]}
if set(changed) != {'C30', 'C34'} or any(before[ref]['footprint'] != after[ref]['footprint'] for ref in before):
    raise ValueError(f'Unexpected footprint identity/placement changes: {changed}')

def outline_identity(value):
    return sorted((int(item.GetShape()), xy(item.GetStart()), xy(item.GetEnd()), xy(item.GetCenter()), item.GetWidth())
                  for item in value.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts)

if outline_identity(baseline_board) != outline_identity(board) or board.GetCopperLayerCount() != baseline_board.GetCopperLayerCount():
    raise ValueError('Board outline or layer count changed')
preserved_geometry = {'baseline_revision': baseline_revision,
                      'baseline_pcb_sha256': hashlib.sha256(baseline_bytes).hexdigest(),
                      'only_changed_footprint_placements': changed,
                      'all_footprint_ids_unchanged': True, 'outline_unchanged': True,
                      'copper_layers': board.GetCopperLayerCount()}

source_paths = [OWNER/'fabrication-legend-constraints.json', OWNER/'pours.json', OWNER/'search-two-sided.json', OWNER/'floorplan.json', OWNER/'routes.json',
                ROOT/'symbols/zudo-pd.kicad_sym', ROOT/'boards/board-p/fp-lib-table',
                *Path(__file__).parent.glob('*.py'), Path(__file__).with_name('run.sh'),
                ROOT/'scripts/schgen/board_p_spec.py',
                ROOT/'boards/board-p/board-p.kicad_sch', ROOT/'boards/board-p/board-p.kicad_pro']
for footprint in board.GetFootprints():
    name = str(footprint.GetFPID().GetUniStringLibItemName())
    for library in ['footprints/kicad', 'footprints/kicad/zudo-power.pretty']:
        path = ROOT/library/(name+'.kicad_mod')
        if path.exists():
            source_paths.append(path)
for owner_name in ['tps16630pwpr', 'diodes-dmp3036sfg-7', 'csd18543q3a', 'tvs2200drvr']:
    source_paths.extend((ROOT/'.claude/skills'/('component-'+owner_name)).glob('*.json'))
source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(set(source_paths))}

report = {'tested_base_revision': (args.execution_revision or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()), 'source_state': 'Candidate source hashes below bind the working tree; this report is not a release or supplier approval.', 'source_hashes': source_hashes, 'pcb_sha256': hashlib.sha256(PCB.read_bytes()).hexdigest(), 'kicad_version': pcbnew.GetBuildVersion(), 'component_evidence_hashes': {name: hashlib.sha256((ROOT/'.claude/skills'/('component-'+name)/'facts.json').read_bytes()).hexdigest() for name in ['tps16630pwpr','diodes-dmp3036sfg-7','csd18543q3a']}, 'conditioned_loss': conditioned_loss, 'preserved_geometry': preserved_geometry, 'u2_front_spreading': u2_front_spreading, 'connected_back_copper': connected_back, 'thermal_vias': thermal, 'via_fabrication': via_fabrication_summary, 'decoupling': decoupling, 'local_returns': local_returns, 'local_via_openings': local_via_openings, 'scope': 'Local pad/via/B.Cu fill geometry only. DRC, complete net connectivity, manufacturing tenting/stencil review and bench thermal acceptance are separate.', 'manufacturing_residual': expected['thermal_via_policy']}
Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: {len(thermal)} thermal vias and {len(decoupling)} local decoupler distances; supplier process and thermal rating remain open')
