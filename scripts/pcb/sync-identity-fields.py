#!/usr/bin/env python3
"""Copy the spec's exact LCSC fields onto a PCB whose footprints and values already match the spec.

usage: python3 sync-identity-fields.py <board-b|board-p|board-p15> <output.kicad_pcb>

Only same-footprint identity changes are allowed (a stock substitution on the same land); a footprint
difference stops the script, because changed lands need the lands-sync path and a native DRC review.
Every changed reference is printed. Native DRC with schematic parity is still required on the output.
"""
import argparse
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load  # noqa: E402

PCB = {'board-p15': 'boards/board-p15/board-p15-draft.kicad_pcb'}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('board', choices=['board-b', 'board-p', 'board-p15'])
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit('Choose a new output path; review the synchronized board before replacing the source')
spec = importlib.import_module(args.board.replace('-', '_') + '_spec')
source = ROOT / PCB.get(args.board, f'boards/{args.board}/{args.board}.kicad_pcb')
text = source.read_text()
tree = load(source)
changed, edits = [], {}
for fp in find_all(tree, 'footprint'):
    props = {atom(p[1]): p for p in find_all(fp, 'property')}
    ref = atom(props['Reference'][2]) if 'Reference' in props else None
    if ref not in spec.COMPONENTS:
        continue
    _, value, lcsc, footprint, _, _ = spec.COMPONENTS[ref]
    if atom(fp[1]) != footprint:
        raise SystemExit(f'{ref}: footprint {atom(fp[1])} differs from spec {footprint}; use the lands-sync path')
    if 'Value' in props and atom(props['Value'][2]) != value:
        raise SystemExit(f'{ref}: value change {atom(props["Value"][2])} -> {value} needs a reviewed edit')
    for field in ('LCSC', 'LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
        if field in props and atom(props[field][2]) != lcsc:
            old = atom(props[field][2])
            edits.setdefault((field, old), set()).add(lcsc)
            changed.append(f'{ref}.{field}: {old} -> {lcsc}')
# Text-level edit keeps KiCad's own formatting: each old field value must map to one new value, and the file may
# hold that exact property only where the parsed board says it changes.
for (field, old), new in sorted(edits.items()):
    if len(new) != 1:
        raise SystemExit(f'{field} {old} maps to several values {sorted(new)}')
    needle = f'(property "{field}" "{old}"'
    expected = sum(1 for c in changed if c.split(': ')[1].startswith(old) and c.split(': ')[0].endswith('.' + field))
    if text.count(needle) != expected:
        raise SystemExit(f'{needle}: {text.count(needle)} occurrences, expected {expected}')
    text = text.replace(needle, f'(property "{field}" "{new.pop()}"')
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(text)
for fp in find_all(load(args.output), 'footprint'):
    props = {atom(p[1]): atom(p[2]) for p in find_all(fp, 'property')}
    ref = props.get('Reference')
    if ref in spec.COMPONENTS:
        for field in ('LCSC', 'LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
            assert props.get(field, spec.COMPONENTS[ref][2]) == spec.COMPONENTS[ref][2], (ref, field)
print('\n'.join(changed) or 'no identity change')
