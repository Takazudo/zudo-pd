"""Owned B20 finishing details: probe legend and proven dead-end fanout cleanup.

The CLI updates an existing routed board without rerouting. Native DRC is required
on its result. The builder/applicator use the same functions during regeneration.
"""
import math
import sys
import wx
_KICAD_APP = wx.GetApp() or wx.App(False)
import pcbnew as p


def probe_labels(board):
    fp = next(f for f in board.GetFootprints() if f.GetReference() == 'P1')
    labels = sorted((t for t in fp.GraphicalItems() if isinstance(t, p.PCB_TEXT)), key=lambda t: t.GetPosition().x)
    if len(labels) != 4:
        raise RuntimeError('P1 must retain four unambiguous contact ordinals')
    pads = sorted(fp.Pads(), key=lambda pad: int(pad.GetNumber()))
    if [pad.GetNumber() for pad in pads] != ['1', '2', '3', '4']:
        raise RuntimeError('P1 contact numbers changed')
    nets = [pad.GetNetname() for pad in pads]
    if nets[1:3] != ['PDOK', 'GND'] or any(not (nets[i].startswith('unconnected-(P1-') and nets[i].endswith(f'-Pad{i+1})')) for i in (0, 3)):
        raise RuntimeError('P1 role legend disagrees with actual PDOK/GND/NC nets')
    for i in (0, 3):
        if sum(pad.GetNetname() == nets[i] for f in board.GetFootprints() for pad in f.Pads()) != 1 or any(t.GetNetname() == nets[i] for t in board.GetTracks()):
            raise RuntimeError('P1 NC contact has another electrical connection')
    for number, (text, pad) in enumerate(zip(labels, pads), 1):
        text.SetText(str(number))
        text.SetTextSize(p.VECTOR2I(p.FromMM(1), p.FromMM(1)))
        text.SetTextThickness(p.FromMM(.15))
        text.SetPosition(p.VECTOR2I(pad.GetPosition().x + p.FromMM(1.27), pad.GetPosition().y))
        text.SetTextAngle(p.EDA_ANGLE(0, p.DEGREES_T))
    legend_text = 'P1 LEFT>RIGHT: NC PDOK GND NC'
    owned_legends = {legend_text, 'P1 1:NC 2:PDOK 3:GND 4:NC', 'P1 PAD > #  1:NC 2:PDOK 3:GND 4:NC', 'P1 LEFT>RIGHT: 1 NC  2 PDOK  3 GND  4 NC'}
    legends = [x for x in board.GetDrawings() if isinstance(x, p.PCB_TEXT) and x.GetText() in owned_legends]
    if len(legends) > 1:
        raise RuntimeError('Duplicate owned P1 role legends')
    legend = legends[0] if legends else p.PCB_TEXT(board)
    legend.SetText(legend_text)
    legend.SetTextSize(p.VECTOR2I(p.FromMM(1), p.FromMM(1)))
    legend.SetTextThickness(p.FromMM(.15))
    legend.SetPosition(p.VECTOR2I(p.FromMM(92.2), p.FromMM(1.2)))
    legend.SetLayer(p.F_SilkS)
    from deterministic_ids import drawing_id
    drawing_id(legend)
    if not legends:
        board.Add(legend)


