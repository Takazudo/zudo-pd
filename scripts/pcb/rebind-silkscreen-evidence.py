#!/usr/bin/env python3
"""Reuse the current verified solid geometry only after a strict back-silk proof.

This does not rerun STEP export, model surface comparison or solid collisions.
It preserves their executed evidence and records the exact equivalence boundary.
The prior checked prototype package is read before it is replaced; no old CAD
snapshot is retained. Copper/pads/models/filled zones/outline/front silk are never
excluded from the comparison. Native label, model-path and body checks are fresh.
"""
import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load

PROOF = ROOT / 'boards/board-b/artwork/geometry-reuse-verification.json'
PREVIEW = ROOT / 'boards/board-b/assembly-preview'
GROUP = 'Board B back artwork'
GRAPHICS = {'gr_text', 'gr_poly', 'gr_line', 'gr_arc', 'gr_rect', 'gr_circle', 'gr_curve'}
NUMBER = re.compile(r'^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$', re.I)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def serialize(node):
    if isinstance(node, list):
        return '(' + ' '.join(serialize(v) for v in node) + ')'
    return json.dumps(node[1], ensure_ascii=False) if node[0] == 'str' else node[1]


def props(node):
    return {atom(n[1]): atom(n[2]) for n in find_all(node, 'property')}


def normalized(node, project):
    if isinstance(node, list):
        if node and atom(node[0]) == 'model':
            node = list(node)
            path = Path(atom(node[1]).replace('${KIPRJMOD}', str(project.resolve())))
            path = (path if path.is_absolute() else project.resolve() / path).resolve()
            require(path.is_file() and path.is_relative_to(ROOT), 'Missing/nonlocal model: ' + str(path))
            node[1] = ('str', str(path.relative_to(ROOT)))
        return [normalized(n, project) for n in node]
    kind, value = node
    if kind == 'atom' and NUMBER.fullmatch(value):
        number = Decimal(value)
        return (kind, '0' if number == 0 else str(number.normalize()))
    return node


def physical(tree, project):
    excluded, excluded_indices, seen = set(), set(), set()
    for index, node in enumerate(tree[1:]):
        if not isinstance(node, list):
            continue
        ids = find_all(node, 'uuid')
        require(len(ids) <= 1, 'Object has multiple UUIDs')
        if ids:
            uid = atom(ids[0][1])
            require(uid not in seen, 'Duplicate top-level UUID: ' + uid)
            seen.add(uid)
        layers = find_all(node, 'layer')
        if atom(node[0]) in GRAPHICS and layers and atom(layers[0][1]) == 'B.SilkS':
            require(len(ids) == 1, 'Back graphic lacks a unique UUID')
            excluded.add(atom(ids[0][1]))
            excluded_indices.add(index)
    kept = []
    for index, node in enumerate(tree[1:]):
        if not isinstance(node, list):
            kept.append(node)
            continue
        if index in excluded_indices:
            continue
        if atom(node[0]) == 'group' and atom(node[1]) == GROUP:
            members = find_all(node, 'members')
            require(len(members) == 1 and {atom(v) for v in members[0][1:]} <= excluded,
                    'Artwork group contains non-back-silkscreen geometry')
            continue
        kept.append(normalized(node, project))
    # KiCad may reorder independent top-level objects on save. All child order,
    # UUIDs and values are retained, apart from exact numeric spelling and the
    # checked export-only model path rebasing above.
    return [tree[0], *sorted(kept, key=lambda n: json.dumps(n, sort_keys=True))]


def mechanical_physical(contract):
    result = copy.deepcopy(contract)
    del result['terminal_blocks']['rail_labels']
    return result


def check_hashes(folder, records):
    for name, expected in records.items():
        require(sha(folder / name) == expected, 'Stale evidence: ' + str(folder / name))


