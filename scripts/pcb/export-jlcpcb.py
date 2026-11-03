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

# Every copper layer of the board is plotted (copper_layers()), then these non-copper layers. Phase 33: a 4-layer board
# (B20) also gets its In1.Cu / In2.Cu gerbers; a 2-layer board plots exactly the earlier set.
NON_COPPER_LAYERS = 'F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Paste,B.Paste'
LAYERS = 'F.Cu,B.Cu,' + NON_COPPER_LAYERS   # the 2-layer plot set
# Board P variants. board-p15 is the separate 15 V product's draft (dec-separate-products); its PCB keeps the
# -draft suffix in the repository and is staged as board-p15.kicad_pcb so schematic-parity DRC can pair it.
P_BOARDS = ('board-p', 'board-p15')
# Board B variants. board-b20-draft is the 20 V switcher-direct draft (phase 33 binding); its schematic comes from
# board_b20_spec.py and its inventory placements from board_b20_components.py.
B_BOARDS = ('board-b', 'board-b20-draft')
PCB_FILES = {'board-p15': 'board-p15-draft.kicad_pcb'}
SPEC_MODULES = {'board-b20-draft': 'board_b20_spec'}
# Reports and the stack preview belong to one Board P + Board B pair. PD20: board-p is Board P r3 (20 V / 5 A), so it
# pairs only with board-b20-draft; the 15 V Board B pairs with board-p15. The retired r2 board-p + Board B stack keeps its
# records (manufacturing/power-budget.json, boards/board-b/assembly-preview/, PCB in git at 6cb02c8) but is not exported.
PAIRS = {
    ('board-p15', 'board-b'): {'budget': 'power-budget-p15.json', 'layout': 'power-layout.json', 'notes': 'package-notes-p15.md',
                               'preview': 'boards/board-b/assembly-preview-p15'},
    ('board-p', 'board-b20-draft'): {'budget': 'power-budget-b20.json', 'layout': 'power-layout-b20.json',
                                     'notes': 'package-notes-b20.md', 'preview': 'boards/board-b20-draft/assembly-preview'},
}
POWER_BUDGETS = {p: pair['budget'] for (p, _), pair in PAIRS.items()}
ORDER_NOTES = {p: pair['notes'] for (p, _), pair in PAIRS.items()}
PARTNER = {**{p: b for p, b in PAIRS}, **{b: p for p, b in PAIRS}}


def pcb_path(name, root=None):
    return (root or ROOT) / 'boards' / name / PCB_FILES.get(name, name + '.kicad_pcb')


def spec_module(name):
    return SPEC_MODULES.get(name, name.replace('-', '_') + '_spec')


def copper_layers(pcb):
    """Copper layer names in stack order (F.Cu, inner layers, B.Cu) from the board's layer table."""
    names = [atom(entry[1]) for entry in find_all(pcb, 'layers')[0][1:]
             if isinstance(entry, list) and len(entry) > 2 and atom(entry[1]).endswith('.Cu')]
    inner = sorted((n for n in names if n not in ('F.Cu', 'B.Cu')), key=lambda n: int(n[2:-3]))
    require('F.Cu' in names and 'B.Cu' in names, 'Board layer table lacks F.Cu/B.Cu')
    return ['F.Cu', *inner, 'B.Cu']


def plot_layers(pcb):
    return ','.join(copper_layers(pcb)) + ',' + NON_COPPER_LAYERS


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


LOCAL_PREFIXES = []   # tool wrapper directories, set in main(); never written into a package


def neutral(text):
    """Command-log text with the repository root and local tool-wrapper directories removed."""
    for prefix in sorted(LOCAL_PREFIXES + [str(ROOT) + '/'], key=len, reverse=True):
        text = text.replace(prefix, '')
    return text


def run(args, log):
    args = [str(a) for a in args]
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    with log.open('a') as stream:
        stream.write(neutral('\n$ ' + ' '.join(args) + '\n' + result.stdout + result.stderr))
    require(result.returncode == 0, f'Command failed ({result.returncode}); see {log}')
    return result.stdout.strip()


