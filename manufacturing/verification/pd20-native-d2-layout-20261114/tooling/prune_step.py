"""Delete (or trim to the last attachment) the items KiCad's DRC reports as dangling. usage: prune_step.py IN OUT drc.json log.json"""
import json, math, sys
import wx; _a = wx.App(False)
import pcbnew as p
b = p.LoadBoard(sys.argv[1]); r = json.load(open(sys.argv[3]))
ids = {i['uuid'] for v in r['violations'] if v['type'] in ('track_dangling', 'via_dangling') for i in v['items']}
P2 = lambda v: (p.ToMM(v.x), p.ToMM(v.y))
def segd(q, a, c):
    dx, dy = c[0]-a[0], c[1]-a[1]; n = dx*dx+dy*dy
    t = 0 if n == 0 else max(0, min(1, ((q[0]-a[0])*dx+(q[1]-a[1])*dy)/n))
    return math.dist(q, (a[0]+t*dx, a[1]+t*dy)), t
tracks = list(b.GetTracks()); log = json.load(open(sys.argv[4])) if len(sys.argv) > 4 and __import__('os').path.exists(sys.argv[4]) else []
kill = []
for t in tracks:
    if t.m_Uuid.AsString() not in ids: continue
    if t.GetNetname() == 'GND': continue
    if t.Type() == p.PCB_VIA_T:
        kill.append(t); log.append([t.GetNetname(), 'via', P2(t.GetPosition())]); continue
    a, z = P2(t.GetStart()), P2(t.GetEnd())
    # which end is free: an end touching nothing else of the net
    def touched(q):
        for o in tracks:
            if o is t or o.GetNetname() != t.GetNetname(): continue
            if o.Type() == p.PCB_VIA_T:
                if math.dist(q, P2(o.GetPosition())) < 0.4: return True
            elif o.GetLayer() == t.GetLayer() and segd(q, P2(o.GetStart()), P2(o.GetEnd()))[0] < p.ToMM(o.GetWidth())/2: return True
        for f in b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == t.GetNetname() and pd.IsOnLayer(t.GetLayer()) and pd.HitTest(p.VECTOR2I(p.FromMM(q[0]), p.FromMM(q[1]))): return True
        return False
    ta, tz = touched(a), touched(z)
    if math.dist(a, z) < 0.3: ta = tz = False
    if ta and tz:   # dangling by KiCad but both ends touch: leave for review
        log.append([t.GetNetname(), 'kept-both-ends-touch', a, z]); continue
    if not ta and not tz:
        kill.append(t); log.append([t.GetNetname(), t.GetLayerName(), a, z]); continue
    keep, free = (a, z) if ta else (z, a)
    att = []
    for o in tracks:
        if o is t or o.GetNetname() != t.GetNetname(): continue
        pts = [P2(o.GetPosition())] if o.Type() == p.PCB_VIA_T else ([P2(o.GetStart()), P2(o.GetEnd())] if o.GetLayer() == t.GetLayer() else [])
        for q in pts:
            d, u = segd(q, keep, free)
            if d < p.ToMM(t.GetWidth())/2 and 1e-6 < u < 1 - 1e-6: att.append(u)
    if not att:
        kill.append(t); log.append([t.GetNetname(), t.GetLayerName(), a, z]); continue
    u = max(att); q = (keep[0] + (free[0]-keep[0])*u, keep[1] + (free[1]-keep[1])*u)
    v = p.VECTOR2I(p.FromMM(q[0]), p.FromMM(q[1]))
    if ta: t.SetEnd(v)
    else: t.SetStart(v)
    log.append([t.GetNetname(), 'trim ' + t.GetLayerName(), free, q])
for t in kill: b.Delete(t)
b.Save(sys.argv[2]); json.dump(log, open(sys.argv[4], 'w'), indent=0)
print('dangling', len(ids), 'deleted', len(kill))
