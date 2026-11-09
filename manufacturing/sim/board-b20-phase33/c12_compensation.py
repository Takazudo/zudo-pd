"""Reproduce and audit the bounded C12 initial-tolerance AC sensitivity experiment.

prepare emits exact decks and a command manifest in a NEW local directory; it never runs Docker.
summarize verifies all three retained datasets, source/model/deck/log/wave hashes and AC coverage.
No result is a global stability, physical performance, or order-readiness verdict.
"""
import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE = HERE.parent / 'board-b20-phase7/ac/m12_full_19_47n.cir'
TEMPLATE_SHA = '6beb19f8c58b613355c97d7bcf7c3b8823748af41f8d16a0807cee7a87ab6d45'
MODEL_SHA = 'de1769384346d63575929e1d3f0063bd8b92c1a89a86ba33165b3d20f55dd790'
MODEL_ZIP_SHA = 'e74a8842728963360a0342e940ac96ee93b8ec8d21b65005a2b8152202550597'
IMAGE = 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
CALIBRATION = HERE / 'c12-ac-calibration-20261109.json'
INIT = 'set ngbehavior=psa\nset num_threads=1\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cases(mode):
    calibration = json.loads(CALIBRATION.read_text())['cases']
    loads = [('light_50ma', .05)] if mode == 'light' else [('continuous', 1.6), ('transient_20ms', 1.9), ('let_through_max', 2.0)]
    for vin in (19, 21):
        for label, current in loads:
            for capacitance in (44.65, 49.35):
                name = f'm12_{vin}_{label}_{str(capacitance).replace(".", "p")}n'
                resistance = 12.13 / current if mode == 'approximate' else calibration[name]['load_resistance_ohm']
                if mode != 'approximate':
                    c = calibration[name]
                    require(abs(resistance - (c['calibration_voltage_v'] / current - .068)) < 1e-12,
                            'calibration does not match declared voltage/current/postfilter resistance')
                yield name, {'vin_v': vin, 'target_current_a': current, 'capacitance_nf': capacitance, 'load_resistance_ohm': resistance}


def deck(name, case):
    require(sha(TEMPLATE) == TEMPLATE_SHA, 'historical template changed; review before reusing this recipe')
    return (TEMPLATE.read_text().replace('VIN vin sg 19', f'VIN vin sg {case["vin_v"]}')
            .replace('CCP cz 0 47n', f'CCP cz 0 {case["capacitance_nf"]}n')
            .replace('RLOAD sg pre 6.065', f'RLOAD sg pre {case["load_resistance_ohm"]:.15g}')
            .replace('wrdata m12_full_19_47n.dat t', f'option numdgt=15\nwrdata {name}.dat t'))


def prepare(mode, model, output):
    require(sha(model) == MODEL_SHA, 'wrong vendor model bytes')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'ac').mkdir()
    (output / 'lib').mkdir()
    shutil.copyfile(model, output / 'lib/tps54560_avg.lib')
    (output / 'ac/.spiceinit').write_text(INIT)
    result = {'status': 'NOT RUN', 'mode': mode, 'image': IMAGE, 'model_conversion': 'none', 'cases': {}}
    for name, case in cases(mode):
        path = output / 'ac' / (name + '.cir')
        path.write_text(deck(name, case))
        command = ['bash', str(Path.home() / '.codex/scripts/heavy-guard.sh'), '--', 'docker', 'run', '--rm',
                   '--platform', 'linux/amd64', '--cpus', '1', '--user', '0', '-v', f'{output.resolve()}:/w',
                   '-w', '/w/ac', '--entrypoint', 'ngspice', IMAGE, '-b', name + '.cir']
        result['cases'][name] = {**case, 'deck_sha256': sha(path), 'command': command, 'status': 'NOT RUN'}
    (output / 'prepared.json').write_text(json.dumps(result, indent=2) + '\n')


