"""Shared machinery for generating KiCad schematics from a board spec module.

A spec module defines:
  PROJECT_NAME  -- KiCad project name ('board-p')
  OUT           -- output path relative to repo root
  PAPER         -- sheet size ('A3')
  COMPONENTS    -- {ref: (lib_symbol, value, lcsc, footprint, dnp, (x, y))}
  NETS          -- {net_name: ['REF.PIN', ...]}
  NO_CONNECT    -- ['REF.PIN', ...]
  LIB_PATH      -- optional symbol library path relative to repo root, for an
                   isolated candidate library (default symbols/zudo-led-lamp.kicad_sym)

Every connected pin gets a global label at its endpoint (no wires); floating
pins get no_connect markers. Connectivity is verified separately by
verify_netlist.py diffing a kicad-cli netlist export against the same spec.

All node UUIDs are derived deterministically from stable identity strings
(project + ref/net/pin), not random — the "Regen-idempotency check" step in
.github/workflows/component-spec-skills.yml regenerates all projects and diffs
the result against the checked-in .kicad_sch; random UUIDs would make that
diff non-empty on every run regardless of whether the spec actually changed.
"""
import math
import os
import uuid

from sexp import load, atom, find_all

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
LIB_PATH = os.path.join(PROJ, 'symbols', 'zudo-led-lamp.kicad_sym')

# Fixed, arbitrary namespace for uuid5 — only needs to be stable across runs.
_UUID_NAMESPACE = uuid.UUID('a3f0c9d2-2f3e-4a9b-9b0f-3c1d7e8f4a10')


def new_uuid(seed):
    """Deterministic UUID derived from `seed` (see module docstring)."""
    return str(uuid.uuid5(_UUID_NAMESPACE, seed))


class Library:
    def __init__(self, path=LIB_PATH):
        self.text = open(path).read()
        self.tree = load(path)

    def extract_symbol_raw(self, name):
        needle = f'(symbol "{name}"'
        i = self.text.find(needle)
        assert i >= 0, f'symbol {name} not found'
        depth = 0
        j = i
        in_str = False
        while j < len(self.text):
            c = self.text[j]
            if in_str:
                if c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return self.text[i:j + 1]
            j += 1
        raise AssertionError('unbalanced s-expression')

    def pins_of(self, name):
        for sym in find_all(self.tree, 'symbol'):
            if atom(sym[1]) != name:
                continue
            out = []
            for sub in find_all(sym, 'symbol'):
                for pin in find_all(sub, 'pin'):
                    at = find_all(pin, 'at')[0]
                    num = atom(find_all(pin, 'number')[0][1])
                    pname = atom(find_all(pin, 'name')[0][1])
                    length = float(atom(find_all(pin, 'length')[0][1]))
                    ang = float(atom(at[3])) if len(at) > 3 else 0.0
                    out.append((num, pname, float(atom(at[1])), float(atom(at[2])), ang, length))
            return out
        raise AssertionError(f'symbol {name} not found in parsed lib')


def check_coverage(spec, pin_cache):
    """Every pin of every component must be in exactly one net or NC."""
    used = {}
    for net, specs in spec.NETS.items():
        for s in specs:
            assert s not in used, f'{s} appears in both {used[s]} and {net}'
            used[s] = net
    for s in spec.NO_CONNECT:
        assert s not in used, f'{s} is both connected and NC'
        used[s] = 'NC'
    for ref, comp in spec.COMPONENTS.items():
        numbers = {num for num, *_ in pin_cache[comp[0]]}
        for num in numbers:
            assert f'{ref}.{num}' in used, f'pin {ref}.{num} not assigned to any net or NC'
    for s in used:
        ref, num = s.split('.')
        assert ref in spec.COMPONENTS, f'unknown ref {ref}'
        numbers = {n for n, *_ in pin_cache[spec.COMPONENTS[ref][0]]}
        assert num in numbers, f'{s}: pin {num} not in symbol ({sorted(numbers)})'
    return len(used)


def abs_pin_positions(spec, pin_cache, ref):
    """{pin_number: [(x, y, label_angle)]} in sheet coords (y down)."""
    symname, _v, _l, _fp, _dnp, (X, Y) = spec.COMPONENTS[ref]
    out = {}
    for num, _pname, px, py, ang, _length in pin_cache[symname]:
        x = X + px
        y = Y - py
        rad = math.radians(ang)
        dx, dy = math.cos(rad), -math.sin(rad)
        away = (-dx, -dy)
        if abs(away[0]) > abs(away[1]):
            label_ang = 0 if away[0] > 0 else 180
        else:
            label_ang = 270 if away[1] > 0 else 90
        out.setdefault(num, []).append((x, y, label_ang))
    return out


