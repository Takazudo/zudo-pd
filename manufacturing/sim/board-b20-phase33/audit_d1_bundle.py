#!/usr/bin/env python3
"""Audit a downloaded phase33 D1 diagnostic artifact and write a compact, repository-safe receipt.

Reuses completed evidence: it never runs a simulation, never dispatches a workflow and never judges a candidate.
It verifies the archive against the digest GitHub recorded, every bundle member against the run's own hashes.json,
the absence of vendor model bytes, the identity control, the per-deck runner receipts (solver image, solver version,
model and .spiceinit hashes, original-only policy), that every executed deck is the deck the diagnostic manifest
recorded (variant decks differ only by their labelled solver option), and that the run's diagnostic JSON is the
one retained in this directory. Optionally it binds an offline re-analysis made with the executed revision's own
analyzer. The archive, waveforms and vendor models stay outside the repository.

usage:
  audit_d1_bundle.py audit ZIP --run-meta META.json --diagnostic NAME --retained FILE
                       [--reanalysis FILE] [--derived-decks FILE] --output RECEIPT.json
  audit_d1_bundle.py check                     (offline: retained receipts and results agree)
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

HERE = Path(__file__).resolve().parent
IMAGE = 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
SOLVER = 'ngspice-44.2'
VENDOR_SUFFIXES = {'.lib', '.zip', '.mod', '.cir.lib'}
# Same option ladder as osc_bank.VARIANTS / t2_rev2.VARIANTS: the variant deck is the recorded deck with one option changed.
VARIANTS = {'abstol': ('abstol=1e-9', 'abstol=1e-8'), 'rshunt': ('rshunt=1e10', 'rshunt=1e9')}
RECEIPTS = {
    'osc_bank': ('d1-osc-bank-audit-20261113.json', 'd1-osc-bank-20261112.json'),
    'ceiling_corners': ('d1-ceiling-corners-audit-20261113.json', 'd1-ceiling-corners-20261112.json'),
}
DIAGNOSTIC_FILES = {'osc_bank': ('osc-bank.json', 'bank-manifest.json', 'bank'),
                    'ceiling_corners': ('ceiling-corners.json', 'ceiling-manifest.json', 'ceiling')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def member_sha(zf, name, chunk=1 << 20):
    h = hashlib.sha256()
    with zf.open(name) as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def is_vendor(name):
    path = PurePosixPath(name)
    return 'lib' in path.parts[:-1] or path.suffix.lower() in VENDOR_SUFFIXES


def check_members(zf):
    """Every member against hashes.json, both directions, streamed; and no vendor model bytes."""
    names = [i.filename for i in zf.infolist() if not i.is_dir()]
    hashes = json.loads(zf.read('hashes.json'))
    listed, present = set(hashes), set(names) - {'hashes.json'}
    mismatched = sorted(n for n in sorted(listed & present) if member_sha(zf, n) != hashes[n])
    return {
        'members': len(names),
        'hashes_json_entries': len(hashes),
        'uncompressed_bytes': sum(i.file_size for i in zf.infolist()),
        'missing_from_archive': sorted(listed - present),
        'unlisted_in_hashes_json': sorted(present - listed),
        'hash_mismatches': mismatched,
        'vendor_model_members': sorted(n for n in names if is_vendor(n)),
    }, hashes


def receipts(zf, prefix):
    """label -> runner receipt, for every ladder receipt under PREFIX/<label>/ladder-*/receipt.json."""
    out = {}
    for name in zf.namelist():
        parts = PurePosixPath(name).parts
        if len(parts) == 4 and parts[0] == prefix and parts[2].startswith('ladder-') and parts[3] == 'receipt.json':
            if parts[1] in out:
                raise ValueError(f'{prefix}/{parts[1]}: more than one ladder receipt')
            out[parts[1]] = (f'{prefix}/{parts[1]}/{parts[2]}', json.loads(zf.read(name)))
    return out


def unvariant(label):
    """('v-abstol-nom-nom') -> ('abstol', 'nom-nom'); a pinned label -> (None, label)."""
    for variant in VARIANTS:
        if label.startswith(f'v-{variant}-'):
            return variant, label[len(f'v-{variant}-'):]
    return None, label


def deck_rows(zf, prefix, manifest, lib_hashes, spiceinit):
    rows, problems = {}, []
    for label, (run_dir, receipt) in sorted(receipts(zf, prefix).items()):
        variant, base = unvariant(label)
        (name, recorded), = manifest['labels'][base].items()
        deck = zf.read(f'{run_dir}/{name}/{name}.cir').decode()
        attempts = receipt['cases'][name]['attempts']
        row = {'label': label, 'track': 'pinned' if variant is None else f'matched variant {variant} (labelled)',
               'runner_status': receipt['status'], 'attempts': len(attempts),
               'executed_deck_sha256': sha(deck.encode())}
        if attempts[-1]['deck_sha256'] != row['executed_deck_sha256'] or receipt['input_sha256'][f'{name}.cir'] != row['executed_deck_sha256']:
            problems.append(f'{label}: receipt deck hash differs from the collected deck')
        if variant is None:
            row['deck_matches_manifest'] = row['executed_deck_sha256'] == recorded['deck_sha256']
        else:
            old, new = VARIANTS[variant]
            row['variant_option_only'] = deck.count(new) == 1 and old not in deck
            row['deck_matches_manifest'] = sha(deck.replace(new, old).encode()) == recorded['deck_sha256']
        for key, ok in (('deck_matches_manifest', row['deck_matches_manifest']),
                        ('variant_option_only', row.get('variant_option_only', True))):
            if not ok:
                problems.append(f'{label}: {key} failed')
        identity = {
            'image': receipt['image'] == IMAGE, 'platform': receipt['platform'] == 'linux/amd64',
            'solver': SOLVER in receipt['solver_version_output'] and receipt['solver_version_returncode'] == 0,
            'original_only': receipt['variant_policy'] == 'original-only', 'clean_source': receipt['source_dirty'] is False,
            'spiceinit': receipt['input_sha256'].get('.spiceinit') == spiceinit,
            'models': {k: v for k, v in receipt['input_sha256'].items() if k.startswith('lib/')} == lib_hashes,
        }
        bad = sorted(k for k, ok in identity.items() if not ok)
        if bad:
            problems.append(f'{label}: runner identity mismatch {bad}')
        rows[label] = row
    return rows, problems


def summarize_result(result):
    decks = {}
    for label, row in result['decks'].items():
        decks[label] = {k: row[k] for k in ('entry', 'pinned', 'variant_abstol', 'variant_rshunt', 'measured_under')
                        if k in row}
        if 'abort' in row:
            decks[label]['pinned_abort_time_s'] = row['abort'].get('time_s')
    return {'decks': decks, 'unknown': result['unknown'], 'flags': result.get('flags'),
            'variant_cross_check': result['variant_cross_check']}


def audit(zip_path, meta, diagnostic, retained, reanalysis=None, derived=None):
    files, manifest_name, prefix = DIAGNOSTIC_FILES[diagnostic]
    run, artifact = meta['run'], meta['artifact']
    zip_sha = file_sha(zip_path)
    problems = []
    if f'sha256:{zip_sha}' != artifact['digest']:
        problems.append('archive SHA-256 differs from the recorded artifact digest')
    if Path(zip_path).stat().st_size != artifact['size_in_bytes']:
        problems.append('archive size differs from the recorded artifact size')
    if run['conclusion'] != 'success' or run['run_attempt'] != 1:
        problems.append('run is not a successful first attempt')
    with zipfile.ZipFile(zip_path) as zf:
        members, hashes = check_members(zf)
        for key in ('missing_from_archive', 'unlisted_in_hashes_json', 'hash_mismatches', 'vendor_model_members'):
            if members[key]:
                problems.append(f'bundle {key}: {members[key][:5]}')
        identity = json.loads(zf.read('identity.json'))
        manifest = json.loads(zf.read('manifest.json'))
        diag_manifest = json.loads(zf.read(manifest_name))
        result_bytes = zf.read(files)
        lib_hashes = {k: v for k, v in manifest['vendor_sha256'].items() if k.startswith('lib/')}
        for rev, what in ((identity['source_revision'], 'identity'), (manifest['source_revision'], 'manifest')):
            if rev != run['head_sha']:
                problems.append(f'{what} source revision differs from the run head')
        if identity['status'] != 'REPRODUCED' or not identity['solver_identity_matches']:
            problems.append('identity control did not reproduce')
        rows, deck_problems = deck_rows(zf, prefix, diag_manifest, lib_hashes, manifest['spiceinit_sha256'])
        problems += deck_problems
        ladder = [(n, json.loads(zf.read(n))) for n in zf.namelist() if PurePosixPath(n).parts[0].startswith('ladder-')
                  and n.endswith('receipt.json')]
        hashes_json_sha = sha(zf.read('hashes.json'))
    if not ladder or any(r['status'] != 'COMPLETE' for _, r in ladder):
        problems.append('identity-pair ladder receipt missing or not COMPLETE')
    expected_labels = set(diag_manifest['labels'])
    pinned_run = {r['label'] for r in rows.values() if r['track'] == 'pinned'}
    result = json.loads(result_bytes)
    if sha(result_bytes) != sha(Path(retained).read_bytes()):
        problems.append('retained result differs from the artifact result')
    executed_bases = {unvariant(label)[1] for label in rows}
    if executed_bases != expected_labels:
        problems.append(f'executed decks do not cover the manifest labels: {sorted(executed_bases ^ expected_labels)}')
    if set(result['decks']) != expected_labels:
        problems.append('result rows do not match the manifest labels')
    for label, row in result['decks'].items():
        ran_pinned = label in pinned_run
        recorded = row.get('pinned')
        if ran_pinned != (recorded in ('COMPLETE', 'ABORTED')):
            problems.append(f'{label}: pinned row {recorded!r} does not match the executed decks')
        for variant in VARIANTS:
            vrow = rows.get(f'v-{variant}-{label}')
            if row.get(f'variant_{variant}') == 'COMPLETE' and (vrow is None or vrow['runner_status'] != 'COMPLETE'):
                problems.append(f'{label}: variant {variant} row has no completed executed deck')
    receipt = {
        'record': f'Audit of the completed phase33 {diagnostic} diagnostic artifact (reused evidence, no rerun)',
        'scope': 'archive identity, bundle completeness, executed-deck and solver identity, pinned-versus-variant '
                 'labelling and re-analysis binding; judges no candidate and changes no contract ceiling',
        'electrical_acceptance': 'NOT ESTABLISHED',
        'run': run,
        'jobs': meta.get('jobs'),
        'metadata_read_utc': meta.get('metadata_read_utc'),
        'artifact': {**artifact, 'downloaded_zip_sha256': zip_sha, 'downloaded_zip_bytes': Path(zip_path).stat().st_size},
        'bundle': {**members, 'hashes_json_sha256': hashes_json_sha},
        'identity_control': {'status': identity['status'], 'source_revision': identity['source_revision'],
                             'solver_identity_matches': identity['solver_identity_matches'],
                             'cases': {k: v['matches'] for k, v in identity['cases'].items()}},
        'inputs': {'source_revision': manifest['source_revision'], 'spiceinit_sha256': manifest['spiceinit_sha256'],
                   'vendor_sha256': manifest['vendor_sha256'], 'solver_image': IMAGE, 'solver': SOLVER,
                   'identity_pair_receipts': {PurePosixPath(n).parts[0]: r['status'] for n, r in ladder}},
        'diagnostic': {'criteria': diag_manifest['criteria'], 'manifest_sha256': hashes[manifest_name],
                       'labels': len(expected_labels), 'executed_decks': rows,
                       'result_file': files, 'result_sha256': sha(result_bytes),
                       'retained_as': Path(retained).name, 'summary': summarize_result(result)},
    }
    if derived is not None:
        receipt['deck_derivation'] = derived
        if not derived.get('all_match'):
            problems.append('decks re-derived at the execution revision differ from the recorded manifest')
    if reanalysis is not None:
        receipt['reanalysis'] = reanalysis
        if reanalysis['differing_keys'] != reanalysis.get('expected_differing_keys', []):
            problems.append(f"re-analysis differs: {reanalysis['differing_keys']}")
    receipt['problems'] = problems
    receipt['audit_status'] = 'VERIFIED' if not problems else 'FAILED VERIFICATION'
    return receipt


def compare_reanalysis(path, retained, analyzer, python, expected=()):
    a, b = json.loads(Path(path).read_bytes()), json.loads(Path(retained).read_bytes())
    differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return {'analyzer': analyzer, 'python': python, 'output_sha256': file_sha(path),
            'byte_identical': file_sha(path) == file_sha(retained), 'differing_keys': differing,
            'expected_differing_keys': sorted(expected)}


def check():
    """Offline: each retained receipt verified, names its retained result by hash, and keeps acceptance open."""
    failures = []
    for diagnostic, (receipt_name, result_name) in RECEIPTS.items():
        receipt = json.loads((HERE / receipt_name).read_text())
        result_bytes = (HERE / result_name).read_bytes()
        result = json.loads(result_bytes)
        if receipt['audit_status'] != 'VERIFIED' or receipt['problems']:
            failures.append(f'{receipt_name}: not verified')
        if receipt['electrical_acceptance'] != 'NOT ESTABLISHED':
            failures.append(f'{receipt_name}: electrical acceptance must stay NOT ESTABLISHED')
        diag = receipt['diagnostic']
        if diag['retained_as'] != result_name or diag['result_sha256'] != sha(result_bytes):
            failures.append(f'{result_name}: retained result is not the audited artifact result')
        if diag['summary'] != summarize_result(result):
            failures.append(f'{receipt_name}: deck summary does not match the retained result')
        if receipt['artifact']['digest'] != f"sha256:{receipt['artifact']['downloaded_zip_sha256']}":
            failures.append(f'{receipt_name}: archive digest mismatch')
        if 'judges nothing' not in result['diagnostic']:
            failures.append(f'{result_name}: not the measure-only diagnostic')
        for label, row in diag['summary']['decks'].items():
            measured = row.get('measured_under') or ''
            variant = any(row.get(f'variant_{v}') == 'COMPLETE' for v in VARIANTS)
            if variant != measured.startswith('matched variant') or (not variant and measured != 'pinned'):
                failures.append(f'{label}: pinned and variant rows are not separated')
    for line in failures:
        print(f'FAIL: {line}', file=sys.stderr)
    if not failures:
        print('PASS: D1 OSC-bank and ceiling-corners audit receipts agree with the retained results (not electrical acceptance)')
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    a = sub.add_parser('audit')
    a.add_argument('zip', type=Path)
    a.add_argument('--run-meta', type=Path, required=True)
    a.add_argument('--diagnostic', choices=sorted(DIAGNOSTIC_FILES), required=True)
    a.add_argument('--retained', type=Path, required=True)
    a.add_argument('--reanalysis', type=Path, help='JSON from compare_reanalysis()')
    a.add_argument('--derived-decks', type=Path, help='JSON: decks re-derived at the execution revision')
    a.add_argument('--output', type=Path, required=True)
    sub.add_parser('check')
    args = parser.parse_args(argv)
    if args.command == 'check':
        return check()
    load = lambda p: json.loads(p.read_text()) if p else None  # noqa: E731
    receipt = audit(args.zip, load(args.run_meta), args.diagnostic, args.retained, load(args.reanalysis),
                    load(args.derived_decks))
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['audit_status'])
    for line in receipt['problems']:
        print(f'  {line}')
    return 0 if receipt['audit_status'] == 'VERIFIED' else 1


if __name__ == '__main__':
    sys.exit(main())
