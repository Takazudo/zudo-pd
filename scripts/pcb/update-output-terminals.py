#!/usr/bin/env python3
"""Replace the archived guarded board's output connectors, preserving power stages.

The hash-locked input supplies the reviewed power-stage routing. Only the four
terminal branches, footprints, edge outline and associated markings change.
The new board must be refilled, checked and reference-label processed afterwards.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import tempfile
import wx
_APP = wx.App(False)
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/schgen'))
import board_b_spec as spec
from schgen_core import new_uuid
from board_b_layout import PLACEMENTS, edge_primitives
from sexp import atom,find_all,load
from pcb_common import serialize

BASE_SHA = '542ddf8d3d6cd25dacc79a87f5e4a205c8f30865874f90bd7c469684f2e1578e'
def xy(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Choose a new output PCB')
    if hashlib.sha256(args.input.read_bytes()).hexdigest()!=BASE_SHA:
        raise ValueError('Source is not the reviewed guarded PCB')
    tree=load(args.input)
    found=[]
    for fp in list(find_all(tree,'footprint')):
        ref=next(atom(v[2]) for v in find_all(fp,'property') if atom(v[1])=='Reference')
        if ref in ('J6','J7','J8','J9'):tree.remove(fp);found.append(ref)
    if set(found)!={'J6','J7','J8','J9'}:raise ValueError('Missing original terminals')
    # These branches alone terminate at the removed Fastons. No power-stage
    # copper, thermal vias, feedback routes or central ground stitches are moved.
    expected={'-12V rail':4,'+12V rail':3,'+5V rail':3,'GND':2}
    removed={name:0 for name in expected}
    for track in list(find_all(tree,'segment')):
        name=atom(find_all(track,'net')[0][1])
        if name in expected and min(float(atom(find_all(track,key)[0][1])) for key in ('start','end'))<12:
            tree.remove(track);removed[name]+=1
    if removed!=expected: raise ValueError('Reviewed terminal branches changed: '+str(removed))
    for item in list(tree):
        if not isinstance(item,list):continue
        layers=find_all(item,'layer')
        if layers and atom(layers[0][1])=='Edge.Cuts':tree.remove(item)
        elif atom(item[0])=='gr_text':
            if atom(item[1]) in ('-12V','GND','+12V','+5V'):tree.remove(item)
            elif atom(item[1])=='zudo-pd B / guarded prototype':item[1]=('str','zudo-pd B / terminal prototype')
    # Remove through the parsed tree before loading. KiCad 10's legacy SWIG
    # bindings can invalidate later wrappers after BOARD.Remove during a batch.
    with tempfile.TemporaryDirectory(prefix='terminal-placement-') as scratch:
        temporary=Path(scratch)/'board.kicad_pcb';temporary.write_text(serialize(tree)+'\n')
        board=p.LoadBoard(str(temporary))
    for ref in ('J6','J7'):
        symbol,value,lcsc,footprint,dnp,_=spec.COMPONENTS[ref]
        if lcsc!='C8465': raise ValueError('Expected reviewed two-pole terminal')
        fp=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),footprint.split(':')[1])
        board.Add(fp);fp.SetFPID(p.LIB_ID(*footprint.split(':',1)))
        fp.SetReference(ref);fp.SetValue(value);fp.SetDNP(dnp)
        fp.SetAttributes(p.FP_THROUGH_HOLE)
        fp.SetPath(p.KIID_PATH('/'+new_uuid('board-b:root')+'/'+new_uuid('board-b:'+ref+':instance')))
        fp.SetField('LCSC',lcsc);fp.GetField('LCSC').SetVisible(False)
        for alias in ('LCSC Part','LCSC Part #','JLCPCB Part #'):
            if fp.GetField(alias):fp.SetField(alias,lcsc);fp.GetField(alias).SetVisible(False)
        x,y,angle=PLACEMENTS[ref];fp.SetPosition(xy(x,y));fp.SetOrientationDegrees(angle)
        fp.Value().SetVisible(False);fp.Reference().SetTextSize(xy(.8,.8))
        fp.Reference().SetTextThickness(p.FromMM(.15));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        fp.Reference().SetPosition(xy(x,y-6.6))
        for pad in fp.Pads():
            key=ref+'.'+pad.GetNumber()
            name=next(name for name,pins in spec.NETS.items() if key in pins)
            pad.SetNet(board.FindNet(name))
    def route(name,points,layer):
        for a,b in zip(points,points[1:]):
            track=p.PCB_TRACK(board);track.SetStart(xy(*a));track.SetEnd(xy(*b))
            track.SetWidth(p.FromMM(1.0));track.SetLayer(layer);track.SetNet(board.FindNet(name))
            track.SetLocked(True);board.Add(track)
    route('-12V rail',[(7,33.46),(2.25,38.21),(2.25,59.7497),(19.4487,76.9484)],p.B_Cu)
    route('+12V rail',[(7,46.46),(10,49.46),(10,65.7295),(19.9672,75.6967)],p.B_Cu)
    route('+5V rail',[(7,51.54),(7,71.46),(11.2364,75.6964),(35.9336,75.6964)],p.F_Cu)
    # J6.1 joins the connected ground pours directly after refill.
    for primitive in edge_primitives():
        item=p.PCB_SHAPE(board);item.SetShape(p.SHAPE_T_SEGMENT)
        item.SetStart(xy(*primitive['start']));item.SetEnd(xy(*primitive['end']))
        item.SetLayer(p.Edge_Cuts);item.SetWidth(p.FromMM(.05));board.Add(item)
    for name,y in [('-12V',33.46),('GND',38.54),('+12V',46.46),('+5V',51.54)]:
        text=p.PCB_TEXT(board);text.SetText(name);text.SetPosition(xy(.8,y))
        text.SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T));text.SetTextSize(xy(.8,.8))
        text.SetTextThickness(p.FromMM(.15));text.SetLayer(p.F_SilkS);board.Add(text)
    args.output.parent.mkdir(parents=True,exist_ok=True);p.SaveBoard(str(args.output),board)
    print('Updated two terminal footprints, four output branches and plain outline:',args.output)

if __name__=='__main__': main()
