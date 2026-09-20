#!/usr/bin/env python3
"""Synchronize the reviewed protection part identity and lands into a new PCB copy."""
import argparse
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import load
from pcb_common import serialize, sync_surface_part

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('board', choices=['board-p', 'board-b'])
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit('Choose a new output path; review the synchronized board before replacing the source')
spec = importlib.import_module(args.board.replace('-', '_') + '_spec')
source = ROOT / 'boards' / args.board / (args.board + '.kicad_pcb')
tree = load(source)
ref = 'D5' if args.board == 'board-p' else 'D3'
sync_surface_part(tree, ref, spec.COMPONENTS[ref], ROOT / 'footprints/kicad/zudo-power.pretty', args.board)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(serialize(tree) + '\n')
print(f'{args.board}/{ref}: exact identity/lands updated; native DRC and schematic parity required')
