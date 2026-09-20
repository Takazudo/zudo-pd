#!/usr/bin/env python3
"""Generate the Board B placement from the current schematic spec using KiCad Python.

Writes an unrouted placement to a new path; never overwrites a routed design.
"""
import argparse
import json
from pathlib import Path
import sys
import wx
_KICAD_APP = wx.App(False)
import pcbnew as p

from pcb_common import pcb_net_name

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import board_b_spec as spec
from schgen_core import new_uuid

from board_b_layout import WIDTH, HEIGHT, PLACEMENTS, MOUNTING_HOLES, FIDUCIALS


def mm(x,y):
    return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite a PCB; choose a fresh placement path')
    assert set(PLACEMENTS)==set(spec.COMPONENTS), (set(spec.COMPONENTS)-set(PLACEMENTS),set(PLACEMENTS)-set(spec.COMPONENTS))
    board=p.BOARD()
    board.SetCopperLayerCount(2)
    ds=board.GetDesignSettings()
    ds.SetBoardThickness(p.FromMM(1.6))
    ds.SetAuxOrigin(mm(0,HEIGHT))
    nets={}
    for code,name in enumerate(spec.NETS,1):
        net=p.NETINFO_ITEM(board,pcb_net_name(name),code); board.Add(net); nets[name]=net
    pin_nets={pin:net for name,pins in spec.NETS.items() for pin in pins for net in [nets[name]]}
    for ref,comp in spec.COMPONENTS.items():
        symbol,value,lcsc,footprint,dnp,_=comp
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),footprint.split(':')[1])
        if not fp: raise ValueError(footprint)
        board.Add(fp)
        fp.SetFPID(p.LIB_ID(*footprint.split(':',1)))
        fp.SetReference(ref); fp.SetValue(value)
        fp.SetField('LCSC',lcsc)
        fp.GetField('LCSC').SetVisible(False)
        for alias in ('LCSC Part','LCSC Part #','JLCPCB Part #'):
            if fp.GetField(alias):
                fp.SetField(alias,lcsc);fp.GetField(alias).SetVisible(False)
        fp.SetPath(p.KIID_PATH('/'+new_uuid('board-b:root')+'/'+new_uuid('board-b:'+ref+':instance')))
        fp.SetDNP(dnp)
        if not lcsc:
            fp.SetAttributes(fp.GetAttributes() | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        pos=PLACEMENTS[ref]
        fp.SetPosition(mm(*pos[:2])); fp.SetOrientationDegrees(pos[2])
        if len(pos)>3 and pos[3]=='bottom': fp.Flip(fp.GetPosition(),False)
        if ref == 'P1':
            for graphic in fp.GraphicalItems():
                if isinstance(graphic,p.PCB_TEXT):
                    graphic.SetText({'SCL':'ATT','SDA':'PDOK'}.get(graphic.GetText(),graphic.GetText()))
        fp.Value().SetVisible(False)
        if ref in ('R7','R8','R9','LED2','LED3','LED4'):fp.Reference().SetVisible(False)
        fp.Reference().SetTextSize(mm(.9,.9)); fp.Reference().SetTextThickness(p.FromMM(.15))
        bounds=fp.GetBoundingBox(False,False)
        fp.Reference().SetPosition(mm(pos[0],p.ToMM(bounds.GetTop())-1.1))
        fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        for pad in fp.Pads():
            key=ref+'.'+pad.GetNumber()
            if key in pin_nets: pad.SetNet(pin_nets[key])
            elif key not in spec.NO_CONNECT and pad.GetAttribute()!=p.PAD_ATTRIB_NPTH:
                raise ValueError('Unassigned pad '+key)
    pads={fp.GetReference()+'.'+pad.GetNumber():pad for fp in board.GetFootprints() for pad in fp.Pads()}
    def padxy(key):
        pos=pads[key].GetPosition();return (p.ToMM(pos.x),p.ToMM(pos.y))
    def route(net_key,points,width,layer=p.F_Cu):
        for a,b in zip(points,points[1:]):
            track=p.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b));track.SetWidth(p.FromMM(width))
            track.SetLayer(layer);track.SetNet(pads[net_key].GetNet());track.SetLocked(True);board.Add(track)
    # Keep the synchronous buck's switch, bootstrap and ceramic input loops local.
    route('U2.3',[padxy('U2.3'),padxy('C6.1')],.45)
    route('U2.4',[padxy('U2.4'),padxy('C6.2')],.45)
    route('U2.3',[padxy('C6.1'),padxy('C39.1')],1.0)
    route('U2.4',[padxy('C6.2'),padxy('C39.2'),(32.2,24.5)],1.0)
    via=p.PCB_VIA(board);via.SetPosition(mm(32.2,24.5));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
    via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads['U2.4'].GetNet());board.Add(via)
    route('U2.5',[padxy('U2.5'),(31.5,18),(32.2,18)],.45)
    route('U2.5',[(32.2,18),padxy('L1.1')],1.0)
    route('U2.6',[padxy('U2.6'),padxy('C38.1')],.25)
    route('U2.5',[padxy('C38.2'),(31.5,padxy('C38.2')[1]),(31.5,18)],.25)
    route('U2.1',[padxy('U2.1'),(26,17.05),padxy('R1.1')],.25)
    route('U2.1',[padxy('R2.2'),(26,15),padxy('R1.1')],.25)
    for top,cap in [('R20','C40'),('R23','C41')]:
        start,end=padxy(top+'.1'),padxy(cap+'.1')
        route(top+'.1',[start,(86,start[1]),(86,end[1]),end],.25)
    route('U8.4',[padxy('U8.4'),padxy('U8.5')],.4)
    route('U2.2',[padxy('U2.2'),(25.5,18),(25.5,18.95),padxy('U2.3')],.25)
    # Dedicated output-current trunks keep the narrow feedback branches out of the load path.
    for regulator,cap,cap_pin,fuse,bus_y in [('U6','C40','1','PTC1',23),('U7','C41','1','PTC2',51),('U8','C42','2','PTC3',77)]:
        output_pin=regulator+('.5' if regulator=='U8' else '.4')
        cap_pin=cap+'.'+cap_pin;fuse_pin=fuse+'.1'
        start,finish=padxy(output_pin),padxy(cap_pin)
        assert pads[output_pin].GetNetCode()==pads[cap_pin].GetNetCode()==pads[fuse_pin].GetNetCode()
        route(output_pin,[start,(85.25,start[1]),finish],1.0)
        first,second=(90,bus_y),(98.5,padxy(fuse_pin)[1])
        route(output_pin,[finish,(87,finish[1]+4.5),first],1.0)
        route(output_pin,[first,(98.5,bus_y),second],1.0,p.B_Cu)
        route(output_pin,[second,padxy(fuse_pin)],1.0)
        for point in (first,second):
            via=p.PCB_VIA(board);via.SetPosition(mm(*point));via.SetWidth(p.FromMM(1.2));via.SetDrill(p.FromMM(.6))
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[output_pin].GetNet());board.Add(via)
    # Wide local capacitor branches are part of the load path, independent of
    # any thin feedback traces the router adds later.
    route('C19.1',[padxy('C19.1'),(85,66.5964),(85.25,66.5964)],1.0)
    for key,via_point,bus_point in [
        ('C21.1',(95.5,27),(95.5,23)),
        ('C23.1',(95.5,55),(95.5,51)),
        ('C25.2',(96,78.8),(96,77)),
        ('C18.1',(85,54.5),(90,51)),
    ]:
        route(key,[padxy(key),via_point],1.0)
        route(key,[via_point,bus_point],1.0,p.B_Cu)
        via=p.PCB_VIA(board);via.SetPosition(mm(*via_point));via.SetWidth(p.FromMM(1.2))
        via.SetDrill(p.FromMM(.6));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[key].GetNet());board.Add(via)
    # Inverting U4's local reference and enable belong to its negative tab.
    # Strap them before routing so signal escapes cannot split their pour.
    route('U4.3',[padxy('U4.3'),padxy('U4.6')],1.0)
    route('U4.5',[padxy('U4.5'),(24.34,66.6),padxy('U4.6')],1.0)
    negative_bulk_via=(54,58.5)
    route('C12.2',[padxy('C12.2'),negative_bulk_via],1.0)
    route('C12.2',[(23.09,70),(34,59),negative_bulk_via,(67.999,63.666)],1.0,p.B_Cu)
    via=p.PCB_VIA(board);via.SetPosition(mm(*negative_bulk_via));via.SetWidth(p.FromMM(1.2))
    via.SetDrill(p.FromMM(.6));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads['C12.2'].GetNet());board.Add(via)
    # Small indicator/feedback branches need local via escapes; forcing a
    # 1 mm autorouter branch out of these narrow socket gaps strands the pads.
    for key,point in [('R7.1',(57,87.8)),('R8.1',(57,91.2)),
                      ('R9.1',(56.5,94.2)),('R6.2',(32,58.2))]:
        route(key,[padxy(key),point],.25)
        via=p.PCB_VIA(board);via.SetPosition(mm(*point));via.SetWidth(p.FromMM(1.0))
        via.SetDrill(p.FromMM(.4));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[key].GetNet());board.Add(via)
    route('R6.2',[(32,58.2),(30,58.2),(23.09,63.5)],.25,p.B_Cu)
    thermal_vias=[]
    for ref in ('U4','U6','U7','U8'):
        fp=next(f for f in board.GetFootprints() if f.GetReference()==ref)
        tab=next(pad for pad in fp.Pads() if pad.GetNumber()=='6')
        pos=tab.GetPosition();cx,cy=p.ToMM(pos.x),p.ToMM(pos.y)
        size=tab.GetSize();rx,ry=p.ToMM(size.x)/2+1.0,p.ToMM(size.y)/2+1.0
        points=[(cx+sign*rx,cy+dy) for sign in (-1,1) for dy in (-3,0,3)]
        points += [(cx+dx,cy+sign*ry) for sign in (-1,1) for dx in (-2.5,0,2.5)]
        for x,y in points:
            via=p.PCB_VIA(board);via.SetPosition(mm(x,y));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(tab.GetNet())
            board.Add(via);thermal_vias.append((ref,x,y))
        # Reserve a connected back-copper frame below each hot tab before
        # autorouting. Other nets cannot cut between the tab and its via array.
        route(ref+'.6',[(cx-rx,cy-ry),(cx+rx,cy-ry),(cx+rx,cy+ry),
                        (cx-rx,cy+ry),(cx-rx,cy-ry)],1.0,p.B_Cu)
        route(ref+'.6',[(cx-rx,cy),(cx+rx,cy)],1.0,p.B_Cu)
        route(ref+'.6',[(cx,cy-ry),(cx,cy+ry)],1.0,p.B_Cu)
    for i,(x,y) in enumerate(MOUNTING_HOLES,1):
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),'MountingHole_M3')
        fp.SetFPID(p.LIB_ID('zudo-pd','MountingHole_M3'));fp.SetReference('H'+str(i))
        fp.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x,y));fp.Value().SetVisible(False);fp.Reference().SetVisible(False)
        board.Add(fp)
    for i,(x,y) in enumerate(FIDUCIALS,1):
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),'Fiducial_1mm_Mask2mm')
        fp.SetFPID(p.LIB_ID('zudo-pd','Fiducial_1mm_Mask2mm'));fp.SetReference('FID'+str(i))
        fp.SetAttributes(p.FP_SMD | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x,y));fp.Value().SetVisible(False);fp.Reference().SetVisible(False);board.Add(fp)
    for a,b in [((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,HEIGHT)),((WIDTH,HEIGHT),(0,HEIGHT)),((0,HEIGHT),(0,0))]:
        line=p.PCB_SHAPE(board);line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(mm(*a));line.SetEnd(mm(*b));line.SetLayer(p.Edge_Cuts);line.SetWidth(p.FromMM(.05));board.Add(line)
    for text,x,y,size in [('zudo-pd B / compact prototype',68,3,1),
                          ('-12 / RED',50.29,78.5,0.8),('-12 / RED',90.39,78.5,0.8),
                          ('+12',65.8,86.5,.8),('+5',65.8,89.9,.8),('-12',65.8,93.3,.8)]:
        item=p.PCB_TEXT(board);item.SetText(text);item.SetPosition(mm(x,y));item.SetTextSize(mm(size,size));item.SetTextThickness(p.FromMM(.15));item.SetLayer(p.F_SilkS);board.Add(item)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    p.SaveBoard(str(args.output),board)
    stackup='\n'.join([
        '    (stackup',
        '      (layer "F.SilkS" (type "Top Silk Screen"))',
        '      (layer "F.Paste" (type "Top Solder Paste"))',
        '      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))',
        '      (layer "F.Cu" (type "copper") (thickness 0.07))',
        '      (layer "dielectric 1" (type "core") (thickness 1.44) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))',
        '      (layer "B.Cu" (type "copper") (thickness 0.07))',
        '      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))',
        '      (layer "B.Paste" (type "Bottom Solder Paste"))',
        '      (layer "B.SilkS" (type "Bottom Silk Screen"))',
        '      (copper_finish "None") (dielectric_constraints no)',
        '    )',
    ])
    content=args.output.read_text()
    assert '(stackup' not in content
    args.output.write_text(content.replace('(setup\n','(setup\n'+stackup+'\n',1))
    print(f'Placed {len(spec.COMPONENTS)} components on {WIDTH} x {HEIGHT} mm Board B: {args.output}')


if __name__=='__main__': main()
