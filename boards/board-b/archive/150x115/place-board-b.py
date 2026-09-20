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

PLACEMENTS = {
    'J5': (12.9, 37.7, 180, 'bottom'), 'P1': (12.9, 44, 0),
    'J6': (10, 58, 90), 'J9': (10, 72, 90), 'J7': (10, 86, 90), 'J8': (10, 100, 90),
    'J10': (55, 102.77, 0), 'J11': (96, 102.77, 0),
    'LED2': (120, 106, 90), 'LED3': (127, 106, 90), 'LED4': (134, 106, 90),
    'R7': (120, 101, 90), 'R8': (127, 101, 90), 'R9': (134, 101, 90),
}
for row, refs in zip((18, 48, 78), (
    ['U2','D1','L1','C5','C6','C3','C31','R1','R2','C14','C20','U6','C17','C21','PTC1','TVS1','TP3'],
    ['U3','D2','L2','C7','C8','C4','C32','R3','R4','C15','C22','U7','C18','C23','PTC2','TVS2','TP4'],
    ['U4','D3','L3','C9','C10','C11','C33','R5','R6','C16','C24','U8','C19','C25','PTC3','TVS3','TP5'],
)):
    offsets = [(45,0,0),(57,1,90),(69,0,0),(46,13,180),(56,7,0),
               (84,0,0),(61,-10,0),(56,-7,0),(51,-8,90),
               (95,-8,90),(95,6,90),(111,0,0),(123,-7,0),(128,3,0),
               (139,-4,90),(140,5,90),(87,-9,0)]
    for ref,(x,dy,angle) in zip(refs,offsets):
        PLACEMENTS[ref] = (x,row+dy,angle)
PLACEMENTS['C12']=(80,91,0)
# The negative regulator's tab is VIN, not system ground.
PLACEMENTS['U8']=(111,78,0)

for removed in ('D1','C31'):
    PLACEMENTS.pop(removed)
PLACEMENTS.update({
    'U2':(53,18,180),'L1':(61,18,0),'R1':(50,12,90),'R2':(47,15,0),
    'C5':(35,24,90),'C6':(53,21,0),'C39':(53,24.5,0),'C46':(45.5,29,180),
    'C38':(54,13.5,90),'C3':(69,18,0),'C14':(69,13.5,0),'C20':(69,22.5,0),
    'C36':(75,16,0),'C37':(75,20.5,0),
    'C17':(120,26,0),'C40':(123,18,0),'C21':(134,31,0),'PTC1':(140,13,90),'TVS1':(144,23,90),
    'C18':(120,56,0),'C41':(123,48,0),'C23':(134,61,0),'PTC2':(140,43,90),'TVS2':(144,53,90),
    'C19':(120,70,0),'C42':(123,78,180),'C25':(134,91,180),'PTC3':(140,73,90),'TVS3':(144,83,90),
    'R20':(124,8,0),'R21':(124,11,0),'R22':(130,11,0),
    'R23':(124,38,0),'R24':(124,41,0),'R25':(130,41,0),
})


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
    ds.SetAuxOrigin(mm(0,115))
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
    route('U2.4',[padxy('C6.2'),padxy('C39.2'),(56.2,24.5)],1.0)
    via=p.PCB_VIA(board);via.SetPosition(mm(56.2,24.5));via.SetWidth(p.FromMM(1.0));via.SetDrill(p.FromMM(.4))
    via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads['U2.4'].GetNet());board.Add(via)
    route('U2.5',[padxy('U2.5'),(55.5,18),(56.2,18)],.45)
    route('U2.5',[(56.2,18),padxy('L1.1')],1.0)
    route('U2.6',[padxy('U2.6'),padxy('C38.1')],.25)
    route('U2.5',[padxy('C38.2'),(55.5,padxy('C38.2')[1]),(55.5,18)],.25)
    route('U2.1',[padxy('U2.1'),(50,17.05),padxy('R1.1')],.25)
    route('U2.1',[padxy('R2.2'),(50,15),padxy('R1.1')],.25)
    for top,cap in [('R20','C40'),('R23','C41')]:
        start,end=padxy(top+'.1'),padxy(cap+'.1')
        route(top+'.1',[start,(120,start[1]),(120,end[1]),end],.25)
    route('U8.4',[padxy('U8.4'),padxy('U8.5')],.4)
    route('U2.2',[padxy('U2.2'),(49.5,18),(49.5,18.95),padxy('U2.3')],.25)
    # Dedicated output-current trunks keep the narrow feedback branches out of the load path.
    for regulator,cap,cap_pin,fuse,bus_y in [('U6','C40','1','PTC1',25),('U7','C41','1','PTC2',55),('U8','C42','2','PTC3',85)]:
        output_pin=regulator+('.5' if regulator=='U8' else '.4')
        cap_pin=cap+'.'+cap_pin;fuse_pin=fuse+'.1'
        start,finish=padxy(output_pin),padxy(cap_pin)
        assert pads[output_pin].GetNetCode()==pads[cap_pin].GetNetCode()==pads[fuse_pin].GetNetCode()
        route(output_pin,[start,(119.25,start[1]),finish],1.0)
        first,second=(124,bus_y),(136.5,padxy(fuse_pin)[1])
        route(output_pin,[finish,(121,finish[1]+4.5),first],1.0)
        route(output_pin,[first,(136.5,bus_y),second],1.0,p.B_Cu)
        route(output_pin,[second,padxy(fuse_pin)],1.0)
        for point in (first,second):
            via=p.PCB_VIA(board);via.SetPosition(mm(*point));via.SetWidth(p.FromMM(1.2));via.SetDrill(p.FromMM(.6))
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pads[output_pin].GetNet());board.Add(via)
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
    for i,(x,y) in enumerate([(4,4),(23,4),(12.8,32.6),(146,4),(4,111),(146,111)],1):
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),'MountingHole_M3')
        fp.SetFPID(p.LIB_ID('zudo-pd','MountingHole_M3'));fp.SetReference('H'+str(i))
        fp.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x,y));fp.Value().SetVisible(False);fp.Reference().SetVisible(False)
        board.Add(fp)
    for i,(x,y) in enumerate([(12,8),(140,8),(18,107)],1):
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),'Fiducial_1mm_Mask2mm')
        fp.SetFPID(p.LIB_ID('zudo-pd','Fiducial_1mm_Mask2mm'));fp.SetReference('FID'+str(i))
        fp.SetAttributes(p.FP_SMD | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.SetPosition(mm(x,y));fp.Value().SetVisible(False);fp.Reference().SetVisible(False);board.Add(fp)
    for a,b in [((0,0),(150,0)),((150,0),(150,115)),((150,115),(0,115)),((0,115),(0,0))]:
        line=p.PCB_SHAPE(board);line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(mm(*a));line.SetEnd(mm(*b));line.SetLayer(p.Edge_Cuts);line.SetWidth(p.FromMM(.05));board.Add(line)
    for text,x,y,size in [('zudo-pd / Board B / prototype',85,36,1.3),('PD module below',13.5,18,1),('15V ONLY',13.5,23,1),
                          ('-12V / RED',68,98,1),('-12V / RED',109,98,1),('+12',120,111,.9),('+5',127,111,.9),('-12',134,111,.9)]:
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
    print(f'Placed {len(spec.COMPONENTS)} components on 150 x 115 mm Board B: {args.output}')


if __name__=='__main__': main()
