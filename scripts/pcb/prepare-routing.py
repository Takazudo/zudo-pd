#!/usr/bin/env python3
"""Export a placement to DSN with explicit project widths for local routing."""
import argparse
import json
import math
from pathlib import Path
import re
import sys
import wx
_KICAD_APP = wx.App(False)
import pcbnew as p

from pcb_common import pcb_net_name

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
import board_b_spec as spec
from sexp import atom, find_all, parse, tokenize


def require(ok, message):
    if not ok:
        raise ValueError(message)


def network(text):
    # DSN's parser header contains `(string_quote ")`, which is not a KiCad
    # quoted string. Parse only the ordinary s-expression network section.
    starts = list(re.finditer(r'^[ \t]*\(network(?=\s|\))', text, re.M))
    require(len(starts) == 1, 'Expected exactly one native DSN network')
    start = starts[0].start()
    depth = 0
    quoted = escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == '\\' and quoted:
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
        if quoted:
            continue
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return parse(tokenize(text[start:index+1]))
    raise ValueError('Unterminated native DSN network section')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('board',type=Path)
parser.add_argument('dsn',type=Path)
args=parser.parse_args()
config=json.loads((ROOT/'boards/board-b/board-b.kicad_pro').read_text())['net_settings']
required_widths = {'Default': .25, 'Power': 1.0, 'PD feed': 1.5}
class_names = [c['name'] for c in config['classes']]
require(len(class_names) == len(set(class_names)), 'Duplicate project netclass names')
require(set(class_names) >= set(required_widths), 'Run configure-board-b.py before routing; refusing default-only widths')
for cls in config['classes']:
    if cls['name'] in required_widths:
        require(math.isclose(cls['track_width'], required_widths[cls['name']], abs_tol=1e-9),
                f'{cls["name"]}: unexpected routing width; run configure-board-b.py')
    require(math.isfinite(cls['clearance']) and cls['clearance'] >= .25,
            f'{cls["name"]}: routing clearance below 0.25 mm')
b=p.LoadBoard(str(args.board))
require(p.ExportSpecctraDSN(b,str(args.dsn)), 'Native DSN export failed')
text=args.dsn.read_text()
# Native pcbnew's headless DSN exporter does not resolve project netclass patterns.
classes={c['name']:c for c in config['classes']}
expected_names={pcb_net_name(n) for n in spec.NETS}
require(len(expected_names)==len(spec.NETS), 'Encoded net-name collision')
native_names = [atom(node[1]) for node in find_all(network(text), 'net')]
require(len(native_names) == len(set(native_names)), 'Duplicate native DSN net names')
require(set(native_names) == expected_names,
        f'Native DSN/spec net mismatch: missing={sorted(expected_names-set(native_names))}; extra={sorted(set(native_names)-expected_names)}')
assigned={n:'Default' for n in sorted(expected_names)}
seen_patterns = set()
for pattern in config['netclass_patterns']:
    require(pattern['pattern'] in assigned, 'Project pattern does not name a current exact net')
    require(pattern['pattern'] not in seen_patterns, 'Duplicate exact netclass assignment')
    seen_patterns.add(pattern['pattern'])
    assigned[pattern['pattern']]=pattern['netclass']
missing=set(assigned.values())-set(classes)
if missing:raise ValueError(f'Undefined netclasses: {sorted(missing)}')
# Replace every native netclass block. KiCad may export both its default and
# named classes; retaining either would assign a net to two routing classes.
ranges=[]
for match in re.finditer(r'^    \(class ',text,re.M):
    start=match.start();depth=0;quoted=False;escape=False
    for i in range(start,len(text)):
        c=text[i]
        if escape:escape=False;continue
        if c=='\\' and quoted:escape=True;continue
        if c=='"':quoted=not quoted
        if quoted:continue
        if c=='(':depth+=1
        if c==')':
            depth-=1
            if depth==0:ranges.append((start,i+1));break
require(bool(ranges), 'No native netclass blocks were found')
blocks=[]
emitted=[]
for name,cls in classes.items():
    names=[n for n,c in assigned.items() if c==name]
    emitted.extend(names)
    nets=' '.join(json.dumps(n, ensure_ascii=False) for n in names)
    if not nets:continue
    blocks.append(f'    (class {json.dumps(name)} {nets}\n      (circuit (use_via "Via[0-1]_1200:600_um"))\n      (rule (width {cls["track_width"]*1000:g}) (clearance {cls["clearance"]*1000:g}))\n    )')
require(len(emitted)==len(spec.NETS) and set(emitted)==expected_names, 'Incomplete DSN netclass coverage')
for start,end in reversed(ranges):text=text[:start]+text[end:]
text=text[:ranges[0][0]]+'\n'.join(blocks)+text[ranges[0][0]:]
text=text.replace('Via[0-1]_600:300_um','Via[0-1]_1200:600_um')
# The DSN via name carries KiCad's drill diameter for SES import.
text=text.replace('(shape (circle F.Cu 600))','(shape (circle F.Cu 1200))').replace('(shape (circle B.Cu 600))','(shape (circle B.Cu 1200))')
actual_assignments = {}
for node in find_all(network(text), 'class'):
    class_name = atom(node[1])
    require(class_name in classes, 'Unexpected retained native netclass')
    for member in node[2:]:
        if isinstance(member, list):
            continue
        name = atom(member)
        require(name not in actual_assignments, f'DSN net assigned more than once: {name}')
        actual_assignments[name] = class_name
require(actual_assignments == assigned, 'Emitted DSN class assignments differ from reviewed project policy')
args.dsn.write_text(text)
print(f'{args.dsn}: {len(assigned)} nets with explicit clearance/width classes')
