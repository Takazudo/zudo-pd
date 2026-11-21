"""Rebind named B20 footprints to a geometry-identical library footprint (pure Python, text level).

usage: sync-footprint-identity.py IN.kicad_pcb OUT.kicad_pcb OLD_LIB_ID NEW_LIB_ID REFS OUT.json
REFS is a comma-separated list of reference designators.

The new library footprint must carry exactly the same pads (number, type, shape, position, size, layers)
as each placed instance's old library footprint. For each named instance only the footprint library
identity, its description, the 3D model path and the library-inherited "LCSC Part" property change;
placement, pads, nets, copper and fills are untouched. Every other footprint must not use OLD_LIB_ID's
geometry by accident: instances of OLD_LIB_ID that are not named stay as they are.
The script then proves the result with a sexp comparison: reverting those four items on OUT gives IN.
Value/LCSC fields are left to sync-fields.py, and fills to finalize_refill.py.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, parse, tokenize  # noqa: E402

LIB = ROOT / 'footprints/kicad'


def lib_text(lib_id):
    return (LIB / f'{lib_id.split(":", 1)[1]}.kicad_mod').read_text()


def lib_pads(text):
    tree = parse(tokenize(text))
    pads = []
    for item in tree:
        if isinstance(item, list) and item and atom(item[0]) == 'pad':
            at = next(p for p in item if isinstance(p, list) and atom(p[0]) == 'at')
            size = next(p for p in item if isinstance(p, list) and atom(p[0]) == 'size')
            layers = next(p for p in item if isinstance(p, list) and atom(p[0]) == 'layers')
            pads.append((atom(item[1]), atom(item[2]), atom(item[3]), tuple(float(atom(v)) for v in at[1:3]),
                         tuple(float(atom(v)) for v in size[1:3]), tuple(sorted(atom(v) for v in layers[1:]))))
    return sorted(pads)


def lib_field(text, key):
    match = re.search(rf'\({key} "((?:[^"\\]|\\.)*)"', text)
    if not match:
        raise SystemExit(f'library footprint lacks {key}')
    return match.group(1)


def lib_model(text):
    return re.search(r'\(model "([^"]+)"', text).group(1)


def blocks(text):
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint "', text)]
    ends = starts[1:] + [None]
    out = []
    for s, e in zip(starts, ends):
        if e is None:
            # last footprint ends where the next top-level item starts
            m = re.search(r'\n\t\((?!footprint )', text[s + 1:])
            e = s + 1 + m.start() if m else len(text)
        else:
            m = re.search(r'\n\t\((?!footprint )', text[s + 1:e])
            e = s + 1 + m.start() if m else e
        out.append((s, e))
    return out


def reference(block):
    return re.search(r'\(property "Reference" "([^"]+)"', block).group(1)


def footprints(tree):
    return {atom(next(p for p in fp if isinstance(p, list) and atom(p[0]) == 'property' and atom(p[1]) == 'Reference')[2]): fp
            for fp in tree if isinstance(fp, list) and fp and atom(fp[0]) == 'footprint'}


def revert(fp, old_id, old_descr, old_model):
    out = [fp[0], ('str', old_id)]
    for item in fp[2:]:
        if isinstance(item, list) and item and atom(item[0]) == 'descr':
            item = [item[0], ('str', old_descr)] + item[2:]
        elif isinstance(item, list) and item and atom(item[0]) == 'model':
            item = [item[0], ('str', old_model)] + item[2:]
        out.append(item)
    return out


def main():
    src, dst, old_id, new_id, refs, report = sys.argv[1:7]
    refs = set(filter(None, refs.split(',')))
    old_lib, new_lib = lib_text(old_id), lib_text(new_id)
    if lib_pads(old_lib) != lib_pads(new_lib):
        raise SystemExit('library pads differ: not a geometry-identical rebind')
    new_descr, new_model = lib_field(new_lib, 'descr'), lib_model(new_lib)
    if '"LCSC Part"' in new_lib:
        raise SystemExit('new library footprint must not carry an LCSC Part property')
    raw = Path(src).read_text()
    out, pos, seen, lcsc_parts = [], 0, set(), {}
    for s, e in blocks(raw):
        block = raw[s:e]
        ref = reference(block)
        if ref not in refs:
            continue
        if not block.startswith(f'\n\t(footprint "{old_id}"'):
            raise SystemExit(f'{ref}: placed footprint is not {old_id}')
        old_descr = re.search(r'\n\t\t\(descr "((?:[^"\\]|\\.)*)"\)', block).group(1)
        old_model = re.search(r'\(model "([^"]+)"', block).group(1)
        if old_model != lib_model(old_lib):
            raise SystemExit(f'{ref}: model path {old_model} is not the old library model')
        new_block = block.replace(f'(footprint "{old_id}"', f'(footprint "{new_id}"', 1)
        new_block = new_block.replace(f'(descr "{old_descr}")', f'(descr "{new_descr}")', 1)
        new_block = new_block.replace(f'(model "{old_model}"', f'(model "{new_model}"', 1)
        prop = re.search(r'\n\t\t\(property "LCSC Part" "([^"]*)"\n(?:\t\t\t.*\n)*?\t\t\)', new_block)
        if prop:
            lcsc_parts[ref] = prop.group(1)
            new_block = new_block[:prop.start()] + new_block[prop.end():]
        out.append(raw[pos:s] + new_block)
        pos = e
        seen.add(ref)
    if seen != refs:
        raise SystemExit(f'references not found: {sorted(refs - seen)}')
    text = ''.join(out) + raw[pos:]
    Path(dst).write_text(text)

    before, after = parse(tokenize(raw)), parse(tokenize(text))
    fb, fa = footprints(before), footprints(after)
    checks = {}
    for ref in sorted(refs):
        b, a = fb[ref], fa[ref]
        b_descr = next(atom(i[1]) for i in b if isinstance(i, list) and i and atom(i[0]) == 'descr')
        b_model = next(atom(i[1]) for i in b if isinstance(i, list) and i and atom(i[0]) == 'model')
        a_reverted = revert(a, old_id, b_descr, b_model)
        b_cmp = [i for i in b if not (isinstance(i, list) and i and atom(i[0]) == 'property' and atom(i[1]) == 'LCSC Part')]
        if json.dumps(a_reverted, default=str) != json.dumps(b_cmp, default=str):
            raise SystemExit(f'{ref}: footprint differs beyond library id, description, model and LCSC Part')
        checks[ref] = {'lcsc_part_removed': lcsc_parts.get(ref)}
    rest_b = [i for i in before if not (isinstance(i, list) and i and atom(i[0]) == 'footprint' and footprints([i]).keys() & refs)]
    rest_a = [i for i in after if not (isinstance(i, list) and i and atom(i[0]) == 'footprint' and footprints([i]).keys() & refs)]
    if json.dumps(rest_b, default=str) != json.dumps(rest_a, default=str):
        raise SystemExit('content outside the named footprints changed')
    result = {'scope': 'B20 footprint library-identity rebind to geometry-identical pads; not electrical acceptance',
              'old_lib_id': old_id, 'new_lib_id': new_id, 'library_pads_identical': True,
              'before_sha256': hashlib.sha256(raw.encode()).hexdigest(),
              'after_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'references': checks, 'other_content_identical': True}
    Path(report).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