def verify_power_report_freshness(root=ROOT, board_p='board-p', board_b='board-b'):
    """Reject stale report contents, even when the report files hash correctly."""
    pair = PAIRS[(board_p, board_b)]
    for key in ('layout', 'budget'):
        require((root/'manufacturing'/pair[key]).is_file(),
                f'No power report for {board_p} + {board_b}: manufacturing/{pair[key]} is missing')
    layout = json.loads((root/'manufacturing'/pair['layout']).read_text())
    budget = json.loads((root/'manufacturing'/pair['budget']).read_text())
    require(isinstance(layout, dict) and isinstance(budget, dict), 'Invalid power report structure')
    require(budget.get('board_p', 'board-p') == board_p, f"{pair['budget']} is not bound to {board_p}")
    require(budget.get('board_b', 'board-b') == board_b, f"{pair['budget']} is not bound to {board_b}")
    pcb_hashes = {name: digest(pcb_path(name, root)) for name in (board_p, board_b)}
    require(layout.get('status') == 'PASS' and layout.get('pcb_sha256') == pcb_hashes[board_b],
            f"Stale {pair['layout']}: regenerate it from the current filled {board_b}")
    for name in (board_p, board_b):
        spec_name = name.replace('-', '_')
        require(budget.get(spec_name+'_spec_sha256') == digest(root/'scripts/schgen'/(spec_module(name)+'.py')),
                f"Stale {pair['budget']}: {name} schematic specification changed")
    require(budget.get('protection_pcb_source_sha256') == pcb_hashes,
            f"Stale {pair['budget']}: Board P or Board B PCB changed")
    copper = budget.get('actual_filled_copper')
    require(isinstance(copper, dict) and copper.get('pcb_sha256') == pcb_hashes[board_b],
            f"Stale {pair['budget']}: filled-copper PCB hash differs from current {board_b}")
    require(copper.get('negative_zones') == layout.get('negative_filled_zone_areas')
            and copper.get('ground_zone_areas_mm2') == layout.get('ground_filled_zone_areas_mm2'),
            f"Stale {pair['budget']}: copper measurements differ from {pair['layout']}")


def check_reused_geometry(report):
    """Cached solid evidence must retain its checked silk-only binding."""
    reuse = report.get('geometry_evidence_reuse')
    if reuse is None:
        return
    require(reuse.get('mode') == 'REUSED_VERIFIED_GEOMETRY', 'Unknown geometry evidence reuse mode')
    proof_path = ROOT/'boards/board-b/artwork/geometry-reuse-verification.json'
    require(reuse.get('proof') == str(proof_path.relative_to(ROOT))
            and reuse.get('proof_sha256') == digest(proof_path), 'Geometry reuse proof changed')
    proof = json.loads(proof_path.read_text())
    require(proof.get('status') == 'PASS' and proof.get('mode') == 'BACK_SILK_ONLY_GEOMETRY_EQUIVALENCE', 'Geometry equivalence did not pass')
    for name in ('board-b', 'board-p'):
        require(proof.get('current_pcb_sha256', {}).get(name) == digest(ROOT/'boards'/name/(name+'.kicad_pcb')), 'Geometry reuse PCB changed: '+name)
    require(proof.get('current_mechanical_spec_sha256') == digest(ROOT/'boards/board-b/mechanical.json'), 'Geometry reuse contract changed')
    require(proof.get('generator') == 'scripts/pcb/rebind-silkscreen-evidence.py'
            and proof.get('generator_sha256') == digest(ROOT/proof['generator']), 'Geometry reuse verifier changed')
    require(proof.get('bound_source_sha256'), 'Geometry reuse lacks dependency locks')
    for name, expected in proof['bound_source_sha256'].items():
        require(digest(ROOT/name) == expected, 'Geometry reuse dependency changed: '+name)


def check_assembly_freshness(board_p='board-p', board_b='board-b'):
    """Require the portable assembly preview to match the current PCB and models."""
    folder=ROOT/PAIRS[(board_p,board_b)]['preview']
    require((folder/'verification.json').is_file(),f'No stack preview for {board_p} + {board_b}: {folder.relative_to(ROOT)}/verification.json is missing')
    report=json.loads((folder/'verification.json').read_text())
    require(report.get('board_p','board-p')==board_p,'Assembly preview is not built with '+board_p)
    check_reused_geometry(report)
    require(report.get('status')=='PASS','Assembly preview checks must pass')
    require(report.get('pd_transform')=='P(x,y) -> B(y-0.5,x+12)' and math.isclose(report.get('board_p_top_z_mm',0),11.1,abs_tol=1e-6),'Assembly must use the reviewed front-side PD stack')
    require(report.get('populated_cross_board_clearance',{}).get('status')=='PASS','Full populated cross-board collision proof is required')
    require(report.get('c5_envelope_clearance',{}).get('status')=='PASS','Maximum C5 envelope check is required')
    require(report.get('project_support_collar_clearance',{}).get('status')=='PASS','Project corner-support clearance check is required')
    require(report.get('generator_sha256')==digest(ROOT/'scripts/pcb/export-assembly-preview.py'),'Assembly preview generator changed')
    require(report.get('mechanical_spec_sha256')==digest(ROOT/'boards/board-b/mechanical.json'),'Assembly mechanical specification changed')
    require(set(report.get('pcb_sha256',{}))=={board_p,board_b},'Assembly preview binds other boards')
    for name in (board_p,board_b):
        require(report.get('pcb_sha256',{}).get(name)==digest(pcb_path(name)),'Assembly PCB changed: '+name)
    require(report.get('model_sources_sha256') and report.get('artifact_sha256'),'Assembly proof is missing model/artifact hashes')
    require(report.get('verification_sources_sha256'),'Assembly proof lacks checker hashes')
    for name,sha in report['verification_sources_sha256'].items():require(digest(ROOT/name)==sha,'Assembly geometry checker changed: '+name)
    for name,sha in report['model_sources_sha256'].items():require(digest(ROOT/name)==sha,'Assembly model source changed: '+name)
    for name,sha in report['artifact_sha256'].items():require(digest(folder/name)==sha,'Assembly preview artifact changed: '+name)
    require(report.get('original_B_nonmodel_geometry_unchanged') is True,'Assembly preview altered Board B geometry')


