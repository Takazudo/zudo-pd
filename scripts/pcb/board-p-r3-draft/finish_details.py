"""Apply reviewed P-r3 contact ordinals and reverse-side role tables after fill.

Usage: pinned pcbnew Python finish_details.py INPUT.kicad_pcb OUTPUT.kicad_pcb
Preserves every serialized object except the exact 34 artwork UUIDs recorded
in OUTPUT.proposal.json. Never fills zones, changes pads or edits the library.
The final-stage transform is idempotent. Native DRC/parity is a separate gate.
"""
from pathlib import Path
import sys,json,hashlib,math,uuid
import wx
APP=wx.GetApp() or wx.App(False)
import pcbnew as p
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
source,destination=map(Path,sys.argv[1:])
if source.resolve()==destination.resolve():raise ValueError('Use a separate candidate destination; preserve input proof')
constraints=json.loads((ROOT/'boards/board-p/r3-draft/fabrication-legend-constraints.json').read_text())['constraints']
if constraints!={'minimum_text_height_mm':1.0,'minimum_character_line_width_mm':.15,'minimum_pad_to_silkscreen_mm':.15}:raise ValueError('Fabrication constraints changed; review artwork before use')
board=p.LoadBoard(str(source))
fps={fp.GetReference():fp for fp in board.GetFootprints()}
plans={'J2':[('SCL','SCL','1','SCL'),('SDA','SDA','2','SDA'),('GND','GND','3','GND'),('NC','NC','4','unconnected-(J2-Pad4)')],
       'J3':[('CC1D','CC1D','1','CC1DB'),('CC2D','CC2D','2','CC2DB'),('VREG','VREG','3','VREG_2V7'),('VDD','VBUS','4','VBUS_IN'),('RST','GND','5','GND'),('ATT','ATT','6','ATT'),('PDOK','PDOK','7','PDOK'),('VBEN','VBEN','8','VBEN_PIN')]}
changes=[];ids=set()
def point(item):q=item.GetPosition();return [p.ToMM(q.x),p.ToMM(q.y)]
def size(item):q=item.GetTextSize();return [p.ToMM(q.x),p.ToMM(q.y)]
for ref,rows in plans.items():
 fp=fps[ref];texts={item.GetText():item for item in fp.GraphicalItems() if isinstance(item,p.PCB_TEXT) and item.GetLayer()==p.F_SilkS};pads={pad.GetNumber():pad for pad in fp.Pads()}
 original={row[0] for row in rows}|{'<-- EDGE'}
 finished={row[2] for row in rows}|{'EDGE'}
 if set(texts) not in [original,finished]:raise ValueError((ref,'unexpected functional text set',set(texts)))
 already_finished=set(texts)==finished
 for old,new,pin,net in rows:
  pad=pads[pin]
  if pad.GetNetname()!=net:raise ValueError((ref,pin,net,pad.GetNetname()))
  text=texts[pin if already_finished else old];before={'text':text.GetText(),'at':point(text),'size':size(text),'angle':text.GetTextAngle().AsDegrees()}
  at=[3.85 if ref=='J2' else 23.15, 25.3 if ref=='J3' and pin=='4' else point(pad)[1]]
  new=str(pin)
  nearest=min(pads.values(),key=lambda other:math.dist(at,point(other)))
  if nearest.GetNumber()!=pin:raise ValueError('Ordinal would be closer to another contact')
  text.SetText(new);text.SetTextSize(p.VECTOR2I(p.FromMM(1.0),p.FromMM(1.0)));text.SetTextThickness(p.FromMM(.15));text.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));text.SetPosition(p.VECTOR2I(*map(p.FromMM,at)))
  uid=text.m_Uuid.AsString();ids.add(uid);changes.append({'owner':ref,'pad':pin,'net':net,'uuid':uid,'before':before,'after':{'text':new,'at':at,'size':size(text),'angle':0}})
 edge=texts['EDGE' if already_finished else '<-- EDGE'];before={'text':edge.GetText(),'at':point(edge),'size':size(edge)};at=[3.8,23.5] if ref=='J2' else [25.2,14.7]
 edge.SetText('EDGE');edge.SetTextSize(p.VECTOR2I(p.FromMM(1.0),p.FromMM(1.0)));edge.SetTextThickness(p.FromMM(.15));edge.SetTextAngle(p.EDA_ANGLE(0 if ref=='J2' else 90,p.DEGREES_T));edge.SetPosition(p.VECTOR2I(*map(p.FromMM,at)))
 ids.add(edge.m_Uuid.AsString());changes.append({'owner':ref,'uuid':edge.m_Uuid.AsString(),'before':before,'after':{'text':'EDGE','at':at,'size':size(edge),'angle':edge.GetTextAngle().AsDegrees()}})
 boundary=0 if ref=='J2' else 27;inset=.3 if ref=='J2' else 26.7
 lines=[item for item in fp.GraphicalItems() if isinstance(item,p.PCB_SHAPE) and item.GetLayer()==p.F_SilkS and abs(p.ToMM(item.GetStart().x)-(inset if already_finished else boundary))<1e-6 and abs(p.ToMM(item.GetEnd().x)-(inset if already_finished else boundary))<1e-6]
 if len(lines)!=1:raise ValueError((ref,'edge guide count',len(lines)))
 line=lines[0];a=line.GetStart();b=line.GetEnd();a.x=p.FromMM(inset);b.x=p.FromMM(inset);line.SetStart(a);line.SetEnd(b)
 ids.add(line.m_Uuid.AsString());changes.append({'owner':ref,'uuid':line.m_Uuid.AsString(),'edge_guide_x_before':boundary,'edge_guide_x_after':inset})
