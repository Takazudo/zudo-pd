#!/usr/bin/env python3
"""Check the renewal Board B's explicit power paths and filled thermal copper.

Run with KiCad's Python interpreter. This checks geometry, not current capacity,
thermal resistance, transient behavior, or assembly qualification.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

import wx
_KICAD_APP = wx.App(False)
import pcbnew as p
from pcb_common import pcb_net_name
from board_b_layout import GROUND_CORRIDOR, GROUND_STITCHES

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import board_b_spec as spec

EPS_MM = .001
LAYERS = (p.F_Cu, p.B_Cu)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def xy(vector):
    return (int(vector.x), int(vector.y))


def mm(point):
    return [round(p.ToMM(value), 6) for value in point]


def point(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def layer_name(layer):
    return 'F.Cu' if layer == p.F_Cu else 'B.Cu'


def on_segment(pt, start, end):
    """Centerline incidence, with a 1 um numeric tolerance, including tees."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    if not length2:
        return sum((a - b) ** 2 for a, b in zip(pt, start)) <= p.FromMM(EPS_MM) ** 2
    ratio = max(0., min(1., ((pt[0] - start[0]) * dx + (pt[1] - start[1]) * dy) / length2))
    return (pt[0] - start[0] - ratio * dx) ** 2 + (pt[1] - start[1] - ratio * dy) ** 2 <= p.FromMM(EPS_MM) ** 2


def main_path(board, source, capacitor, fuse):
    """Prove an explicit >=1 mm trace path without zones or thin sense traces.

Pad copper joins centerline vertices within that pad. Track tees and split
segments are supported. This is intentionally conservative about arbitrary
edge-only copper contact, which should be reviewed rather than silently accepted.
"""
    net = source.GetNetCode()
    require(net > 0 and capacitor.GetNetCode() == net and fuse.GetNetCode() == net,
            'Output, capacitor and PTC do not share the expected net')
    tracks, vias, nodes = [], [], set()
    for item in board.GetTracks():
        if item.GetNetCode() != net:
            continue
        if isinstance(item, p.PCB_VIA):
            diameter, drill = p.ToMM(item.GetWidth(p.F_Cu)), p.ToMM(item.GetDrill())
            if diameter < 1.0 - EPS_MM or (diameter - drill) / 2 < .25 - EPS_MM:
                continue
            if not all(item.IsOnLayer(layer) for layer in LAYERS):
                continue
            vias.append(item)
            nodes.update((*xy(item.GetPosition()), layer) for layer in LAYERS)
        elif isinstance(item, p.PCB_TRACK) and not isinstance(item, p.PCB_ARC):
            if p.ToMM(item.GetWidth()) < 1.0 - EPS_MM:
                continue
            tracks.append(item)
            nodes.update(((*xy(item.GetStart()), item.GetLayer()), (*xy(item.GetEnd()), item.GetLayer())))
    required_pads = (source, capacitor, fuse)
    for pad in required_pads:
        require(pad.IsOnLayer(p.F_Cu), 'Expected front-side power terminal')
        nodes.add((*xy(pad.GetPosition()), p.F_Cu))
    # An output route may change layers through a plated socket/terminal pad.
    # Include actual same-net pad copper as graph edges, just like via annuli;
    # omitting these would reject a physically continuous wide route.
    pads=[pad for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetCode()==net]
    for pad in pads:
        for layer in LAYERS:
            if pad.IsOnLayer(layer):nodes.add((*xy(pad.GetPosition()),layer))
    graph = collections.defaultdict(set)

    def connect(group):
        group = list(group)
        if not group:
            return
        first = group[0]
        for other in group[1:]:
            graph[first].add(other)
            graph[other].add(first)

    for track in tracks:
        connect(node for node in nodes if node[2] == track.GetLayer()
                and on_segment(node[:2], xy(track.GetStart()), xy(track.GetEnd())))
    for via in vias:
        connect((*xy(via.GetPosition()), layer) for layer in LAYERS)
    for pad in pads:
        for layer in LAYERS:
            if pad.IsOnLayer(layer):
                connect(node for node in nodes if node[2]==layer
                        and pad.HitTest(p.VECTOR2I(node[0],node[1])))
        if pad.GetAttribute()==p.PAD_ATTRIB_PTH:
            connect((*xy(pad.GetPosition()),layer) for layer in LAYERS if pad.IsOnLayer(layer))
    start = (*xy(source.GetPosition()), p.F_Cu)
    target = (*xy(fuse.GetPosition()), p.F_Cu)
    capacitor_node = (*xy(capacitor.GetPosition()), p.F_Cu)
    seen, todo = {start}, collections.deque([start])
    while todo:
        for node in sorted(graph[todo.popleft()]):
            if node not in seen:
                seen.add(node)
                todo.append(node)
    # Reachability is sufficient; the mandatory capacitor copper must be in the
    # same wide network, while the DRC verifies all other board connections.
    require(target in seen and capacitor_node in seen,
            'No complete >=1 mm output-to-capacitor/PTC power path')
    return {'minimum_trace_width_mm': 1.0, 'narrow_feedback_and_zones_excluded': True,
            'capacitor_and_ptc_reachable': True, 'qualifying_tracks': len(tracks),
            'qualifying_vias': len(vias)}


