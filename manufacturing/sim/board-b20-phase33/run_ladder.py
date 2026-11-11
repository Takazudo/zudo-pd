"""Run phase33 solver variants with fresh outputs and retained execution provenance.

Success means complete waveforms, not compliance with the electrical contract.
Analyze the printed accepted directory with both strengthened analysis scripts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import uuid
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from analysis_inputs import load, START_CASES, REENTRY_CASES

IMAGE = 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
VARIANTS = (('original', None), ('rshunt', ('rshunt=1e10', 'rshunt=1e9')),
            ('maxstep', (' 0 5u', ' 0 2u')), ('abstol', ('abstol=1e-9', 'abstol=1e-8')),
            ('reltol', ('reltol=1e-3', 'reltol=3e-3')), ('gear', ('method=trap', 'method=gear')),
            ('gear-rshunt', None))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_executed_inputs(attempt_root, input_sha256):
    """Bind the lib/ tree and .spiceinit an attempt actually mounted to the runner's input snapshot.

    The solver reads the per-attempt copies, not inputs/, so a snapshot match alone does not prove
    what executed. Returns the executed digests; raises ValueError naming the first mismatch.
    """
    attempt_root = Path(attempt_root)
    expected = {k: v for k, v in input_sha256.items() if k.startswith('lib/')}
    if '.spiceinit' not in input_sha256 or not expected:
        raise ValueError('runner input snapshot lacks .spiceinit or lib/ entries')
    library = attempt_root / 'lib'
    if not library.is_dir() or library.is_symlink():
        raise ValueError(f'{attempt_root}: executed library directory missing')
    executed = {}
    for path in sorted(library.rglob('*')):
        relative = 'lib/' + path.relative_to(library).as_posix()
        if path.is_symlink():
            raise ValueError(f'{attempt_root}: executed input {relative} is a symlink, not a retained copy')
        if path.is_file():
            executed[relative] = digest(path)
    for relative in sorted(expected.keys() - executed.keys()):
        raise ValueError(f'{attempt_root}: executed input missing: {relative}')
    for relative in sorted(executed.keys() - expected.keys()):
        raise ValueError(f'{attempt_root}: unexpected executed input: {relative}')
    for relative in sorted(expected):
        if executed[relative] != expected[relative]:
            raise ValueError(f'{attempt_root}: executed input {relative} differs from runner input snapshot')
    if attempt_root.is_symlink() or (attempt_root / 'tracking').is_symlink():
        raise ValueError(f'{attempt_root}: executed attempt or tracking directory is a symlink, not a retained copy')
    settings = attempt_root / 'tracking' / '.spiceinit'
    if settings.is_symlink() or not settings.is_file():
        raise ValueError(f'{attempt_root}: executed settings missing: tracking/.spiceinit')
    executed['tracking/.spiceinit'] = digest(settings)
    if executed['tracking/.spiceinit'] != input_sha256['.spiceinit']:
        raise ValueError(f'{attempt_root}: executed settings tracking/.spiceinit differ from runner input snapshot')
    return executed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('cases', nargs='+', choices=START_CASES + REENTRY_CASES)
    parser.add_argument('--original-only', action='store_true', help='run the supplied deck without fallback solver changes (for bounded convergence comparisons)')
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    source = (base / args.directory).resolve()
    if not source.is_dir() or len(set(args.cases)) != len(args.cases):
        parser.error('existing input directory and unique cases required')
    for name in args.cases:
        if not (source / (name + '.cir')).is_file():
            parser.error('missing deck: ' + name)
    if not (source / '.spiceinit').is_file() or not (source.parent / 'lib').is_dir():
        parser.error('input .spiceinit and sibling lib directory required')
    run = Path(tempfile.mkdtemp(prefix='ladder-', dir=source.parent))
    accepted = run / 'accepted'
    accepted.mkdir()
    inputs = run / 'inputs'
    inputs.mkdir()
    shutil.copytree(source.parent / 'lib', inputs / 'lib')
    shutil.copyfile(source / '.spiceinit', inputs / '.spiceinit')
    for name in args.cases:
        shutil.copyfile(source / (name + '.cir'), inputs / (name + '.cir'))
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source, capture_output=True, text=True)
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'image': IMAGE,
               'platform': os.environ.get('DOCKER_DEFAULT_PLATFORM', 'linux/amd64'),
               'source_revision': git.stdout.strip() if git.returncode == 0 else None,
               'requested_cases': args.cases,
               'variant_policy': 'original-only' if args.original_only else 'fallback-ladder',
               'source_dirty': bool(subprocess.run(['git', 'status', '--porcelain'], cwd=source, capture_output=True, text=True).stdout),
               'runner_sha256': {name: digest(base / name) for name in ('run_ladder.sh', 'run_ladder.py', 'analysis_inputs.py')},
               'input_sha256': {str(p.relative_to(inputs)): digest(p) for p in inputs.rglob('*') if p.is_file()},
               'status': 'RUNNING', 'cases': {}}
    def save():
        (run / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    print(f'Run evidence: {run}', flush=True)
    try:
        version_container = 'phase33-version-' + uuid.uuid4().hex
        try:
            version = subprocess.run(['docker', 'run', '--rm', '--name', version_container, '--platform', receipt['platform'],
                                      '--entrypoint', 'ngspice', IMAGE, '--version'],
                                     capture_output=True, text=True, timeout=60)
        finally:
            cleanup = subprocess.run(['docker', 'rm', '-f', version_container], capture_output=True, text=True, timeout=30)
            if cleanup.returncode and 'No such container:' not in cleanup.stderr:
                receipt['status'] = 'FAILED'
                raise RuntimeError('Version probe container cleanup failed')
        receipt['solver_version_output'] = version.stdout + version.stderr
        receipt['solver_version_returncode'] = version.returncode
        if version.returncode != 0:
            receipt['status'] = 'FAILED'
            return 1
        save()
        for name in args.cases:
            attempts = []
            receipt['cases'][name] = {'status': 'FAILED', 'attempts': attempts}
            original = (inputs / (name + '.cir')).read_text()
            for index, (label, replacement) in enumerate(VARIANTS[:1] if args.original_only else VARIANTS):
                root = run / name / str(index)
                work = root / 'tracking'
                work.mkdir(parents=True)
                shutil.copytree(inputs / 'lib', root / 'lib')
                shutil.copyfile(inputs / '.spiceinit', work / '.spiceinit')
                deck = original.replace(*replacement) if replacement else original
                if label == 'gear-rshunt':
                    deck = deck.replace('method=trap', 'method=gear').replace('rshunt=1e10', 'rshunt=1e9')
                (work / (name + '.cir')).write_text(deck)
                container = 'phase33-' + uuid.uuid4().hex
                command = ['docker', 'run', '--rm', '--name', container, '--platform', receipt['platform'], '--cpus', '1', '--user', '0',
                           '-v', f'{root}:/w', '-w', '/w/tracking', '--entrypoint', 'ngspice', IMAGE, '-b', name + '.cir']
                attempt = {'variant': label, 'command': command, 'deck_sha256': digest(work / (name + '.cir'))}
                attempts.append(attempt)
                save()
                log = work / (name + '.log')
                with log.open('w') as output:
                    try:
                        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=3000)
                        attempt['returncode'] = result.returncode
                    except subprocess.TimeoutExpired:
                        attempt['returncode'] = 124
                    finally:
                        # Killing a Docker client does not guarantee stopping its container.
                        cleanup = subprocess.run(['docker', 'rm', '-f', container], capture_output=True, text=True, timeout=30)
                        attempt['cleanup_returncode'] = cleanup.returncode
                        attempt['cleanup_stderr'] = cleanup.stderr
                        if cleanup.returncode and 'No such container:' not in cleanup.stderr:
                            receipt['status'] = 'FAILED'
                            attempt['status'] = 'CLEANUP_FAILED'
                            save()
                            raise RuntimeError('Docker cleanup failed; refusing another solver attempt')
                attempt['log_sha256'] = digest(log)
                waveform = work / (name + '.dat')
                if waveform.exists():
                    attempt['waveform_sha256'] = digest(waveform)
                try:
                    if attempt['returncode'] != 0 or re.search(r'aborted', log.read_text(), re.I):
                        raise ValueError('solver failed, timed out, or aborted')
                    load(waveform)
                except (ValueError, OSError) as error:
                    attempt['status'] = 'FAILED'
                    attempt['reason'] = str(error)
                    save()
                    continue
                attempt['status'] = 'COMPLETE'
                receipt['cases'][name]['status'] = 'COMPLETE'
                receipt['cases'][name]['selected_variant'] = index
                for suffix in ('.cir', '.dat', '.log'):
                    shutil.copyfile(work / (name + suffix), accepted / (name + suffix))
                save()
                break
            print(name, receipt['cases'][name]['status'], flush=True)
        complete = all(c['status'] == 'COMPLETE' for c in receipt['cases'].values())
        receipt['status'] = 'COMPLETE' if complete else 'FAILED'
        save()
        print(f'Accepted waveforms: {accepted}', flush=True)
        return 0 if complete else 1
    finally:
        if receipt['status'] == 'RUNNING':
            receipt['status'] = 'INTERRUPTED'
        save()


if __name__ == '__main__':
    sys.exit(main())
