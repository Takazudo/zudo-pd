"""D1 per-rail reference extraction (#235, wave 2 task W2-D).

Rebuilds the 2 us refined nom/adv inputs from Git plus the hash-recorded TI model archives,
appends one output-only wrdata line that saves the RAMP reference nodes, and after the
pinned runner has executed them checks that the primary and supplemental waveforms are
byte-identical to the retained 2026-11-09 refinement. Only then are the reference nodes
analysed against the D1 hypotheses.

Diagnostic only: electrical_acceptance stays NOT ESTABLISHED and the recorded 2 us ceiling
exceedances stay recorded failures. Vendor model bytes are never written to the output
evidence; only their hashes are.

usage:
  extract_reference.py prepare WORK --manifest PATH [--archives DIR]
  (run_ladder.py WORK/tracking nom adv --original-only)
  extract_reference.py identity WORK --manifest PATH --output PATH
  extract_reference.py analyze WORK --output PATH
  extract_reference.py collect WORK --evidence DIR [--extra-dir DIR]

The work directory is not a Git checkout, so the runner receipt's source_revision is None and
its source_dirty means "not a repository"; the source is bound by GITHUB_SHA in the manifest.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

from analysis_inputs import load
from c12_compensation import INIT
from prepare_refinement import transform
import time

from run_ladder import IMAGE, VARIANTS, verify_executed_inputs

HERE = Path(__file__).resolve().parent
EXECUTION = HERE / 'execution-20261110.json'
REFINEMENT = HERE / 'startup-refinement-20261109.json'
CASES = ('nom', 'adv')
# Accepted executed variant of each case in the 2026-11-09 baseline (execution-20261110.json)
BASELINE_VARIANT = {'nom': 'original', 'adv': 'rshunt'}
REFERENCE_VECTORS = ('ramp', 'ramp_p12', 'ramp_p5', 'ramp_m12', 'clp12', 'clp5', 'clpm12')
ARCHIVES = {'sbomab6': {'OPAx187.LIB': 'lib/opax187.lib'},
            'slpm286': {'CSD18543Q3A.LIB': 'lib/csd18543q3a_ngspice.lib'}}
DOWNLOAD_TIMEOUT_S = 120
DOWNLOAD_MAX_BYTES = 64 * 1024 * 1024
# Excursion rail -> (case, main waveform column after time, reference node, clamp output node,
# sign of the output excursion relative to a rising reference: +5 tracks, -12 inverts)
FAILED = {'+5': ('nom', 2, 'ramp_p5', 'clp5', 1), '-12': ('adv', 3, 'ramp_m12', 'clpm12', -1)}
NEIGHBOURHOOD_S = 100e-6
# Reporting band for classification only; it is not a tolerance on any contract value.
IDEAL_BAND = 1.05
SUPPORTED, REFUTED, UNRESOLVED, NOT_RUN = 'SUPPORTED', 'REFUTED', 'UNRESOLVED', 'NOT RUN'


class NotRun(Exception):
    """A required external input is unavailable or differs from its recorded hash."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records():
    execution = json.loads(EXECUTION.read_text())
    refinement = json.loads(REFINEMENT.read_text())
    return execution['model_recovery'], refinement


def reference_line(name):
    return f"wrdata {name}-ref.txt " + ' '.join(f'v({v})' for v in REFERENCE_VECTORS)


def convert_param(data):
    """Documented syntax-only conversion: exactly five '.PARAM name value' lines become 'name=value'."""
    pattern = re.compile(rb'^(\.PARAM[ \t]+[A-Za-z_][A-Za-z0-9_]*)[ \t]+([^ \t\r\n=]+)([ \t]*\r?)$', re.M | re.I)
    converted, count = pattern.subn(rb'\1=\2\3', data)
    if count != 5:
        raise ValueError(f'expected exactly five .PARAM name value lines, found {count}')
    return converted