# Readable role tables on the reverse, outside component courtyards and holes.
for ref,rows in plans.items():
    x,y=(13.5,1.2) if ref=='J2' else (23.0,8.2)
    labels=[ref+' MAP']+[pin+' '+role for _old,role,pin,_net in rows]
    for index,label in enumerate(labels):
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'zudo-pd/r3/probe-legend/'+ref+'/'+str(index)))
        matches=[item for item in board.GetDrawings() if item.m_Uuid.AsString()==uid]
        if len(matches)>1 or (matches and not isinstance(matches[0],p.PCB_TEXT)):raise ValueError('Legend UUID collision')
        text=matches[0] if matches else p.PCB_TEXT(board)
        text.SetText(label);text.SetLayer(p.B_SilkS);text.SetMirrored(True)
        text.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)));text.SetTextThickness(p.FromMM(.15));text.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        text.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y+1.35*index)))
        text.m_Uuid.Clone(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'zudo-pd/r3/probe-legend/'+ref+'/'+str(index)))))
        if not matches:board.Add(text)
        ids.add(text.m_Uuid.AsString());changes.append({'owner':ref,'uuid':text.m_Uuid.AsString(),'added_role_legend':label,'at':point(text),'layer':'B.Silkscreen','size':size(text),'stroke_mm':.15})

def bounds(item):
    box=item.GetBoundingBox();return tuple(p.ToMM(v) for v in [box.GetLeft(),box.GetTop(),box.GetRight(),box.GetBottom()])
def gap(a,b):
    return math.hypot(max(b[0]-a[2],a[0]-b[2],0),max(b[1]-a[3],a[1]-b[3],0))
functional=[item for fp in board.GetFootprints() for item in fp.GraphicalItems() if isinstance(item,p.PCB_TEXT) and item.m_Uuid.AsString() in ids]
functional += [item for item in board.GetDrawings() if isinstance(item,p.PCB_TEXT) and item.m_Uuid.AsString() in ids]
fab=[]
for text in functional:
    box=bounds(text);mask=p.F_Mask if text.GetLayer()==p.F_SilkS else p.B_Mask
    contacts=[]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnLayer(mask):continue
            b=bounds(pad);margin=max(0,p.ToMM(pad.GetSolderMaskExpansion(mask)));b=(b[0]-margin,b[1]-margin,b[2]+margin,b[3]+margin)
            contacts.append((gap(box,b),fp.GetReference()+'.'+pad.GetNumber()))
    minimum,closest=min(contacts)
    fab.append({'text':text.GetText(),'layer':board.GetLayerName(text.GetLayer()),'at':point(text),'bbox_mm':box,'minimum_pad_opening_gap_mm':minimum,'closest_pad':closest,'edge_gap_mm':min(box[0],box[1],27-box[2],40-box[3])})
for ref in ['Q3','D13']:
 field=fps[ref].Reference();ids.add(field.m_Uuid.AsString())
 # Preserve the actual reference field on its own fabrication layer.
 field.SetLayer(p.F_Fab if ref=='Q3' else p.B_Fab)
 changes.append({'uuid':field.m_Uuid.AsString(),'reference':ref,'action':'move reference from silk to same-side Fab; existing other Fab objects unchanged'})
d5=fps['D5'];pads={pad.GetNumber():pad for pad in d5.Pads()}
if pads['1'].GetNetname()!='GND' or pads['4'].GetNetname()!='VBUS_IN':raise ValueError('D5 pin identity changed')
small=next(g for g in d5.GraphicalItems() if g.m_Uuid.AsString()=='958fb347-76a6-54a9-bb7e-00068731d04e')
large=next(g for g in d5.GraphicalItems() if g.m_Uuid.AsString()=='0914bcb9-da3f-5ef6-b0fb-4571a332e33d')
ids.update([small.m_Uuid.AsString(),large.m_Uuid.AsString()]);small.SetLayer(p.Cmts_User)
large.SetCenter(p.VECTOR2I(p.FromMM(10.05),p.FromMM(12.1)));large.SetEnd(p.VECTOR2I(p.FromMM(10.15),p.FromMM(12.1)));large.SetWidth(p.FromMM(.15));large.SetFilled(True)
changes.extend([{'uuid':small.m_Uuid.AsString(),'action':'retain tiny duplicate on nonmanufacturing comments layer'}, {'uuid':large.m_Uuid.AsString(),'action':'single filled pin1 corner circle','center_mm':[10.05,12.1],'radius_mm':.10,'stroke_mm':.15}])

