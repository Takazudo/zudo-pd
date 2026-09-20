#!/usr/bin/env python3
"""Verify a generated .kicad_sch's label geometry against its spec module.

Re-derives every symbol pin's absolute endpoint from the emitted file itself
(embedded lib_symbols + instance placements) and checks, independently of
schgen_core's own placement math:

  1. every global label sits exactly on a pin endpoint (no orphan labels)
  2. no coordinate carries two different net names, and no coordinate is
     shared by pins the spec assigns to different nets (no implicit shorts)
  3. the label->pin net map equals spec.NETS exactly
  4. no_connect markers resolve to exactly the spec's NO_CONNECT pins

This closes the gap where a label-placement bug in schgen_core would produce
output that is stable, idempotent, and baseline-matching but electrically
wrong: spec-vs-baseline and regen-idempotency checks only see the spec and
the bytes, never the geometry. Needs no KiCad.

Usage: python3 verify_geometry.py <spec_module> <kicad_sch>
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schgen_core
from sexp import load, atom, find_all

# KiCad coordinates are mm; quantize to 0.1 um so float round-trips through
# the file's %g formatting cannot split one physical point into two keys.
def _key(x, y):
    return (round(float(x) * 10000), round(float(y) * 10000))


def read_schematic(sch_path):
    """Parse the emitted schematic into (lib_pins, instances, labels, ncs).

    lib_pins:  {lib_id: [(pin_number, px, py)]}
    instances: [(ref, lib_id, X, Y, angle)]
    labels:    [(net_name, x, y)]
    ncs:       [(x, y)]
    """
    tree = load(sch_path)

    lib_pins = {}
    for lib_symbols in find_all(tree, 'lib_symbols'):
        for sym in find_all(lib_symbols, 'symbol'):
            lib_id = atom(sym[1])
            pins = []
            for sub in find_all(sym, 'symbol'):
                for pin in find_all(sub, 'pin'):
                    at = find_all(pin, 'at')[0]
                    num = atom(find_all(pin, 'number')[0][1])
                    pins.append((num, float(atom(at[1])), float(atom(at[2]))))
            lib_pins[lib_id] = pins

    instances = []
    for sym in find_all(tree, 'symbol'):
        lib_id_nodes = find_all(sym, 'lib_id')
        if not lib_id_nodes:
            continue
        lib_id = atom(lib_id_nodes[0][1])
        at = find_all(sym, 'at')[0]
        ref = None
        for prop in find_all(sym, 'property'):
            if atom(prop[1]) == 'Reference':
                ref = atom(prop[2])
        angle = float(atom(at[3])) if len(at) > 3 else 0.0
        instances.append((ref, lib_id, float(atom(at[1])), float(atom(at[2])), angle))

    labels = []
    for label in find_all(tree, 'global_label'):
        at = find_all(label, 'at')[0]
        labels.append((atom(label[1]), float(atom(at[1])), float(atom(at[2]))))

    ncs = []
    for nc in find_all(tree, 'no_connect'):
        at = find_all(nc, 'at')[0]
        ncs.append((float(atom(at[1])), float(atom(at[2]))))

    return lib_pins, instances, labels, ncs


def run_check(spec, sch_path):
    """Return a list of human-readable problems; empty means clean."""
    problems = []
    lib_pins, instances, labels, ncs = read_schematic(sch_path)

    # spec-side truth: which net does each REF.PIN belong to ('NC' for NO_CONNECT)
    spec_net_of = {}
    for net, pins in spec.NETS.items():
        for s in pins:
            spec_net_of[s] = net
    for s in spec.NO_CONNECT:
        spec_net_of[s] = 'NC'

    # Power flags are schematic-only declarations, not physical NETS members.
    # Still verify their exact pin, label, library and position; never ignore
    # arbitrary #FLG symbols because a stray flag can conceal a real ERC fault.
    flag_pins = {}
    for index, (net, position) in enumerate(getattr(spec, 'ERC_POWER_FLAGS', {}).items(), 1):
        ref = f'#FLG{index:03d}'
        if net not in spec.NETS:
            problems.append(f'{ref}: power flag references unknown net "{net}"')
        flag_pins[f'{ref}.1'] = net
        matching = [instance for instance in instances if instance[0] == ref]
        if len(matching) != 1:
            problems.append(f'{ref}: expected exactly one declared power flag, found {len(matching)}')
        elif matching[0][1] != 'zudo-pd:PWR_FLAG' or _key(*matching[0][2:4]) != _key(*position):
            problems.append(f'{ref}: power flag library or position differs from spec')
    spec_net_of.update(flag_pins)

    # every pin endpoint, derived from the file alone
    endpoint_pins = {}  # coordinate key -> ['REF.PIN', ...]
    for ref, lib_id, X, Y, angle in instances:
        if angle != 0.0:
            problems.append(f'{ref}: unexpected instance rotation {angle} '
                            f'(generator always emits 0; endpoint math assumes it)')
            continue
        if ref is None:
            problems.append(f'symbol instance of {lib_id} has no Reference property')
            continue
        for num, px, py in lib_pins.get(lib_id, []):
            endpoint_pins.setdefault(_key(X + px, Y - py), []).append(f'{ref}.{num}')

    # 1 + derived net map: each label must land on a pin endpoint
    derived_net_of = {}  # 'REF.PIN' -> net name, per the labels in the file
    label_at = {}  # coordinate key -> net name
    for net, x, y in labels:
        k = _key(x, y)
        if k in label_at and label_at[k] != net:
            problems.append(f'labels "{label_at[k]}" and "{net}" share coordinate ({x:g}, {y:g})')
        label_at[k] = net
        pins_here = endpoint_pins.get(k)
        if not pins_here:
            problems.append(f'orphan label "{net}" at ({x:g}, {y:g}): no pin endpoint there')
            continue
        for s in pins_here:
            if s in derived_net_of and derived_net_of[s] != net:
                problems.append(f'{s} carries two labels: "{derived_net_of[s]}" and "{net}"')
            derived_net_of[s] = net

    # 2: no coordinate may join pins the spec assigns to different nets
    for k, pins_here in endpoint_pins.items():
        nets_here = {spec_net_of.get(s, f'<unassigned {s}>') for s in pins_here}
        if len(nets_here) > 1:
            problems.append(f'pins {sorted(pins_here)} share a coordinate but belong to '
                            f'different nets: {sorted(nets_here)} (implicit short)')

    # 3: derived net map == spec.NETS exactly
    expected_net_of = {s: net for net, pins in spec.NETS.items() for s in pins}
    expected_net_of.update(flag_pins)
    for s, net in sorted(expected_net_of.items()):
        got = derived_net_of.pop(s, None)
        if got is None:
            problems.append(f'{s}: spec assigns net "{net}" but no label lands on its endpoint')
        elif got != net:
            problems.append(f'{s}: spec assigns net "{net}" but label says "{got}"')
    for s, net in sorted(derived_net_of.items()):
        problems.append(f'{s}: label "{net}" present but spec does not connect this pin')

    # 4: no_connect markers == NO_CONNECT list
    nc_pins = set()
    for x, y in ncs:
        pins_here = endpoint_pins.get(_key(x, y))
        if not pins_here:
            problems.append(f'no_connect at ({x:g}, {y:g}) sits on no pin endpoint')
            continue
        nc_pins.update(pins_here)
    expected_nc = set(spec.NO_CONNECT)
    for s in sorted(expected_nc - nc_pins):
        problems.append(f'{s}: in NO_CONNECT but no no_connect marker on its endpoint')
    for s in sorted(nc_pins - expected_nc):
        problems.append(f'{s}: no_connect marker present but pin is not in NO_CONNECT')

    return problems


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('spec_module',
                        help='path to a .py spec module, or a dotted module name')
    parser.add_argument('kicad_sch', help='generated .kicad_sch to verify')
    args = parser.parse_args(argv)

    try:
        spec = schgen_core.load_spec_module(args.spec_module)
    except schgen_core.SchgenError as err:
        print(f'verify_geometry: error: {err}', file=sys.stderr)
        return 1

    problems = run_check(spec, args.kicad_sch)
    if problems:
        print(f'verify_geometry: {len(problems)} problem(s) in {args.kicad_sch}')
        for problem in problems:
            print(f'  - {problem}')
        return 1

    n_pins = sum(len(pins) for pins in spec.NETS.values())
    print(f'verify_geometry: OK — {args.kicad_sch}: every label on a pin endpoint, '
          f'{n_pins} spec pins matched, no cross-net coordinate collisions')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
