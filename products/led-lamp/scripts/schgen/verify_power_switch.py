#!/usr/bin/env python3
"""Audit the fitted JLCPCB toggle and its ON/OFF feed topology."""
import argparse
from pathlib import Path

import board_l_spec as spec
from schgen_core import Library, abs_pin_positions
from sexp import atom, find_all, load

ROOT = Path(__file__).resolve().parents[2]


def field(node, key):
    return atom(find_all(node, key)[0][1])


def check_topology(nets):
    inverse = {pin: name for name, pins in nets.items() for pin in pins}
    assert len(inverse) == sum(map(len, nets.values())), 'A pin occurs on multiple nets'
    assert set(nets['VBUS_L']) == {'J2.1', 'J2.2', 'F1.1'}
    assert set(nets['V15_FUSED']) == {'F1.2', 'SW2.2'}
    for pin in ['SW2.1', 'U2.8', 'U4.3', 'D10.1']:
        assert inverse[pin] == 'V15', pin
    assert inverse['D10.2'] == 'GND'
    assert inverse['J2.5'] == inverse['J2.6'] == 'GND'
    assert inverse['J2.3'] == 'ATT' and inverse['J2.4'] == 'PDOK'
    assert {pin for pin in inverse if pin.startswith('SW2.')} >= {'SW2.1', 'SW2.2'}
    if 'SW2.3' in inverse:
        assert set(nets[inverse['SW2.3']]) == {'SW2.3'}, 'OFF throw must be isolated on the PCB'
    assert 'SW2.3' in spec.NO_CONNECT
    # State graph of the deliberate conductive feed elements: fuse and toggle.
    for closed in (False, True):
        graph = {name: set() for name in nets}
        pairs = [('F1.1', 'F1.2')] + ([('SW2.2', 'SW2.1')] if closed else [])
        for a, b in pairs:
            x, y = inverse[a], inverse[b]
            graph[x].add(y)
            graph[y].add(x)
        seen, todo = set(), [inverse['J2.1']]
        while todo:
            net = todo.pop()
            if net not in seen:
                seen.add(net)
                todo.extend(graph[net] - seen)
        assert (inverse['U2.8'] in seen) == closed
        assert (inverse['U4.3'] in seen) == closed
        assert 'GND' not in seen


def check_schematic(path):
    tree = load(str(path))
    instances = {next(atom(p[2]) for p in find_all(s, 'property') if atom(p[1]) == 'Reference'): s
                 for s in find_all(tree, 'symbol')}
    assert 'J5' not in instances
    sw = instances['SW2']
    assert field(sw, 'on_board') == 'yes' and field(sw, 'in_bom') == 'yes'
    assert field(sw, 'dnp') == 'no'
    props = {atom(p[1]): atom(p[2]) for p in find_all(sw, 'property')}
    assert props['Footprint'] == spec.COMPONENTS['SW2'][3]
    assert props['LCSC'] == 'C5446803'
    assert not spec.EXTERNAL_COMPONENTS
    library = Library()
    name = spec.COMPONENTS['SW2'][0]
    pin_cache = {name: library.pins_of(name)}
    labels = {(round(float(atom(a[1])), 4), round(float(atom(a[2])), 4)): atom(n[1])
              for n in find_all(tree, 'global_label') for a in find_all(n, 'at')}
    nc = {(round(float(atom(a[1])), 4), round(float(atom(a[2])), 4))
          for n in find_all(tree, 'no_connect') for a in find_all(n, 'at')}
    for pin, positions in abs_pin_positions(spec, pin_cache, 'SW2').items():
        for x, y, _ in positions:
            pos = (round(x, 4), round(y, 4))
            if pin == '3':
                assert pos in nc and pos not in labels
            else:
                assert labels[pos] == {'1': 'V15', '2': 'V15_FUSED'}[pin]
    master = ROOT / 'footprints/kicad/SW-TH_SS-12D01-G020.kicad_mod'
    mirror = ROOT / 'footprints/kicad/zudo-led-lamp.pretty' / master.name
    assert master.read_bytes() == mirror.read_bytes()
    pads = find_all(load(str(master)), 'pad')
    assert {atom(p[1]) for p in pads} == {'1', '2', '3'}
    assert all(atom(p[2]) == 'thru_hole' for p in pads)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--netlist')
    args = parser.parse_args()
    check_topology(spec.NETS)
    check_schematic(ROOT / spec.OUT)
    if args.netlist:
        nets = {}
        for net in find_all(find_all(load(args.netlist), 'nets')[0], 'net'):
            nets[field(net, 'name')] = [field(n, 'ref') + '.' + field(n, 'pin') for n in find_all(net, 'node')]
        check_topology(nets)
    print('PASS: C5446803 fitted PCB identity, common/throw mapping, isolated OFF throw and ON/OFF feed topology; not a bench back-power test')


if __name__ == '__main__':
    main()
