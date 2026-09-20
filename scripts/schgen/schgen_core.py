"""Shared machinery for generating KiCad schematics from a board spec module.

A spec module defines:
  PROJECT_NAME  -- KiCad project name ('board-a')
  OUT           -- output path relative to repo root
  PAPER         -- sheet size ('A3')
  COMPONENTS    -- {ref: (lib_symbol, value, lcsc, footprint, dnp, (x, y))}
  NETS          -- {net_name: ['REF.PIN', ...]}
  NO_CONNECT    -- ['REF.PIN', ...]

Every connected pin gets a global label at its endpoint (no wires); floating
pins get no_connect markers. Connectivity is verified separately by
verify_netlist.py diffing a kicad-cli netlist export against the same spec.

All node UUIDs are derived deterministically from stable identity strings
(project + ref/net/pin), not random. This matters for any future
regen-idempotency check (see scripts/schgen/README.md): regenerating a board
from its spec and diffing the result against the checked-in .kicad_sch only
tells you anything if the diff is empty whenever the spec is unchanged --
random UUIDs would make that diff non-empty on every run regardless of
whether the spec actually changed.
"""
import importlib
import importlib.util
import math
import os
import uuid
from pathlib import Path

from sexp import load, atom, find_all

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
LIB_PATH = os.path.join(PROJ, 'symbols', 'zudo-pd.kicad_sym')

# Fixed, arbitrary namespace for uuid5 — only needs to be stable across runs.
_UUID_NAMESPACE = uuid.UUID('a3f0c9d2-2f3e-4a9b-9b0f-3c1d7e8f4a10')


class SchgenError(Exception):
    """A spec or library problem the user must fix — reported as a message,
    not a traceback."""


def load_spec_module(spec_module_arg):
    """Load a spec module from either a filesystem .py path or a dotted
    module name on sys.path. Shared by every schgen CLI tool."""
    path = Path(spec_module_arg)
    if path.suffix == '.py' or path.exists():
        module_spec = importlib.util.spec_from_file_location(path.stem, path)
        if module_spec is None or module_spec.loader is None:
            raise SchgenError(f'could not load spec module from {spec_module_arg}')
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module
    return importlib.import_module(spec_module_arg)


def new_uuid(seed):
    """Deterministic UUID derived from `seed` (see module docstring)."""
    return str(uuid.uuid5(_UUID_NAMESPACE, seed))


class Library:
    def __init__(self, path=LIB_PATH):
        with open(path, encoding='utf-8') as f:
            self.text = f.read()
        self.tree = load(path)

    def extract_symbol_raw(self, name):
        needle = f'(symbol "{name}"'
        i = self.text.find(needle)
        if i < 0:
            raise SchgenError(f'symbol {name} not found in {LIB_PATH}')
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
        raise SchgenError(f'unbalanced s-expression while extracting symbol {name}')

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
        raise SchgenError(f'symbol {name} not found in parsed lib {LIB_PATH}')


def check_coverage(spec, pin_cache):
    """Every pin of every component must be in exactly one net or NC.

    Collects every violation before failing, so a spec with several
    mis-assigned pins reports them all in one run instead of one per regen.
    """
    problems = []
    used = {}
    for net, specs in spec.NETS.items():
        for s in specs:
            if s in used:
                problems.append(f'{s} appears in both {used[s]} and {net}')
            used[s] = net
    for s in spec.NO_CONNECT:
        if s in used:
            problems.append(f'{s} is both connected and NC')
        used[s] = 'NC'
    for ref, comp in spec.COMPONENTS.items():
        numbers = {num for num, *_ in pin_cache[comp[0]]}
        for num in numbers:
            if f'{ref}.{num}' not in used:
                problems.append(f'pin {ref}.{num} not assigned to any net or NC')
    for s in used:
        ref, num = s.split('.')
        if ref not in spec.COMPONENTS:
            problems.append(f'unknown ref {ref}')
            continue
        numbers = {n for n, *_ in pin_cache[spec.COMPONENTS[ref][0]]}
        if num not in numbers:
            problems.append(f'{s}: pin {num} not in symbol ({sorted(numbers)})')
    if problems:
        raise SchgenError('coverage check failed:\n  ' + '\n  '.join(problems))
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


def _emit_header(spec, root_uuid):
    return [
        '(kicad_sch',
        '\t(version 20260306)',
        '\t(generator "eeschema")',
        '\t(generator_version "10.0")',
        f'\t(uuid "{root_uuid}")',
        f'\t(paper "{spec.PAPER}")',
    ]