# The native shape bbox conservatively includes the printed circle and stroke.
box=bounds(large);polarity_gaps=[]
for fp in board.GetFootprints():
 for pad in fp.Pads():
  if not pad.IsOnLayer(p.F_Mask):continue
  pb=bounds(pad);margin=max(0,p.ToMM(pad.GetSolderMaskExpansion(p.F_Mask)))
  pb=(pb[0]-margin,pb[1]-margin,pb[2]+margin,pb[3]+margin)
  polarity_gaps.append((gap(box,pb),fp.GetReference()+'.'+pad.GetNumber()))
if min(polarity_gaps)[0]<.15:raise ValueError(('D5 cue mask-opening clearance',min(polarity_gaps)))
# Exact owner maxima: D5 DRV2.1x2.1; adjacent Q3 SON3.25x3.25.
# Reject changed placements before applying these reviewed body rectangles.
if point(d5)!=[11.3,10.6] or point(fps['Q3'])!=[7.9,11.5]:raise ValueError('Polarity cue placement context changed')
bodies={'D5':[10.25,9.55,12.35,11.65],'Q3':[6.275,9.875,9.525,13.125]}
body_gaps={ref:gap(box,body) for ref,body in bodies.items()}
if min(body_gaps.values())<.15:raise ValueError(('D5 cue body clearance',body_gaps))
nearest=min(pads.values(),key=lambda pad:math.dist([10.05,12.1],point(pad)))
if nearest.GetNumber()!='1':raise ValueError('Cue is not closest to D5 pin1')
polarity_checks={'cue_bbox_mm':box,'minimum_pad_opening_gap':min(polarity_gaps),'maximum_body_gaps_mm':body_gaps,'cue_nearest_pin':'D5.1','scope':'Two silk reference fields moved to same-side Fab; duplicate tiny D5 dot retained on comments layer; one printed pin1 cue. No body, pad, model or copper changes.'}

if len(ids)!=34:raise ValueError('Expected exactly34 reviewed artwork objects')
# Artwork-only save must not rewrite either source or destination project settings.
if not p.SaveBoard(str(destination),board,True):raise RuntimeError('Native artwork save failed')
def serialize(node):
 if isinstance(node,list):return '('+' '.join(serialize(value) for value in node)+')'
 return json.dumps(node[1],ensure_ascii=False) if node[0]=='str' else node[1]
def immutable(node):
 if not isinstance(node,list):return node
 direct=find_all(node,'uuid')
 if direct and atom(direct[0][1]) in ids:return None
 return [value for child in node if (value:=immutable(child)) is not None]
a=hashlib.sha256(serialize(immutable(load(str(source)))).encode()).hexdigest();b=hashlib.sha256(serialize(immutable(load(str(destination)))).encode()).hexdigest()
report={'executed_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_pcb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_pcb_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'changed_items':changes,'unchanged_except_approved_artwork':a==b,'immutable_before_sha256':a,'immutable_after_sha256':b,'fabrication_checks':fab,'scope':'Only J2/J3 functional silk text, their two edge guides, the explicit B-side role tables, Q3/D13 reference layers and two D5 pin1 cue objects may change. Pads, copper/fills, nets, placement, outlines, models and all other artwork remain byte-semantic identical.'}
report['polarity_checks']=polarity_checks
report['source_hashes']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [Path(__file__),ROOT/'boards/board-p/r3-draft/fabrication-legend-constraints.json',ROOT/'.claude/skills/component-tvs2200drvr/facts.json',ROOT/'.claude/skills/component-tvs2200drvr/pin-map.json',ROOT/'.claude/skills/component-csd18543q3a/facts.json']}
report['pcb_sha256']=report['candidate_pcb_sha256']
destination.with_suffix('.proposal.json').write_text(json.dumps(report,indent=2)+'\n')
if a!=b:raise ValueError('Final artwork stage changed more than approved artwork nodes')
print('PASS: exact non-artwork fingerprint; changed',len(ids),'functional/guide objects')

failures=[row for row in fab if row['minimum_pad_opening_gap_mm']<.15-1e-6 or row['edge_gap_mm']<.2-1e-6]
if failures:raise ValueError('Published fabrication clearance guard: '+json.dumps(failures))
print('PASS: functional legend1.0mm/.15mm with conservative pad-opening gaps>=.15mm and edge gaps>=.2mm')