def negative_controls(tree, project):
    baseline = physical(tree, project)
    def reject(name, change):
        candidate = copy.deepcopy(tree)
        change(candidate)
        try:
            differs = physical(candidate, project) != baseline
        except ValueError:
            differs = True
        require(differs, 'Invariant accepted negative control: ' + name)
        return name
    def bump(node, key, index=1):
        item = find_all(node, key)[0]
        item[index] = ('atom', str(Decimal(atom(item[index])) + Decimal('.01')))
    def change_fill(t):
        zone = next(z for z in find_all(t, 'zone') if find_all(z, 'filled_polygon'))
        point = find_all(find_all(find_all(zone, 'filled_polygon')[0], 'pts')[0], 'xy')[0]
        point[1] = ('atom', str(Decimal(atom(point[1])) + Decimal('.01')))
    def duplicate_silk_uuid(t, tag):
        graphic = next(n for n in find_all(t, 'gr_text') if atom(find_all(n, 'layer')[0][1]) == 'B.SilkS')
        physical_node = copy.deepcopy(find_all(t, tag)[0])
        find_all(physical_node, 'uuid')[0][1] = find_all(graphic, 'uuid')[0][1]
        bump(physical_node, 'start')
        t.append(physical_node)
    cases = [reject('track width', lambda t: bump(find_all(t, 'segment')[0], 'width')),
             reject('component position', lambda t: bump(find_all(t, 'footprint')[0], 'at')),
             reject('via position', lambda t: bump(find_all(t, 'via')[0], 'at')),
             reject('pad net', lambda t: find_all(find_all(find_all(t, 'footprint')[0], 'pad')[0], 'net')[0].__setitem__(1, ('str', 'WRONG_NET'))),
             reject('filled zone vertex', change_fill),
             reject('outline vertex', lambda t: bump(next(n for n in find_all(t, 'gr_line') if atom(find_all(n, 'layer')[0][1]) == 'Edge.Cuts'), 'start')),
             reject('model transform', lambda t: bump(find_all(find_all(find_all(t, 'footprint')[0], 'model')[0], 'offset')[0], 'xyz')),
             reject('copper reusing silk UUID', lambda t: duplicate_silk_uuid(t, 'segment')),
             reject('outline reusing silk UUID', lambda t: duplicate_silk_uuid(t, 'gr_line'))]
    allowed = copy.deepcopy(tree)
    label = next(n for n in find_all(allowed, 'gr_text') if atom(find_all(n, 'layer')[0][1]) == 'B.SilkS')
    bump(label, 'at')
    require(physical(allowed, project) == baseline, 'Back-silk-only positive control failed')
    return {'status': 'PASS', 'negative_controls': cases, 'back_silk_positive_control': 'PASS',
            'label_identity_boundary': 'Back-label identity/style is separately checked by the native mechanical validator.'}