def derive_decks():
    """Rebuild the refined decks from Git and add the one output-only reference line."""
    _, refinement = records()
    expected = refinement['preparation']['inputs']
    rshunt = dict(VARIANTS)['rshunt']
    decks = {}
    for name in CASES:
        text = (HERE / 'tracking' / f'{name}.cir').read_text()
        if BASELINE_VARIANT[name] == 'rshunt':
            if text.count(rshunt[0]) != 1:
                raise ValueError(f'{name}: expected one {rshunt[0]} for the accepted rshunt variant')
            text = text.replace(*rshunt)
        refined = transform(text, name)
        if sha(refined.encode()) != expected[f'tracking/{name}.cir']:
            raise ValueError(f'{name}: refined deck does not reproduce the recorded hash')
        if refined.count('.endc') != 1:
            raise ValueError(f'{name}: expected one control block')
        line = reference_line(name)
        decks[name] = {'refined': refined, 'executed': refined.replace('.endc', line + '\n.endc'), 'added_line': line}
    return decks


def fetch(url, digest):
    """One bounded attempt; any failure or hash difference is NOT RUN, never retried here."""
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT_S
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'phase33-reference-extraction'})
        chunks, size = [], 0
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_S) as response:
            while chunk := response.read(1 << 20):
                size += len(chunk)
                if size > DOWNLOAD_MAX_BYTES or time.monotonic() > deadline:
                    raise TimeoutError(f'exceeded {DOWNLOAD_MAX_BYTES} bytes or {DOWNLOAD_TIMEOUT_S} s')
                chunks.append(chunk)
        data = b''.join(chunks)
    except Exception as error:  # noqa: BLE001 - every transport failure is recorded verbatim
        raise NotRun(f'{url}: {type(error).__name__}: {error}') from error
    if sha(data) != digest:
        raise NotRun(f'{url}: sha256 {sha(data)} differs from recorded {digest}')
    return data


