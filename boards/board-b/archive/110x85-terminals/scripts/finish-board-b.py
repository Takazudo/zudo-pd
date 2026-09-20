#!/usr/bin/env python3
"""Import a reviewed local routing session and add copper pours for Board B."""
import argparse
import json
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
    board=p.LoadBoard(str(args.placement))
    if board.GetAreaCount():raise ValueError('Use the unflooded placement, not an already routed board')
    refs={f.GetReference() for f in board.GetFootprints()}
    if not set(spec.COMPONENTS)<=refs or {'J8','J9'}&refs:raise ValueError('Placement does not match the current terminal specification')
    if not p.ImportSpecctraSES(board,str(args.session)):raise SystemExit('KiCad rejected the routing session')
    # Final current-spec routing is checked by native DRC and verify-board-b;
    # no geometry-specific completion from a previous session is applied here.
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