def make_proof(package):
    manifest = json.loads((package / 'manifest.json').read_text())
    checksummed = set()
    for line in (package / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name not in checksummed and (package / name).resolve().is_relative_to(package), 'Invalid/duplicate prior checksum path')
        checksummed.add(name)
        require(sha(package / name) == digest, 'Prior package checksum differs: ' + name)
    required = {'manifest.json', 'board-b/source/board-b.kicad_pcb', 'board-b/source/mechanical.json',
                'mechanical/assembly/verification.json', 'step-datum-verification.json'}
    require(required <= checksummed and bool(manifest.get('artifact_hashes'))
            and set(manifest['artifact_hashes']) <= checksummed, 'Incomplete prior package checksum coverage')
    check_hashes(package, manifest['artifact_hashes'])
    records = {row['board']: row for row in manifest['boards']}
    require(set(records) == {'board-b', 'board-p'} and len(manifest['boards']) == 2, 'Expected one checked record per board')
    board_record = records['board-b']
    old_report_path = package / 'mechanical/assembly/verification.json'
    old_report = json.loads(old_report_path.read_text())
    for board in ('board-b', 'board-p'):
        source_key = f'boards/{board}/{board}.kicad_pcb'
        require(records[board]['source_hashes'][source_key] == old_report['pcb_sha256'][board], 'Prior manifest/assembly PCB binding differs')
    require(board_record['source_hashes']['boards/board-b/mechanical.json'] == old_report['mechanical_spec_sha256'], 'Prior manifest/mechanical binding differs')
    require(sha(PREVIEW / 'verification.json') == sha(old_report_path), 'Current cached preview differs from prior checked package')
    check_hashes(PREVIEW, old_report['artifact_sha256'])
    check_hashes(ROOT, old_report['model_sources_sha256'])
    require(old_report['status'] == 'PASS' and old_report['original_B_nonmodel_geometry_unchanged'] is True, 'Prior assembly did not pass')
    for name in ('populated_cross_board_clearance', 'c5_envelope_clearance', 'project_support_collar_clearance'):
        require(old_report[name]['status'] == 'PASS', 'Missing prior geometry check: ' + name)
    require(old_report['generator_sha256'] == sha(ROOT / 'scripts/pcb/export-assembly-preview.py'), 'Collision/assembly generator changed')
    allowed_checker = 'scripts/pcb/verify-compact-mechanics.py'
    for name, digest in old_report['verification_sources_sha256'].items():
        if name != allowed_checker:
            require(sha(ROOT / name) == digest, 'Geometry evidence dependency changed: ' + name)
    current = ROOT / 'boards/board-b/board-b.kicad_pcb'
    previous = package / 'board-b/source/board-b.kicad_pcb'
    before, after = load(previous), load(current)
    a, b = physical(before, previous.parent), physical(after, current.parent)
    require(a == b, 'Non-back-silkscreen PCB structure changed; run full CAD verification')
    old_mechanical_path = package / 'board-b/source/mechanical.json'
    old_mechanical = json.loads(old_mechanical_path.read_text())
    current_mechanical = json.loads((ROOT / 'boards/board-b/mechanical.json').read_text())
    require(sha(old_mechanical_path) == old_report['mechanical_spec_sha256'], 'Prior mechanical contract lock differs')
    require(mechanical_physical(old_mechanical) == mechanical_physical(current_mechanical),
            'Mechanical geometry contract changed; only rail-label metadata may differ')
    require(sha(ROOT / 'boards/board-p/board-p.kicad_pcb') == old_report['pcb_sha256']['board-p'], 'Board P changed')
    datum_path = ROOT / 'footprints/kicad/step-datum-verification.json'
    datum = json.loads(datum_path.read_text())
    require(sha(datum_path) == sha(package / 'step-datum-verification.json'), 'Current datum evidence differs from checked package')
    require(datum['status'] == 'PASS' and datum['review_sha256'] == sha(ROOT / 'scripts/pcb/step-datum-normalizations.json')
            and datum['verifier_sha256'] == sha(ROOT / 'scripts/pcb/verify-step-datums.py'), 'Datum source changed')
    for model in datum['models']:
        require(model['status'] == 'PASS', 'Prior datum model failed')
        for extension in ('step', 'wrl'):
            require(sha(ROOT / 'footprints/kicad/zudo-pd.3dshapes' / model[extension]) == model[extension + '_sha256'], 'Datum model bytes changed')
    bindings = dict(old_report['model_sources_sha256'])
    for name in {*old_report['verification_sources_sha256'], 'boards/board-b/board-b.kicad_pcb',
                 'boards/board-p/board-p.kicad_pcb', 'boards/board-b/mechanical.json',
                 'scripts/pcb/export-assembly-preview.py', 'scripts/pcb/rebind-silkscreen-evidence.py',
                 'scripts/pcb/check-model-paths.py', 'scripts/pcb/verify-step-datums.py',
                 'scripts/pcb/step-datum-normalizations.json'}:
        if name == str(PROOF.relative_to(ROOT)):
            continue
        bindings[name] = sha(ROOT / name)
    proof = {'status': 'PASS', 'mode': 'BACK_SILK_ONLY_GEOMETRY_EQUIVALENCE',
             'generator': str(Path(__file__).relative_to(ROOT)), 'generator_sha256': sha(Path(__file__)),
             'current_pcb_sha256': {board: sha(ROOT / 'boards' / board / (board + '.kicad_pcb')) for board in ('board-b', 'board-p')},
             'previous_source_pcb_sha256': old_report['pcb_sha256'],
             'previous_exported_pcb_sha256': sha(previous), 'previous_manifest_sha256': sha(package / 'manifest.json'),
             'previous_assembly_report_sha256': sha(old_report_path), 'previous_datum_report_sha256': sha(datum_path),
             'assembly_original_execution_pcb_sha256': old_report.get('geometry_evidence_reuse', {}).get('original_execution_pcb_sha256', old_report['pcb_sha256']),
             'assembly_original_execution_report_sha256': old_report.get('geometry_evidence_reuse', {}).get('original_execution_report_sha256', sha(old_report_path)),
             'datum_original_execution_pcb_sha256': datum.get('geometry_evidence_reuse', {}).get('original_execution_pcb_sha256', old_report['pcb_sha256']),
             'datum_original_execution_report_sha256': datum.get('geometry_evidence_reuse', {}).get('original_execution_report_sha256', sha(datum_path)),
             'bound_source_sha256': bindings,
             'non_back_silk_structure_sha256': json_sha(a),
             'current_mechanical_spec_sha256': sha(ROOT / 'boards/board-b/mechanical.json'),
             'physical_mechanical_contract_sha256': json_sha(mechanical_physical(current_mechanical)),
             'source_model_sha256': old_report['model_sources_sha256'],
             'retained_step_sha256': {name: sha(PREVIEW / name) for name in ('populated-stack.step', 'board-p-stacked.step')},
             'invariant_scope': 'Every non-B.SilkS top-level node, including complete footprints/pads/models, copper tracks/vias, zones and filled polygons, setup, outline and front silkscreen. Only independent top-level ordering, exact numeric spelling and verified model-path rebasing are normalized.',
             'excluded_scope': 'Board-level B.SilkS graphics and the known artwork group containing only those graphics. Mechanical JSON may differ only in terminal_blocks.rail_labels.',
             'negative_tests': negative_controls(after, current.parent),
             'reuse_boundary': 'Previously executed STEP/model-surface/populated-collision results apply to identical geometry. Those expensive checks were not rerun. Prior package hashes identify evidence read during this check, not a retained backup directory.'}
    return proof, old_report, datum, after