def rail_typography(board):
    """B20-local 1 mm front labels; shared Board B/P15 contract stays unchanged."""
    from deterministic_ids import stable_id
    mappings = {'-12V': ('J6', '2', 'M12_OUT', 45.46), 'GND': ('J6', '1', 'GND', 50.54),
                '+12V': ('J7', '2', 'P12_OUT', 58.46), '+5V': ('J7', '1', 'P5_OUT', 63.54)}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    labels = {}
    for text, (ref, pin, net, y) in mappings.items():
        pad = next(q for q in fps[ref].Pads() if q.GetNumber() == pin)
        found = [t for t in board.GetDrawings() if isinstance(t, p.PCB_TEXT) and t.GetLayer() == p.F_SilkS and t.GetText() == text]
        if len(found) != 1 or pad.GetNetname() != net:
            raise RuntimeError(f'{text}: terminal label/net identity changed')
        label = found[0]
        if (label.GetPosition() != p.VECTOR2I(p.FromMM(.8),p.FromMM(y)) or label.IsMirrored()
                or abs(label.GetTextAngle().AsDegrees()-90)>1e-6):
            raise RuntimeError(f'{text}: front label location/orientation changed')
        labels[text] = label
    # Validate before mutating typography. Outline checks below also reject
    # changed source shapes or any incomplete previously clipped representation.
    for label in labels.values():
        label.SetTextSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)))
        label.SetTextThickness(p.FromMM(.15))
    for ref, cy, names in [('J6',48.,['-12V','GND']),('J7',61.,['+12V','+5V'])]:
        fp = fps[ref]
        if fp.GetPosition()!=p.VECTOR2I(p.FromMM(7),p.FromMM(cy)) or abs(fp.GetOrientation().AsDegrees()-90)>1e-6:
            raise RuntimeError(f'{ref}: terminal placement changed')
        x0,x1,y0,y1 = map(p.FromMM,[1.38,11.62,cy-5.2,cy+5.2])
        intervals=[]
        for name in names:
            box=labels[name].GetBoundingBox();gap=p.FromMM(.21) # .15 clearance + .06 outline half-width
            intervals.append((box.GetTop()-gap,box.GetBottom()+gap))
        intervals.sort()
        segments=[((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1))]
        cursor=y0
        for lo,hi in intervals:
            if lo<cursor or hi>y1:raise RuntimeError('Label clip exceeds reviewed terminal edge')
            if lo>cursor:segments.append(((x0,cursor),(x0,lo)))
            cursor=hi
        if cursor<y1:segments.append(((x0,cursor),(x0,y1)))
        shapes=[g for g in fp.GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_SilkS]
        def line_key(g):
            return (tuple(sorted((point(g.GetStart()),point(g.GetEnd())))),p.ToMM(g.GetWidth()))
        expected={ (tuple(sorted(((a[0]/1e6,a[1]/1e6),(b[0]/1e6,b[1]/1e6)))),.12) for a,b in segments }
        if len(shapes)==len(segments) and all(g.GetShape()==p.SHAPE_T_SEGMENT for g in shapes):
            if {line_key(g) for g in shapes}!=expected:raise RuntimeError('Previously clipped terminal silk changed')
            continue
        if len(shapes)!=1 or shapes[0].GetShape()!=p.SHAPE_T_RECT:raise RuntimeError('Unexpected terminal silk primitives')
        rect=shapes[0];start,end=rect.GetStart(),rect.GetEnd()
        if (sorted([start.x,end.x])!=[x0,x1] or sorted([start.y,end.y])!=[y0,y1]
                or rect.GetWidth()!=p.FromMM(.12)):
            raise RuntimeError('Terminal rectangle geometry changed')
        fp.Delete(rect)
        for i,(start,end) in enumerate(segments):
            g=p.PCB_SHAPE(fp);g.SetShape(p.SHAPE_T_SEGMENT);g.SetLayer(p.F_SilkS);g.SetWidth(p.FromMM(.12))
            g.SetStart(p.VECTOR2I(*start));g.SetEnd(p.VECTOR2I(*end));stable_id(g,'terminal-label-silk',ref,i);fp.Add(g)


def artwork(board):
    probe_labels(board)
    rail_typography(board)


def save_preserving_projects(board, output, source):
    """Pinned KiCad 10.0.6 saves PCB only; never rewrite project sidecars."""
    from pathlib import Path
    paths = {Path(source).with_suffix('.kicad_pro'), Path(output).with_suffix('.kicad_pro')}
    original = {path: path.read_bytes() if path.exists() else None for path in paths}
    if not p.SaveBoard(str(output), board, True):
        raise RuntimeError(f'KiCad failed to save PCB: {output}')
    for path, content in original.items():
        actual = path.read_bytes() if path.exists() else None
        if actual != content:
            raise RuntimeError(f'PCB-only save changed project sidecar: {path}')


def point(v):
    return p.ToMM(v.x), p.ToMM(v.y)