def check_step_datums(board_p='board-p', board_b='board-b'):
    """Require the sampled model-datum proof to cover the current populated boards."""
    report=json.loads((ROOT/'footprints/kicad/step-datum-verification.json').read_text())
    check_reused_geometry(report)
    require(report.get('status')=='PASS', 'STEP datum verification must pass')
    require(report.get('review_sha256')==digest(ROOT/'scripts/pcb/step-datum-normalizations.json'), 'STEP datum review changed')
    require(report.get('verifier_sha256')==digest(ROOT/'scripts/pcb/verify-step-datums.py'), 'STEP datum verifier changed')
    boards={row['path']:row['sha256'] for row in report.get('boards',[])}
    for name in (board_p,board_b):
        path=str(pcb_path(name).relative_to(ROOT))
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


def export_import_closure(name):
    """Local Python files imported by the exporter, the scripts it runs and the exported board's spec."""
    import modulefinder
    entries = [Path(__file__), ROOT/'scripts/pcb/verify-board-b.py', ROOT/'scripts/pcb/verify-power-layout.py',
               ROOT/'scripts/pcb/check-model-paths.py', ROOT/'scripts/pcb/check-model-bodies.py',
               ROOT/'scripts/schgen/verify_netlist.py', ROOT/'scripts/schgen'/(spec_module(name) + '.py'),
               ROOT/'.claude/skills/component-spec-audit/scripts/validate.py',
               ROOT/'.claude/skills/circuit-spec-integration/scripts/check_forward_tests.py']
    path = [str(ROOT/'scripts/schgen'), str(ROOT/'scripts/pcb'), str(ROOT/'.claude/skills/component-spec-audit/scripts')]
    found = set()
    for entry in entries:
        finder = modulefinder.ModuleFinder(path=path + sys.path, excludes=['pcbnew', 'wx', 'numpy', 'scipy'])
        finder.run_script(str(entry))
        found.update(Path(m.__file__).resolve() for m in finder.modules.values() if m.__file__)
        found.add(entry.resolve())
    return {p for p in found if p.is_relative_to(ROOT)}