def _emit_lib_symbols(spec, lib):
    embedded = []
    seen = set()
    for ref, comp in spec.COMPONENTS.items():
        symname = comp[0]
        if symname in seen:
            continue
        seen.add(symname)
        raw = lib.extract_symbol_raw(symname)
        raw = raw.replace(f'(symbol "{symname}"', f'(symbol "zudo-pd:{symname}"', 1)
        embedded.append('\t\t' + raw.replace('\n', '\n\t\t'))
    if getattr(spec, 'ERC_POWER_FLAGS', {}):
        raw = lib.extract_symbol_raw('PWR_FLAG')
        raw = raw.replace('(symbol "PWR_FLAG"', '(symbol "zudo-pd:PWR_FLAG"', 1)
        embedded.append('\t\t' + raw.replace('\n', '\n\t\t'))
    return ['\t(lib_symbols'] + embedded + ['\t)']


def _emit_power_flags(spec, root_uuid):
    """Declare externally/converter-supplied nets without adding PCB/BOM parts."""
    parts = []
    for index, (net, (x, y)) in enumerate(getattr(spec, 'ERC_POWER_FLAGS', {}).items(), 1):
        if net not in spec.NETS:
            raise SchgenError(f'ERC power flag references unknown net {net}')
        ref = f'#FLG{index:03d}'
        uid = new_uuid(f'{spec.PROJECT_NAME}:power-flag:{net}')
        parts.append(f'''\t(symbol
        (lib_id "zudo-pd:PWR_FLAG") (at {x:g} {y:g} 0) (unit 1)
        (exclude_from_sim no) (in_bom no) (on_board no) (dnp no)
        (uuid "{uid}")
        (property "Reference" "{ref}" (at {x:g} {y + 1.905:g} 0)
            (effects (font (size 1.27 1.27)) (hide yes)))
        (property "Value" "PWR_FLAG" (at {x:g} {y + 3.81:g} 0)
            (effects (font (size 1.27 1.27))))
        (pin "1" (uuid "{new_uuid(uid + ':pin')}"))
        (instances (project "{spec.PROJECT_NAME}"
            (path "/{root_uuid}" (reference "{ref}") (unit 1))))
    )
    (global_label "{net}" (shape input) (at {x:g} {y:g} 0)
        (effects (font (size 1.27 1.27)) (justify left))
        (uuid "{new_uuid(uid + ':label')}"))''')
    return parts


def _emit_symbol_instances(spec, pin_cache, root_uuid):
    parts = []
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
        body.append(f'\t\t(lib_id "zudo-pd:{symname}")')
        body.append(f'\t\t(at {X:g} {Y:g} 0)')
        body.append('\t\t(unit 1)')
        body.append('\t\t(exclude_from_sim no)')
        # JLCPCB assembly convention: an orderable line always carries an LCSC
        # number; bare-copper pad groups (pogo pads, test pads) never do and
        # must be ABSENT from the assembly BOM/CPL, not present with a blank
        # part number, so they are emitted in_bom=no. They stay on_board=yes
        # -- they are real board features.
        body.append(f'\t\t(in_bom {"yes" if lcsc else "no"})')
        body.append('\t\t(on_board yes)')
        body.append(f'\t\t(dnp {"yes" if dnp else "no"})')
        body.append(f'\t\t(uuid "{new_uuid(f"{spec.PROJECT_NAME}:{ref}:instance")}")')
        props = [
            ('Reference', ref, ref_pos[0], ref_pos[1], False),
            ('Value', value, val_pos[0], val_pos[1], False),
            ('Footprint', fp, X, Y, True),
            ('Datasheet', '', X, Y, True),
        ]
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
    return parts


def _emit_global_labels(spec, pin_cache):
    parts = []
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
    return parts


def _emit_no_connects(spec, pin_cache):
    parts = []
    for s in spec.NO_CONNECT:
        ref, num = s.split('.')
        for nc_idx, (x, y, _ang) in enumerate(abs_pin_positions(spec, pin_cache, ref)[num]):
            nc_uuid = new_uuid(f'{spec.PROJECT_NAME}:nc:{s}:{nc_idx}')
            parts.append(f'\t(no_connect\n\t\t(at {x:g} {y:g})\n\t\t(uuid "{nc_uuid}")\n\t)')
    return parts


def generate(spec):
    lib = Library()
    pin_cache = {}
    for ref, comp in spec.COMPONENTS.items():
        if comp[0] not in pin_cache:
            pin_cache[comp[0]] = lib.pins_of(comp[0])

    n = check_coverage(spec, pin_cache)
    print(f'coverage OK: {n} pin specs over {len(spec.COMPONENTS)} components')

    root_uuid = new_uuid(f'{spec.PROJECT_NAME}:root')
    parts = []
    parts.extend(_emit_header(spec, root_uuid))
    parts.extend(_emit_lib_symbols(spec, lib))
    parts.extend(_emit_symbol_instances(spec, pin_cache, root_uuid))
    parts.extend(_emit_power_flags(spec, root_uuid))
    parts.extend(_emit_global_labels(spec, pin_cache))
    parts.extend(_emit_no_connects(spec, pin_cache))
    parts.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)')
    parts.append('\t(embedded_fonts no)')
    parts.append(')')

    out_path = os.path.join(PROJ, spec.OUT)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts) + '\n')
    print(f'wrote {out_path}')
    return out_path
