#!/usr/bin/env python3
"""Relocate the PD interface and edge probes on the frozen front-stack PCB.

Preserves the power stages apart from a 1.25mm diode shift and the local U3
feedback network. The final reviewed route polylines are replayed separately.
Always refill, run native DRC/parity and regenerate populated assembly checks.
"""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
import wx
_APP=wx.App(False)
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
from pcb_common import serialize
from board_b_layout import PLACEMENTS,MOUNTING_HOLES,SUPPORT_REFS,POGO_LEGEND_CENTER
BASE_SHA='4e6e97f685d4a275c2a51a3130ec2c08da5122932800bc6f25a4fd119d807a3d'
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--routes',type=Path);args=parser.parse_args()
 if args.output.exists():raise ValueError('Choose a new output')
 if hashlib.sha256(args.input.read_bytes()).hexdigest()!=BASE_SHA:raise ValueError('Unreviewed source PCB')
 old=p.LoadBoard(str(args.input));old_pads={f.GetReference()+'.'+a.GetNumber():(round(p.ToMM(a.GetPosition().x),4),round(p.ToMM(a.GetPosition().y),4)) for f in old.GetFootprints() for a in f.Pads()}
 tree=load(args.input);removed={}
 ground_ends={old_pads[k] for k in ['C5.2','C46.2','R4.2','P1.3']}
 old_pre_ends={old_pads[k] for k in ['C32.2','R3.1']}
 for segment in list(find_all(tree,'segment')):
  net=atom(find_all(segment,'net')[0][1]);layer=atom(find_all(segment,'layer')[0][1]);width=float(atom(find_all(segment,'width')[0][1]))
  ends=[tuple(float(atom(v)) for v in find_all(segment,k)[0][1:3]) for k in ('start','end')]
  remove=(net in ('ATT','PDOK','Net-(U3-Feedback)') or (net=='GND' and (any(pt in ground_ends for pt in ends) or (min(pt[0] for pt in ends)<40 and min(pt[1] for pt in ends)<34)))
    or (net=='+15V INPUT' and width==1.5 and min(pt[1] for pt in ends)<38.6)
    or ('+13.44V PRE' in net and min(pt[1] for pt in ends)<4.0)
    or ('+6.519V PRE' in net and layer=='F.Cu' and max(pt[0] for pt in ends)<50 and min(pt[1] for pt in ends)<29)
    or ('-14.145V PRE' in net and ((layer=='B.Cu' and width==.25 and min(pt[0] for pt in ends)>=32 and max(pt[1] for pt in ends)<=48.2) or (layer=='F.Cu' and min(pt[1] for pt in ends)<4.0))))
  if remove:tree.remove(segment);removed[net]=removed.get(net,0)+1
  else:
   for key in ('start','end'):
    node=find_all(segment,key)[0];pt=tuple(float(atom(v)) for v in node[1:3])
    if pt in (old_pads['D2.1'],old_pads['D2.2']):node[1]=('atom',str(pt[0]-1.25))
 for v in list(find_all(tree,'via')):
  net=atom(find_all(v,'net')[0][1]);at=tuple(float(atom(x)) for x in find_all(v,'at')[0][1:3])
  if net in ('ATT','PDOK','Net-(U3-Feedback)') or (net=='+15V INPUT' and at[1]<38.6 and at!=(40,21.2)) or ('-14.145V PRE' in net and at[1]<5):tree.remove(v)
 for f in list(find_all(tree,'footprint')):
  props={atom(n[1]):atom(n[2]) for n in find_all(f,'property')}
  if props['Reference'] in SUPPORT_REFS:tree.remove(f)
 for text in find_all(tree,'gr_text'):
  if atom(text[1])=='TP3 13.44V / TP4 6.519V / TP5 -14.145V':find_all(text,'at')[0][1:3]=[('atom',str(x)) for x in POGO_LEGEND_CENTER]
 with tempfile.TemporaryDirectory() as temp:
  path=Path(temp)/'input.kicad_pcb';path.write_text(serialize(tree)+'\n');b=p.LoadBoard(str(path))
 fps={f.GetReference():f for f in b.GetFootprints()}
 for ref in ('J5','C5','C46','C32','R3','R4','D2','P1','TP3','TP4','TP5'):
  f=fps[ref];x,y,angle=PLACEMENTS[ref];f.SetPosition(xy(x,y));f.SetOrientationDegrees(angle)
  f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 refs={'J5':(34.4,17.8),'C5':(18,12),'C46':(28,3.3),'C32':(26,20),'R3':(22.8,27.7),'R4':(23.6,26),'D2':(33.75,30.4),'C8':(30.7,41),'P1':(60,5.8),'TP3':(66.35,4.5),'TP4':(68.89,4.5),'TP5':(71.43,4.5)}
 for ref,pos in refs.items():fps[ref].Reference().SetPosition(xy(*pos))
 fps['PTC1'].Reference().SetPosition(xy(103.5,7.5));fps['PTC1'].Reference().SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T))
 for i,pos in enumerate(MOUNTING_HOLES,1):
  ref='H'+str(i)
  if ref in SUPPORT_REFS:
   f=p.FootprintLoad(str(ROOT/'footprints/kicad/zudo-power.pretty'),'MountingHole_HC11_3mm');b.Add(f);f.SetReference(ref);f.SetFPID(p.LIB_ID('zudo-pd','MountingHole_HC11_3mm'));f.SetAttributes(p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);f.Value().SetVisible(False);f.Reference().SetVisible(False)
  else:f=fps[ref]
  f.SetPosition(xy(*pos))
 def route(net,points,width,layer):
  for a,c in zip(points,points[1:]):
   t=p.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);b.Add(t);t.SetNet(b.FindNet(net))
 def via(net,point,diameter=1.5,drill=.6):
  if any(a.GetAttribute()==p.PAD_ATTRIB_PTH and a.GetNetname()==net and a.HitTest(xy(*point)) for f in b.GetFootprints() for a in f.Pads()):return
  v=p.PCB_VIA(b);v.SetPosition(xy(*point));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetWidth(p.FromMM(diameter));v.SetDrill(p.FromMM(drill));v.SetIsFree(True);b.Add(v);v.SetNet(b.FindNet(net))
 route('+15V INPUT',[(37.2,18.55),(37.2,21.09),(40,21.2)],1.5,p.B_Cu)
 route('+15V INPUT',[(40,21.2),(41.48,21.5)],1.5,p.F_Cu)
 route('+15V INPUT',[(13.5,6),(13.5,2.5)],1.5,p.F_Cu);via('+15V INPUT',(13.5,2.5))
 route('+15V INPUT',[(29.52,6.5),(31.5,4.52),(31.5,2.5),(13.5,2.5)],1.5,p.F_Cu)
 # Local feedback network, kept away from U3's switch node.
 route('Net-(U3-Feedback)',[(25,22),(25,23),(24,24),(24,29),(25.25,29)],.25,p.F_Cu)
 route('Net-(U3-Feedback)',[(26,26.75),(24,26.75)],.25,p.F_Cu)
 route('Net-(U3-Feedback)',[(24,29),(24,34.3),(28.16,34.3)],.25,p.F_Cu)
 pre='{slash}DC-DC Conversion{slash}+6.519V PRE'
 route(pre,[(27,22),(27,23),(28,24),(28,29),(26.75,29)],.25,p.F_Cu)
 # Return the local divider ground island through a via beside, outside, its pad.
 route('GND',[(26,25.25),(26,24)],.4,p.F_Cu);via('GND',(26,24),1,.4)
 # Paste-free test-pad escapes; only measurement current uses these branches.
 for ref in ('TP3','TP4','TP5'):
  pad=next(iter(fps[ref].Pads()));x,y=PLACEMENTS[ref][:2];net=pad.GetNetname()
  route(net,[(x,y),(x,3.8)],.25,p.F_Cu);via(net,(x,3.8),1,.4)
 if args.routes:
  for item in json.loads(args.routes.read_text()):
   for a,c in zip(item['points'],item['points'][1:]):
    if a==c:continue
    if a[2]!=c[2]:via(item['net'],a[:2],item['via_diameter'],item['via_drill'])
    else:route(item['net'],[a[:2],c[:2]],item['width'],[p.F_Cu,p.B_Cu][a[2]])
 args.output.parent.mkdir(parents=True,exist_ok=True);p.SaveBoard(str(args.output),b)
 print('Removed affected segments',removed);print(args.output)
if __name__=='__main__':main()
