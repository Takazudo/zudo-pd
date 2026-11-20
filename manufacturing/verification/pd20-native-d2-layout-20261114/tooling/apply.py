"""D2: apply the back-side placement and routes to the saved B20 PCB with pinned pcbnew.
usage: apply.py IN.kicad_pcb OUT.kicad_pcb plan.json"""
import json, math, sys
import wx; _a = wx.App(False)
import pcbnew as p
src, dst, plan = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
b = p.LoadBoard(src)
mm = lambda x, y: p.VECTOR2I(p.FromMM(x), p.FromMM(y))
ROOT_SHEET = 'ebdc04b8-a5cc-5f1a-b351-a66b514f754d'
def net(name):
    n = b.FindNet(name)
    if n is None:
        n = p.NETINFO_ITEM(b, name); b.Add(n); n = b.FindNet(name)
    return n
near = lambda a, x, y, tol=0.02: abs(p.ToMM(a.x) - x) < tol and abs(p.ToMM(a.y) - y) < tol
fps = {f.GetReference(): f for f in b.GetFootprints()}
# 1-3. collect removals first, then remove in one pass
tracks = list(b.GetTracks())
kill = [t for t in tracks if t.GetNetname() in plan['drop_nets']]
for x, y in plan['remove_gnd_vias']:
    hits = [t for t in tracks if t.Type() == p.PCB_VIA_T and t.GetNetname() == 'GND' and near(t.GetPosition(), x, y)]
    assert len(hits) == 1, (x, y, len(hits)); kill.append(hits[0])
for t in kill: b.Delete(t)
for ref in plan['remove_refs']: b.Delete(fps[ref])
print('removed', len(kill), 'copper items and', len(plan['remove_refs']), 'footprints')
# 4. add the back-side footprints
for e in plan['parts']:
    fp = p.FootprintLoad(plan['lib'], e['fp']); b.Add(fp)
    fp.SetFPID(p.LIB_ID('zudo-pd', e['fp'])); fp.SetReference(e['ref']); fp.SetValue(e['value'])
    fp.SetField('LCSC', e['lcsc']); lf = fp.GetField('LCSC'); lf.SetVisible(False); lf.SetTextThickness(p.FromMM(0.15))
    # library footprints can carry a default supplier alias (SOD-123 has LCSC Part C92321); the exporter requires it to match
    for alias in ('LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
        if fp.HasField(alias): fp.SetField(alias, e['lcsc'])
    fp.SetPath(p.KIID_PATH('/' + ROOT_SHEET + '/' + e['sym_uuid']))
    fp.Value().SetVisible(False)
    fp.Reference().SetLayer(p.F_Fab); fp.Reference().SetTextSize(mm(0.5, 0.5)); fp.Reference().SetTextThickness(p.FromMM(0.08))
    fp.SetPosition(mm(*e['at'][:2])); fp.Reference().SetPosition(mm(*e['at'][:2]))
    fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(e['at'][2])
    for pd in fp.Pads():
        n = e['nets'].get(pd.GetNumber())
        if n: pd.SetNet(net(n))
    got = {pd.GetNumber(): (round(p.ToMM(pd.GetPosition().x), 3), round(p.ToMM(pd.GetPosition().y), 3)) for pd in fp.Pads()}
    for num, c in e['pad_xy'].items():
        assert math.dist(got[num], c) < 0.01, (e['ref'], num, got[num], c)
# 5. add routed copper
for it in plan['items']:
    n = net(it[0])
    if it[1] == 't':
        t = p.PCB_TRACK(b); t.SetStart(mm(*it[2])); t.SetEnd(mm(*it[3])); t.SetWidth(p.FromMM(it[5]))
        t.SetLayer(b.GetLayerID(it[4])); t.SetNet(n); b.Add(t)
    else:
        v = p.PCB_VIA(b); v.SetPosition(mm(*it[2])); v.SetWidth(p.FromMM(0.8)); v.SetDrill(p.FromMM(0.3))
        v.SetLayerPair(p.F_Cu, p.B_Cu); v.SetNet(n); b.Add(v)
# 7. value/LCSC sync of the D2 gate-network resistors redrawn in the schematic (#303)
fps = {f.GetReference(): f for f in b.GetFootprints()}
for ref, (val, lcsc) in plan.get('field_sync', {}).items():
    fps[ref].SetValue(val); fps[ref].SetField('LCSC', lcsc)
b.Save(dst)
print('saved', dst)
