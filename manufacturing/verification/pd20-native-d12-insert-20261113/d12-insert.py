"""D12: insert R77-R80 (0402 C25741) into the saved B20 PCB with pinned pcbnew. usage: d12-insert.py IN.kicad_pcb OUT.kicad_pcb plan.json"""
import json,math,sys,pcbnew as p
src,dst,plan=sys.argv[1],sys.argv[2],json.load(open(sys.argv[3]))
b=p.LoadBoard(src)
mm=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
ROOT='ebdc04b8-a5cc-5f1a-b351-a66b514f754d'
LIB=plan['lib']
def net(name):
    n=b.FindNet(name)
    if n is None:
        n=p.NETINFO_ITEM(b,name); b.Add(n); n=b.FindNet(name)
    return n
def near(a,x,y,tol=0.02): return abs(p.ToMM(a.x)-x)<tol and abs(p.ToMM(a.y)-y)<tol
def find_seg(layer,a,c,netname):
    hits=[t for t in b.GetTracks() if t.Type()==p.PCB_TRACE_T and t.GetLayerName()==layer and t.GetNetname()==netname and
          ((near(t.GetStart(),*a) and near(t.GetEnd(),*c)) or (near(t.GetStart(),*c) and near(t.GetEnd(),*a)))]
    assert len(hits)==1,(layer,a,c,netname,len(hits)); return hits[0]
def find_via(x,y,netname):
    hits=[t for t in b.GetTracks() if t.Type()==p.PCB_VIA_T and near(t.GetPosition(),x,y) and t.GetNetname()==netname]
    assert len(hits)==1,(x,y,netname); return hits[0]
def seg(layer,a,c,n,w=0.2):
    t=p.PCB_TRACK(b); t.SetStart(mm(*a)); t.SetEnd(mm(*c)); t.SetWidth(p.FromMM(w)); t.SetLayer(b.GetLayerID(layer)); t.SetNet(n); b.Add(t)
def via(x,y,n):
    v=p.PCB_VIA(b); v.SetPosition(mm(x,y)); v.SetWidth(p.FromMM(0.8)); v.SetDrill(p.FromMM(0.3)); v.SetLayerPair(p.F_Cu,p.B_Cu); v.SetNet(n); b.Add(v)
fps={f.GetReference():f for f in b.GetFootprints()}
for e in plan['parts']:
    div,inn=net(e['div']),net(e['in'])
    fp=p.FootprintLoad(LIB,'R0402'); b.Add(fp)
    fp.SetFPID(p.LIB_ID('zudo-pd','R0402')); fp.SetReference(e['ref']); fp.SetValue('100k')
    fp.SetField('LCSC','C25741'); fp.GetField('LCSC').SetVisible(False); fp.GetField('LCSC').SetTextThickness(p.FromMM(0.15))
    fp.SetPath(p.KIID_PATH('/'+ROOT+'/'+e['sym_uuid']))
    fp.Value().SetVisible(False); fp.Reference().SetLayer(p.F_Fab); fp.Reference().SetTextSize(mm(0.5,0.5)); fp.Reference().SetTextThickness(p.FromMM(0.08))
    fp.SetOrientationDegrees(e['rot']); fp.SetPosition(mm(*e['at'])); fp.Reference().SetPosition(mm(*e['at'])); fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    pads={pd.GetNumber():pd for pd in fp.Pads()}
    d1=math.dist([p.ToMM(pads['1'].GetPosition().x),p.ToMM(pads['1'].GetPosition().y)],e['div_target'])
    d2=math.dist([p.ToMM(pads['2'].GetPosition().x),p.ToMM(pads['2'].GetPosition().y)],e['div_target'])
    if d2<d1 and not e.get("noflip"): fp.SetOrientationDegrees(e['rot']+180)
    pads['1'].SetNet(div); pads['2'].SetNet(inn)
    P1=[p.ToMM(pads['1'].GetPosition().x),p.ToMM(pads['1'].GetPosition().y)];P2=[p.ToMM(pads['2'].GetPosition().x),p.ToMM(pads['2'].GetPosition().y)]
    print(e['ref'],'pad1',P1,'pad2',P2)
    # repin
    u,pn=e['repin'].split('.'); [pd for pd in fps[u].Pads() if pd.GetNumber()==pn][0].SetNet(inn)
    for r in e.get('remove',[]): b.Remove(find_seg(r[0],r[1],r[2],e['div']))
    for r in e.get('renet_segs',[]): find_seg(r[0],r[1],r[2],e['div']).SetNet(inn)
    for v in e.get('remove_vias',[]): b.Remove(find_via(v[0],v[1],e['div']))
    for v in e.get('renet_vias',[]): find_via(v[0],v[1],e['div']).SetNet(inn)
    for s in e.get('add',[]):
        n=div if s['net']=='div' else inn
        pts=[P1 if q=='pad1' else P2 if q=='pad2' else q for q in s['pts']]
        if s['k']=='via': via(*pts[0],n)
        else:
            for a,c in zip(pts,pts[1:]): seg(s['layer'],a,c,n)
b.Save(dst)
print('saved',dst)
