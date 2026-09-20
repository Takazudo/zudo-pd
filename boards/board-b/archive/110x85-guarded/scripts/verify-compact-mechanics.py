#!/usr/bin/env python3
"""Verify the compact Board B Faston and top-edge pogo mechanics, without saving it.

Run with KiCad's Python. Import verify_compact_mechanics() to reuse the checks.
The outline follows the current notched board_b_layout contract. A temporary PCB can explicitly name its
intended project directory with --project-dir for ${KIPRJMOD} model resolution.
The check covers the bare terminals and pogo contact area, not the unspecified
female Faston housings or the complete programming clip.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import wx
_KICAD_APP = wx.GetApp() or wx.App(False)
import pcbnew as p
from board_b_layout import WIDTH, HEIGHT, P1_CENTER, edge_primitives
from pcb_common import pcb_net_name

ROOT = Path(__file__).resolve().parents[2]
FASTON_NETS = {'J6': '-12V rail', 'J9': 'GND', 'J7': '+12V rail', 'J8': '+5V rail'}
POGO_NETS = {'1': 'ATT', '2': 'PDOK', '3': 'GND', '4': None}
RAIL_CONTACTS = {'TP3': '+13.44V PRE', 'TP4': '+6.519V PRE', 'TP5': '-14.145V PRE'}
CONTRACT_PATH = ROOT / '3dp-files/faston-cover/pcb-contract.json'
TOL = .01


def xy(item):
    q = item.GetPosition()
    return p.ToMM(q.x), p.ToMM(q.y)


def bounds(item):
    b = item.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))


def close(a, b, tol=TOL):
    return abs(a - b) <= tol


def angle(a):
    return a % 360


def outline_bounds(board):
    """Match every line and arc, including all three rounded retention notches."""
    edges = [x for x in board.GetDrawings() if x.GetLayer() == p.Edge_Cuts]
    expected = edge_primitives()
    if len(edges) != len(expected):
        raise ValueError('Edge.Cuts primitive count differs from the full rounded-notch contract')
    def pt(v): return (p.ToMM(v.x), p.ToMM(v.y))
    def same(a,b): return len(a)==len(b) and all(close(x,y,.001) for x,y in zip(a,b))
    remaining = list(edges)
    for want in expected:
        shape = p.SHAPE_T_SEGMENT if want['type']=='line' else p.SHAPE_T_ARC
        matches = [e for e in remaining if e.GetShape()==shape
                   and ((same(pt(e.GetStart()),want['start']) and same(pt(e.GetEnd()),want['end']))
                        or (same(pt(e.GetStart()),want['end']) and same(pt(e.GetEnd()),want['start'])))
                   and (want['type']=='line' or same(pt(e.GetArcMid()),want['mid']))]
        if len(matches)!=1:
            raise ValueError('Missing, duplicate or changed Edge.Cuts primitive: '+str(want))
        remaining.remove(matches[0])
    return 0., 0., float(WIDTH), float(HEIGHT)


@lru_cache(maxsize=8)
def model_points(path):
    """The retained EasyEDA WRL uses KiCad's 0.1-inch model coordinate unit."""
    text = Path(path).read_text()
    result = []
    for block in re.findall(r'point\s*\[([^]]+)\]', text):
        nums = [float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?', block)]
        if len(nums) % 3:
            raise ValueError('Malformed WRL coordinate triplets')
        result.extend(tuple(nums[i + k] * 2.54 for k in range(3)) for i in range(0, len(nums), 3))
    if not result:
        raise ValueError('No coordinates in the Faston model')
    return result


def model_local_points(fp, project_dir):
    models = list(fp.Models())
    if len(models) != 1:
        raise ValueError('Faston must carry one reviewed model')
    m = models[0]
    if not (close(m.m_Rotation.x, 0) and close(m.m_Rotation.y, 0)
            and close(angle(m.m_Rotation.z), 90)):
        raise ValueError('Faston model must rotate Z=90 degrees; X/Y=0')
    if any(not close(v, 0) for v in (m.m_Offset.x, m.m_Offset.y, m.m_Offset.z)):
        raise ValueError('Faston model offset must be zero; the old Y=-7 mm shift is incorrect')
    if any(not close(v, 1) for v in (m.m_Scale.x, m.m_Scale.y, m.m_Scale.z)):
        raise ValueError('Faston model scale must be 1')
    raw_path = str(m.m_Filename).replace('${KIPRJMOD}', str(project_dir))
    path = Path(os.path.expandvars(raw_path))
    if not path.is_absolute():
        path = project_dir / path
    path = path.resolve()
    if path.name != 'CONN-TH_63951-1.wrl' or not path.is_file():
        raise ValueError('Faston reviewed WRL cannot be resolved: ' + str(path))
    # KiCad applies negative model Z rotation in its right-handed 3D world;
    # PCB local Y points down. For reviewed Z=90 this becomes (rawY, rawX, Z).
    local = [(v[1], v[0], v[2]) for v in model_points(str(path))]
    lim = [(min(v[k] for v in local), max(v[k] for v in local)) for k in range(3)]
    if not (close(lim[1][1] - lim[1][0], 20.32, .05)
            and close(lim[0][1] - lim[0][0], .81, .05)
            and close(lim[2][1], 8.89, .05) and close(lim[2][0], -3.81, .05)):
        raise ValueError('Faston model dimensions differ from the reviewed TE drawing')
    for sign, target in [(-1, -2.54), (1, 2.54)]:
        leg = [v for v in local if v[2] < -1.6 and v[1] * sign > 0]
        cx = (min(v[0] for v in leg) + max(v[0] for v in leg)) / 2
        cy = (min(v[1] for v in leg) + max(v[1] for v in leg)) / 2
        if not (close(cx, 0, .1) and close(cy, target, .1)):
            raise ValueError('Faston model solder leg does not align with its PCB hole')
    return local, str(path)


def verify_compact_mechanics(board, pcb_path, width=WIDTH, height=HEIGHT,
                             project_dir=None, copper_edge=.30, pogo_setback=1.80):
    """Return a JSON-ready report. No board, footprint or project is modified."""
    pcb_path = Path(pcb_path).resolve()
    project_dir = Path(project_dir).resolve() if project_dir else pcb_path.parent
    contract = json.loads(CONTRACT_PATH.read_text())
    errors, terminals = [], []
    try:
        x0, y0, x1, y1 = outline_bounds(board)
    except ValueError as e:
        return {'status': 'FAIL', 'errors': [str(e)]}
    if not (close(x1 - x0, width) and close(y1 - y0, height)):
        errors.append(f'Outline is {x1-x0:.3f} x {y1-y0:.3f}, expected {width} x {height} mm')
    if contract['world']['pcb_size_mm'] != [width,height]:
        errors.append('Cover contract and board dimensions differ')
    terminal_centers = {item['reference']:item['center_mm'] for item in contract['fastons']['placements']}
    if (contract['fastons']['layer']!='B.Cu' or contract['fastons']['orientation_deg']!=270
            or contract['fastons']['mating_direction_pcb']!=[1,0]
            or contract['fastons']['model_rotation_xyz_deg']!=[0,0,90]
            or contract['fastons']['model_offset_xyz_mm']!=[0,0,0]
            or set(terminal_centers)!=set(FASTON_NETS) or len(contract['fastons']['placements'])!=4):
        errors.append('Cover contract differs from the reviewed four inward bottom terminals')
    fps = {}
    for f in board.GetFootprints():
        if f.GetReference() in fps:
            errors.append('Duplicate footprint reference ' + f.GetReference())
        fps[f.GetReference()] = f
    for ref, net in FASTON_NETS.items():
        try:
            f = fps[ref]
            if f.GetLayer() != p.B_Cu or not close(angle(f.GetOrientationDegrees()), 270):
                raise ValueError('requires bottom-side footprint rotation 270 degrees for inward +X blade')
            if f.GetFPIDAsString().split(':')[-1] != 'CONN-TH_1217754-1':
                raise ValueError('unexpected Faston footprint')
            pads = {q.GetNumber(): q for q in f.Pads()}
            if set(pads) != {'1', '2'}:
                raise ValueError('expected exactly pads 1 and 2')
            fx, fy = xy(f)
            if not all(close(a,b) for a,b in zip((fx,fy),terminal_centers[ref])):
                raise ValueError('Faston origin differs from the cover contract')
            margins = []
            for num, dx in [('1', -2.54), ('2', 2.54)]:
                q = pads[num]; px, py = xy(q)
                if not (close(px, fx + dx) and close(py, fy) and q.GetNetname() == net):
                    raise ValueError('pad ' + num + ' position or rail net is wrong')
                if q.GetAttribute() != p.PAD_ATTRIB_PTH:
                    raise ValueError('Faston solder legs must use plated through-holes')
                if not all(close(p.ToMM(v), expected) for v, expected in [
                        (q.GetSize().x, 2.2), (q.GetSize().y, 2.2),
                        (q.GetDrillSize().x, 1.4), (q.GetDrillSize().y, 1.4)]):
                    raise ValueError('pad or drill differs from reviewed 2.2/1.4 mm geometry')
                clearance = min(px - 1.1 - x0, x1 - px - 1.1, py - 1.1 - y0, y1 - py - 1.1)
                for notch in contract['notch_geometry']['notches']:
                    cy=notch['center_y_mm']; half=contract['notch_geometry']['pocket_width_mm']/2
                    dx=max(px-1.1-contract['notch_geometry']['total_depth_mm'],0)
                    dy=max(cy-half-(py+1.1),(py-1.1)-(cy+half),0)
                    clearance=min(clearance,math.hypot(dx,dy))
                if clearance < copper_edge - TOL:
                    raise ValueError(f'pad {num} copper-to-edge {clearance:.3f} mm is below {copper_edge:.3f}')
                margins.append(clearance)
            local, model = model_local_points(f, project_dir)
            # Bottom-side flip plus 270 degrees maps local +Y to board +X.
            world = [(fx+v[1], fy+v[0]) for v in local]
            metal = [min(v[0] for v in world),min(v[1] for v in world),
                     max(v[0] for v in world),max(v[1] for v in world)]
            if metal[0]<x0-TOL or metal[1]<y0-TOL or metal[2]>x1+TOL or metal[3]>y1+TOL:
                raise ValueError('Faston metal overhangs the board envelope')
            # A conservative rectangle around each full notch also contains its arcs.
            for notch in contract['notch_geometry']['notches']:
                cy=notch['center_y_mm']; half=contract['notch_geometry']['pocket_width_mm']/2
                if metal[0]<contract['notch_geometry']['total_depth_mm'] and metal[1]<cy+half and metal[3]>cy-half:
                    raise ValueError('Faston metal overlaps a retention-notch envelope')
            blade_tip_x = metal[2]
            shoulder_x = blade_tip_x - 7.92
            terminals.append({'reference': ref, 'origin_mm': [fx, fy], 'rotation_deg': 270,
                              'layer':'B.Cu','mating_direction_pcb':[1,0], 'metal_xy_bounds_mm':metal,
                              'rail': net, 'blade_tip_x_mm': blade_tip_x,
                              'mating_shoulder_x_mm': shoulder_x,
                              'minimum_pad_edge_clearance_mm': min(margins), 'model': model})
        except (KeyError, ValueError, OSError) as e:
            errors.append(ref + ': ' + str(e))
    # Bare-terminal pad clearance, not a claim about an unspecified cable receptacle.
    for a, b in zip(sorted(terminals, key=lambda t:t['origin_mm'][1]),
                    sorted(terminals, key=lambda t:t['origin_mm'][1])[1:]):
        gap = b['origin_mm'][1] - a['origin_mm'][1] - 2.2
        if gap < copper_edge - TOL:
            errors.append(f'{a["reference"]}/{b["reference"]}: transverse pad gap {gap:.3f} mm too small')
    pogo = {}
    try:
        f = fps['P1']; fx, fy = xy(f)
        if f.GetFPIDAsString().split(':')[-1] != 'PogoEdge_BoardB_1x04_P2.54mm':
            raise ValueError('P1 must use the dedicated Board B edge-contact footprint')
        if not all(close(a,b) for a,b in zip((fx,fy),P1_CENTER)):
            raise ValueError('P1 origin differs from the seven-contact jig contract')
        if f.GetLayer() != p.F_Cu or not close(angle(f.GetOrientationDegrees()), 0):
            raise ValueError('top-edge pogo row requires front-side rotation 0 degrees')
        if not close(fy - y0, pogo_setback):
            raise ValueError(f'pad-center setback {fy-y0:.3f} mm differs from jig value {pogo_setback:.3f}')
        pads = {q.GetNumber(): q for q in f.Pads()}
        if len(list(f.Pads())) != 4 or set(pads) != {'1', '2', '3', '4'}:
            raise ValueError('P1 must contain exactly four pads')
        for i, dx in enumerate([-3.81, -1.27, 1.27, 3.81], 1):
            q = pads[str(i)]; px, py = xy(q); want = POGO_NETS[str(i)]
            net_ok = q.GetNetname() == want if want else q.GetNetCode() == 0 or q.GetNetname().startswith('unconnected-')
            if not (close(px, fx + dx) and close(py, fy) and net_ok):
                raise ValueError(f'pad {i} order, pitch, position or net is wrong')
            if not (close(p.ToMM(q.GetSize().x), 1.5) and close(p.ToMM(q.GetSize().y), 2.5)
                    and close(angle(q.GetOrientationDegrees()), 0)):
                raise ValueError(f'pad {i} must be 1.5 x 2.5 mm at zero rotation')
            layers = q.GetLayerSet()
            if not (layers.Contains(p.F_Cu) and layers.Contains(p.F_Mask)) or any(
                    layers.Contains(layer) for layer in [p.F_Paste, p.B_Paste, p.B_Cu]):
                raise ValueError(f'pad {i} must expose front copper without solder paste')
            if min(px - .75 - x0, x1 - px - .75, py - 1.25 - y0, y1 - py - 1.25) < copper_edge - TOL:
                raise ValueError(f'pad {i} violates copper-to-edge clearance')
        labels = {}
        for item in [f.Reference(), f.Value(), *list(f.GraphicalItems())]:
            if item.GetLayer() not in (p.F_SilkS, p.B_SilkS):
                continue
            if hasattr(item, 'IsVisible') and not item.IsVisible():
                continue
            left, top, right, bottom = bounds(item)
            if left < x0 - TOL or top < y0 - TOL or right > x1 + TOL or bottom > y1 + TOL:
                raise ValueError('visible P1 label/guide protrudes outside the board')
            if hasattr(item, 'GetText'):
                labels[item.GetText()] = xy(item)
        for text, dx in [('ATT', -3.81), ('PDOK', -1.27), ('GND', 1.27), ('NC', 3.81)]:
            if text not in labels or not close(labels[text][0], fx + dx, .3) or labels[text][1] <= fy + 1.25:
                raise ValueError('missing/misplaced per-pad label ' + text)
        if any(t in labels for t in ['SCL', 'SDA', 'RESET', '<-- EDGE']):
            raise ValueError('P1 retains misleading programming labels or edge guide')
        for i,(ref,rail) in enumerate(RAIL_CONTACTS.items()):
            contact=fps[ref]; qs=list(contact.Pads()); target=(fx+6.35+i*2.54,fy)
            if contact.GetFPIDAsString().split(':')[-1]!='PogoEdge_1x01_1.5x2.5mm' or len(qs)!=1 or qs[0].GetNumber()!='1':
                raise ValueError(ref+': wrong single-contact footprint')
            q=qs[0]
            if contact.GetLayer()!=p.F_Cu or not close(angle(contact.GetOrientationDegrees()),0) or not all(close(a,b) for a,b in zip(xy(q),target)):
                raise ValueError(ref+': wrong edge setback, order or 2.54 mm pitch')
            if q.GetNetname()!=pcb_net_name('/DC-DC Conversion/'+rail):
                raise ValueError(ref+': incorrect intermediate rail')
            if not (close(p.ToMM(q.GetSize().x),1.5) and close(p.ToMM(q.GetSize().y),2.5) and close(angle(q.GetOrientationDegrees()),0)):
                raise ValueError(ref+': incorrect pogo contact dimensions')
            if q.GetAttribute()!=p.PAD_ATTRIB_SMD or q.GetShape()!=p.PAD_SHAPE_RECT or set(q.GetLayerSet().Seq())!={p.F_Cu,p.F_Mask}:
                raise ValueError(ref+': must be rectangular front copper/mask only, no paste')
            if not contact.Reference().IsVisible() or contact.Reference().GetText()!=ref or xy(contact.Reference())[1]<=fy+1.25:
                raise ValueError(ref+': missing inward reference label')
        for ref in ('P1',*RAIL_CONTACTS):
            contact=fps[ref]; attrs=contact.GetAttributes()
            lcsc=contact.GetField('LCSC')
            if not attrs&p.FP_EXCLUDE_FROM_BOM or not attrs&p.FP_EXCLUDE_FROM_POS_FILES or list(contact.Models()) or (lcsc and lcsc.GetText()):
                raise ValueError(ref+': bare contacts must have no model/orderable/BOM/CPL entry')
            for q in contact.Pads():
                if q.GetAttribute()!=p.PAD_ATTRIB_SMD or q.GetShape()!=p.PAD_SHAPE_RECT or set(q.GetLayerSet().Seq())!={p.F_Cu,p.F_Mask}:
                    raise ValueError(ref+': bare pad must expose only front copper and mask')
        pogo = {'origin_mm': [fx, fy], 'rotation_deg': 0, 'pad_count': 4,
                'pitch_mm': 2.54, 'center_to_top_edge_mm': fy-y0,
                'copper_to_top_edge_mm': fy-y0-1.25,
                'left_to_right': ['ATT', 'PDOK', 'GND', 'NC', '+13.44V', '+6.519V', '-14.145V'],
                'total_contact_count':7,'shared_return':'P1.3','bom_cpl_excluded':True,'solder_paste': False}
    except (KeyError, ValueError) as e:
        errors.append('P1: ' + str(e))
    return {'status': 'FAIL' if errors else 'PASS', 'outline_mm': [x0,y0,x1,y1],
            'cover_contract_sha256':hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
            'full_notched_outline':'PASS',
            'fastons': terminals, 'pogo': pogo, 'errors': errors,
            'qualification_limits': ['Female Faston receptacle/housing envelope is not specified.',
                                     'Pad-edge clearances use conservative bounding boxes around copper and complete rounded-notch envelopes.',
                                     'Actual programming clip fit and repeated insertion force remain unmeasured.']}


def self_test():
    import importlib.util
    modspec=importlib.util.spec_from_file_location('board_check',ROOT/'scripts/pcb/verify-board-b.py')
    pdcheck=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(pdcheck)
    def point(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
    def fixture():
        b=p.BOARD();nets={}
        for name in [*FASTON_NETS.values(),'ATT','PDOK',*[pcb_net_name('/DC-DC Conversion/'+v) for v in RAIL_CONTACTS.values()]]:
            if name not in nets:
                n=p.NETINFO_ITEM(b,name,len(nets)+1);b.Add(n);nets[name]=n
        def footprint(ref,name,position,rotation=0,bottom=False):
            f=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),name);b.Add(f)
            f.SetFPID(p.LIB_ID('zudo-pd',name));f.SetReference(ref);f.SetPosition(point(*position));f.SetOrientationDegrees(rotation)
            if bottom:f.Flip(f.GetPosition(),False)
            f.Reference().SetPosition(point(position[0],7 if ref=='P1' else position[1]+2.7))
            f.Value().SetVisible(False)
            return f
        contract=json.loads(CONTRACT_PATH.read_text())
        for item in contract['fastons']['placements']:
            f=footprint(item['reference'],'CONN-TH_1217754-1',item['center_mm'],270,True)
            for q in f.Pads():q.SetNet(nets[FASTON_NETS[item['reference']]])
        f=footprint('P1','PogoEdge_BoardB_1x04_P2.54mm',P1_CENTER)
        for q in f.Pads():
            if POGO_NETS[q.GetNumber()]:q.SetNet(nets[POGO_NETS[q.GetNumber()]])
        for i,(ref,rail) in enumerate(RAIL_CONTACTS.items()):
            f=footprint(ref,'PogoEdge_1x01_1.5x2.5mm',(P1_CENTER[0]+6.35+i*2.54,P1_CENTER[1]))
            next(iter(f.Pads())).SetNet(nets[pcb_net_name('/DC-DC Conversion/'+rail)])
        mechanical=json.loads((ROOT/'boards/board-p/mechanical.json').read_text())
        centers=[item['center'] for item in mechanical['interface']['pads']]
        from board_b_layout import pd_to_board_b
        center=(sum(v[0] for v in centers)/6,sum(v[1] for v in centers)/6)
        footprint('J5','HDR-TH_6P-P2.54-V-F',pd_to_board_b(center),90,True)
        for i,hole in enumerate(mechanical['mounting_holes'],1):
            footprint('H'+str(i),'MountingHole_M3',pd_to_board_b(hole['center']))
        for item in edge_primitives():
            e=p.PCB_SHAPE();e.SetLayer(p.Edge_Cuts)
            if item['type']=='arc':
                e.SetShape(p.SHAPE_T_ARC);e.SetArcGeometry(point(*item['start']),point(*item['mid']),point(*item['end']))
            else:
                e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(point(*item['start']));e.SetEnd(point(*item['end']))
            b.Add(e)
        return b
    def verify(b):return verify_compact_mechanics(b,ROOT/'boards/board-b/board-b.kicad_pcb')
    b=fixture();r=verify(b)
    if r['status']!='PASS':raise AssertionError(r)
    pdcheck.verify_pd_mating({f.GetReference():f for f in b.GetFootprints()})
    def wrong_model(b,offset=False):
        models=b.FindFootprintByReference('J6').Models();m=models[0]
        if offset:m.m_Offset.y=-7
        else:m.m_Rotation.z=0
        models.clear();models.push_back(m)
    def remove_cut(b):
        next(e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts and e.GetShape()==p.SHAPE_T_ARC).SetLayer(p.Dwgs_User)
    def wrong_arc(b):
        e=next(e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts and e.GetShape()==p.SHAPE_T_ARC)
        mid=e.GetArcMid();mid.x+=p.FromMM(.1);e.SetArcGeometry(e.GetStart(),mid,e.GetEnd())
    def wrong_paste(b):
        q=next(iter(b.FindFootprintByReference('TP3').Pads()));layers=q.GetLayerSet();layers.AddLayer(p.F_Paste);q.SetLayerSet(layers)
    cases=[('wrong model rotation',lambda b:wrong_model(b)),
           ('old model offset',lambda b:wrong_model(b,True)),
           ('wrong Faston direction',lambda b:b.FindFootprintByReference('J6').SetOrientationDegrees(90)),
           ('Faston overhang',lambda b:b.FindFootprintByReference('J6').SetPosition(point(-1,37))),
           ('wrong Faston side',lambda b:b.FindFootprintByReference('J6').Flip(point(6,37),False)),
           ('interior pogo row',lambda b:b.FindFootprintByReference('P1').SetPosition(point(40,10))),
           ('wrong rail pogo edge',lambda b:b.FindFootprintByReference('TP3').SetPosition(point(46.35,3))),
           ('wrong rail pogo order',lambda b:b.FindFootprintByReference('TP4').SetPosition(point(51.43,1.8))),
           ('rail pogo paste',wrong_paste),
           ('rail pogo BOM enabled',lambda b:b.FindFootprintByReference('TP5').SetAttributes(p.FP_SMD)),
           ('removed notch arc',remove_cut),('altered notch arc',wrong_arc),
           ('extruding pogo reference',lambda b:b.FindFootprintByReference('P1').Reference().SetPosition(point(40,-2))),
           ('wrong pogo label',lambda b:next(x for x in b.FindFootprintByReference('P1').GraphicalItems() if hasattr(x,'GetText') and x.GetText()=='ATT').SetText('SCL'))]
    for label,mutate in cases:
        b=fixture();mutate(b)
        if verify(b)['status']!='FAIL':raise AssertionError('Negative control accepted: '+label)
    pd_cases=[('wrong PD rotation',lambda b:b.FindFootprintByReference('J5').SetOrientationDegrees(0)),
              ('wrong PD hole transform',lambda b:b.FindFootprintByReference('H3').SetPosition(point(12.8,32.6)))]
    for label,mutate in pd_cases:
        b=fixture();mutate(b)
        try:pdcheck.verify_pd_mating({f.GetReference():f for f in b.GetFootprints()})
        except ValueError:pass
        else:raise AssertionError('Negative control accepted: '+label)
    return {'status':'PASS','self_tests':1+len(cases)+len(pd_cases),'negative_controls':[x[0] for x in cases+pd_cases]}


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('pcb',nargs='?',type=Path)
    a.add_argument('--width',type=float,default=WIDTH);a.add_argument('--height',type=float,default=HEIGHT)
    a.add_argument('--project-dir',type=Path);a.add_argument('--output',type=Path);a.add_argument('--self-test',action='store_true')
    args=a.parse_args()
    if args.self_test:r=self_test()
    elif args.pcb:r=verify_compact_mechanics(p.LoadBoard(str(args.pcb.resolve())),args.pcb,args.width,args.height,args.project_dir)
    else:a.error('pcb path required unless --self-test is used')
    text=json.dumps(r,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text,end='');return 0 if r['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