def segment_distance(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = 0 if length == 0 else max(0, min(1, ((q[0]-a[0])*dx+(q[1]-a[1])*dy)/length))
    return math.dist(q, (a[0]+t*dx, a[1]+t*dy))


def segments_distance(a, b, c, d):
    def cross(u, v, w):
        return (v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0])
    if (max(min(a[0],b[0]), min(c[0],d[0])) <= min(max(a[0],b[0]), max(c[0],d[0])) and
            max(min(a[1],b[1]), min(c[1],d[1])) <= min(max(a[1],b[1]), max(c[1],d[1])) and
            cross(a,b,c)*cross(a,b,d) <= 0 and cross(c,d,a)*cross(c,d,b) <= 0):
        return 0.0
    return min(segment_distance(a,c,d), segment_distance(b,c,d), segment_distance(c,a,b), segment_distance(d,a,b))


def remove_unused_fanouts(board):
    """Remove only the three reviewed dead-end via/stub pairs, with geometry guards."""
    if any(not isinstance(item,p.PCB_VIA) and item.GetClass() != 'PCB_TRACK' for item in board.GetTracks()):
        raise RuntimeError('Dead-end proof supports straight tracks only; unexpected routed primitive')
    removed = []
    to_remove = []
    for net, xy in (('C_FB', (22.9, 50.4)), ('EN_E', (18.7, 49.2)), ('RAMP', (88.4, 55.3))):
        matches = [v for v in board.GetTracks() if isinstance(v, p.PCB_VIA) and v.GetNetname() == net and math.dist(point(v.GetPosition()), xy) < 1e-6]
        if not matches:
            continue  # Already finished, or a future route has no via at this reviewed site.
        if len(matches) != 1:
            raise RuntimeError(f'Duplicate reviewed via at {xy}')
        via = matches[0]
        radius = p.ToMM(via.GetWidth(p.F_Cu))/2
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                gap = math.hypot(max(p.ToMM(bb.GetLeft())-xy[0], 0, xy[0]-p.ToMM(bb.GetRight())), max(p.ToMM(bb.GetTop())-xy[1], 0, xy[1]-p.ToMM(bb.GetBottom()))) - radius
                if gap <= 1e-6:
                    raise RuntimeError(f'{net} reviewed via now touches pad copper/bounds')
        if any(isinstance(other, p.PCB_VIA) and other.m_Uuid.AsString() != via.m_Uuid.AsString() and math.dist(point(other.GetPosition()), xy) <= radius+p.ToMM(other.GetWidth(p.F_Cu))/2+1e-6 for other in board.GetTracks()):
            raise RuntimeError(f'{net} reviewed via now touches another via')
        contacts = [t for t in board.GetTracks() if not isinstance(t, p.PCB_VIA) and t.GetNetname() == net and
                    segment_distance(xy, point(t.GetStart()), point(t.GetEnd())) <= p.ToMM(via.GetWidth(t.GetLayer()) + t.GetWidth()) / 2 + 1e-6]
        if len(contacts) != 1 or contacts[0].GetLayer() != p.F_Cu:
            raise RuntimeError(f'{net} via at {xy} is no longer a single-layer dead-end')
        stub = contacts[0]
        if math.dist(point(stub.GetStart()), xy) < 1e-6:
            tip = stub.GetEnd()
        elif math.dist(point(stub.GetEnd()), xy) < 1e-6:
            tip = stub.GetStart()
        else:
            raise RuntimeError(f'{net} via no longer ends its stub')
        owners = [pad for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetname() == net and pad.IsOnLayer(p.F_Cu) and pad.HitTest(tip)]
        if len(owners) != 1:
            raise RuntimeError(f'{net} stub no longer ends directly in one source pad')
        pad = owners[0]
        # Reject another branch using this stub outside the source pad. Exact
        # straight-segment distances bound copper contact; native DRC checks connectivity.
        for t in board.GetTracks():
            if isinstance(t, p.PCB_VIA) or t == stub or t.GetNetname() != net or t.GetLayer() != p.F_Cu:
                continue
            a, b = point(stub.GetStart()), point(stub.GetEnd())
            near = segments_distance(a, b, point(t.GetStart()), point(t.GetEnd())) <= p.ToMM(stub.GetWidth()+t.GetWidth())/2
            if near and not (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd())):
                raise RuntimeError(f'{net} dead-end stub now supports another branch')
        # These three signal nets have no copper zones; don't generalize this to ground vias.
        if any(z.GetNetname() == net and not z.GetIsRuleArea() for z in board.Zones()):
            raise RuntimeError(f'{net} now has a zone; dead-end proof must be reviewed')
        to_remove.extend((stub, via))
        removed.append({'net': net, 'via_mm': xy, 'source_pad': pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber()})
    for item in to_remove:
        # KiCad 10.0.6 Remove transfers ownership to Python; on loaded boards
        # GC of removed wrappers can invalidate the board. Delete owns disposal.
        board.Delete(item)
    return removed