def export_board(name, output, cli, inventory, kicad_python, board_p='board-p', board_b='board-b'):
    dest = output / name
    require(not dest.exists(), f'Refusing to overwrite {dest}')
    original = ROOT / 'boards' / name
    spec = importlib.import_module(spec_module(name))
    require(pcb_path(name).is_file(), f'Missing {pcb_path(name).name}')
    for suffix in ('.kicad_sch', '.kicad_pro'):
        require((original / (name + suffix)).is_file(), f'Missing {name}{suffix}')
    source, raw, gerbers, checks = [dest / p for p in ('source', 'raw', 'gerbers', 'checks')]
    for folder in (source, raw, gerbers, checks):
        folder.mkdir(parents=True)
    log = checks / 'commands.log'
    pcb = load(pcb_path(name))
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
    # B20 draft files stay out of this package's lock only while the import closure of every script the export runs
    # proves they do not feed it; scripts/pcb/board-b20/ is a subdirectory and was never globbed
    closure = export_import_closure(name)
    unlocked = sorted(path for path in dependencies if 'b20' in path.name and path.resolve() not in closure)
    dependencies.difference_update(unlocked)
    dependencies.add(ROOT/'scripts/pcb/step-datum-normalizations.json')
    dependencies.add(ROOT/'footprints/kicad/step-datum-verification.json')
    dependencies.update(ROOT / 'manufacturing' / filename for filename in ('power-budget.md', 'power-layout.json', *ORDER_NOTES.values()))
    dependencies.update(ROOT / 'manufacturing' / POWER_BUDGETS[p] for p in P_BOARDS if (ROOT / 'manufacturing' / POWER_BUDGETS[p]).is_file())
    if board_b != 'board-b':
        dependencies.update(ROOT / 'manufacturing' / PAIRS[(board_p, board_b)][key] for key in ('budget', 'layout', 'notes'))
    dependencies.update((ROOT / 'boards/board-p').rglob('*.json'))
    dependencies.update(path for path in original.rglob('*') if path.is_file() and path.suffix in ('.json', '.bin'))
    dependencies.update((ROOT / 'boards/board-b').glob('*.json'))
    dependencies.update(path for path in (ROOT/'boards/board-b/supports').rglob('*') if path.is_file())
    dependencies.update(path for path in (ROOT/'boards/board-b/artwork').rglob('*')
                        if path.is_file() and path.suffix.lower() in ('.svg', '.md', '.json', '.png'))
    if name in B_BOARDS:
        dependencies.update(path for path in (ROOT/PAIRS[(board_p,board_b)]['preview']).rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.json','.md','.stl','.step','.wrl','.png','.zip','.kicad_pcb','.kicad_pro'))
    dependencies.update(p for p in (ROOT / 'boards/board-b/routing').glob('*') if p.is_file())
    dependencies.add(ROOT / 'symbols/zudo-pd.kicad_sym')
    dependencies.update((ROOT / '.claude/skills').glob('component-*/**/*.json'))
    dependencies.update((ROOT / '.claude/skills/circuit-spec-integration').glob('**/*.json'))
    dependencies.update(ROOT / 'footprints/kicad/zudo-power.pretty' / (comp[3].split(':')[1] + '.kicad_mod') for comp in spec.COMPONENTS.values())
    for fp in footprints.values():
        local_name=atom(fp[1]).split(':')[-1]+'.kicad_mod'
        for directory in ('footprints/kicad','footprints/kicad/zudo-power.pretty'):
            local=ROOT/directory/local_name
            if local.is_file():dependencies.add(local)
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
        staged = name + '.kicad_pcb' if path == pcb_path(name) else path.name
        if path.suffix in ('.kicad_pcb', '.kicad_pro') and staged.rsplit('.', 1)[0] != name:
            continue   # e.g. board-p15-draft.kicad_pro: the staged project is <name>.kicad_pro
        hashes[str(path.relative_to(ROOT))] = digest(path)
        content = path.read_text().replace('${KIPRJMOD}/../../', '${KIPRJMOD}/' + os.path.relpath(ROOT, source) + '/')
        (source / staged).write_text(content)
    for path in [ROOT / 'scripts/schgen' / (spec_module(name) + '.py'),
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
    run([sys.executable, ROOT/'scripts/pcb/check-model-bodies.py',board_path,'--output',checks/'model-bodies.json'],log)
    run([cli, 'pcb', 'render', '--width', '1800', '--height', '1400', '--quality', 'high',
         '--rotate', '20,0,-15', '--zoom', '0.8', '-o', dest / '3d-top.png', board_path], log)
    run([cli, 'sch', 'erc', '--format', 'json', '-o', checks / 'erc.json', sch_path], log)
    erc = json.loads((checks / 'erc.json').read_text())
    erc_items = [v for sheet in erc['sheets'] for v in sheet['violations']]
    require(not any(v['severity'] == 'error' for v in erc_items), f'{name}: ERC errors; see {checks}')
    run([cli, 'sch', 'export', 'pdf', '-o', dest / 'schematic.pdf', sch_path], log)
    run([cli, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', raw / (name + '.net'), sch_path], log)
    run([sys.executable, ROOT / 'scripts/schgen/verify_netlist.py', spec_module(name), raw / (name + '.net')], log)
    copper = copper_layers(pcb)
    run([cli, 'pcb', 'export', 'gerbers', '-l', plot_layers(pcb), '--use-drill-file-origin', '--subtract-soldermask', '-o', gerbers, board_path], log)
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
    for layer in copper[1:-1]:
        require(any(layer.replace('.', '_') in p.name for p in files), f'{name}: missing {layer} gerber')
    with zipfile.ZipFile(dest / f'{name}-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.name)
    result = {'board': name, 'copper_layers': copper, 'fitted_components': len(included), 'bom_lines': len(bom), 'excluded': excluded,
              'assembly_sides': dict(collections.Counter(r['Layer'] for r in cpl)), 'source_hashes': hashes,
              'source_lock_exclusions': {str(path.relative_to(ROOT)): 'B20 draft file outside the import closure of the export scripts' for path in unlocked},
              'drc_errors': 0, 'unconnected': 0, 'erc_errors': 0,
              'erc_warnings': len(erc_items), 'drc_warnings': len(drc['violations']),
              'parity_warnings': len(drc['schematic_parity']), 'origin_mm': [ox, oy],
              'rotation_policy': 'Native KiCad rotations; verify exact-part orientation in assembly preview'}
    (checks / 'export-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--boards', nargs='+', choices=(*P_BOARDS, *B_BOARDS), default=['board-p15', 'board-b'])
    parser.add_argument('--kicad-cli', default=shutil.which('kicad-cli'))
    mac_python = Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3')
    parser.add_argument('--kicad-python', default=str(mac_python) if mac_python.is_file() else sys.executable,
                        help='Python with pcbnew and wx for required PCB geometry checks')
    args = parser.parse_args()
    require(args.kicad_cli, 'kicad-cli is required; no skipped fabrication checks')
    LOCAL_PREFIXES.extend(sorted({str(Path(tool).resolve().parent) + '/' for tool in (args.kicad_cli, args.kicad_python)
                                  if tool and Path(tool).is_absolute() and not str(Path(tool).resolve()).startswith(str(ROOT))}))
    p_boards = [b for b in args.boards if b in P_BOARDS]
    b_boards = [b for b in args.boards if b in B_BOARDS]
    require(len(p_boards) <= 1 and len(b_boards) <= 1 and len(set(args.boards)) == len(args.boards),
            'Export at most one Board P variant and one Board B variant, each board once')
    board_p = p_boards[0] if p_boards else PARTNER[b_boards[0]]
    board_b = b_boards[0] if b_boards else PARTNER[p_boards[0]]
    require((board_p, board_b) in PAIRS, f'No reviewed stack pairing for {board_p} + {board_b}')
    pair = PAIRS[(board_p, board_b)]
    verify_power_report_freshness(board_p=board_p, board_b=board_b)
    check_step_datums(board_p, board_b)
    output = args.output.resolve()
    require(not output.exists(), 'Choose a new staging directory; replace the current prototype outputs only after validation')
    # Either board alone is still half of the P+B stack, so every export carries the stack proof (review F11).
    check_assembly_freshness(board_p, board_b)
    output.mkdir(parents=True)
    run([sys.executable, ROOT / '.claude/skills/component-spec-audit/scripts/validate.py', '--strict'], output / 'preflight.log')
    run([sys.executable, ROOT / '.claude/skills/circuit-spec-integration/scripts/check_forward_tests.py', '--strict'], output / 'preflight.log')
    inventory = json.loads((ROOT / '.claude/skills/component-spec-audit/references/inventory.json').read_text())
    results = [export_board(name, output, args.kicad_cli, inventory, args.kicad_python, board_p, board_b) for name in args.boards]
    for result in results:
        for path, expected in result['source_hashes'].items():
            require(digest(ROOT / path) == expected, f'Source changed during export: {path}')
    manifest = {'purpose': 'Development review files, not an order: fabrication and assembly review; electrical validation is separate',
                'kicad_version': subprocess.check_output([args.kicad_cli, '--version'], text=True).strip(),
                'git_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'boards': results}
    shutil.copyfile(ROOT / 'manufacturing' / pair['notes'], output / 'ORDER-NOTES.md')
    for filename in (pair['budget'], 'power-budget.md', pair['layout']):
        shutil.copyfile(ROOT / 'manufacturing' / filename, output / filename)
    shutil.copyfile(ROOT/'footprints/kicad/step-datum-verification.json',output/'step-datum-verification.json')
    shutil.copyfile(ROOT/'scripts/pcb/step-datum-normalizations.json',output/'step-datum-normalizations.json')
    shutil.copytree(ROOT/pair['preview'],output/'mechanical/assembly',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(ROOT/'boards/board-b/supports',output/'mechanical/supports')
    manifest['artifact_hashes'] = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file() and path.suffix not in ('.lck', '.kicad_prl')}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files = [path for path in sorted(output.rglob('*')) if path.is_file() and path.suffix not in ('.lck', '.kicad_prl')]
    (output / 'SHA256SUMS').write_text(''.join(digest(path) + '  ' + str(path.relative_to(output)) + '\n' for path in files))
    print(json.dumps({r['board']: {k: v for k, v in r.items() if k not in ('source_hashes', 'excluded')} for r in results}, indent=2))


if __name__ == '__main__':
    main()
