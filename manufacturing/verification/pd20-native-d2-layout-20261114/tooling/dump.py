import json,sys
import wx; _a=wx.App(False)
import pcbnew as p
b=p.LoadBoard(sys.argv[1]); mm=p.ToMM
o={'fps':[],'tracks':[],'vias':[],'zones':[]}
for fp in b.GetFootprints():
    cy=[g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() in (p.F_CrtYd,p.B_CrtYd)]
    if cy:
        box=[min(mm(c.GetLeft()) for c in cy),min(mm(c.GetTop()) for c in cy),max(mm(c.GetRight()) for c in cy),max(mm(c.GetBottom()) for c in cy)]
    else:
        bb=fp.GetBoundingBox(False,False); box=[mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom())]
    pads=[]
    for pd in fp.Pads():
        bb=pd.GetBoundingBox()
        pads.append({'num':pd.GetNumber(),'net':pd.GetNetname(),'layers':[l for l,i in (('F',p.F_Cu),('In1',p.In1_Cu),('In2',p.In2_Cu),('B',p.B_Cu)) if pd.IsOnLayer(i)],
          'bbox':[mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom())],'c':[mm(pd.GetPosition().x),mm(pd.GetPosition().y)],'drill':mm(pd.GetDrillSize().x)})
    o['fps'].append({'ref':fp.GetReference(),'fp':str(fp.GetFPID().GetLibItemName()),'side':'B' if fp.IsFlipped() else 'F','at':[mm(fp.GetPosition().x),mm(fp.GetPosition().y)],'rot':fp.GetOrientationDegrees(),'cy':box,'pads':pads})
for t in b.GetTracks():
    if t.Type()==p.PCB_VIA_T:
        o['vias'].append({'c':[mm(t.GetPosition().x),mm(t.GetPosition().y)],'d':mm(t.GetWidth(p.F_Cu)),'drill':mm(t.GetDrill()),'net':t.GetNetname()})
    else:
        o['tracks'].append({'a':[mm(t.GetStart().x),mm(t.GetStart().y)],'b':[mm(t.GetEnd().x),mm(t.GetEnd().y)],'w':mm(t.GetWidth()),'l':t.GetLayerName(),'net':t.GetNetname()})
for z in b.Zones():
    ol=z.Outline().Outline(0)
    o['zones'].append({'name':z.GetZoneName(),'net':z.GetNetname(),'rule':z.GetIsRuleArea(),'layers':[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],'prio':z.GetAssignedPriority(),'pts':[[mm(ol.CPoint(i).x),mm(ol.CPoint(i).y)] for i in range(ol.PointCount())]})
json.dump(o,open(sys.argv[2],'w'))