def build_models(archives, expected):
    """Return {lib path: bytes} from archives keyed by name, verifying members and outputs."""
    recovery, _ = records()
    built, hashes = {}, {}
    for name, members in ARCHIVES.items():
        data = archives[name]
        if sha(data) != recovery['files'][f'{name}.zip']:
            raise NotRun(f'{name}.zip differs from its recorded hash')
        hashes[f'{name}.zip'] = sha(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member, target in members.items():
                found = [i for i in archive.namelist() if Path(i).name == member]
                if len(found) != 1:
                    raise NotRun(f'{name}.zip: expected one {member}, found {found}')
                raw = archive.read(found[0])
                if sha(raw) != recovery['files'][f'{name}/{member}']:
                    raise NotRun(f'{name}/{member} differs from its recorded hash')
                hashes[f'{name}/{member}'] = sha(raw)
                built[target] = convert_param(raw) if target.endswith('_ngspice.lib') else raw
    for target, data in built.items():
        if sha(data) != expected[target]:
            raise ValueError(f'{target}: built model {sha(data)} does not reproduce recorded {expected[target]}')
        hashes[target] = sha(data)
    return built, hashes


def prepare(work, archive_dir=None):
    recovery, refinement = records()
    expected = refinement['preparation']['inputs']
    if sha(INIT.encode()) != expected['tracking/.spiceinit']:
        raise ValueError('.spiceinit does not reproduce the recorded hash')
    decks = derive_decks()
    archives = {}
    for name in ARCHIVES:
        if archive_dir:
            archives[name] = (Path(archive_dir) / f'{name}.zip').read_bytes()
        else:
            archives[name] = fetch(recovery['source_urls'][name], recovery['files'][f'{name}.zip'])
    built, vendor = build_models(archives, expected)
    work = Path(work)
    (work / 'tracking').mkdir(parents=True)
    (work / 'lib').mkdir()
    for target, data in built.items():
        (work / target).write_bytes(data)
    (work / 'tracking/.spiceinit').write_text(INIT)
    manifest = {'source_revision': os.environ.get('GITHUB_SHA'), 'vendor_sha256': vendor,
                'spiceinit_sha256': sha(INIT.encode()), 'cases': {}}
    for name, deck in decks.items():
        (work / 'tracking' / f'{name}.cir').write_text(deck['executed'])
        manifest['cases'][name] = {'refined_deck_sha256': sha(deck['refined'].encode()),
                                   'executed_deck_sha256': sha(deck['executed'].encode()),
                                   'added_output_only_line': deck['added_line']}
    return manifest


def single_run(work):
    runs = sorted(Path(work).glob('ladder-*'))
    if len(runs) != 1:
        raise ValueError(f'{work}: expected exactly one runner directory, found {len(runs)}')
    return runs[0]


def attempt_dir(run, name):
    return Path(run) / name / '0' / 'tracking'


def identity(run, manifest):
    """Byte identity of the executed decks and the retained primary/supplemental outputs."""
    _, refinement = records()
    receipt = json.loads((Path(run) / 'receipt.json').read_text())
    result = {'cases': {}}
    prepared = {k: v for k, v in refinement['preparation']['inputs'].items() if k.startswith('lib/')}
    solver = {refinement['cases'][name]['solver_version_output'] for name in CASES}
    ok = (receipt.get('status') == 'COMPLETE' and receipt.get('image') == IMAGE and receipt.get('platform') == 'linux/amd64'
          and receipt.get('variant_policy') == 'original-only' and len(solver) == 1
          and receipt.get('solver_version_output') in solver)
    result['solver_identity_matches'] = ok
    result['source_revision'] = manifest.get('source_revision')
    for name in CASES:
        work = attempt_dir(run, name)
        retained = refinement['cases'][name]
        observed = {'executed_deck': sha((work / f'{name}.cir').read_bytes()),
                    'main_waveform': sha((work / f'{name}.dat').read_bytes()),
                    'supplemental_waveform': sha((work / f'{name}-osc-cap.txt').read_bytes())}
        wanted = {'executed_deck': manifest['cases'][name]['executed_deck_sha256'],
                  'main_waveform': retained['main_waveform_sha256'],
                  'supplemental_waveform': retained['supplemental_waveform_sha256']}
        matches = {k: observed[k] == wanted[k] for k in observed}
        try:
            executed = verify_executed_inputs(Path(run) / name / '0', receipt['input_sha256'])
            matches['executed_models_and_settings'] = (
                {k: v for k, v in executed.items() if k.startswith('lib/')} == prepared
                and executed['tracking/.spiceinit'] == refinement['preparation']['inputs']['tracking/.spiceinit'])
        except (ValueError, KeyError, OSError) as error:
            matches['executed_models_and_settings'] = False
            observed['executed_inputs_error'] = str(error)
        ok = ok and all(matches.values())
        result['cases'][name] = {'observed_sha256': observed, 'expected_sha256': wanted, 'matches': matches}
    result['status'] = 'REPRODUCED' if ok else 'NOT REPRODUCED'
    return result


def load_reference(path, rows):
    data = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        values = [float(x) for x in line.split()]
        if len(values) != 2 * len(REFERENCE_VECTORS):
            raise ValueError(f'{path}:{number}: expected {2 * len(REFERENCE_VECTORS)} columns')
        if any(abs(x - values[0]) > 1e-10 for x in values[::2]):
            raise ValueError(f'{path}:{number}: wrdata time columns disagree')
        data.append(dict(zip(('t',) + REFERENCE_VECTORS, (values[0], *values[1::2]))))
    if len(data) != len(rows) or any(abs(a['t'] - b[0]) > 1e-12 for a, b in zip(data, rows)):
        raise ValueError(f'{path}: reference and main waveform time coordinates differ')
    return data


def deck_gain(deck, rail):
    """Ideal tracking gain from the drawn feedback resistors of the executed deck."""
    values = {}
    for line in deck.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] in ('RT5A', 'RT5B', 'RT12NA', 'RT12NB'):
            values[parts[0]] = float(parts[3].lower().replace('k', 'e3'))
    if rail == '+5':
        return 1 + values['RT5A'] / values['RT5B']
    return values['RT12NB'] / values['RT12NA']


