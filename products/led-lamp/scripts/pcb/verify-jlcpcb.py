#!/usr/bin/env python3
"""Independently check JLCPCB artifacts and render their Gerber ZIPs (gerbonara)."""

import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import shutil
import sys
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load


def require(condition, message):
    if not condition:
        raise ValueError(message)


def props(node):
    return {atom(p[1]): atom(p[2]) for p in find_all(node, 'property')}


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('--package', action='store_true', help='Write order notes, hashes and a handoff ZIP')
    args = parser.parse_args()
    release = args.release.resolve()
    manifest = json.loads((release / 'manifest.json').read_text())
    from gerbonara import LayerStack
    import resvg_py
    results = []
    for board in manifest['boards']:
        name = board['board']
        dest = release / name
        spec = importlib.import_module(name.replace('-', '_') + '_spec')
        expected = {ref: item[2] for ref, item in spec.COMPONENTS.items()
                    if item[2] and (not item[4] or ref in board['population_overrides'])}
        bom = {}
        for row in read_csv(dest / 'bom.csv'):
            for ref in row['Designator'].split(','):
                require(ref not in bom, f'{name}: duplicate BOM reference {ref}')
                bom[ref] = row['JLCPCB Part #']
        require(bom == expected, f'{name}: BOM differs from authorized population')
        cpl = read_csv(dest / 'cpl.csv')
        raw_positions = {r['Ref']: r for r in read_csv(dest / 'raw/positions.csv')}
        corrections = json.loads((ROOT / 'manufacturing/jlcpcb-rotation-corrections.json').read_text()).get(name, {})
        require(board.get('rotation_corrections', {}) == corrections, f'{name}: rotation manifest mismatch')
        require(len(cpl) == len(expected) and {r['Designator'] for r in cpl} == set(expected),
                f'{name}: CPL/BOM reference mismatch')
        source = load(dest / 'source' / (name + '.kicad_pcb'))
        fps = {props(fp)['Reference']: fp for fp in find_all(source, 'footprint')
               if props(fp)['Reference'] in expected}
        sch = load(dest / 'source' / (name + '.kicad_sch'))
        symbols = {props(s).get('Reference'): s for s in find_all(sch, 'symbol')}
        ox, oy = board['origin_mm']
        for row in cpl:
            ref = row['Designator']
            fp = fps[ref]
            require(props(fp)['LCSC'] == props(fp)['LCSC Part'] == expected[ref],
                    f'{name}/{ref}: snapshot identity mismatch')
            require('dnp' not in [atom(a) for a in find_all(fp, 'attr')[0][1:]],
                    f'{name}/{ref}: snapshot PCB still DNP')
            require(atom(find_all(symbols[ref], 'dnp')[0][1]) == 'no',
                    f'{name}/{ref}: snapshot schematic still DNP')
            at = find_all(fp, 'at')[0]
            x, y = float(row['Mid X'].removesuffix('mm')), float(row['Mid Y'].removesuffix('mm'))
            require(abs(x - (float(atom(at[1])) - ox)) < .0001 and
                    abs(y - (oy - float(atom(at[2])))) < .0001,
                    f'{name}/{ref}: incorrect coordinate')
            side = 'Top' if atom(find_all(fp, 'layer')[0][1]) == 'F.Cu' else 'Bottom'
            require(row['Layer'] == side, f'{name}/{ref}: wrong placement side')
            require(math.isfinite(float(row['Rotation'])) and 0 <= float(row['Rotation']) < 360,
                    f'{name}/{ref}: invalid rotation')
            correction = corrections.get(ref)
            if correction:
                require(correction['lcsc'] == expected[ref], f'{name}/{ref}: correction part mismatch')
            target_rotation = (float(raw_positions[ref]['Rot']) +
                               (correction['offset_degrees'] if correction else 0)) % 360
            require(math.isclose(float(row['Rotation']), target_rotation, abs_tol=.0001),
                    f'{name}/{ref}: incorrect JLCPCB rotation')
        drc = json.loads((dest / 'checks/drc.json').read_text())
        erc = json.loads((dest / 'checks/erc.json').read_text())
        erc_items = [v for s in erc['sheets'] for v in s['violations']]
        require(not any(v['severity'] == 'error' for v in erc_items), f'{name}: ERC errors')
        require(not drc['unconnected_items'], f'{name}: unrouted connections')
        require(not any(v['severity'] == 'error' for key in ('violations', 'schematic_parity')
                        for v in drc[key]), f'{name}: DRC errors')
        for path, sha in board['source_hashes'].items():
            require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha,
                    f'{name}: source changed since export')
        archive = dest / f'{name}-gerbers.zip'
        with zipfile.ZipFile(archive) as z:
            require(z.testzip() is None, f'{name}: corrupted ZIP')
            require(set(z.namelist()) == {p.name for p in (dest / 'gerbers').iterdir()},
                    f'{name}: ZIP layer mismatch')
            for path in (dest / 'gerbers').iterdir():
                require(z.read(path.name) == path.read_bytes(), f'{name}: stale archived layer')
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always')
            stack = LayerStack.open(archive)
        parser_warnings = [str(m.message) for m in messages if not issubclass(m.category, ResourceWarning)]
        require(all('G90 header statement found after end of header' in m for m in parser_warnings),
                f'{name}: unexpected Gerber parser warnings: {parser_warnings}')
        require(len(stack.copper_layers) == 2, f'{name}: expected two copper layers')
        require(stack.drill_pth is not None and stack.drill_npth is not None,
                f'{name}: missing separate plated/nonplated drills')
        # Outline aperture width expands bounds by 0.05 mm; dimensions below are centerlines.
        width, height = stack.outline.size('mm')
        expected_size = {'board-p': (27, 40), 'board-l': (60, 60), 'swd-adapter': (36, 18.1)}[name]
        require(abs(width - expected_size[0]) < .06 and abs(height - expected_size[1]) < .06,
                f'{name}: incorrect outline size {width}x{height}')
        for side in ('top', 'bottom'):
            svg = str(stack.to_pretty_svg(side=side))
            (dest / f'gerber-{side}.svg').write_text(svg)
            (dest / f'gerber-{side}.png').write_bytes(resvg_py.svg_to_bytes(svg_string=svg, width=1200, dpi=96))
        result = {'board': name, 'bom_cpl_identity': 'PASS', 'population': 'PASS',
                  'positions_sides': 'PASS', 'rotations': 'PASS', 'source_hashes': 'PASS', 'gerber_zip': 'PASS',
                  'independent_gerber_parse': 'PASS', 'fitted_components': len(expected),
                  'outline_bounds_mm': [width, height],
                  'erc_errors': 0, 'erc_warnings': len(erc_items),
                  'drc_errors': 0, 'drc_warnings': len(drc['violations']),
                  'parity_warnings': len(drc['schematic_parity'])}
        result['excellon_parser_note'] = 'KiCad places G90 after the header; parsed as absolute coordinates'
        results.append(result)
        print(json.dumps(result), flush=True)
    (release / 'checks/independent-validation.json').write_text(json.dumps(results, indent=2) + '\n')
    if args.package:
        shutil.copyfile(ROOT / 'manufacturing/README.md', release / 'ORDER-NOTES.md')
        shutil.copyfile(ROOT / 'manufacturing/jlcpcb-rotation-corrections.json', release / 'rotation-corrections.json')
        summary = ['# JLCPCB upload sets', '',
                   'Prepared for quoting and placement review; read ORDER-NOTES.md before checkout.', '',
                   '| Board | Gerber ZIP | BOM | CPL | Fitted parts |',
                   '| --- | --- | --- | --- | --- |']
        for result in results:
            name = result['board']
            summary.append(f'| {name} | [{name}-gerbers.zip]({name}/{name}-gerbers.zip) | '
                           f'[bom.csv]({name}/bom.csv) | [cpl.csv]({name}/cpl.csv) | '
                           f'{result["fitted_components"]} |')
        summary += ['', 'All intended fitted components, including all connector headers, are requested',
                    'for JLCPCB soldering. Intentional Board P DNP options remain excluded.', '',
                    'RV1 CPL rotation is corrected from 0 to 180 degrees, matching the user-adjusted',
                    'JLCPCB bottom preview on 2026-09-19. Do not apply that correction a second time.', '',
                    'Board L RV1: confirm manufacturer-compatible soldering and 1.6 mm board seating',
                    'with JLCPCB. Stock and their placement preview still need checkout review.', '',
                    'Checks: no DRC/ERC errors; no unrouted connections; BOM/CPL identities and',
                    'population match; Gerber/drill ZIPs independently parsed and rendered.',
                    'Existing DRC/ERC warnings are retained under each board/checks directory.', '']
        (release / 'README.md').write_text('\n'.join(summary))
        files = [p for p in sorted(release.rglob('*')) if p.is_file()
                 and p.name not in ('SHA256SUMS', '.DS_Store') and p.suffix not in ('.lck', '.kicad_prl')]
        hashes = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(release)) for p in files]
        sums = release / 'SHA256SUMS'
        sums.write_text('\n'.join(hashes) + '\n')
        bundle = release.parent / f'zudo-led-lamp-{release.name}.zip'
        with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in files + [sums]:
                z.write(path, str(path.relative_to(release)))
        with zipfile.ZipFile(bundle) as z:
            require(z.testzip() is None, 'Corrupted handoff ZIP')
        print(f'Packaged: {bundle} ({bundle.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
