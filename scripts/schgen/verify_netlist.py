#!/usr/bin/env python3
"""Diff a kicad-cli netlist export against a board spec's net table.

Usage: python3 verify_netlist.py <spec_module> <netlist_file>
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schgen_core
from sexp import load, atom, find_all


def read_netlist_nets(netlist_path):
    """{net_name: {'REF.PIN', ...}} from a kicad-cli s-expression netlist."""
    nl = load(netlist_path)
    nets_node = find_all(nl, 'nets')[0]
    actual = {}
    for net in find_all(nets_node, 'net'):
        # KiCad escapes literal label slashes to distinguish them from hierarchy
        # separators in netlist names (KiCad issue 12959 / UnescapeString).
        # Decode the known representation, retaining all connectivity checks.
        name = atom(find_all(net, 'name')[0][1]).replace('{slash}', '/')
        if name in actual:
            raise ValueError(f'duplicate net name after KiCad slash decoding: {name}')
        nodes = set()
        for node in find_all(net, 'node'):
            ref = atom(find_all(node, 'ref')[0][1])
            pin = atom(find_all(node, 'pin')[0][1])
            nodes.add(f'{ref}.{pin}')
        actual[name] = nodes
    return actual


def verify(spec, actual):
    expected = {name: set(specs) for name, specs in spec.NETS.items()}
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
    return ok


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('spec_module',
                        help='path to a .py spec module, or a dotted module name')
    parser.add_argument('netlist_file', help='kicad-cli netlist export to diff')
    args = parser.parse_args(argv)

    try:
        spec = schgen_core.load_spec_module(args.spec_module)
    except schgen_core.SchgenError as err:
        print(f'verify_netlist: error: {err}', file=sys.stderr)
        return 1
    actual = read_netlist_nets(args.netlist_file)
    return 0 if verify(spec, actual) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
