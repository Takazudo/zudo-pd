#!/usr/bin/env python3
"""Move the PD mating interface to the component side of the reviewed PCB.

This hash-locked transformation preserves the conversion stages, replaces the
affected connector/input routes, moves the bulk input capacitor and adds back
rail labels. Native refill, DRC/parity and populated CAD checks are mandatory.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import tempfile
import wx
_APP=wx.App(False)
import pcbnew as p

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
from pcb_common import serialize,pcb_net_name
from board_b_layout import PLACEMENTS,MOUNTING_HOLES
from schgen_core import new_uuid
import board_b_spec as spec

BASE_SHA='6d309a4272b5e54b984e65e1533f74294fb9acc8140347970d2e1b53e1bb1741'
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Choose a new output')
    if hashlib.sha256(args.input.read_bytes()).hexdigest()!=BASE_SHA:raise ValueError('Unreviewed input PCB')
    tree=load(args.input)
    for fp in list(find_all(tree,'footprint')):
        props={atom(n[1]):atom(n[2]) for n in find_all(fp,'property')};ref=props['Reference']
        if ref=='J5':tree.remove(fp)
        elif ref in ('PTC1','PTC2'):
            library=load(ROOT/'footprints/kicad/zudo-power.pretty'/(spec.COMPONENTS[ref][3].split(':')[1]+'.kicad_mod'))
            for model in list(find_all(fp,'model')):fp.remove(model)
            fp.extend(find_all(library,'model'))
    ground_ends={(14,14.5),(37.7,10.29),(37.7,7.75),(39.16,11.75)}
    input_ends={(14,23.5),(37.7,17.91),(37.7,20.45),(37.79,18)}
    removed={}
    for segment in list(find_all(tree,'segment')):
        net=atom(find_all(segment,'net')[0][1])
        ends=[tuple(float(atom(v)) for v in find_all(segment,k)[0][1:3]) for k in ('start','end')]
        remove=(net in ('ATT','PDOK') or (net=='GND' and any(pt in ground_ends for pt in ends))
                or (net=='+15V INPUT' and any(pt in input_ends for pt in ends))
                or ('-14.145V PRE' in net and atom(find_all(segment,'layer')[0][1])=='B.Cu' and min(pt[1] for pt in ends)<45)
                or (net in ('-12V rail','+12V rail','+5V rail') and min(pt[0] for pt in ends)<12))
        if remove:tree.remove(segment);removed[net]=removed.get(net,0)+1
        else:
            for key in ('start','end'):
                point=find_all(segment,key)[0];pt=tuple(float(atom(v)) for v in point[1:3])
                if pt in ((40,8.25),(40,9.75),(40,10.6),(41.25,11.75)):
                    point[1]=('atom',str(pt[0]+.5))
    for item in list(find_all(tree,'gr_text')):
        if atom(item[1]) in ('-12V','GND','+12V','+5V'):tree.remove(item)
        elif atom(item[1])=='zudo-pd B / terminal prototype':item[1]=('str','zudo-pd B / front stack')
    with tempfile.TemporaryDirectory(prefix='front-stack-') as temp:
        intermediate=Path(temp)/'board.kicad_pcb';intermediate.write_text(serialize(tree)+'\n')
        board=p.LoadBoard(str(intermediate))
    footprints={fp.GetReference():fp for fp in board.GetFootprints()}
    for ref in ('C5','J6','J7','R1','R2'):
        fp=footprints[ref];x,y,angle=PLACEMENTS[ref];old=fp.GetPosition()
        dx,dy=x-p.ToMM(old.x),y-p.ToMM(old.y);r=fp.Reference().GetPosition()
        fp.SetPosition(xy(x,y));fp.SetOrientationDegrees(angle)
        fp.Reference().SetPosition(xy(p.ToMM(r.x)+dx,p.ToMM(r.y)+dy))
    footprints['R1'].Reference().SetPosition(xy(40.5,5.5))
    for i,position in enumerate(MOUNTING_HOLES,1):footprints['H'+str(i)].SetPosition(xy(*position))
    symbol,value,lcsc,footprint,dnp,_=spec.COMPONENTS['J5']
    fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),footprint.split(':')[1]);board.Add(fp)
    fp.SetFPID(p.LIB_ID(*footprint.split(':',1)));fp.SetReference('J5');fp.SetValue(value);fp.SetDNP(dnp)
    fp.SetPath(p.KIID_PATH('/'+new_uuid('board-b:root')+'/'+new_uuid('board-b:J5:instance')))
    fp.SetField('LCSC',lcsc);fp.GetField('LCSC').SetVisible(False);fp.Value().SetVisible(False)
    for alias in ('LCSC Part','LCSC Part #','JLCPCB Part #'):
        if fp.GetField(alias):fp.SetField(alias,lcsc);fp.GetField(alias).SetVisible(False)
    x,y,angle=PLACEMENTS['J5'];fp.SetPosition(xy(x,y));fp.SetOrientationDegrees(angle)
    fp.Reference().SetPosition(xy(34.8,19.8));fp.Reference().SetTextSize(xy(.8,.8))
    fp.Reference().SetTextThickness(p.FromMM(.15));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    for pad in fp.Pads():
        net=next(net for net,pins in spec.NETS.items() if 'J5.'+pad.GetNumber() in pins);pad.SetNet(board.FindNet(net))
    def route(net,points,layer=p.F_Cu,width=1):
        for a,b in zip(points,points[1:]):
            t=p.PCB_TRACK(board);t.SetStart(xy(*a));t.SetEnd(xy(*b));t.SetLayer(layer)
            t.SetWidth(p.FromMM(width));t.SetNet(board.FindNet(net));t.SetLocked(True);board.Add(t)
    def via(net,point,diameter=1.2,drill=.6):
        v=p.PCB_VIA(board);v.SetPosition(xy(*point));v.SetLayerPair(p.F_Cu,p.B_Cu)
        v.SetWidth(p.FromMM(diameter));v.SetDrill(p.FromMM(drill));v.SetIsFree(True);board.Add(v);v.SetNet(board.FindNet(net))
    route('-12V rail',[(7,45.46),(2.25,50.21),(2.25,65.5),(13.6984,76.9484),(19.4487,76.9484)],p.B_Cu)
    route('+12V rail',[(7,58.46),(10,61.46),(10,65.7295),(19.9672,75.6967)],p.B_Cu)
    route('+5V rail',[(7,63.54),(7,71.46),(11.2364,75.6964),(35.9336,75.6964)])
    route('+15V INPUT',[(12.1733,23.5),(12.1733,36.8267),(10.5,38.5),(7,38.5)],width=1.5)
    route('+15V INPUT',[(29.7492,17.91),(34.5,17.91)],width=1.5);via('+15V INPUT',(34.5,17.91))
    route('+15V INPUT',[(37.7,6.55),(37.7,9.09),(35.5,6.89),(27,6.89),(27,17.91),(34.5,17.91)],p.B_Cu,1.5)
    route('+15V INPUT',[(34.5,17.91),(34.5,19.7625),(37.7,22.9625),(37.7,39.2625)],p.B_Cu,1.5)
    route('+15V INPUT',[(37.7,23.5),(40,21.2)],p.B_Cu,1.5);via('+15V INPUT',(40,21.2))
    route('+15V INPUT',[(40,21.2),(41.48,21.5)],width=1.5)
    route('ATT',[(37.7,11.63),(35.9546,9.8846),(35.9546,3.6621),(36.19,3.4267),(36.19,1.8)],width=.25)
    route('PDOK',[(37.7,14.17),(39.4,12.47),(39.4,4.5)],p.B_Cu,.25)
    via('PDOK',(39.4,4.5),1,.4)
    route('PDOK',[(39.4,4.5),(38.73,3.83),(38.73,1.8)],width=.25)
    # Low-current rail measurement branch; all load paths retain their wider copper.
    route(pcb_net_name('/DC-DC Conversion/-14.145V PRE'),[[32.0, 48.2], [32.0, 47.45], [32.75, 46.7], [32.75, 46.45], [39.0, 40.2], [39.0, 39.7], [39.25, 39.45], [39.25, 35.7], [39.5, 35.45], [39.5, 29.7], [39.75, 29.45], [39.75, 28.95], [40.0, 28.7], [40.0, 28.45], [40.25, 28.2], [40.25, 27.95], [40.5, 27.7], [40.5, 27.45], [40.75, 27.2], [40.75, 26.95], [41.0, 26.7], [41.0, 26.2], [41.25, 25.95], [41.25, 25.7], [41.5, 25.45], [41.5, 25.2], [41.75, 24.95], [41.75, 24.7], [42.0, 24.45], [42.0, 24.2], [42.25, 23.95], [42.25, 23.7], [42.5, 23.45], [42.5, 4.95], [43.0, 4.45], [50.25, 4.45], [50.5, 4.2], [50.75, 4.2], [51.0, 3.95], [51.1784, 3.9415]],p.B_Cu,.25)
    for label,y in [('-12V',45.46),('GND',50.54),('+12V',58.46),('+5V',63.54)]:
        for layer,x,size,angle in [(p.F_SilkS,.8,.8,90),(p.B_SilkS,2.8,1.2,0)]:
            t=p.PCB_TEXT(board);t.SetText(label);t.SetPosition(xy(x,y));t.SetLayer(layer)
            t.SetTextSize(xy(size,size));t.SetTextThickness(p.FromMM(.15));t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
            t.SetMirrored(layer==p.B_SilkS);board.Add(t)
    args.output.parent.mkdir(parents=True,exist_ok=True);p.SaveBoard(str(args.output),board)
    print('Removed affected segments:',removed);print(args.output)

if __name__=='__main__':main()