def analyze_waveform(path):
    rows = [tuple(map(float, line.split())) for line in path.read_text().splitlines() if line.strip()]
    require(len(rows) == 201 and all(len(row) == 3 and all(map(math.isfinite, row)) for row in rows),
            'expected 201 finite frequency/real/imaginary rows')
    require(abs(rows[0][0] - 100) < 1e-6 and abs(rows[-1][0] - 1e6) < .01,
            'frequency endpoints must be 100 Hz and 1 MHz')
    require(all(b[0] > a[0] for a, b in zip(rows, rows[1:])), 'frequency must strictly increase')
    unwrapped, previous, offset = [], None, 0
    for frequency, real, imaginary in rows:
        magnitude = abs(complex(real, imaginary))
        require(magnitude > 0, 'zero transfer magnitude cannot be interpolated logarithmically')
        phase = math.degrees(math.atan2(imaginary, real))
        if previous is not None:
            while phase + offset - previous > 180:
                offset -= 360
            while phase + offset - previous < -180:
                offset += 360
        phase += offset
        previous = phase
        unwrapped.append((frequency, magnitude, phase))
    unity, phase_crossings = [], []
    for (f1, m1, p1), (f2, m2, p2) in zip(unwrapped, unwrapped[1:]):
        # Include a crossing exactly on a sampled endpoint once (at the right endpoint).
        if (m1 > 1 >= m2) or (m1 < 1 <= m2):
            k = math.log(m1) / (math.log(m1) - math.log(m2))
            unity.append({'direction': 'descending' if m1 > m2 else 'ascending',
                          'frequency_hz': f1 * (f2 / f1) ** k,
                          'phase_margin_deg': 180 + p1 + (p2 - p1) * k})
        if (p1 > -180 >= p2) or (p1 < -180 <= p2):
            k = (-180 - p1) / (p2 - p1)
            gain = math.exp(math.log(m1) + (math.log(m2) - math.log(m1)) * k)
            phase_crossings.append({'frequency_hz': f1 * (f2 / f1) ** k, 'gain_margin_db': -20 * math.log10(gain)})
    require(any(x['direction'] == 'descending' for x in unity), 'no descending unity-gain crossing')
    return {'samples': len(rows), 'unity_crossings': unity, 'minus180_phase_crossings': phase_crossings}


def audit(directory, mode):
    receipt_path = directory / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    expected = dict(cases(mode))
    require(receipt['status'] == 'COMPLETE' and set(receipt['cases']) == set(expected), 'incomplete or unexpected cases')
    require(receipt['image'] == IMAGE and receipt['platform'] == 'linux/amd64', 'solver image/platform differs')
    require(sha(directory / 'lib/tps54560_avg.lib') == MODEL_SHA, 'executed model changed')
    require((directory / 'ac/.spiceinit').read_text() == INIT, 'solver settings changed')
    result = {}
    for name, case in expected.items():
        prior = receipt['cases'][name]
        require(prior['status'] == 'COMPLETE' and prior['returncode'] == 0, f'{name}: solver failure')
        command = prior['command']
        expected_tail = ['docker', 'run', '--rm', '--platform', 'linux/amd64', '--cpus', '1', '--user', '0',
                         '-v', f'{directory.resolve()}:/w', '-w', '/w/ac', '--entrypoint', 'ngspice', IMAGE, '-b', name + '.cir']
        require(len(command) == len(expected_tail) + 3 and command[0] == 'bash'
                and command[2] == '--' and command[3:] == expected_tail,
                f'{name}: executed command differs from reviewed solver invocation')
        path = directory / 'ac' / name
        require(path.with_suffix('.cir').read_text() == deck(name, case), f'{name}: deck differs from recipe')
        for suffix, key in [('.cir', 'deck_sha256'), ('.log', 'log_sha256'), ('.dat', 'waveform_sha256')]:
            require(sha(path.with_suffix(suffix)) == prior[key], f'{name}: changed {suffix}')
        log = path.with_suffix('.log').read_text()
        require(not re.search(r'aborted|fatal error', log, re.I), f'{name}: aborted solver log')
        values = dict(re.findall(r'(v\((?:sg|pre)\))\s*=\s*([+\-\d.eE]+)', log))
        require(len(values) == 2, f'{name}: missing DC operating point')
        actual = (float(values['v(sg)']) - float(values['v(pre)'])) / case['load_resistance_ohm']
        uncertainty = sum(.5 * 10 ** Decimal(v).as_tuple().exponent for v in values.values()) / case['load_resistance_ohm']
        if mode != 'approximate':
            require(abs(actual - case['target_current_a']) + uncertainty < 1e-5, f'{name}: DC load target not met')
        result[name] = {**case, **analyze_waveform(path.with_suffix('.dat')),
                        'dc_current_from_log_a': actual, 'dc_log_rounding_bound_a': uncertainty,
                        'dc_target_tolerance_a': None if mode == 'approximate' else 1e-5,
                        **{key: prior[key] for key in ('deck_sha256', 'log_sha256', 'waveform_sha256')}}
    return {'raw_directory': str(directory.relative_to(ROOT)), 'receipt_sha256': sha(receipt_path),
            'source_base_revision': receipt['source_base_revision'], 'source_worktree_modified': receipt['source_worktree_modified'],
            'input_sha256': receipt['inputs_sha256'], 'cases': result}