def generate(spec):
    lib = Library(os.path.join(PROJ, spec.LIB_PATH) if hasattr(spec, 'LIB_PATH') else LIB_PATH)
    pin_cache = {}
    for ref, comp in spec.COMPONENTS.items():
        if comp[0] not in pin_cache:
            pin_cache[comp[0]] = lib.pins_of(comp[0])

    n = check_coverage(spec, pin_cache)
    print(f'coverage OK: {n} pin specs over {len(spec.COMPONENTS)} components')

    root_uuid = new_uuid(f'{spec.PROJECT_NAME}:root')
    parts = []
    parts.append('(kicad_sch')
    parts.append('\t(version 20260306)')
    parts.append('\t(generator "eeschema")')
    parts.append('\t(generator_version "10.0")')
    parts.append(f'\t(uuid "{root_uuid}")')
    parts.append(f'\t(paper "{spec.PAPER}")')

    embedded = []
    seen = set()
    for ref, comp in spec.COMPONENTS.items():
        symname = comp[0]
        if symname in seen:
            continue
        seen.add(symname)
        raw = lib.extract_symbol_raw(symname)
        raw = raw.replace(f'(symbol "{symname}"', f'(symbol "zudo-led-lamp:{symname}"', 1)
        embedded.append('\t\t' + raw.replace('\n', '\n\t\t'))
    parts.append('\t(lib_symbols')
    parts.extend(embedded)
    parts.append('\t)')

    label_overrides = getattr(spec, 'LABEL_OVERRIDES', {})
    for ref, (symname, value, lcsc, fp, dnp, (X, Y)) in spec.COMPONENTS.items():
        pins = pin_cache[symname]
        pys = [py for _num, _pn, _px, py, _ang, _len in pins]
        has_horizontal_pins = any(ang in (0.0, 180.0) for *_x, ang, _l in pins)
        if has_horizontal_pins:
            # pins on left/right: reference above the body, value below
            ref_pos = (X, Y - max(pys) - 5.08)
            val_pos = (X, Y - min(pys) + 5.08)
        else:
            # single row of vertical pins (body hangs below): text right and below
            ref_pos = (X + 12.7, Y - 2.54)
            val_pos = (X, Y + 7.62)
        ov = label_overrides.get(ref, {})
        ref_pos = ov.get('Reference', ref_pos)
        val_pos = ov.get('Value', val_pos)
        body = []
        body.append('\t(symbol')
        body.append(f'\t\t(lib_id "zudo-led-lamp:{symname}")')
        body.append(f'\t\t(at {X:g} {Y:g} 0)')
        body.append('\t\t(unit 1)')
        body.append('\t\t(exclude_from_sim no)')
        external = getattr(spec, 'EXTERNAL_COMPONENTS', {}).get(ref)
        if external:
            assert not lcsc and not fp, f'{ref}: external part must have no LCSC or PCB footprint'
        body.append(f'\t\t(in_bom {"yes" if lcsc or external else "no"})')
        body.append(f'\t\t(on_board {"no" if external else "yes"})')
        body.append(f'\t\t(dnp {"yes" if dnp else "no"})')
        body.append(f'\t\t(uuid "{new_uuid(f"{spec.PROJECT_NAME}:{ref}:instance")}")')
        props = [
            ('Reference', ref, ref_pos[0], ref_pos[1], False),
            ('Value', value, val_pos[0], val_pos[1], False),
            ('Footprint', fp, X, Y, True),
            ('Datasheet', external['datasheet'] if external else '', X, Y, True),
        ]
        if external:
            for key, field in [('mpn', 'MPN'), ('manufacturer', 'Manufacturer'), ('supplier', 'Supplier'), ('order_code', 'Supplier Part')]:
                props.append((field, external[key], X, Y, True))
            props.append(('Assembly', 'External panel mount; see component wiring specification', X, Y, True))
        if lcsc:
            props.append(('LCSC', lcsc, X, Y + 7.62, True))
        for pname, pval, px, py, hide in props:
            hide_s = '\n\t\t\t\t(hide yes)' if hide else ''
            body.append(
                f'\t\t(property "{pname}" "{pval}"\n\t\t\t(at {px:g} {py:g} 0)'
                f'\n\t\t\t(effects\n\t\t\t\t(font (size 1.27 1.27)){hide_s}\n\t\t\t)\n\t\t)')
        for pin_idx, (num, *_rest) in enumerate(pin_cache[symname]):
            pin_uuid = new_uuid(f'{spec.PROJECT_NAME}:{ref}:pin:{num}:{pin_idx}')
            body.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{pin_uuid}")\n\t\t)')
        body.append(
            f'\t\t(instances\n\t\t\t(project "{spec.PROJECT_NAME}"\n\t\t\t\t(path "/{root_uuid}"'
            f'\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        body.append('\t)')
        parts.append('\n'.join(body))

    for net, specs in spec.NETS.items():
        for s in specs:
            ref, num = s.split('.')
            for label_idx, (x, y, ang) in enumerate(abs_pin_positions(spec, pin_cache, ref)[num]):
                justify = {0: 'left', 90: 'left', 180: 'right', 270: 'right'}[ang]
                label_uuid = new_uuid(f'{spec.PROJECT_NAME}:label:{net}:{s}:{label_idx}')
                parts.append(
                    f'\t(global_label "{net}"\n'
                    f'\t\t(shape passive)\n'
                    f'\t\t(at {x:g} {y:g} {ang})\n'
                    f'\t\t(effects\n\t\t\t(font (size 1.27 1.27))\n\t\t\t(justify {justify})\n\t\t)\n'
                    f'\t\t(uuid "{label_uuid}")\n'
                    f'\t)')

    for s in spec.NO_CONNECT:
        ref, num = s.split('.')
        for nc_idx, (x, y, _ang) in enumerate(abs_pin_positions(spec, pin_cache, ref)[num]):
            nc_uuid = new_uuid(f'{spec.PROJECT_NAME}:nc:{s}:{nc_idx}')
            parts.append(f'\t(no_connect\n\t\t(at {x:g} {y:g})\n\t\t(uuid "{nc_uuid}")\n\t)')

    parts.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)')
    parts.append('\t(embedded_fonts no)')
    parts.append(')')

    out_path = os.path.join(PROJ, spec.OUT)
    open(out_path, 'w').write('\n'.join(parts) + '\n')
    print(f'wrote {out_path}')
    return out_path
