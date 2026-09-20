#!/usr/bin/env python3
"""Import a reviewed local routing session and add copper pours for Board B."""
import argparse
import json
from pathlib import Path
import sys
import wx
_KICAD_APP = wx.App(False)
import pcbnew as p

from pcb_common import pcb_net_name, sync_surface_part, sync_lcsc_aliases

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
    board=p.LoadBoard(str(args.placement))
    if not p.ImportSpecctraSES(board,str(args.session)):raise SystemExit('KiCad rejected the routing session')
    pads={fp.GetReference()+'.'+pad.GetNumber():pad for fp in board.GetFootprints() for pad in fp.Pads()}
    def route(key,points,layer=p.F_Cu,width=1):
        for a,b in zip(points,points[1:]):
            track=p.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
            track.SetWidth(p.FromMM(width));track.SetLayer(layer);track.SetNet(pads[key].GetNet())
            track.SetLocked(True);board.Add(track)
    # Keep the precision-divider escape traces outside the 0603 pad gap.
    # KiCad's native 0.25 mm netclass check is stricter than the router's
    # pad-corner approximation, so these two feedback paths are explicit.
    route('R24.2',[(124.75,41),(124.75,42.2647),(120.9897,42.2647)],width=.25)
    # Complete the local capacitor branches that the router cannot join to the
    # locked output buses. Native DRC verifies these against the imported copper.
    route('C19.1',[(119,70),(119,74.5964),(119.25,74.5964)])
    for key,start,via_point,bus_point in [
        ('C23.1',(131.33,61),(127.5,61),(127.5,55)),
        ('C25.2',(129.5,91),(129.5,87.5),(129.5,85)),
    ]:
        route(key,[start,via_point]);route(key,[via_point,bus_point],p.B_Cu)
        via=p.PCB_VIA(board);via.SetPosition(mm(*via_point));via.SetWidth(p.FromMM(1.2))
        via.SetDrill(p.FromMM(.6));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[key].GetNet());board.Add(via)
    # Board-specific assembly labels; keep the canonical component artwork intact.
    labels={'C40':(128,23),'C41':(128,53),'U2':(49,21),'C39':(53,28.3),'C3':(69,15.75),
            'C20':(69,20.25),'C37':(75,18.25),'C8':(59.5,55),
            'C10':(59.5,85),'R21':(124,13.1),'R24':(124,43.1),
            'LED2':(123.3,106),'LED3':(130.3,106),'LED4':(137.3,106),
            'PTC1':(140,17.5),'P1':(12.9,40.5)}
    for fp in board.GetFootprints():
        ref=fp.GetReference()
        if ref in labels:
            fp.Reference().SetPosition(mm(*labels[ref]))
        if ref in ('C3','C20','C37'):
            fp.Reference().SetTextSize(mm(.8,.8))
    for item in board.GetDrawings():
        if isinstance(item,p.PCB_TEXT) and item.GetText()=='zudo-pd / Board B / prototype':
            item.SetPosition(mm(85,4))
    for ref,y in [('J6',55.5),('J9',69.5),('J7',83.5),('J8',97.5)]:
        rail=next(net for net,pins in spec.NETS.items() if ref+'.1' in pins).removesuffix(' rail')
        label=p.PCB_TEXT(board);label.SetText(rail);label.SetPosition(mm(20,y))
        label.SetLayer(p.F_SilkS);label.SetTextSize(mm(1,1));label.SetTextThickness(p.FromMM(.15));board.Add(label)
    negative=pcb_net_name(next(net for net,pins in spec.NETS.items() if 'U8.6' in pins))
    for layer in (p.F_Cu,p.B_Cu):
        u8_points=([(90,64),(113.5,64),(113.5,98),(90,98)] if layer==p.F_Cu else
                   [(90,63),(149,63),(149,99),(90,99)])
        for net,points,priority in [('GND',[(.5,.5),(149.5,.5),(149.5,114.5),(.5,114.5)],0),
                                    (negative,[(29,66),(52,66),(52,98),(29,98)],1),
                                    (negative,u8_points,1)]:
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
    sync_surface_part(tree, 'D3', spec.COMPONENTS['D3'], ROOT/'footprints/kicad/zudo-power.pretty', 'board-b')
    u7_corners={(124.0183,41),(124.0183,41.5534),(123.307,42.2647)}
    u6_moves={(125.2604,7.1933):(125.6,7.1933),(128.5183,10.4512):(128.5183,10.1116)}
    removed,moved=0,0
    for segment in list(find_all(tree,'segment')):
        net=atom(find_all(segment,'net')[0][1])
        start,end=find_all(segment,'start')[0],find_all(segment,'end')[0]
        coords=[tuple(float(atom(v)) for v in n[1:]) for n in (start,end)]
        if net=='U7 ADJ' and atom(find_all(segment,'layer')[0][1])=='F.Cu' and any(v in u7_corners for v in coords):
            tree.remove(segment);removed+=1
        if net=='U6 ADJ':
            for point,coordinate in zip((start,end),coords):
                if coordinate in u6_moves:
                    point[1:]=[('atom',str(v)) for v in u6_moves[coordinate]];moved+=1
    assert (removed,moved)==(4,4), 'Routing session changed: review the explicit feedback corrections'
    for fp in find_all(tree,'footprint'):
        properties={atom(n[1]):atom(n[2]) for n in find_all(fp,'property')}
        ref=properties['Reference']
        if ref=='P1':
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
    def serialize(node):
        if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
        return json.dumps(node[1],ensure_ascii=False) if node[0]=='str' else node[1]
    args.output.write_text(serialize(tree)+'\n')
    print(f'{args.output}: {len(find_all(tree,"segment"))+len(find_all(tree,"via"))} tracks/vias; refill and run DRC before any export')


if __name__=='__main__':main()
