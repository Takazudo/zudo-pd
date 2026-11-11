"""Prove a finalized B20 PCB differs from its predecessor only in the expected Value/LCSC fields.

usage: verify-field-sync.py BEFORE.kicad_pcb AFTER.kicad_pcb EXPECTED_REFS OUT.json
Pure Python (sexp). Every filled polygon is removed from both boards. On AFTER, the Value and LCSC
property strings of each expected footprint are set back to their BEFORE strings. The two trees must
then be identical, and the filled polygons must be byte-identical, so the refill did not move copper.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, parse, tokenize  # noqa: E402


def fills(node, out):
    if isinstance(node, list):
        if node and atom(node[0]) == 'filled_polygon':
            out.append(json.dumps(node, default=str))
        for item in node:
            fills(item, out)
    return out


def strip(node):
    if not isinstance(node, list):
        return node
    return [strip(item) for item in node if not (isinstance(item, list) and item and atom(item[0]) == 'filled_polygon')]


def footprint_fields(tree):
    found = {}
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'footprint':
            props = {atom(p[1]): p for p in item if isinstance(p, list) and p and atom(p[0]) == 'property'}
            found[atom(props['Reference'][2])] = props
    return found


def main():
    before_path, after_path, refs, out = sys.argv[1], sys.argv[2], set(sys.argv[3].split(',')), Path(sys.argv[4])
    raw_before, raw_after = Path(before_path).read_bytes(), Path(after_path).read_bytes()
    before, after = parse(tokenize(raw_before.decode())), parse(tokenize(raw_after.decode()))
    old, new = footprint_fields(before), footprint_fields(after)
    changes = {}
    for ref in sorted(refs):
        changes[ref] = {}
        for name in ('Value', 'LCSC'):
            was, now = old[ref][name][2], new[ref][name][2]
            changes[ref][name] = [atom(was), atom(now)]
            new[ref][name][2] = was
    if strip(before) != strip(after):
        raise SystemExit('Finalized PCB differs outside the expected Value/LCSC fields')
    if fills(before, []) != fills(after, []):
        raise SystemExit('Refill changed filled copper')
    result = {'scope': 'Value-only B20 field sync: non-field PCB content and filled copper unchanged; not electrical acceptance',
              'before_sha256': hashlib.sha256(raw_before).hexdigest(),
              'after_sha256': hashlib.sha256(raw_after).hexdigest(),
              'changed_fields': changes, 'fills_identical': True, 'nonfield_content_identical': True}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
