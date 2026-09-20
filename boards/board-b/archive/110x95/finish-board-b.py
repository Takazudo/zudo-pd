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
    expected_session='922cfeb63c436ead9ece58319ddd0e2326578a3a16c70ab3cbea9e7efed058e2'
    if hashlib.sha256(args.session.read_bytes()).hexdigest()!=expected_session:
        raise ValueError('Routing session changed: review the final LED branch and ground stitches before import')
    board=p.LoadBoard(str(args.placement))
    if not p.ImportSpecctraSES(board,str(args.session)):raise SystemExit('KiCad rejected the routing session')
    pads={fp.GetReference()+'.'+pad.GetNumber():pad for fp in board.GetFootprints() for pad in fp.Pads()}
    def route(key,points,layer=p.F_Cu,width=1):
        for a,b in zip(points,points[1:]):
            track=p.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
            track.SetWidth(p.FromMM(width));track.SetLayer(layer);track.SetNet(pads[key].GetNet())
            track.SetLocked(True);board.Add(track)
    # Reviewed completion of the low-current negative-rail indicator branch.
    # Its 0.25 mm sense/LED wiring is excluded from all 1 mm load-path proofs.
    route('R9.1',[(57,93.3),(57.5,93.95)],width=.25)
    route('R9.1',[(57.5,93.95),(65.25,93.95),(65.5,93.7),(86.75,93.7),
                  (96.25,84.2),(96.5,84.2)],p.B_Cu,.25)
    route('R9.1',[(96.5,84.2),(93.75,81.45)],p.F_Cu,.25)
    route('R9.1',[(93.75,81.45),(93.25,80.95),(93.25,79.7),(90.5,76.95)],p.B_Cu,.25)
    for key,points in [('R9.1',[(57.5,93.95),(96.5,84.2),(93.75,81.45)]),
                       ('U6.6',[(40,64),(48,66),(58,70),(50,74)])]:
        for x,y in points:
            via=p.PCB_VIA(board);via.SetPosition(mm(x,y));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[key].GetNet());board.Add(via)
    # References are placed by the generator; functional connector labels stay
    # on the board even when their mating metal intentionally projects beyond it.
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
    # Remove the abandoned original indicator escape; the reviewed route above
    # leaves the resistor on the opposite side of that local routing barrier.
    removed_vias=removed_segments=0
    for via in list(find_all(tree,'via')):
        at=find_all(via,'at')[0]
        if [float(atom(v)) for v in at[1:3]]==[56.5,94.2]:tree.remove(via);removed_vias+=1
    for segment in list(find_all(tree,'segment')):
        ends=[[float(atom(v)) for v in find_all(segment,k)[0][1:3]] for k in ('start','end')]
        if [56.5,94.2] in ends and [57.0,93.3] in ends:tree.remove(segment);removed_segments+=1
    if (removed_vias,removed_segments)!=(1,1):raise ValueError('Indicator escape changed; review completion')
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
        if ref in ('J10','J11','J6','J9','J7','J8'):
            for line in list(find_all(fp,'fp_line')):
                if atom(find_all(line,'layer')[0][1])!='F.SilkS':continue
                start,end=find_all(line,'start')[0],find_all(line,'end')[0]
                a,b=[[float(atom(v)) for v in n[1:]] for n in (start,end)]
                limit=11.73 if ref in ('J10','J11') else PLACEMENTS[ref][0]-.5
                if a[1]>=limit and b[1]>=limit:fp.remove(line);continue
                if a[1]>limit:a=[b[0]+(a[0]-b[0])*(limit-b[1])/(a[1]-b[1]),limit]
                if b[1]>limit:b=[a[0]+(b[0]-a[0])*(limit-a[1])/(b[1]-a[1]),limit]
                start[1:]=[('atom',str(v)) for v in a];end[1:]=[('atom',str(v)) for v in b]
    def serialize(node):
        if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
        return json.dumps(node[1],ensure_ascii=False) if node[0]=='str' else node[1]
    args.output.write_text(serialize(tree)+'\n')
    print(f'{args.output}: {len(find_all(tree,"segment"))+len(find_all(tree,"via"))} tracks/vias; refill and run DRC before any export')


if __name__=='__main__':main()