def ground_width_screen(polygon, policy):
    """Sample separate same-net runs; aggregate width is not one continuous plane."""
    require(policy['minimum_aggregate_mm'] >= 20 and policy['minimum_largest_mm'] >= 10,
            'Ground screening policy is weaker than the reviewed 20/10 mm thresholds')
    require(policy['x_end'] > policy['x_start'] and policy['ys'], 'Invalid ground sample range')
    result = []
    for y in policy['ys']:
        runs, start, end, active_polygon = [], None, None, None
        for index in range(round((policy['x_end']-policy['x_start'])/.5)+1):
            x = policy['x_start'] + index * .5
            matches = [i for i in range(polygon.OutlineCount()) if polygon.Contains(point(x,y),i)]
            require(len(matches)<=1, 'Ambiguous ground sample belongs to multiple polygons')
            current_polygon = matches[0] if matches else None
            # Never combine adjacent samples from different polygons as a run.
            if start is not None and current_polygon != active_polygon:
                runs.append({'x_start_mm':start,'x_end_mm':end,'width_mm':end-start,'polygon_index':active_polygon})
                start = None
            if current_polygon is not None:
                if start is None:start=x
                end=x;active_polygon=current_polygon
        if start is not None:
            runs.append({'x_start_mm':start,'x_end_mm':end,'width_mm':end-start,'polygon_index':active_polygon})
        aggregate = sum(run['width_mm'] for run in runs)
        largest = max((run['width_mm'] for run in runs), default=0)
        require(aggregate >= policy['minimum_aggregate_mm'],
                f'Back GND aggregate sampled width {aggregate:g} mm below {policy["minimum_aggregate_mm"]:g} mm at y={y}')
        require(largest >= policy['minimum_largest_mm'],
                f'Back GND largest sampled run {largest:g} mm below {policy["minimum_largest_mm"]:g} mm at y={y}')
        result.append({'y_mm':y,'aggregate_sampled_width_mm':aggregate,
                       'largest_sampled_run_mm':largest,'runs':runs})
    return result


def verify_ground_stitches(board, ground, expected_centers):
    """Prove the seven intentional plated returns without permitting via-in-paste."""
    require(len(expected_centers)==7 and len({tuple(v) for v in expected_centers})==7,
            'Expected exactly seven distinct ground stitch positions')
    vias = [item for item in board.GetTracks() if isinstance(item,p.PCB_VIA)]
    paste_pads = [(fp.GetReference()+'.'+pad.GetNumber(),pad) for fp in board.GetFootprints()
                  for pad in fp.Pads() if pad.IsOnLayer(p.F_Paste) or pad.IsOnLayer(p.B_Paste)]
    result=[]
    for x,y in expected_centers:
        center=point(x,y)
        matches=[v for v in vias if abs(v.GetPosition().x-center.x)<=p.FromMM(EPS_MM)
                 and abs(v.GetPosition().y-center.y)<=p.FromMM(EPS_MM)]
        require(len(matches)==1,f'Missing/duplicate required GND stitch at {x},{y}')
        via=matches[0]
        require(via.GetNetname()=='GND',f'Ground stitch at {x},{y} has wrong net')
        require(abs(p.ToMM(via.GetWidth(p.F_Cu))-1.0)<EPS_MM and abs(p.ToMM(via.GetDrill())-.4)<EPS_MM,
                f'Ground stitch at {x},{y} must be 1.0/0.4 mm')
        polygons=[]
        for layer in LAYERS:
            indices=[i for i in range(ground[layer].OutlineCount()) if ground[layer].Contains(center,i)]
            require(via.IsOnLayer(layer) and len(indices)==1,
                    f'Ground stitch at {x},{y} does not join a filled {layer_name(layer)} ground polygon')
            polygons.append({'layer':layer_name(layer),'polygon_index':indices[0]})
        for ref,pad in paste_pads:
            box=pad.GetBoundingBox();box.Inflate(p.FromMM(.7))
            require(not box.Contains(center),f'Ground stitch at {x},{y} enters the expanded paste-pad box of {ref}')
        result.append({'center_mm':[x,y],'net':'GND','diameter_mm':1.0,'drill_mm':.4,
                       'connected_polygons':polygons,'outside_paste_pad_boxes_plus_0_7mm':True})
    return result