def summarize(base):
    approximate = base / 'run'
    require(sha(approximate / 'receipt.json') == json.loads(CALIBRATION.read_text())['approximate_receipt_sha256'],
            'calibration receipt changed')
    datasets = {label: audit(base / directory, mode) for label, directory, mode in
                [('approximate_load_calibration', 'run', 'approximate'),
                 ('contract_targets', 'run-current-targets', 'contract'), ('light_targets', 'run-light-targets', 'light')]}
    return {'schema_version': 1, 'scope': 'C12 initial-tolerance averaged inverter inner-loop sensitivity',
            'data_integrity_status': 'COMPLETE', 'electrical_acceptance': 'NOT ESTABLISHED',
            'reviewed_endpoint_cases': 16, 'separate_calibration_cases': 12,
            'recipe_sha256': sha(Path(__file__)), 'calibration_sha256': sha(CALIBRATION),
            'template_sha256': TEMPLATE_SHA, 'original_model_sha256': MODEL_SHA, 'model_conversion': 'none',
            'vendor_package': {'url': 'https://www.ti.com/lit/zip/slvmcu2', 'sha256': MODEL_ZIP_SHA,
                               'recovery_receipt': 'tmp/phase33-model-recovery/recovery-manifest.json'},
            'image': IMAGE, 'platform': 'linux/amd64', 'solver_version_output': (base / 'solver-version.txt').read_text(),
            'solver_version_output_sha256': sha(base / 'solver-version.txt'), 'datasets': datasets,
            'limits': ['No global stability or phase-margin acceptance criterion is adopted.',
                       'Only C12 initial +/-5% endpoints; RCCP is nominal 8.2k. Temperature and other tolerances are not swept.',
                       'Existing PA effective capacitance, ESR and inductance remain; no guaranteed installed MLCC minimum.',
                       'Outer servo, tracking/disconnection, full stack, switching ripple and fault-current behavior are omitted.',
                       'Transient and let-through labels are steady AC loads, not 20 ms or maximum-delivered-current qualification.',
                       'The 50 mA averaged-model points do not qualify no-load operation or CCM/DCM mode transitions.',
                       'DC current tolerance 1e-5 A is a numerical load-target check, not an excess-current allowance.',
                       'First approximate-load data remain separate and are not relabelled exact contract-current cases.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--mode', choices=('approximate', 'contract', 'light'), required=True)
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    review = sub.add_parser('summarize')
    review.add_argument('--raw-root', type=Path, required=True)
    review.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.mode, args.model, args.output)
    else:
        result = summarize(args.raw_root.resolve())
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print('COMPLETE: 16 endpoint cases and 12 separate calibration cases; electrical acceptance NOT ESTABLISHED')


if __name__ == '__main__':
    main()