def reuse_record(proof, kind, previous_report_sha, checks):
    return {'mode': 'REUSED_VERIFIED_GEOMETRY', 'proof': str(PROOF.relative_to(ROOT)),
            'proof_sha256': sha(PROOF), 'previous_report_sha256': previous_report_sha,
            'original_execution_pcb_sha256': proof[kind + '_original_execution_pcb_sha256'],
            'original_execution_report_sha256': proof[kind + '_original_execution_report_sha256'],
            'checks_not_rerun': checks, 'reason': proof['reuse_boundary']}


def refresh_staged(stage, proof, old_report, datum, current_tree, cli, kpython, package, proof_hash):
    previous_preview = load(stage / 'preview.kicad_pcb')
    old_fps = {props(f)['Reference']: f for f in find_all(previous_preview, 'footprint')}
    current = copy.deepcopy(current_tree)
    for fp in find_all(current, 'footprint'):
        ref = props(fp)['Reference']
        old = old_fps[ref]
        for node in list(find_all(fp, 'model')):
            fp.remove(node)
        fp.extend(copy.deepcopy(find_all(old, 'model')))
    display = old_fps['PD_PREVIEW']
    attrs = {atom(n) for a in find_all(display, 'attr') for n in a[1:]}
    require({'board_only', 'exclude_from_pos_files', 'exclude_from_bom'} <= attrs, 'Cached display footprint is not excluded')
    current.append(copy.deepcopy(display))
    def nonmodels(tree):
        value = copy.deepcopy(tree)
        for fp in find_all(value, 'footprint'):
            for model in list(find_all(fp, 'model')):
                fp.remove(model)
        return value
    require(nonmodels(current[:-1]) == nonmodels(current_tree), 'Preview reconstruction altered source non-model nodes')
    preview_path = stage / 'preview.kicad_pcb'
    preview_path.write_text(serialize(current) + '\n')
    def run(args):
        result = subprocess.run([str(v) for v in args], cwd=ROOT, text=True, capture_output=True)
        require(result.returncode == 0, 'Fresh check failed: ' + result.stdout + result.stderr)
    run([kpython, ROOT / 'scripts/pcb/verify-board-b.py', ROOT / 'boards/board-b/board-b.kicad_pcb', '--output', stage / 'mechanical-check.json'])
    run([sys.executable, ROOT / 'scripts/pcb/check-model-bodies.py', ROOT / 'boards/board-b/board-b.kicad_pcb', '--output', stage / 'board-b-model-bodies.json'])
    run([sys.executable, ROOT / 'scripts/pcb/check-model-paths.py', preview_path, '--output', stage / 'model-paths.json'])
    for side in ('top', 'bottom'):
        run([cli, 'pcb', 'render', '--side', side, '--rotate', '20,0,-15', '--width', '1800', '--height', '1400', '--quality', 'high', '--zoom', '.8', '--output', stage / (side + '.png'), preview_path])
    (stage / 'preview.kicad_prl').unlink(missing_ok=True)
    require(not list(stage.glob('*.lck')), 'Close the preview before freezing evidence')
    for name, digest in proof['retained_step_sha256'].items():
        require(sha(stage / name) == digest, 'Retained STEP was modified')
    check_hashes(ROOT, proof['bound_source_sha256'])
    require(sha(PROOF) == proof_hash, 'Equivalence proof changed during refresh')
    result = copy.deepcopy(old_report)
    result['pcb_sha256'] = proof['current_pcb_sha256']
    result['mechanical_spec_sha256'] = proof['current_mechanical_spec_sha256']
    result['verification_sources_sha256'] = {name: proof['bound_source_sha256'][name]
                                           for name in old_report['verification_sources_sha256']
                                           if name != str(PROOF.relative_to(ROOT))}
    result['verification_sources_sha256'][str(Path(__file__).relative_to(ROOT))] = proof['generator_sha256']
    result['verification_sources_sha256'][str(PROOF.relative_to(ROOT))] = sha(PROOF)
    result['geometry_evidence_reuse'] = reuse_record(proof, 'assembly', proof['previous_assembly_report_sha256'], ['Native STEP exports', 'All 1,460 populated cross-board solid comparisons', 'C5/terminal/support solid-envelope checks'])
    result['fresh_checks'] = ['Native mechanical identity including the exact user back-label contract', 'Opaque component-body sanity', 'Portable model paths', 'Native top and bottom render']
    for board in datum['boards']:
        board['sha256'] = proof['bound_source_sha256'][board['path']]
    datum['geometry_evidence_reuse'] = reuse_record(proof, 'datum', proof['previous_datum_report_sha256'], ['31 STEP/WRL sampled-surface and datum comparisons'])
    datum_path = ROOT / 'footprints/kicad/step-datum-verification.json'
    require(sha(PREVIEW / 'verification.json') == proof['previous_assembly_report_sha256']
            and sha(datum_path) == proof['previous_datum_report_sha256'], 'Cached evidence changed while refresh was staged')
    try:
        shutil.rmtree(PREVIEW)
        shutil.move(str(stage), str(PREVIEW))
        run([sys.executable, ROOT / 'scripts/pcb/check-model-paths.py', PREVIEW / 'preview.kicad_pcb', '--output', PREVIEW / 'model-paths.json'])
        check_hashes(ROOT, proof['bound_source_sha256'])
        require(sha(PROOF) == proof_hash, 'Equivalence proof changed during promotion')
        result['artifact_sha256'] = {str(p.relative_to(PREVIEW)): sha(p) for p in sorted(PREVIEW.rglob('*')) if p.is_file() and p.name != 'verification.json' and p.suffix not in ('.lck', '.kicad_prl')}
        write(PREVIEW / 'verification.json', result)
        write(datum_path, datum)
    except Exception:
        if PREVIEW.exists():
            shutil.rmtree(PREVIEW)
        shutil.copytree(package / 'mechanical/assembly', PREVIEW)
        shutil.copy2(package / 'step-datum-verification.json', datum_path)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-package', type=Path, default=ROOT / 'manufacturing/releases/corner-support-review')
    parser.add_argument('--refresh-preview', action='store_true')
    parser.add_argument('--kicad-cli', default=shutil.which('kicad-cli'))
    parser.add_argument('--kicad-python', default='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
    args = parser.parse_args()
    proof, report, datum, tree = make_proof(args.previous_package.resolve())
    write(PROOF, proof)
    print('Strict physical/model/mechanical equivalence and negative controls: PASS', flush=True)
    if args.refresh_preview:
        require(args.kicad_cli, 'kicad-cli required for fresh render')
        proof_hash = sha(PROOF)
        with tempfile.TemporaryDirectory(prefix='silk-evidence-', dir=ROOT / 'tmp') as temporary:
            stage = Path(temporary) / 'preview'
            shutil.copytree(PREVIEW, stage)
            check_hashes(stage, report['artifact_sha256'])
            refresh_staged(stage, proof, report, datum, tree, args.kicad_cli, args.kicad_python, args.previous_package.resolve(), proof_hash)
        print('Preview refreshed; original STEP/collision/datum evidence explicitly reused', flush=True)


if __name__ == '__main__':
    main()
