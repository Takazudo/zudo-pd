#!/usr/bin/env python3
"""Verify Board B screw terminals and top-edge pogo mechanics, without saving it.

Run with KiCad's Python. Import verify_compact_mechanics() to reuse the checks.
The plain rectangular outline follows board_b_layout. A temporary PCB can name its
intended project directory with --project-dir for ${KIPRJMOD} model resolution.
The check covers the terminal models, pin assignments and pogo contacts; actual
wire, screwdriver and programming-clip fit remain unmeasured.
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
from board_b_layout import WIDTH, HEIGHT, P1_CENTER, PLACEMENTS, edge_primitives
from pcb_common import pcb_net_name

ROOT = Path(__file__).resolve().parents[2]
TERMINAL_NETS = {'J6': {'1':'GND','2':'-12V rail'}, 'J7': {'1':'+5V rail','2':'+12V rail'}}
POGO_NETS = {'1': 'ATT', '2': 'PDOK', '3': 'GND', '4': None}
RAIL_CONTACTS = {'TP3': '+13.44V PRE', 'TP4': '+6.519V PRE', 'TP5': '-14.145V PRE'}
RAIL_LABEL_PINS = {'-12V':('J6','2'),'GND':('J6','1'),'+12V':('J7','2'),'+5V':('J7','1')}
BACK_RAIL_LABELS = {
    '-12V': {'center_mm':[12.2,46.0], 'size_mm':1.5, 'thickness_mm':.3, 'bold':True},
    'GND': {'center_mm':[11.6,50.5], 'size_mm':1.5, 'thickness_mm':.3, 'bold':True},
    '+12V': {'center_mm':[12.2,58.4], 'size_mm':1.5, 'thickness_mm':.3, 'bold':True},
    '+5V': {'center_mm':[11.8,63.8], 'size_mm':1.5, 'thickness_mm':.24, 'bold':True},
}
CONTRACT_PATH = ROOT / 'boards/board-b/mechanical.json'
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
    """Match all four straight rectangle edges; reject retained notches or extra cuts."""
    edges = [x for x in board.GetDrawings() if x.GetLayer() == p.Edge_Cuts]
    expected = edge_primitives()
    corners=[(0,0),(WIDTH,0),(WIDTH,HEIGHT),(0,HEIGHT),(0,0)]
    rectangle=[{'type':'line','start':list(a),'end':list(b)} for a,b in zip(corners,corners[1:])]
    if expected!=rectangle:
        raise ValueError('Current terminal revision requires the plain rectangular layout contract')
    if len(edges) != len(expected):
        raise ValueError('Edge.Cuts must contain exactly the four rectangle edges')
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
        raise ValueError('No coordinates in the terminal model')
    return result


def model_local_points(fp, project_dir, reviewed):
    models=list(fp.Models())
    if len(models)!=1:raise ValueError('Terminal must carry one reviewed model')
    m=models[0]
    for actual,want,label in [(m.m_Rotation,reviewed['rotation_xyz_deg'],'rotation'),
                              (m.m_Offset,reviewed['offset_xyz_mm'],'offset'),
                              (m.m_Scale,reviewed['scale_xyz'],'scale')]:
        if not all(close(a,b,.001) for a,b in zip((actual.x,actual.y,actual.z),want)):
            raise ValueError('Terminal model '+label+' differs from its reviewed transform')
    # This exact model is installed without a model-node rotation or offset.
    if reviewed['rotation_xyz_deg']!=[0,0,0] or reviewed['offset_xyz_mm']!=[0,0,0] or reviewed['scale_xyz']!=[1,1,1]:
        raise ValueError('Unreviewed terminal model transform contract')
    raw_path=str(m.m_Filename).replace('${KIPRJMOD}',str(project_dir))
    path=Path(os.path.expandvars(raw_path))
    if not path.is_absolute():path=project_dir/path
    path=path.resolve()
    if path.name!=reviewed['file'] or not path.is_file():raise ValueError('Terminal model cannot be resolved: '+str(path))
    raw=model_points(str(path))
    actual=[[min(v[k] for v in raw) for k in range(3)],[max(v[k] for v in raw) for k in range(3)]]
    if any(not close(a,b,.025) for row,want in zip(actual,reviewed['raw_bounds_mm']) for a,b in zip(row,want)):
        raise ValueError('Terminal model geometry differs from the reviewed catalog asset')
    for center in (-2.54,2.54):
        leg=[v for v in raw if v[2]<-1.6 and abs(v[0]-center)<1]
        if not leg:raise ValueError('Terminal model solder leg is absent')
        xy_center=[(min(v[k] for v in leg)+max(v[k] for v in leg))/2 for k in (0,1)]
        if not (close(xy_center[0],center,.025) and close(xy_center[1],0,.025)):
            raise ValueError('Terminal model solder leg does not align with its PCB hole')
    # WRL is right-handed with Y up; footprint-local PCB Y points down.
    return [(v[0],-v[1],v[2]) for v in raw],str(path)


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
    if contract['size_mm']!=[width,height] or contract['edge_primitives']!=edge_primitives():
        errors.append('Mechanical contract differs from the rectangular board layout')
    terminal=contract['terminal_blocks']
    positions={item['reference']:item for item in terminal['placements']}
    if (terminal['layer']!='F.Cu' or terminal['orientation_deg']!=90 or terminal['entry_direction_pcb']!=[-1,0]
            or terminal['local_entry_direction']!=[0,-1] or set(positions)!=set(TERMINAL_NETS) or len(positions)!=2):
        errors.append('Mechanical contract differs from the two top-side, left-entry terminals')
    fps={}
    for f in board.GetFootprints():
        if f.GetReference() in fps:errors.append('Duplicate footprint reference '+f.GetReference())
        fps[f.GetReference()]=f
    if any(ref in fps for ref in ('J8','J9')):
        errors.append('Retired single-rail terminal footprints remain on the current board')
    support_checks=[]
    try:
        support=contract['corner_supports']
        expected_corners={'H4':[width-4,4],'H5':[4,height-4],'H6':[width-4,height-4],'H7':[4,4]}
        if support['placements']!=expected_corners or support['hole_diameter_mm']!=3.0:
            raise ValueError('four independent corner supports require 4mm edge offsets and3mm holes')
        for ref,center in expected_corners.items():
            f=fps[ref];pads=list(f.Pads());attrs=f.GetAttributes()
            if f.GetFPIDAsString()!=support['footprint'] or len(pads)!=1:
                raise ValueError(ref+': incorrect support footprint')
            q=pads[0]
            if not all(close(a,b) for a,b in zip(xy(q),center)):
                raise ValueError(ref+': independent corner position changed')
            if (q.GetAttribute()!=p.PAD_ATTRIB_NPTH or q.GetNetCode()!=0
                    or not all(close(p.ToMM(v),3.0,.001) for v in [q.GetSize().x,q.GetSize().y,q.GetDrillSize().x,q.GetDrillSize().y])):
                raise ValueError(ref+': expected netless3mm NPTH')
            if not attrs&p.FP_BOARD_ONLY or not attrs&p.FP_EXCLUDE_FROM_BOM or not attrs&p.FP_EXCLUDE_FROM_POS_FILES or list(f.Models()):
                raise ValueError(ref+': bare support hole must be board-only/BOM/CPL excluded with no invented HC11 model')
            support_checks.append({'reference':ref,'center_mm':center,'drill_mm':3.0,'independent_from_pd_mounts':True})
    except (KeyError,ValueError) as error:errors.append('Corner supports: '+str(error))
    for ref,nets in TERMINAL_NETS.items():
        try:
            f=fps[ref];fx,fy=xy(f);placement=positions[ref]
            if f.GetLayer()!=p.F_Cu or not close(angle(f.GetOrientationDegrees()),90):
                raise ValueError('requires top-side rotation 90 degrees, wire entries facing left')
            if f.GetFPIDAsString()!=terminal['footprint'] or f.GetFieldText('LCSC')!=terminal['lcsc']:
                raise ValueError('incorrect terminal footprint or C8465 identity')
            if placement['pins']!=nets:raise ValueError('terminal numbered rail contract differs')
            expected_xy=placement['center_mm']
            if not all(close(a,b) for a,b in zip((fx,fy),expected_xy)) or not all(close(a,b) for a,b in zip(PLACEMENTS[ref][:3],(*expected_xy,90))):
                raise ValueError('terminal origin or layout placement differs from mechanical contract')
            pads={q.GetNumber():q for q in f.Pads()}
            if len(list(f.Pads()))!=2 or set(pads)!={'1','2'}:raise ValueError('expected exactly two distinct contacts')
            margins=[];pins=[]
            for number,q in pads.items():
                local_x,local_y=terminal['pad_centers_local_mm'][number];px,py=xy(q)
                if not (close(px,fx+local_y) and close(py,fy-local_x) and q.GetNetname()==nets[number]):
                    raise ValueError('pad '+number+' position or assigned rail is wrong')
                if q.GetAttribute()!=p.PAD_ATTRIB_PTH:raise ValueError('terminal pins require plated through-holes')
                if not all(close(p.ToMM(v),want,.001) for v,want in [(q.GetSize().x,terminal['pad_size_mm'][0]),(q.GetSize().y,terminal['pad_size_mm'][1]),(q.GetDrillSize().x,terminal['drill_mm']),(q.GetDrillSize().y,terminal['drill_mm'])]):
                    raise ValueError('terminal pad/drill geometry differs from the reviewed project choice')
                left,top,right,bottom=bounds(q);margin=min(left-x0,x1-right,top-y0,y1-bottom)
                if margin<copper_edge-TOL:raise ValueError('terminal copper violates board-edge clearance')
                margins.append(margin);pins.append({'pin':number,'center_mm':[px,py],'rail':nets[number]})
            if not close(abs(xy(pads['2'])[1]-xy(pads['1'])[1]),5.08) or xy(pads['2'])[1]>=xy(pads['1'])[1]:
                raise ValueError('pin2 must be uppermost at 5.08 mm pitch')
            local,model=model_local_points(f,project_dir,terminal['model'])
            world=[(fx+v[1],fy-v[0]) for v in local] # model_local_points already converts CAD Y to PCB Y
            envelope=[min(v[0] for v in world),min(v[1] for v in world),max(v[0] for v in world),max(v[1] for v in world)]
            if envelope[0]<x0-TOL or envelope[1]<y0-TOL or envelope[2]>x1+TOL or envelope[3]>y1+TOL:
                raise ValueError('terminal housing model overhangs the board')
            terminals.append({'reference':ref,'origin_mm':[fx,fy],'rotation_deg':90,'layer':'F.Cu',
                              'wire_entry_direction_pcb':[-1,0],'body_xy_bounds_mm':envelope,'pins':pins,
                              'minimum_pad_edge_clearance_mm':min(margins),'model':model,
                              'maximum_tail_projection_screen_mm':terminal['maximum_tail_projection_mm']})
        except (KeyError,ValueError,OSError) as error:errors.append(ref+': '+str(error))
    if len(terminals)==2:
        rows=sorted(terminals,key=lambda item:item['origin_mm'][1])
        if rows[1]['body_xy_bounds_mm'][1]-rows[0]['body_xy_bounds_mm'][3]<copper_edge-TOL:
            errors.append('Terminal housing models overlap or leave insufficient separation')
    rail_labels=[]
    try:
        label_contract=contract['terminal_blocks']['rail_labels']
        if label_contract!={'back_labels':BACK_RAIL_LABELS,'back_rotation_deg':0,'back_mirrored':True,
                            'front_x_mm':.8,'front_size_mm':.8,'front_rotation_deg':90,'front_mirrored':False}:
            raise ValueError('unreviewed front/back rail-label contract')
        for text,(ref,pin) in RAIL_LABEL_PINS.items():
            pad=next(q for q in fps[ref].Pads() if q.GetNumber()==pin);target_y=xy(pad)[1]
            for side,layer in [('front',p.F_SilkS),('back',p.B_SilkS)]:
                labels=[v for v in board.GetDrawings() if isinstance(v,p.PCB_TEXT) and v.GetLayer()==layer and v.GetText()==text]
                if len(labels)!=1:raise ValueError(f'{side} {text}: expected exactly one board text label')
                label=labels[0];position=xy(label)
                reviewed=label_contract['back_labels'][text] if side=='back' else None
                target=reviewed['center_mm'] if reviewed else [label_contract['front_x_mm'],target_y]
                size=reviewed['size_mm'] if reviewed else label_contract['front_size_mm']
                if not all(close(a,b) for a,b in zip(position,target)):
                    raise ValueError(f'{side} {text}: reviewed label position for {ref}.{pin} differs')
                if (label.IsMirrored()!=label_contract[side+'_mirrored']
                        or not close(angle(label.GetTextAngle().AsDegrees()),label_contract[side+'_rotation_deg'])
                        or not all(close(p.ToMM(v),size) for v in [label.GetTextSize().x,label.GetTextSize().y])):
                    raise ValueError(f'{side} {text}: wrong mirror, orientation or text size')
                if reviewed and (label.IsBold()!=reviewed['bold']
                                 or not close(p.ToMM(label.GetTextThickness()),reviewed['thickness_mm'],.001)):
                    raise ValueError(f'{side} {text}: reviewed bold weight or stroke thickness differs')
                rail_labels.append({'side':side,'text':text,'pin':ref+'.'+pin,'center_mm':position,
                                    'mirrored':label.IsMirrored(),'size_mm':size,
                                    'bold':label.IsBold(),'thickness_mm':p.ToMM(label.GetTextThickness())})
    except (KeyError,ValueError,StopIteration) as error:errors.append('Rail labels: '+str(error))
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
        # A label may sit below its pad or beside an end pad; it must stay clear of the
        # pad row's copper and be nearer to its own contact than to any other of the seven.
        row = {'ATT': -3.81, 'PDOK': -1.27, 'GND': 1.27, 'NC': 3.81, **{ref: 6.35 + i * 2.54 for i, ref in enumerate(RAIL_CONTACTS)}}
        for text in ['ATT', 'PDOK', 'GND', 'NC']:
            if text not in labels:
                raise ValueError('missing/misplaced per-pad label ' + text)
            lx, ly = labels[text]
            nearest = min(row, key=lambda name: (lx - fx - row[name]) ** 2 + (ly - fy) ** 2)
            on_copper = any(abs(lx - fx - dx) < .75 and abs(ly - fy) < 1.25 for dx in row.values())
            if nearest != text or on_copper or (lx - fx - row[text]) ** 2 + (ly - fy) ** 2 > 3.0 ** 2:
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
            'mechanical_contract_sha256':hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
            'plain_rectangular_outline':'PASS',
            'terminal_blocks': terminals, 'rail_labels':rail_labels, 'corner_supports':support_checks,'pogo': pogo, 'errors': errors,
            'qualification_limits': ['Catalog terminal models are illustrations; their 3.5 mm tails are shorter than the manufacturer 4.50±0.20 mm dimension. Stack clearance uses 4.7 mm maximum tail projection.',
                                     'Actual wire, screwdriver and installed housing/stack fit remain unmeasured.',
                                     'Actual programming clip fit and repeated insertion force remain unmeasured.']}


def self_test():
    import importlib.util
    modspec=importlib.util.spec_from_file_location('board_check',ROOT/'scripts/pcb/verify-board-b.py')
    pdcheck=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(pdcheck)
    def point(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
    def fixture():
        b=p.BOARD();nets={}
        for name in [*[net for pins in TERMINAL_NETS.values() for net in pins.values()],'ATT','PDOK','+15V INPUT',*[pcb_net_name('/DC-DC Conversion/'+v) for v in RAIL_CONTACTS.values()]]:
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
        for item in contract['terminal_blocks']['placements']:
            f=footprint(item['reference'],contract['terminal_blocks']['footprint'].split(':')[1],item['center_mm'],90)
            f.SetField('LCSC','C8465')
            for q in f.Pads():q.SetNet(nets[TERMINAL_NETS[item['reference']][q.GetNumber()]])
        for text,(ref,pin) in RAIL_LABEL_PINS.items():
            pad=next(q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber()==pin)
            reviewed=BACK_RAIL_LABELS[text]
            for layer,center,size,rotation,mirror in [(p.F_SilkS,(.8,xy(pad)[1]),.8,90,False),
                                                     (p.B_SilkS,reviewed['center_mm'],reviewed['size_mm'],0,True)]:
                label=p.PCB_TEXT(b);label.SetText(text);label.SetLayer(layer);label.SetPosition(point(*center))
                label.SetTextSize(point(size,size));label.SetTextAngle(p.EDA_ANGLE(rotation,p.DEGREES_T));label.SetMirrored(mirror);b.Add(label)
                if layer==p.B_SilkS:
                    label.SetBold(reviewed['bold']);label.SetTextThickness(p.FromMM(reviewed['thickness_mm']))
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
        f=footprint('J5','HDR-TH_6P-P2.54-V-F',pd_to_board_b(center),270)
        pin_nets={'1':'+15V INPUT','2':'+15V INPUT','3':'ATT','4':'PDOK','5':'GND','6':'GND'}
        for q in f.Pads():q.SetNet(nets[pin_nets[q.GetNumber()]])
        for i,hole in enumerate(mechanical['mounting_holes'],1):
            footprint('H'+str(i),'MountingHole_M3',pd_to_board_b(hole['center']))
        for ref,center in contract['corner_supports']['placements'].items():
            footprint(ref,'MountingHole_HC11_3mm',center)
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
        else:m.m_Rotation.z=180
        models.clear();models.push_back(m)
    def remove_cut(b):
        next(e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts).SetLayer(p.Dwgs_User)
    def wrong_edge(b):
        e=next(e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts)
        end=e.GetEnd();end.x+=p.FromMM(.1);e.SetEnd(end)
    def extra_notch(b):
        e=p.PCB_SHAPE();e.SetLayer(p.Edge_Cuts);e.SetShape(p.SHAPE_T_ARC)
        e.SetArcGeometry(point(0,42),point(1,43),point(0,44));b.Add(e)
    def wrong_paste(b):
        q=next(iter(b.FindFootprintByReference('TP3').Pads()));layers=q.GetLayerSet();layers.AddLayer(p.F_Paste);q.SetLayerSet(layers)
    def back_label(b,text='-12V'):
        return next(v for v in b.GetDrawings() if isinstance(v,p.PCB_TEXT) and v.GetLayer()==p.B_SilkS and v.GetText()==text)
    cases=[('wrong model rotation',lambda b:wrong_model(b)),
           ('wrong model offset',lambda b:wrong_model(b,True)),
           ('wrong terminal direction',lambda b:b.FindFootprintByReference('J6').SetOrientationDegrees(270)),
           ('terminal overhang',lambda b:b.FindFootprintByReference('J6').SetPosition(point(-1,36))),
           ('wrong terminal side',lambda b:b.FindFootprintByReference('J6').Flip(point(7,36),False)),
           ('wrong terminal rail',lambda b:next(q for q in b.FindFootprintByReference('J6').Pads() if q.GetNumber()=='1').SetNet(b.FindNet('+12V rail'))),
           ('back rail label wrong mirror',lambda b:back_label(b).SetMirrored(False)),
           ('back rail label swapped position',lambda b:back_label(b).SetPosition(back_label(b,'GND').GetPosition())),
           ('back rail label missing',lambda b:back_label(b).SetLayer(p.Dwgs_User)),
           ('back rail label old text size',lambda b:back_label(b).SetTextSize(point(1.2,1.2))),
           ('back rail label wrong bold weight',lambda b:back_label(b).SetBold(False)),
           ('back plus5 label wrong stroke thickness',lambda b:back_label(b,'+5V').SetTextThickness(p.FromMM(.3))),
           ('front rail label missing',lambda b:next(v for v in b.GetDrawings() if isinstance(v,p.PCB_TEXT) and v.GetLayer()==p.F_SilkS and v.GetText()=='-12V').SetLayer(p.Dwgs_User)),
           ('missing independent upper-left support',lambda b:b.FindFootprintByReference('H7').SetReference('RETIRED_H7')),
           ('wrong corner offset',lambda b:b.FindFootprintByReference('H7').SetPosition(point(5,4))),
           ('wrong HC11 hole diameter',lambda b:next(iter(b.FindFootprintByReference('H7').Pads())).SetDrillSize(point(3.2,3.2))),
           ('interior pogo row',lambda b:b.FindFootprintByReference('P1').SetPosition(point(40,10))),
           ('wrong rail pogo edge',lambda b:b.FindFootprintByReference('TP3').SetPosition(point(P1_CENTER[0]+6.35,3))),
           ('wrong rail pogo order',lambda b:b.FindFootprintByReference('TP4').SetPosition(point(P1_CENTER[0]+11.43,1.8))),
           ('rail pogo paste',wrong_paste),
           ('rail pogo BOM enabled',lambda b:b.FindFootprintByReference('TP5').SetAttributes(p.FP_SMD)),
           ('missing rectangle edge',remove_cut),('altered rectangle edge',wrong_edge),('retained cover notch',extra_notch),
           ('extruding pogo reference',lambda b:b.FindFootprintByReference('P1').Reference().SetPosition(point(40,-2))),
           ('wrong pogo label',lambda b:next(x for x in b.FindFootprintByReference('P1').GraphicalItems() if hasattr(x,'GetText') and x.GetText()=='ATT').SetText('SCL'))]
    for label,mutate in cases:
        b=fixture();mutate(b)
        if verify(b)['status']!='FAIL':raise AssertionError('Negative control accepted: '+label)
    def reverse_pd_numbers(b):
        for q in b.FindFootprintByReference('J5').Pads():q.SetNumber(str(7-int(q.GetNumber())))
    pd_cases=[('wrong PD side',lambda b:b.FindFootprintByReference('J5').Flip(b.FindFootprintByReference('J5').GetPosition(),False)),
              ('wrong PD mirror',lambda b:b.FindFootprintByReference('J5').SetPosition(point(37.7,14.1))),
              ('reversed PD pin numbers',reverse_pd_numbers),
              ('wrong PD power net',lambda b:next(q for q in b.FindFootprintByReference('J5').Pads() if q.GetNumber()=='1').SetNet(b.FindNet('GND'))),
              ('swapped ATT and PDOK',lambda b:next(q for q in b.FindFootprintByReference('J5').Pads() if q.GetNumber()=='3').SetNet(b.FindNet('PDOK'))),
              ('wrong PD rotation',lambda b:b.FindFootprintByReference('J5').SetOrientationDegrees(0)),
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