def verify(path):
    board = p.LoadBoard(str(path))
    fps = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        require(ref not in fps, 'Duplicate footprint reference ' + ref)
        fps[ref] = fp
    expected_nets = {pin: pcb_net_name(net) for net, pins in spec.NETS.items() for pin in pins}

    def pad(ref, number):
        require(ref in fps, 'Missing footprint ' + ref)
        matches = [item for item in fps[ref].Pads() if item.GetNumber() == number]
        require(len(matches) == 1, f'Expected exactly one {ref}.{number} pad')
        require(matches[0].GetNetname() == expected_nets[ref + '.' + number],
                f'{ref}.{number}: incorrect net')
        return matches[0]

    zones = list(board.Zones())
    require(zones and all(zone.IsFilled() for zone in zones), 'Fill all zones before checking')
    filled = [(zone, zone.GetFilledPolysList(zone.GetLayer())) for zone in zones]
    for zone, polygon in filled:
        require(zone.GetLayer() in LAYERS and polygon.OutlineCount() >= 1,
                f'{zone.GetNetname()}: empty/disconnected or unsupported filled zone')
    ground = {}
    for layer in LAYERS:
        matches = [(zone, polygon) for zone, polygon in filled
                   if zone.GetNetname() == 'GND' and zone.GetLayer() == layer]
        require(len(matches) == 1, f'Expected one connected GND pour on {layer_name(layer)}')
        ground[layer] = matches[0][1]

    # Header annuli may form separate polygons on one layer. Prove their
    # interlayer connection through GND plated pads/vias to the main pours;
    # a disconnected polygon cannot pass merely because its net is named GND.
    ground_nodes = {(layer,i) for layer,poly in ground.items() for i in range(poly.OutlineCount())}
    ground_graph = collections.defaultdict(set)
    plated = [pad for fp in fps.values() for pad in fp.Pads()
              if pad.GetAttribute() == p.PAD_ATTRIB_PTH and pad.GetNetname() == 'GND']
    plated += [via for via in board.GetTracks() if isinstance(via,p.PCB_VIA) and via.GetNetname() == 'GND']
    for terminal in plated:
        pos=terminal.GetPosition()
        nodes=[(layer,i) for layer,poly in ground.items() for i in range(poly.OutlineCount())
               if terminal.IsOnLayer(layer) and poly.Contains(pos,i)]
        for a in nodes:
            ground_graph[a].update(nodes)
    start=(p.F_Cu,max(range(ground[p.F_Cu].OutlineCount()), key=lambda i:ground[p.F_Cu].COutline(i).Area()))
    connected,todo={start},[start]
    while todo:
        for node in ground_graph[todo.pop()] - connected:
            connected.add(node);todo.append(node)
    require(connected == ground_nodes,'Ground polygon lacks a plated connection to the common return plane')
    stitches = verify_ground_stitches(board,ground,GROUND_STITCHES)
    thermal, area_records = [], []
    via_items = [item for item in board.GetTracks() if isinstance(item, p.PCB_VIA)]
    for ref in ('U4', 'U6', 'U7', 'U8'):
        tab = pad(ref, '6')
        require(tab.GetLocalZoneConnection() == p.ZONE_CONNECTION_FULL,
                f'{ref}: power tab must connect fully to its pour')
        cx, cy = mm(xy(tab.GetPosition()))
        sx, sy = mm(xy(tab.GetSize()))
        rx, ry = sx / 2 + 1.0, sy / 2 + 1.0
        centers = [(cx + sign * rx, cy + delta) for sign in (-1, 1) for delta in (-3, 0, 3)]
        centers += [(cx + delta, cy + sign * ry) for sign in (-1, 1) for delta in (-2.5, 0, 2.5)]
        matching = {}
        for layer in LAYERS:
            matches = [(zone, poly) for zone, poly in filled
                       if zone.GetLayer() == layer and zone.GetNetname() == tab.GetNetname()
                       and poly.Contains(tab.GetPosition())]
            require(len(matches) == 1, f'{ref}: tab not inside its filled pour on {layer_name(layer)}')
            require(matches[0][0].GetPadConnection() == p.ZONE_CONNECTION_FULL,
                    f'{ref}: thermal pour must use full copper connections')
            polygon = matches[0][1]
            indices = [i for i in range(polygon.OutlineCount()) if polygon.Contains(tab.GetPosition(),i)]
            require(len(indices)==1,f'{ref}: ambiguous tab copper polygon')
            matching[layer] = polygon.UnitSet(indices[0])
            if ref in ('U4', 'U8'):
                area_records.append({'regulator': ref, 'layer': layer_name(layer),
                                     'net': tab.GetNetname(), 'filled_zone_area_mm2': matching[layer].Area() / 1e12,
                                     'excluded_other_polygons_mm2':(polygon.Area()-matching[layer].Area())/1e12})
        for x, y in centers:
            position = point(x, y)
            found = [via for via in via_items
                     if abs(via.GetPosition().x - position.x) <= p.FromMM(EPS_MM)
                     and abs(via.GetPosition().y - position.y) <= p.FromMM(EPS_MM)]
            require(len(found) == 1, f'{ref}: missing/duplicate thermal via at {x},{y}')
            via = found[0]
            require(via.GetNetname() == tab.GetNetname(), f'{ref}: wrong thermal-via net')
            require(abs(p.ToMM(via.GetWidth(p.F_Cu)) - 1.0) < EPS_MM
                    and abs(p.ToMM(via.GetDrill()) - .4) < EPS_MM,
                    f'{ref}: thermal via must be 1.0/0.4 mm')
            for layer in LAYERS:
                require(via.IsOnLayer(layer) and matching[layer].Contains(position),
                        f'{ref}: thermal via disconnected from {layer_name(layer)} pour')
        thermal.append({'regulator': ref, 'tab_net': tab.GetNetname(), 'thermal_vias': len(centers),
                        'tab_and_vias_in_connected_pours_both_layers': True})
    output = []
    for ref, cap, cap_pin, fuse in [('U6', 'C40', '1', 'PTC1'), ('U7', 'C41', '1', 'PTC2'), ('U8', 'C42', '2', 'PTC3')]:
        result = main_path(board, pad(ref, '5' if ref == 'U8' else '4'), pad(cap, cap_pin), pad(fuse, '1'))
        output.append({'regulator': ref, 'capacitor': cap, 'ptc': fuse, **result})
    terminal_paths=[]
    for fuse,tvs,tvs_pin,terminal,terminal_pin in [('PTC1','TVS1','1','J7','2'),('PTC2','TVS2','1','J7','1'),('PTC3','TVS3','2','J6','2')]:
        result=main_path(board,pad(fuse,'2'),pad(tvs,tvs_pin),pad(terminal,terminal_pin))
        terminal_paths.append({'ptc':fuse,'terminal':terminal+'.'+terminal_pin,**result})
    for layer,polygon in ground.items():
        require(polygon.Contains(pad('J6','1').GetPosition()),'Screw-terminal ground pad must join both filled ground planes')
    samples = ground_width_screen(ground[p.B_Cu],GROUND_CORRIDOR)
    return {'board': 'board-b', 'pcb_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'terminal_load_paths':terminal_paths,'terminal_ground_both_planes':'PASS',
            'status': 'PASS', 'thermal_connections': thermal, 'negative_filled_zone_areas': area_records,
            'ground_filled_zone_areas_mm2': {layer_name(layer): poly.Area() / 1e12 for layer, poly in ground.items()},
            'output_power_paths': output, 'ground_polygons_connected_through_plated_terminals':len(connected),
            'required_ground_stitches':stitches,'back_ground_segmented_samples':samples,'ground_sample_policy':GROUND_CORRIDOR,
            'assumptions': ['Thermal-via centers follow the current tab perimeter plus 1 mm placement rule.',
                            'Thermal area counts only the filled polygon containing the tab; other polygons and separate tracks/pads are excluded. Area is not thetaJA.',
                            'Copper area and connected vias do not qualify continuous current or temperature.',
                            'Power-path checks exclude zones and all traces below 1 mm; narrow sensing branches cannot satisfy them.',
                            f'Ground screen uses {GROUND_CORRIDOR} with 0.5 mm samples. Aggregate width adds separate runs across globally connected polygons; it is not a continuous corridor, current-density proof or current rating.',
                            'All seven ground stitches must join front/back filled ground and remain outside every paste-bearing copper-pad bounding box expanded by 0.7 mm; this conservatively keeps their holes away from solder paste.',
                            'Native DRC, schematic identity, manufacturing checks and electrical bench qualification remain separate.']}