def native_self_test(path):
    """Actual-board lifetime/negative controls; never writes the input PCB."""
    import gc
    board = p.LoadBoard(path)
    # Reinsert only a missing reviewed dead-end in memory, so this regression also
    # runs after the canonical PCB has already been cleaned.
    for net, source, target in (('C_FB',(23.6,50.4),(22.9,50.4)), ('EN_E',(18,49.2),(18.7,49.2)), ('RAMP',(89.1,55.3),(88.4,55.3))):
        if any(isinstance(v,p.PCB_VIA) and v.GetNetname()==net and math.dist(point(v.GetPosition()),target)<1e-6 for v in board.GetTracks()):
            continue
        track=p.PCB_TRACK(board);track.SetStart(p.VECTOR2I(*map(p.FromMM,source)));track.SetEnd(p.VECTOR2I(*map(p.FromMM,target)))
        track.SetWidth(p.FromMM(.5));track.SetLayer(p.F_Cu);track.SetNet(board.FindNet(net));board.Add(track)
        via=p.PCB_VIA(board);via.SetPosition(track.GetEnd());via.SetWidth(p.FromMM(.8));via.SetDrill(p.FromMM(.3));via.SetNet(board.FindNet(net));board.Add(via)
        del track,via
    before=len(board.GetTracks())
    fp=next(fp for fp in board.GetFootprints() if fp.GetReference()=='P1')
    nc=next(pad for pad in fp.Pads() if pad.GetNumber()=='4');net=nc.GetNet();nc.SetNet(board.FindNet('GND'))
    try:
        probe_labels(board)
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Negative control accepted a connected NC pad')
    nc.SetNet(net)
    probe_labels(board);probe_labels(board)
    victim=next(pad for fp in board.GetFootprints() if fp.GetReference()=='R11' for pad in fp.Pads() if pad.GetNumber()=='2')
    saved=p.VECTOR2I(victim.GetPosition());victim.SetPosition(p.VECTOR2I(p.FromMM(22.9),p.FromMM(50.4)))
    try:
        remove_unused_fanouts(board)
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Negative control accepted via-to-pad contact')
    victim.SetPosition(saved)
    if len(board.GetTracks()) != before:
        raise RuntimeError('Rejected cleanup partially mutated tracks')
    removed=remove_unused_fanouts(board)
    gc.collect()
    if len(removed)!=3 or len(board.GetTracks())!=before-6 or remove_unused_fanouts(board):
        raise RuntimeError('Permanent deletion/GC/idempotence regression')
    probe_labels(board)
    gc.collect()
    if len(board.GetTracks()) != before-6:
        raise RuntimeError('Board invalid after finishing helper returns')
    print('PASS: actual-board permanent Delete + forced GC/readback; idempotence and NC/pad-contact negative controls')


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--self-test':
        native_self_test(sys.argv[2])
        raise SystemExit(0)
    if len(sys.argv)>1 and sys.argv[1]=='--artwork-only':
        board=p.LoadBoard(sys.argv[2]);artwork(board);save_preserving_projects(board,sys.argv[3],sys.argv[2])
        raise SystemExit(0)
    board = p.LoadBoard(sys.argv[1])
    artwork(board)
    print('Removed dead-end fanouts:', remove_unused_fanouts(board))
    p.ZONE_FILLER(board).Fill(board.Zones())
    save_preserving_projects(board,sys.argv[2],sys.argv[1])