def slopes(times, values, gain):
    """Signed adjacent-sample slopes in V/ms, multiplied by gain (use the sign to select the excursion direction)."""
    return [gain * (values[i + 1] - values[i]) / (times[i + 1] - times[i]) / 1e3 for i in range(len(times) - 1)]


def classify(peak, ideal, ceiling, competing=None):
    """Pre-registered rule on signed slopes in the excursion direction.

    SUPPORTED needs the scaled slope to reach the failed ceiling and, when a competing source
    is named (the common RAMP for the per-rail reference), to exceed that source's peak by the
    same band, so a reference that only follows a steep common RAMP is not attributed to the clamp.
    """
    if peak <= ideal * IDEAL_BAND:
        return REFUTED
    if peak >= ceiling and (competing is None or peak > competing * IDEAL_BAND):
        return SUPPORTED
    return UNRESOLVED


def analyze(run):
    _, refinement = records()
    calc_spec = importlib.util.spec_from_file_location('interface_diagnostics', HERE / 'interface_diagnostics.py')
    diag = importlib.util.module_from_spec(calc_spec)
    calc_spec.loader.exec_module(diag)
    ideal = diag.startup(diag.calculator())['rails']
    result = {'scope': 'D1 reference extraction; diagnostic only', 'electrical_acceptance': 'NOT ESTABLISHED',
              'classification_rule': f'Signed slopes in the excursion direction within +/-{NEIGHBOURHOOD_S * 1e6:g} us of the '
                                     f'recorded excursion, scaled by the deck tracking gain. REFUTED if the peak stays at or '
                                     f'below {IDEAL_BAND} x the ideal tracking slope. SUPPORTED if it reaches the failed exception '
                                     f'ceiling and, for the per-rail reference, also exceeds {IDEAL_BAND} x the scaled common-RAMP '
                                     f'peak. Otherwise UNRESOLVED. SUPPORTED means consistent with the hypothesis in this model, '
                                     f'not proof of cause.',
              'rails': {}}
    for rail, (name, column, ref_name, clamp, sign) in FAILED.items():
        work = attempt_dir(run, name)
        rows = load(work / f'{name}.dat')
        ref = load_reference(work / f'{name}-ref.txt', rows)
        recorded = refinement['cases'][name]['rails'][rail]
        worst = recorded['worst_recorded_bound_exceedance']
        ceiling = recorded['exception']['slope_ceiling_v_per_ms']
        gain = deck_gain((work / f'{name}.cir').read_text(), rail)
        start, end = worst['start_ms'] / 1e3, worst['end_ms'] / 1e3
        index = min(range(len(rows) - 1), key=lambda i: abs(rows[i][0] - start) + abs(rows[i + 1][0] - end))
        near = [i for i in range(len(rows) - 1) if start - NEIGHBOURHOOD_S <= rows[i][0] <= end + NEIGHBOURHOOD_S]
        times = [r[0] for r in rows]
        out = slopes(times, [r[column] for r in rows], sign)
        if abs(out[index] - worst['slope_v_per_ms']) > 1e-9 * worst['slope_v_per_ms']:
            raise ValueError(f'{rail}: selected segment slope {out[index]} differs from recorded {worst["slope_v_per_ms"]}')
        reference = slopes(times, [x[ref_name] for x in ref], gain)
        common = slopes(times, [x['ramp'] for x in ref], gain)
        diode = [ref[i][ref_name] - ref[i][clamp] for i in near + [near[-1] + 1]]
        reference_peak = max(reference[i] for i in near)
        common_peak = max(common[i] for i in near)
        peak_at = max(near, key=lambda i: reference[i])
        result['rails'][rail] = {
            'case': name, 'tracking_gain_from_deck': round(gain, 6),
            'excursion_segment_ms': [round(rows[index][0] * 1e3, 9), round(rows[index + 1][0] * 1e3, 9)],
            'output_slope_at_segment_v_per_ms': out[index], 'recorded_slope_v_per_ms': worst['slope_v_per_ms'],
            'scaled_reference_slope_at_segment_v_per_ms': reference[index],
            'scaled_reference_peak_near_segment_v_per_ms': reference_peak,
            'scaled_reference_peak_offset_from_segment_us': round((rows[peak_at][0] - rows[index][0]) * 1e6, 3),
            'scaled_common_ramp_slope_at_segment_v_per_ms': common[index],
            'scaled_common_ramp_peak_near_segment_v_per_ms': common_peak,
            'ideal_tracking_max_slope_v_per_ms': ideal[rail]['ideal_tracking_max_slope_v_per_ms'],
            'exception_slope_ceiling_v_per_ms': ceiling,
            'clamp_diode_voltage_v': {'window_start': diode[0], 'segment': diode[near.index(index)],
                                      'window_end': diode[-1], 'window_min': min(diode), 'window_max': max(diode)},
            'hypotheses': {'D1-H6 clamp-release reference edge': classify(reference_peak, ideal[rail]['ideal_tracking_max_slope_v_per_ms'], ceiling, common_peak),
                           'D1-H1 recorded common RAMP too steep': classify(common_peak, ideal[rail]['ideal_tracking_max_slope_v_per_ms'], ceiling),
                           'D1-H4 pre-bias overshoot': UNRESOLVED + ' (needs the paired variant run)'},
        }
    return result


