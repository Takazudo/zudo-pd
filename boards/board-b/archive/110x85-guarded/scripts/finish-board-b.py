#!/usr/bin/env python3
"""Import a reviewed local routing session and add copper pours for Board B."""
import argparse
import json
import hashlib
from pathlib import Path
import sys
import wx
_KICAD_APP = wx.App(False)
import pcbnew as p

from pcb_common import pcb_net_name, sync_lcsc_aliases
from board_b_layout import WIDTH, HEIGHT, NEGATIVE_ZONES, PLACEMENTS

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
import board_b_spec as spec
from sexp import atom, find_all, load


def mm(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('placement',type=Path)
    parser.add_argument('session',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Refusing to overwrite; use a new routed output path')
    if hashlib.sha256(args.session.read_bytes()).hexdigest()!='9ac28cc9bcf176e9b68aaf6ca75aefe2434c59f307b66f36171a76b20dc2a7a5':
        raise ValueError('Routing session changed; review indicator, feedback and fiducial completions')
    board=p.LoadBoard(str(args.placement))
    if not p.ImportSpecctraSES(board,str(args.session)):raise SystemExit('KiCad rejected the routing session')
    pads={fp.GetReference()+'.'+pad.GetNumber():pad for fp in board.GetFootprints() for pad in fp.Pads()}
    def route(key,points,layer=p.F_Cu,width=1):
        for a,b in zip(points,points[1:]):
            track=p.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
            track.SetWidth(p.FromMM(width));track.SetLayer(layer);track.SetNet(pads[key].GetNet())
            track.SetLocked(True);board.Add(track)
    # Low-current feedback/indicator branches; excluded from all load-path checks.
    route('R25.1',[[95.25, 27.0], [94.75, 27.0], [94.5, 27.25], [94.25, 27.25], [93.25, 28.25], [91.75, 28.25], [90.75, 27.25], [90.75, 27.0]],width=.25)
    route('R9.1',[(57,83.3),(57.25,82.95),(57.5,82.95)],width=.25)
    route('R9.1',[[57.5, 82.95], [59.5, 80.95], [60.0, 80.95], [60.25, 80.7], [60.5, 80.7], [60.75, 80.45], [85.75, 80.45], [90.5, 75.7], [92.0, 75.7], [92.0, 69.95], [91.75, 69.7], [91.75, 69.45], [91.5, 69.2], [91.5, 68.95], [91.25, 68.7], [91.25, 68.45], [91.0, 68.2], [91.0, 67.95], [90.75, 67.7], [90.75, 67.45], [90.5, 67.2], [90.5, 66.95]],p.B_Cu,.25)
    via=p.PCB_VIA(board);via.SetPosition(mm(57.5,82.95));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
    via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads['R9.1'].GetNet());board.Add(via)
    # The router approximates the fiducial's local1mm clearance; move the marker
    # inward from the offending input trace while retaining its assembly role.
    next(fp for fp in board.GetFootprints() if fp.GetReference()=='FID1').SetPosition(mm(9.5,6))
    # Additional return-plane bridges avoid relying on only two vias for the
    # lower socket ground region; these sites are outside solder-paste pads.
    for x,y in [(48,62),(52,64),(54,64)]:
        via=p.PCB_VIA(board);via.SetPosition(mm(x,y));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
        via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads['U6.6'].GetNet());board.Add(via)
    # References are placed by the generator; functional connector labels stay
    # on the top side above the protected inward-facing bottom terminals.
    for fp in board.GetFootprints():
        if fp.GetReference() == 'P1':
            fp.Reference().SetPosition(mm(40,7))
    for ref in ('J6','J9','J7','J8'):
        rail=next(net for net,pins in spec.NETS.items() if ref+'.1' in pins).removesuffix(' rail')
        label=p.PCB_TEXT(board);label.SetText(rail)
        label.SetPosition(mm(6,PLACEMENTS[ref][1]-3.8))
        label.SetLayer(p.F_SilkS);label.SetTextSize(mm(.8,.8));label.SetTextThickness(p.FromMM(.15));board.Add(label)
    negative=pcb_net_name(next(net for net,pins in spec.NETS.items() if 'U8.6' in pins))
    for layer in (p.F_Cu,p.B_Cu):
        layer_name = 'F.Cu' if layer == p.F_Cu else 'B.Cu'
        outlines = [('GND',[(.5,.5),(WIDTH-.5,.5),(WIDTH-.5,HEIGHT-.5),(.5,HEIGHT-.5)],0)]
        outlines += [(negative,polygons[layer_name],1) for polygons in NEGATIVE_ZONES.values()]
        for net,points,priority in outlines:
            zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet(net));zone.SetAssignedPriority(priority)
            zone.SetLocalClearance(p.FromMM(.3));zone.SetPadConnection(p.ZONE_CONNECTION_FULL)
            zone.SetThermalReliefGap(p.FromMM(.3));zone.SetThermalReliefSpokeWidth(p.FromMM(.6))
            zone.SetMinThickness(p.FromMM(.25));zone.Outline().NewOutline()
            for x,y in points:zone.Outline().Append(p.FromMM(x),p.FromMM(y))
            board.Add(zone)
    # Same-net copper connects power tabs directly; no thermal-relief spokes on those tabs.
    for fp in board.GetFootprints():
        if fp.GetReference() in ('U4','U6','U7','U8'):
            for pad in fp.Pads():
                if pad.GetNumber()=='6':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    p.SaveBoard(str(args.output),board)
    # KiCad 10's imported-footprint DRAWINGS wrapper is opaque in pcbnew.
    # Apply only local silkscreen edits to the serialized generated board.
    tree=load(args.output)
    sync_lcsc_aliases(tree, spec.COMPONENTS)
    obsolete={(56.5,84.2):(57,83.3),(57,81.2):(57,79.9)}
    removed_vias=removed_segments=0
    for via in list(find_all(tree,'via')):
        at=tuple(float(atom(v)) for v in find_all(via,'at')[0][1:3])
        if at in obsolete:tree.remove(via);removed_vias+=1
    for segment in list(find_all(tree,'segment')):
        ends=[tuple(float(atom(v)) for v in find_all(segment,k)[0][1:3]) for k in ('start','end')]
        if any(point in ends and pad in ends for point,pad in obsolete.items()):tree.remove(segment);removed_segments+=1
    if (removed_vias,removed_segments)!=(2,2):raise ValueError('Original indicator escapes changed; review completion')
    for fp in find_all(tree,'footprint'):
        properties={atom(n[1]):atom(n[2]) for n in find_all(fp,'property')}
        ref=properties['Reference']
        if ref=='P1':
            for line in list(find_all(fp,'fp_line')):
                if atom(find_all(line,'layer')[0][1])=='F.SilkS':fp.remove(line)
            nc_pads=[pad for pad in find_all(fp,'pad') if atom(pad[1])=='4']
            assert len(nc_pads)==1
            net=find_all(nc_pads[0],'net')
            if net:net[0][1:]=[('str','unconnected-(P1-NC-Pad4)')]
            else:nc_pads[0].append([('atom','net'),('str','unconnected-(P1-NC-Pad4)')])
            for item in list(find_all(fp,'fp_text')):
                if atom(item[2])=='<-- EDGE':fp.remove(item)
                else:
                    for effects in find_all(item,'effects'):
                        for font in find_all(effects,'font'):
                            for size in find_all(font,'size'):size[1:]=[('atom','0.8'),('atom','0.8')]
        if ref in ('J10','J11'):
            for line in list(find_all(fp,'fp_line')):
                if atom(find_all(line,'layer')[0][1])!='F.SilkS':continue
                start,end=find_all(line,'start')[0],find_all(line,'end')[0]
                a,b=[[float(atom(v)) for v in n[1:]] for n in (start,end)]
                limit=11.73
                if a[1]>=limit and b[1]>=limit:fp.remove(line);continue
                if a[1]>limit:a=[b[0]+(a[0]-b[0])*(limit-b[1])/(a[1]-b[1]),limit]
                if b[1]>limit:b=[a[0]+(b[0]-a[0])*(limit-a[1])/(b[1]-a[1]),limit]
                start[1:]=[('atom',str(v)) for v in a];end[1:]=[('atom',str(v)) for v in b]
    for item in find_all(tree,'gr_text'):
        if atom(item[1])=='TP3 13.44V / TP4 6.519V / TP5 -14.145V':
            find_all(item,'at')[0][2]=('atom','4.25')
    def serialize(node):
        if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
        return json.dumps(node[1],ensure_ascii=False) if node[0]=='str' else node[1]
    args.output.write_text(serialize(tree)+'\n')
    print(f'{args.output}: {len(find_all(tree,"segment"))+len(find_all(tree,"via"))} tracks/vias; refill and run DRC before any export')


if __name__=='__main__':main()
