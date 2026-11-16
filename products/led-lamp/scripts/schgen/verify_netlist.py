#!/usr/bin/env python3
"""Diff a kicad-cli netlist export against a board spec's net table.

Usage: python3 verify_netlist.py <spec_module> <netlist_file>
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import load, atom, find_all

spec = importlib.import_module(sys.argv[1])
nl = load(sys.argv[2])

nets_node = find_all(nl, 'nets')[0]
actual = {}
for net in find_all(nets_node, 'net'):
    name = atom(find_all(net, 'name')[0][1])
    nodes = set()
    for node in find_all(net, 'node'):
        ref = atom(find_all(node, 'ref')[0][1])
        pin = atom(find_all(node, 'pin')[0][1])
        nodes.add(f'{ref}.{pin}')
    actual[name] = nodes

# KiCad's PCB netlist intentionally omits off-board assembly components.
externals = set() if "--assembly" in sys.argv else set(getattr(spec, 'EXTERNAL_COMPONENTS', {}))
# '#'-prefixed refs (e.g. #FLG PWR_FLAG) are virtual ERC symbols; KiCad never exports them.
externals |= {ref for ref in spec.COMPONENTS if ref.startswith('#')}
expected = {name: {node for node in nodes if node.split('.')[0] not in externals}
            for name, nodes in spec.NETS.items()}
expected = {name: nodes for name, nodes in expected.items() if nodes}
ok = True
for name, exp in expected.items():
    act = actual.get(name)
    if act is None:
        print(f'MISSING net {name}')
        ok = False
        continue
    if act != exp:
        print(f'MISMATCH {name}:')
        if exp - act:
            print(f'   missing: {sorted(exp - act)}')
        if act - exp:
            print(f'   extra:   {sorted(act - exp)}')
        ok = False

extra_nets = set(actual) - set(expected)
for name in sorted(extra_nets):
    members = actual[name]
    if name.startswith('unconnected-'):
        node = next(iter(members))
        if len(members) == 1 and node in spec.NO_CONNECT:
            continue
        print(f'BAD unconnected net {name}: {sorted(members)}')
        ok = False
    else:
        print(f'UNEXPECTED net {name}: {sorted(members)}')
        ok = False

nc_seen = {next(iter(actual[n])) for n in actual
           if n.startswith('unconnected-') and len(actual[n]) == 1}
missing_nc = set(spec.NO_CONNECT) - nc_seen
if missing_nc:
    print(f'NC pins missing from netlist: {sorted(missing_nc)}')
    ok = False

total_nodes = sum(len(v) for v in actual.values())
print(f'{"PASS" if ok else "FAIL"}: {len(actual)} nets, {total_nodes} nodes '
      f'({len(expected)} expected nets + {len(extra_nets)} unconnected)')
sys.exit(0 if ok else 1)
