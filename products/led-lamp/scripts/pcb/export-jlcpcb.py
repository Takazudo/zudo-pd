#!/usr/bin/env python3
"""Export the all-connectors-fitted JLCPCB order without changing design sources."""

import argparse
import collections
import csv
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load

BOARDS = ('board-p', 'board-l', 'swd-adapter')
FIT = {'board-p': set(), 'board-l': {'J3'}, 'swd-adapter': {'J1', 'J2'}}
LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Paste,B.Paste'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def props(node):
    return {atom(p[1]): atom(p[2]) for p in find_all(node, 'property')}


def natural(ref):
    return [int(v) if v.isdigit() else v for v in re.split(r'(\d+)', ref)]


def write_csv(path, columns, rows, **kwargs):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, **kwargs)
        writer.writeheader()
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, log):
    result = subprocess.run([str(v) for v in args], cwd=ROOT, text=True, capture_output=True)
    with log.open('a') as stream:
        stream.write('\n$ ' + ' '.join(str(v) for v in args) + '\n' + result.stdout + result.stderr)
    require(result.returncode == 0, f'Command failed ({result.returncode}); see {log}: {args}')
    return result.stdout.strip()


def snapshot_text(text, kind, board, identities, changes):
    pattern = r'(?ms)^\t\(' + kind + r'(?: |\n).*?^\t\)'

    def update(match):
        block = match.group()
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        if not ref_match:
            return block
        ref = ref_match[1]
        if kind == 'footprint':
            def clean_line(line_match):
                line = line_match.group()
                start = re.search(r'\(start ([^)]*)\)', line)
                end = re.search(r'\(end ([^)]*)\)', line)
                if start and end and start[1] == end[1] and re.search(r'\(layer "[FB]\.SilkS"\)', line):
                    changes.append({'file_type': kind, 'ref': ref, 'field': 'degenerate_silkscreen_line',
                                    'old': start[1], 'new': 'omitted zero-length line'})
                    return ''
                return line
            block = re.sub(r'(?ms)^\t\t\(fp_line\n.*?^\t\t\)\n?', clean_line, block)
        if ref in identities:
            lcsc = identities[ref]['lcsc']
            for name in ('LCSC', 'LCSC Part'):
                prop = r'(\(property "' + name + r'" ")([^"]*)(")'
                old = re.search(prop, block)
                if old and old[2] != lcsc:
                    changes.append({'file_type': kind, 'ref': ref, 'field': name,
                                    'old': old[2], 'new': lcsc})
                    block = re.sub(prop, lambda m: m[1] + lcsc + m[3], block)
        if ref in FIT[board]:
            if kind == 'footprint':
                block, count = re.subn(r'(\(attr[^)]*)\bdnp\b', r'\1', block)
            else:
                block, count = re.subn(r'\(dnp yes\)', '(dnp no)', block)
            require(count == 1, f'{board}/{ref}: expected one DNP flag in {kind}')
            block = block.replace(' (hand-fit)', '')
        return block

    return re.sub(pattern, update, text)


