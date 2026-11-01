"""Compare a PCB's pad connectivity with a spec's NETS (or a baseline JSON's nets), pcbnew in the pinned KiCad image.

usage: python3 pcb-net-parity.py <board.kicad_pcb> <spec.py | baseline.json> [<report.json>]
Pads on nets named "unconnected-(...)" or with no net count as unconnected. Bare-copper or DNP parts count like any
other footprint. Exit 0 when every net matches pin for pin, 1 otherwise.
"""
import importlib.util, json, sys
import pcbnew

board, ref = sys.argv[1], sys.argv[2]
if ref.endswith('.json'):
    want = {n: sorted(p) for n, p in json.load(open(ref))['nets'].items()}
    no_connect = None
else:
    s = importlib.util.spec_from_file_location('spec', ref); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    want = {n: sorted(p) for n, p in m.NETS.items()}
    no_connect = sorted(m.NO_CONNECT)
got, unconnected = {}, []
for f in pcbnew.LoadBoard(board).GetFootprints():
    for pad in f.Pads():
        if not pad.GetNumber():
            continue
        pin = f'{f.GetReference()}.{pad.GetNumber()}'
        net = pad.GetNetname()
        if not net or net.startswith('unconnected-'):
            unconnected.append(pin)
        else:
            got.setdefault(net, set()).add(pin)
got = {n: sorted(p) for n, p in got.items()}
diff = {n: {'pcb_only': sorted(set(got.get(n, [])) - set(want.get(n, []))), 'spec_only': sorted(set(want.get(n, [])) - set(got.get(n, [])))}
        for n in sorted(set(got) | set(want)) if got.get(n) != want.get(n)}
nc_diff = None
if no_connect is not None:
    nc_diff = {'pcb_only': sorted(set(unconnected) - set(no_connect)), 'spec_only': sorted(set(no_connect) - set(unconnected))}
ok = not diff and (nc_diff is None or not (nc_diff['pcb_only'] or nc_diff['spec_only']))
report = {'board': board, 'reference': ref, 'verdict': 'PASS' if ok else 'FAIL', 'nets': len(got), 'net_differences': diff,
          'unconnected_pads': sorted(unconnected), 'no_connect_differences': nc_diff}
text = json.dumps(report, indent=1) + '\n'
if len(sys.argv) > 3:
    open(sys.argv[3], 'w').write(text)
print(text)
sys.exit(0 if ok else 1)
