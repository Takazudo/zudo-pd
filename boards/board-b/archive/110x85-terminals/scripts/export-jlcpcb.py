#!/usr/bin/env python3
"""Export a checked, source-locked fabrication review package without changing a PCB."""
import argparse
import collections
import csv
import hashlib
import importlib
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

LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Paste,B.Paste'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def props(node):
    return {atom(p[1]): atom(p[2]) for p in find_all(node, 'property')}


def natural(ref):
    return [int(v) if v.isdigit() else v for v in re.split(r'(\d+)', ref)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, columns, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run(args, log):
    args = [str(a) for a in args]
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    with log.open('a') as stream:
        stream.write('\n$ ' + ' '.join(args) + '\n' + result.stdout + result.stderr)
    require(result.returncode == 0, f'Command failed ({result.returncode}); see {log}')
    return result.stdout.strip()


def verify_power_report_freshness(root=ROOT):
    """Reject stale report contents, even when the report files hash correctly."""
    layout = json.loads((root/'manufacturing/power-layout.json').read_text())
    budget = json.loads((root/'manufacturing/power-budget.json').read_text())
    require(isinstance(layout, dict) and isinstance(budget, dict), 'Invalid power report structure')
    pcb_hashes = {name: digest(root/'boards'/name/(name+'.kicad_pcb'))
                  for name in ('board-p', 'board-b')}
    require(layout.get('status') == 'PASS' and layout.get('pcb_sha256') == pcb_hashes['board-b'],
            'Stale power-layout.json: regenerate it from the current filled Board B')
    for name in ('board-p', 'board-b'):
        spec_name = name.replace('-', '_')
        require(budget.get(spec_name+'_spec_sha256') == digest(root/'scripts/schgen'/(spec_name+'_spec.py')),
                f'Stale power-budget.json: {name} schematic specification changed')
    require(budget.get('protection_pcb_source_sha256') == pcb_hashes,
            'Stale power-budget.json: Board P or Board B PCB changed')
    copper = budget.get('actual_filled_copper')
    require(isinstance(copper, dict) and copper.get('pcb_sha256') == pcb_hashes['board-b'],
            'Stale power-budget.json: filled-copper PCB hash differs from current Board B')
    require(copper.get('negative_zones') == layout.get('negative_filled_zone_areas')
            and copper.get('ground_zone_areas_mm2') == layout.get('ground_filled_zone_areas_mm2'),
            'Stale power-budget.json: copper measurements differ from power-layout.json')


def check_assembly_freshness():
    """Require the portable assembly preview to match the current PCB and models."""
    folder=ROOT/'boards/board-b/assembly-preview'
    report=json.loads((folder/'verification.json').read_text())
    require(report.get('status')=='PASS','Assembly preview checks must pass')
    require(report.get('generator_sha256')==digest(ROOT/'scripts/pcb/export-assembly-preview.py'),'Assembly preview generator changed')
    require(report.get('mechanical_spec_sha256')==digest(ROOT/'boards/board-b/mechanical.json'),'Assembly mechanical specification changed')
    for name in ('board-p','board-b'):
        require(report.get('pcb_sha256',{}).get(name)==digest(ROOT/'boards'/name/(name+'.kicad_pcb')),'Assembly PCB changed: '+name)
    require(report.get('model_sources_sha256') and report.get('artifact_sha256'),'Assembly proof is missing model/artifact hashes')
    require(report.get('verification_sources_sha256'),'Assembly proof lacks checker hashes')
    for name,sha in report['verification_sources_sha256'].items():require(digest(ROOT/name)==sha,'Assembly geometry checker changed: '+name)
    for name,sha in report['model_sources_sha256'].items():require(digest(ROOT/name)==sha,'Assembly model source changed: '+name)
    for name,sha in report['artifact_sha256'].items():require(digest(folder/name)==sha,'Assembly preview artifact changed: '+name)
    require(report.get('original_B_nonmodel_geometry_unchanged') is True,'Assembly preview altered Board B geometry')


def check_step_datums():
    """Require the sampled model-datum proof to cover the current populated boards."""
    report=json.loads((ROOT/'footprints/kicad/step-datum-verification.json').read_text())
    require(report.get('status')=='PASS', 'STEP datum verification must pass')
    require(report.get('review_sha256')==digest(ROOT/'scripts/pcb/step-datum-normalizations.json'), 'STEP datum review changed')
    require(report.get('verifier_sha256')==digest(ROOT/'scripts/pcb/verify-step-datums.py'), 'STEP datum verifier changed')
    boards={row['path']:row['sha256'] for row in report.get('boards',[])}
    for name in ('board-p','board-b'):
        path=f'boards/{name}/{name}.kicad_pcb'
        require(boards.get(path)==digest(ROOT/path), 'STEP datum PCB proof is stale: '+path)
    require(report.get('models'), 'STEP datum report has no models')
    reviewed=json.loads((ROOT/'scripts/pcb/step-datum-normalizations.json').read_text())
    model_names=[model['wrl'] for model in report['models']]
    require(len(model_names)==len(set(model_names)) and set(model_names)=={model['wrl'] for model in reviewed['models']}, 'STEP datum model coverage differs from reviewed set')
    for model in report['models']:
        require(model.get('status')=='PASS', 'STEP datum model failed: '+model['wrl'])
        for extension in ('wrl','step'):
            path=ROOT/'footprints/kicad/zudo-pd.3dshapes'/model[extension]
            require(digest(path)==model[extension+'_sha256'], 'STEP datum asset changed: '+str(path))


def export_board(name, output, cli, inventory, kicad_python):
    dest = output / name
    require(not dest.exists(), f'Refusing to overwrite {dest}')
    original = ROOT / 'boards' / name
    spec = importlib.import_module(name.replace('-', '_') + '_spec')
    for suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro'):
        require((original / (name + suffix)).is_file(), f'Missing {name}{suffix}')
    source, raw, gerbers, checks = [dest / p for p in ('source', 'raw', 'gerbers', 'checks')]
    for folder in (source, raw, gerbers, checks):
        folder.mkdir(parents=True)
    log = checks / 'commands.log'
    pcb = load(original / (name + '.kicad_pcb'))
    footprints = {}
    mechanical = set()
    for fp in find_all(pcb, 'footprint'):
        ref = props(fp).get('Reference')
        require(ref and ref not in footprints, f'Duplicate/empty footprint reference {ref}')
        footprints[ref] = fp
        if ref not in spec.COMPONENTS:
            attrs = {atom(a) for n in find_all(fp, 'attr') for a in n[1:]}
            require({'exclude_from_bom', 'exclude_from_pos_files'} <= attrs,
                    f'Unexpected assembly footprint {name}/{ref}')
            mechanical.add(ref)
    require(set(footprints) - mechanical == set(spec.COMPONENTS), f'{name}: PCB/spec reference mismatch')
    identities = {p['refdes']: line for line in inventory['lines']
                  for p in line['placements'] if p['board'] == name}
    included, excluded = {}, []
    for ref, comp in spec.COMPONENTS.items():
        _, value, lcsc, footprint, dnp, _ = comp
        fp = footprints[ref]
        attrs = {atom(a) for n in find_all(fp, 'attr') for a in n[1:]}
        require(atom(fp[1]) == footprint, f'{name}/{ref}: footprint mismatch')
        require(props(fp).get('Value') == value, f'{name}/{ref}: value mismatch')
        require(('dnp' in attrs) == dnp, f'{name}/{ref}: population mismatch')
        if not lcsc:
            require(any(p['board'] == name and p['refdes'] == ref for p in inventory['exclusions']),
                    f'{name}/{ref}: unregistered bare copper')
            require({'exclude_from_bom', 'exclude_from_pos_files'} <= attrs,
                    f'{name}/{ref}: bare copper has assembly attributes')
            excluded.append({'Designator': ref, 'Reason': 'Bare copper; no physical part', 'LCSC': ''})
            continue
        require(identities[ref]['lcsc'] == lcsc, f'{name}/{ref}: registry mismatch')
        require(props(fp).get('LCSC') == lcsc, f'{name}/{ref}: PCB LCSC mismatch')
        for alias in ('LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
            if alias in props(fp):
                require(props(fp)[alias] == lcsc, f'{name}/{ref}: stale {alias} supplier identity')
        if dnp:
            excluded.append({'Designator': ref, 'Reason': 'Intentional DNP', 'LCSC': lcsc})
        else:
            require(not {'exclude_from_bom', 'exclude_from_pos_files'} & attrs,
                    f'{name}/{ref}: fitted part excluded')
            included[ref] = (identities[ref]['mpn'], lcsc, footprint.split(':')[-1])
    hashes = {}
    dependencies = set((ROOT / 'scripts/schgen').glob('*.py'))
    dependencies.update((ROOT / 'scripts/pcb').glob('*.py'))
    dependencies.add(ROOT/'scripts/pcb/step-datum-normalizations.json')
    dependencies.add(ROOT/'footprints/kicad/step-datum-verification.json')
    dependencies.update(ROOT / 'manufacturing' / filename for filename in ('README.md', 'power-budget.json', 'power-budget.md', 'power-layout.json'))
    dependencies.update((ROOT / 'boards/board-p').rglob('*.json'))
    dependencies.update((ROOT / 'boards/board-b').glob('*.json'))
    if name=='board-b':
        dependencies.update(path for path in (ROOT/'boards/board-b/assembly-preview').rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.json','.md','.stl','.step','.wrl','.png','.zip','.kicad_pcb','.kicad_pro'))
    dependencies.update(p for p in (ROOT / 'boards/board-b/routing').glob('*') if p.is_file())
    dependencies.add(ROOT / 'symbols/zudo-pd.kicad_sym')
    dependencies.update((ROOT / '.claude/skills').glob('component-*/**/*.json'))
    dependencies.update((ROOT / '.claude/skills/circuit-spec-integration').glob('**/*.json'))
    dependencies.update(ROOT / 'footprints/kicad/zudo-power.pretty' / (comp[3].split(':')[1] + '.kicad_mod') for comp in spec.COMPONENTS.values())
    for fp in footprints.values():
        for model in find_all(fp,'model'):
            model_path=Path(atom(model[1]).replace('${KIPRJMOD}',str(original))).resolve()
            require(model_path.is_file() and model_path.is_relative_to(ROOT), f'{name}: unavailable/nonlocal 3D model')
            dependencies.add(model_path)
            if model_path.with_suffix('.step').exists():dependencies.add(model_path.with_suffix('.step'))
    for dependency in dependencies:
        hashes[str(dependency.relative_to(ROOT))] = digest(dependency)
    for path in sorted(original.iterdir()):
        if path.suffix not in ('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_dru') and path.name not in ('fp-lib-table', 'sym-lib-table','mechanical.json'):
            continue
        hashes[str(path.relative_to(ROOT))] = digest(path)
        content = path.read_text().replace('${KIPRJMOD}/../../', '${KIPRJMOD}/' + os.path.relpath(ROOT, source) + '/')
        (source / path.name).write_text(content)
    for path in [ROOT / 'scripts/schgen' / (name.replace('-', '_') + '_spec.py'),
                 ROOT / '.claude/skills/component-spec-audit/references/inventory.json']:
        hashes[str(path.relative_to(ROOT))] = digest(path)
    board_path, sch_path = source / (name + '.kicad_pcb'), source / (name + '.kicad_sch')
    run([cli, 'pcb', 'drc', '--refill-zones', '--save-board', '--schematic-parity',
         '--format', 'json', '-o', checks / 'drc.json', board_path], log)
    drc = json.loads((checks / 'drc.json').read_text())
    errors = [v for key in ('violations', 'unconnected_items', 'schematic_parity')
              for v in drc[key] if v['severity'] == 'error']
    require(not errors and not drc['unconnected_items'], f'{name}: DRC errors or unrouted connections; see {checks}')
    require(all(v['type'] == 'extra_footprint' for v in drc['schematic_parity']), f'{name}: schematic parity mismatch')
    if name == 'board-b':
        run([kicad_python, ROOT / 'scripts/pcb/verify-board-b.py', board_path,
             '--output', checks / 'mechanical-identity.json'], log)
        run([kicad_python, ROOT / 'scripts/pcb/verify-power-layout.py', board_path,
             '--output', checks / 'power-layout.json'], log)
    run([sys.executable, ROOT / 'scripts/pcb/check-model-paths.py', board_path,
         '--output', checks / 'model-paths.json'], log)
    run([cli, 'pcb', 'render', '--width', '1800', '--height', '1400', '--quality', 'high',
         '--rotate', '20,0,-15', '--zoom', '0.8', '-o', dest / '3d-top.png', board_path], log)
    run([cli, 'sch', 'erc', '--format', 'json', '-o', checks / 'erc.json', sch_path], log)
    erc = json.loads((checks / 'erc.json').read_text())
    erc_items = [v for sheet in erc['sheets'] for v in sheet['violations']]
    require(not any(v['severity'] == 'error' for v in erc_items), f'{name}: ERC errors; see {checks}')
    run([cli, 'sch', 'export', 'pdf', '-o', dest / 'schematic.pdf', sch_path], log)
    run([cli, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', raw / (name + '.net'), sch_path], log)
    run([sys.executable, ROOT / 'scripts/schgen/verify_netlist.py', name.replace('-', '_') + '_spec', raw / (name + '.net')], log)
    run([cli, 'pcb', 'export', 'gerbers', '-l', LAYERS, '--use-drill-file-origin', '--subtract-soldermask', '-o', gerbers, board_path], log)
    run([cli, 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'plot', '--excellon-units', 'mm',
         '--excellon-separate-th', '--excellon-oval-format', 'route', '-o', gerbers, board_path], log)
    run([cli, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--use-drill-file-origin',
         '--exclude-dnp', '-o', raw / 'positions.csv', board_path], log)
    grouped = collections.defaultdict(list)
    for ref, identity in included.items():
        grouped[identity].append(ref)
    bom = [{'Comment': mpn, 'Designator': ','.join(sorted(refs, key=natural)), 'Footprint': footprint, 'JLCPCB Part #': lcsc}
           for (mpn, lcsc, footprint), refs in sorted(grouped.items())]
    write_csv(dest / 'bom.csv', ['Comment', 'Designator', 'Footprint', 'JLCPCB Part #'], bom)
    setup = find_all(pcb, 'setup')[0]
    origin = find_all(setup, 'aux_axis_origin')
    ox, oy = [float(atom(v)) for v in origin[0][1:]] if origin else (0, 0)
    cpl = []
    with (raw / 'positions.csv').open() as stream:
        for row in csv.DictReader(stream):
            ref = row['Ref']
            if ref not in included:
                continue
            at = find_all(footprints[ref], 'at')[0]
            x, y = float(row['PosX']), float(row['PosY'])
            require(math.isclose(x, float(atom(at[1])) - ox, abs_tol=.0001) and
                    math.isclose(y, oy - float(atom(at[2])), abs_tol=.0001), f'{name}/{ref}: origin mismatch')
            # JLCPCB's KiCad guide preserves exported PosY (already Cartesian Y-up).
            cpl.append({'Designator': ref, 'Mid X': f'{x:.4f}mm', 'Mid Y': f'{y:.4f}mm',
                        'Layer': row['Side'].capitalize(), 'Rotation': f'{float(row["Rot"]) % 360:g}'})
    require(len(cpl) == len(included) and {r['Designator'] for r in cpl} == set(included), f'{name}: BOM/CPL mismatch')
    write_csv(dest / 'cpl.csv', ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'], sorted(cpl, key=lambda r: natural(r['Designator'])))
    write_csv(dest / 'excluded.csv', ['Designator', 'Reason', 'LCSC'], excluded)
    for side, layer in [('top', 'F'), ('bottom', 'B')]:
        run([cli, 'pcb', 'export', 'svg', '--mode-single', '--fit-page-to-board', '--exclude-drawing-sheet',
             '--sketch-pads-on-fab-layers', '-l', f'{layer}.Cu,{layer}.Fab,{layer}.Silkscreen,Edge.Cuts',
             '-o', dest / f'assembly-{side}.svg', *(['--mirror'] if side == 'bottom' else []), board_path], log)
    files = sorted(gerbers.iterdir())
    require({'.gtl', '.gbl', '.gts', '.gbs', '.gto', '.gbo', '.gm1', '.gtp', '.gbp', '.drl'} <= {p.suffix for p in files}, f'{name}: missing fabrication layer')
    with zipfile.ZipFile(dest / f'{name}-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.name)
    result = {'board': name, 'fitted_components': len(included), 'bom_lines': len(bom), 'excluded': excluded,
              'assembly_sides': dict(collections.Counter(r['Layer'] for r in cpl)), 'source_hashes': hashes,
              'drc_errors': 0, 'unconnected': 0, 'erc_errors': 0,
              'erc_warnings': len(erc_items), 'drc_warnings': len(drc['violations']),
              'parity_warnings': len(drc['schematic_parity']), 'origin_mm': [ox, oy],
              'rotation_policy': 'Native KiCad rotations; verify exact-part orientation in assembly preview'}
    (checks / 'export-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--boards', nargs='+', choices=('board-p', 'board-b'), default=['board-p', 'board-b'])
    parser.add_argument('--kicad-cli', default=shutil.which('kicad-cli'))
    mac_python = Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3')
    parser.add_argument('--kicad-python', default=str(mac_python) if mac_python.is_file() else sys.executable,
                        help='Python with pcbnew and wx for required PCB geometry checks')
    args = parser.parse_args()
    require(args.kicad_cli, 'kicad-cli is required; no skipped fabrication checks')
    verify_power_report_freshness()
    check_step_datums()
    output = args.output.resolve()
    require(not output.exists(), 'Choose a new output directory; releases are immutable')
    if 'board-b' in args.boards:check_assembly_freshness()
    output.mkdir(parents=True)
    run([sys.executable, ROOT / '.claude/skills/component-spec-audit/scripts/validate.py', '--strict'], output / 'preflight.log')
    run([sys.executable, ROOT / '.claude/skills/circuit-spec-integration/scripts/check_forward_tests.py', '--strict'], output / 'preflight.log')
    inventory = json.loads((ROOT / '.claude/skills/component-spec-audit/references/inventory.json').read_text())
    results = [export_board(name, output, args.kicad_cli, inventory, args.kicad_python) for name in args.boards]
    for result in results:
        for path, expected in result['source_hashes'].items():
            require(digest(ROOT / path) == expected, f'Source changed during export: {path}')
    manifest = {'purpose': 'Fabrication and assembly review; electrical validation is separate',
                'kicad_version': subprocess.check_output([args.kicad_cli, '--version'], text=True).strip(),
                'git_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'boards': results}
    shutil.copyfile(ROOT / 'manufacturing/README.md', output / 'ORDER-NOTES.md')
    for filename in ('power-budget.json', 'power-budget.md', 'power-layout.json'):
        shutil.copyfile(ROOT / 'manufacturing' / filename, output / filename)
    shutil.copyfile(ROOT/'footprints/kicad/step-datum-verification.json',output/'step-datum-verification.json')
    shutil.copyfile(ROOT/'scripts/pcb/step-datum-normalizations.json',output/'step-datum-normalizations.json')
    if 'board-b' in args.boards:
        shutil.copytree(ROOT/'boards/board-b/assembly-preview',output/'mechanical/assembly',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    manifest['artifact_hashes'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file() and path.suffix not in ('.lck', '.kicad_prl')}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files = [path for path in sorted(output.rglob('*')) if path.is_file() and path.suffix not in ('.lck', '.kicad_prl')]
    (output / 'SHA256SUMS').write_text(''.join(digest(path) + '  ' + str(path.relative_to(output)) + '\n' for path in files))
    print(json.dumps({r['board']: {k: v for k, v in r.items() if k not in ('source_hashes', 'excluded')} for r in results}, indent=2))


if __name__ == '__main__':
    main()