EVIDENCE_SUFFIXES = ('.cir', '.dat', '.log', '-osc-cap.txt', '-ref.txt')
VENDOR_SUFFIXES = ('.lib', '.zip', '.olb')


def collect(work, evidence, extra_dir=None):
    """Copy decks, logs, waveforms, receipts and reports; never vendor model bytes. Returns the hash list."""
    evidence = Path(evidence)
    evidence.mkdir(parents=True)
    runs = sorted(Path(work).glob('ladder-*'))
    sources = []
    for run in runs:
        sources.append((run / 'receipt.json', f'{run.name}/receipt.json'))
        for name in CASES:
            for suffix in EVIDENCE_SUFFIXES:
                path = attempt_dir(run, name) / f'{name}{suffix}'
                if path.is_file():
                    sources.append((path, f'{run.name}/{name}/{name}{suffix}'))
    if extra_dir and Path(extra_dir).is_dir():
        sources += [(p, p.name) for p in sorted(Path(extra_dir).iterdir()) if p.is_file()]
    hashes = {}
    for source, relative in sources:
        if source.suffix.lower() in VENDOR_SUFFIXES or 'lib' in Path(relative).parts:
            raise ValueError(f'refusing to collect vendor model bytes: {relative}')
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[relative] = sha(target.read_bytes())
    (evidence / 'hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
    return hashes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('work', type=Path); p.add_argument('--archives', type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    i = sub.add_parser('identity'); i.add_argument('work', type=Path); i.add_argument('--manifest', type=Path, required=True)
    i.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('analyze'); a.add_argument('work', type=Path); a.add_argument('--output', type=Path, required=True)
    c = sub.add_parser('collect'); c.add_argument('work', type=Path); c.add_argument('--evidence', type=Path, required=True)
    c.add_argument('--extra-dir', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        try:
            manifest = prepare(args.work, args.archives)
        except NotRun as error:
            args.manifest.write_text(json.dumps({'status': NOT_RUN, 'reason': str(error)}, indent=2) + '\n')
            print(f'NOT RUN: {error}', file=sys.stderr)
            return 2
        except ValueError as error:
            args.manifest.write_text(json.dumps({'status': 'FAILED', 'reason': str(error)}, indent=2) + '\n')
            print(f'FAILED: {error}', file=sys.stderr)
            return 2
        manifest['status'] = 'PREPARED'
        args.manifest.write_text(json.dumps(manifest, indent=2) + '\n')
        return 0
    if args.command == 'identity':
        result = identity(single_run(args.work), json.loads(args.manifest.read_text()))
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(result['status'])
        return 0 if result['status'] == 'REPRODUCED' else 3
    if args.command == 'collect':
        collect(args.work, args.evidence, args.extra_dir)
        return 0
    result = analyze(single_run(args.work))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