def self_test(path):
    """Positive current board plus independent failures; never save a mutated board."""
    positive=verify(path)
    cases=[]
    def rejects(name,call,reason):
        try:call()
        except ValueError as error:
            require(reason in str(error),f'{name}: failed for an unintended reason: {error}')
            cases.append(name)
        else:raise AssertionError('Negative control accepted: '+name)
    def fixture():
        board=p.LoadBoard(str(path))
        ground={layer:next(z.GetFilledPolysList(layer) for z in board.Zones()
                          if z.GetLayer()==layer and z.GetNetname()=='GND') for layer in LAYERS}
        return board,ground
    def stitch(board):
        center=point(*GROUND_STITCHES[-1])
        return next(v for v in board.GetTracks() if isinstance(v,p.PCB_VIA) and xy(v.GetPosition())==xy(center))
    board,ground=fixture(); omitted=stitch(board); tracks=[v for v in board.GetTracks() if v!=omitted]
    class FilteredBoard:
        def GetTracks(self):return tracks
        def GetFootprints(self):return board.GetFootprints()
    rejects('missing new ground stitch',lambda:verify_ground_stitches(FilteredBoard(),ground,GROUND_STITCHES),'Missing/duplicate')
    board,ground=fixture();stitch(board).SetNet(board.FindNet('ATT'))
    rejects('wrong ground stitch net',lambda:verify_ground_stitches(board,ground,GROUND_STITCHES),'wrong net')
    board,ground=fixture();stitch(board).SetDrill(p.FromMM(.3))
    rejects('wrong ground stitch drill',lambda:verify_ground_stitches(board,ground,GROUND_STITCHES),'1.0/0.4')
    # This rejected design candidate lies inside ground copper but beside L3's
    # paste aperture; connectivity alone must not allow the stitching via.
    board,ground=fixture();via=p.PCB_VIA(board);via.SetPosition(point(52,62));via.SetWidth(p.FromMM(1));via.SetDrill(p.FromMM(.4))
    via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(board.FindNet('GND'));board.Add(via)
    centers=[*GROUND_STITCHES[:-1],(52,62)]
    rejects('ground stitch overlaps paste-pad keepout',lambda:verify_ground_stitches(board,ground,centers),'expanded paste-pad box')
    def polygons(intervals):
        shape=p.SHAPE_POLY_SET()
        for left,right in intervals:
            shape.NewOutline()
            # Put grid samples strictly inside the synthetic polygons so the
            # tests do not depend on KiCad's boundary-containment convention.
            for x,y in [(left-.01,50),(right+.01,50),(right+.01,70),(left-.01,70)]:shape.Append(p.FromMM(x),p.FromMM(y))
        return shape
    policy={**GROUND_CORRIDOR,'x_start':0,'x_end':30}
    ground_width_screen(polygons([(0,10),(12,22)]),policy)
    rejects('aggregate width below 20 mm with a sufficient single run',
            lambda:ground_width_screen(polygons([(0,19)]),policy),'aggregate sampled width')
    rejects('largest run below 10 mm despite sufficient aggregate width',
            lambda:ground_width_screen(polygons([(0,8),(9,17),(18,26)]),policy),'largest sampled run')
    board,ground=fixture()
    pads={f.GetReference()+'.'+pad.GetNumber():pad for f in board.GetFootprints() for pad in f.Pads()}
    pads['J6.2'].SetAttribute(p.PAD_ATTRIB_NPTH)
    pads['J6.2'].SetNet(board.FindNet('-12V rail'))
    rejects('unplated terminal cannot bridge copper layers',
            lambda:main_path(board,pads['PTC3.2'],pads['TVS3.2'],pads['J6.2']),'No complete >=1 mm')
    require(hashlib.sha256(path.read_bytes()).hexdigest()==positive['pcb_sha256'],'Source PCB changed during self-test')
    return {'status':'PASS','pcb_sha256':positive['pcb_sha256'],'positive_cases':2,'negative_controls':cases,
            'pcb_and_project_files_not_written':True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', type=Path)
    parser.add_argument('--output', type=Path, help='Write the check report as JSON')
    parser.add_argument('--self-test',action='store_true',help='Check the supplied board, then exercise ground-screen negative controls without saving it')
    args = parser.parse_args()
    result = self_test(args.pcb.resolve()) if args.self_test else verify(args.pcb.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