def export_board(board, output, cli, inventory, converter):
    dest = output / board
    require(not dest.exists(), f'Refusing to overwrite existing release: {dest}')
    source = dest / 'source'
    raw = dest / 'raw'
    gerbers = dest / 'gerbers'
    checks = dest / 'checks'
    for folder in (source, raw, gerbers, checks):
        folder.mkdir(parents=True)
    log = checks / 'commands.log'
    spec = importlib.import_module(board.replace('-', '_') + '_spec')
    identities = {p['refdes']: line for line in inventory['lines']
                  for p in line['placements'] if p['board'] == board}
    original = ROOT / 'boards' / board
    pcb = load(original / (board + '.kicad_pcb'))
    footprints = {}
    for fp in find_all(pcb, 'footprint'):
        ref = props(fp)['Reference']
        if ref in spec.COMPONENTS:
            require(ref not in footprints, f'Duplicate {board}/{ref}')
            footprints[ref] = fp
        else:
            require('exclude_from_bom' in [atom(v) for v in find_all(fp, 'attr')[0][1:]],
                    f'Unknown assembly footprint {board}/{ref}')
    require(set(footprints) == set(spec.COMPONENTS), f'{board}: spec/PCB reference mismatch')
    included = {}
    excluded = []
    for ref, component in spec.COMPONENTS.items():
        _, value, lcsc, footprint, dnp, _ = component
        fp = footprints[ref]
        attrs = [atom(v) for v in find_all(fp, 'attr')[0][1:]]
        require(atom(fp[1]) == footprint, f'{board}/{ref}: footprint mismatch')
        require(('dnp' in attrs) == dnp, f'{board}/{ref}: source population mismatch')
        if not lcsc:
            require(any(p['board'] == board and p['refdes'] == ref for p in inventory['exclusions']),
                    f'Unregistered bare pad {board}/{ref}')
            excluded.append({'Designator': ref, 'Reason': 'Bare copper; no component', 'LCSC': ''})
            continue
        require(identities[ref]['lcsc'] == lcsc, f'{board}/{ref}: registry identity mismatch')
        require(props(fp).get('LCSC') == lcsc, f'{board}/{ref}: schematic LCSC/PCB mismatch')
        if dnp and ref not in FIT[board]:
            excluded.append({'Designator': ref, 'Reason': 'Intentional circuit DNP', 'LCSC': lcsc})
        else:
            require(not {'exclude_from_bom', 'exclude_from_pos_files'} & set(attrs),
                    f'{board}/{ref}: fitted part is excluded')
            included[ref] = (identities[ref]['mpn'], lcsc, footprint.split(':')[-1])
    changes = []
    hashes = {}
    for suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro'):
        path = original / (board + suffix)
        hashes[str(path.relative_to(ROOT))] = digest(path)
        content = path.read_text()
        if suffix in ('.kicad_pcb', '.kicad_sch'):
            content = snapshot_text(content, 'footprint' if suffix == '.kicad_pcb' else 'symbol',
                                    board, identities, changes)
        # Keep project-relative library/model links valid in the retained release snapshot.
        root_relative = os.path.relpath(ROOT, source)
        content = content.replace('${KIPRJMOD}/../../', '${KIPRJMOD}/' + root_relative + '/')
        (source / path.name).write_text(content)
    for name in ('fp-lib-table', 'sym-lib-table'):
        content = (original / name).read_text().replace('${KIPRJMOD}/../../',
                    '${KIPRJMOD}/' + os.path.relpath(ROOT, source) + '/')
        (source / name).write_text(content)
    board_path = source / (board + '.kicad_pcb')
    sch_path = source / (board + '.kicad_sch')
    run([cli, 'pcb', 'drc', '--refill-zones', '--save-board', '--schematic-parity',
         '--format', 'json', '-o', checks / 'drc.json', board_path], log)
    drc = json.loads((checks / 'drc.json').read_text())
    errors = [v for key in ('violations', 'unconnected_items', 'schematic_parity')
              for v in drc[key] if v['severity'] == 'error']
    require(not errors and not drc['unconnected_items'], f'{board}: DRC errors or unrouted connections')
    require(all(v['type'] == 'extra_footprint' for v in drc['schematic_parity']),
            f'{board}: schematic parity mismatch')
    run([cli, 'sch', 'erc', '--format', 'json', '-o', checks / 'erc.json', sch_path], log)
    erc = json.loads((checks / 'erc.json').read_text())
    erc_violations = [v for sheet in erc['sheets'] for v in sheet['violations']]
    require(not any(v['severity'] == 'error' for v in erc_violations), f'{board}: ERC errors')
    run([cli, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o',
         raw / (board + '.net'), sch_path], log)
    run([sys.executable, ROOT / 'scripts/schgen/verify_netlist.py',
         board.replace('-', '_') + '_spec', raw / (board + '.net')], log)
    if board == 'board-l':
        run([sys.executable, ROOT / 'scripts/schgen/verify_power_switch.py', '--netlist',
             raw / (board + '.net')], log)
    run([cli, 'pcb', 'export', 'gerbers', '-l', LAYERS, '--use-drill-file-origin',
         '--subtract-soldermask', '-o', gerbers, board_path], log)
    run([cli, 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'plot',
         '--excellon-units', 'mm', '--excellon-separate-th', '--excellon-oval-format', 'route',
         '-o', gerbers, board_path], log)
    run([cli, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
         '--use-drill-file-origin', '--exclude-dnp', '-o', raw / 'positions.csv', board_path], log)
    grouped = collections.defaultdict(list)
    for ref, identity in included.items():
        grouped[identity].append(ref)
    bom_input = [{'Designator': ','.join(sorted(refs, key=natural)), 'Designation': mpn,
                  'Footprint': footprint, 'Quantity': len(refs)}
                 for (mpn, lcsc, footprint), refs in sorted(grouped.items())]
    write_csv(raw / 'bom.csv', ['Designator', 'Designation', 'Footprint', 'Quantity'], bom_input, delimiter=';')
    bom_rows = converter.convert_bom(raw / 'bom.csv', dest / 'bom.csv')
    for row in bom_rows:
        row['JLCPCB Part #'] = included[row['Designator'].split(',')[0]][1]
    write_csv(dest / 'bom.csv', ['Comment', 'Designator', 'Footprint', 'JLCPCB Part #'], bom_rows)
    with (raw / 'positions.csv').open() as stream:
        positions = list(csv.DictReader(stream))
    setup = find_all(pcb, 'setup')[0]
    origin_node = find_all(setup, 'aux_axis_origin')
    ox, oy = [float(atom(v)) for v in origin_node[0][1:]] if origin_node else (0, 0)
    cpl = []
    corrections = json.loads((ROOT / 'manufacturing/jlcpcb-rotation-corrections.json').read_text()).get(board, {})
    require(set(corrections) <= set(included), f'{board}: correction targets an unfitted part')
    for row in positions:
        ref = row['Ref']
        if ref not in included:
            continue
        at = find_all(footprints[ref], 'at')[0]
        x, y = float(row['PosX']), float(row['PosY'])
        require(math.isclose(x, float(atom(at[1])) - ox, abs_tol=0.0001)
                and math.isclose(y, oy - float(atom(at[2])), abs_tol=0.0001),
                f'{board}/{ref}: coordinate/origin mismatch')
        # JLCPCB's KiCad 10 guide preserves exported PosY; it is already Cartesian Y-up.
        correction = corrections.get(ref)
        if correction:
            require(correction['lcsc'] == included[ref][1], f'{board}/{ref}: rotation correction identity changed')
        rotation = (float(row['Rot']) + (correction['offset_degrees'] if correction else 0)) % 360
        cpl.append({'Designator': ref, 'Mid X': f'{x:.4f}mm', 'Mid Y': f'{y:.4f}mm',
                    'Layer': row['Side'].capitalize(), 'Rotation': f'{rotation:g}'})
    require(len(cpl) == len(included) and {r['Designator'] for r in cpl} == set(included),
            f'{board}: BOM/CPL reference mismatch')
    write_csv(dest / 'cpl.csv', ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'],
              sorted(cpl, key=lambda r: natural(r['Designator'])))
    write_csv(dest / 'excluded.csv', ['Designator', 'Reason', 'LCSC'], excluded)
    for side, layer in [('top', 'F'), ('bottom', 'B')]:
        run([cli, 'pcb', 'export', 'svg', '--mode-single', '--fit-page-to-board',
             '--exclude-drawing-sheet', '--sketch-pads-on-fab-layers',
             '-l', f'{layer}.Cu,{layer}.Fab,{layer}.Silkscreen,Edge.Cuts',
             '-o', dest / f'assembly-{side}.svg', *(['--mirror'] if side == 'bottom' else []), board_path], log)
    files = sorted(gerbers.iterdir())
    require({'.gtl', '.gbl', '.gts', '.gbs', '.gto', '.gbo', '.gm1', '.gtp', '.gbp', '.drl'}
            <= {p.suffix for p in files}, f'{board}: missing fabrication layer')
    for path in files:
        data = path.read_text()
        require(('M30' in data if path.suffix == '.drl' else
                 ('M02*' in data if path.suffix != '.gbrjob' else True)), f'Incomplete {path}')
    with zipfile.ZipFile(dest / f'{board}-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.name)
    result = {'board': board, 'fitted_components': len(included), 'bom_lines': len(bom_rows),
              'assembly_sides': dict(collections.Counter(r['Layer'] for r in cpl)),
              'population_overrides': sorted(FIT[board]), 'excluded': excluded,
              'source_hashes': hashes, 'normalized_stale_fields': changes,
              'drc_errors': len(errors), 'unconnected': len(drc['unconnected_items']),
              'erc_errors': 0, 'erc_warnings': len(erc_violations),
              'drc_warnings': len(drc['violations']), 'parity_warnings': len(drc['schematic_parity']),
              'origin_mm': [ox, oy], 'coordinate_convention': 'KiCad CSV Cartesian X/Y; no additional reflection',
              'rotation_corrections': corrections,
              'rotation_policy': 'Native KiCad rotations plus recorded JLCPCB corrections; confirm placement preview'}
    (checks / 'export-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result | {'source_hashes': 'retained', 'normalized_stale_fields': len(changes)}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--boards', nargs='+', choices=BOARDS, default=BOARDS)
    parser.add_argument('--kicad-cli', default=shutil.which('kicad-cli') or
                        '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
    parser.add_argument('--converter', type=Path, default=Path.home() /
                        '.claude/skills/jlcpcb-bom-generate-from-kicad/scripts/convert_to_jlcpcb.py')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    module = importlib.util.spec_from_file_location('jlc_converter', args.converter)
    converter = importlib.util.module_from_spec(module)
    module.loader.exec_module(converter)
    inventory = json.loads((ROOT / '.claude/skills/component-spec-audit/references/inventory.json').read_text())
    results = [export_board(board, output, args.kicad_cli, inventory, converter) for board in args.boards]
    if (output / 'manifest.json').exists():
        previous = json.loads((output / 'manifest.json').read_text())['boards']
        results += [r for r in previous if r['board'] not in args.boards]
        results.sort(key=lambda r: BOARDS.index(r['board']))
    manifest = {'variant': 'JLCPCB fitted connectors; intentional circuit DNP preserved',
                'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'kicad_version': subprocess.check_output([args.kicad_cli, '--version'], text=True).strip(),
                'boards': results}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for result in results:
        for path, expected in result['source_hashes'].items():
            require(digest(ROOT / path) == expected, f'Source changed during export: {path}')


if __name__ == '__main__':
    main()
