"""Verify the shared P15 r1 source identity record against an explicitly selected revision.

usage: python3 scripts/pcb/board-p15/verify-shared-reference.py (--rev REV | --worktree)
                                                                 [--repo PATH] [--record PATH] [--json OUT]

--rev reads every input from the Git object store at REV (a commit, tag or branch), so uncommitted
files cannot fake a match. --worktree reads the checked-out files instead. The record is read from
the same source unless --record names a file.

The check proves byte identity only. It never reports electrical, mechanical, programmed or physical
acceptance; the record's ordered/received/programmed/measured fields are echoed, not evaluated.
Exit 0 = every required identity matched; 1 = a mismatch or missing input; 2 = usage error.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RECORD = 'boards/board-p15/shared-reference.json'
STATUS_KEYS = ('source_verification', 'ordered', 'received', 'programmed', 'measured')
PHYSICAL_PASS_WORDS = ('PASS', 'ACCEPTED', 'QUALIFIED', 'VALIDATED', 'RELEASED')


class Source:
    def __init__(self, repo, rev=None):
        self.repo, self.rev = Path(repo), rev
        if rev is not None:
            sha = self._git('rev-parse', '--verify', '--quiet', f'{rev}^{{commit}}')
            if sha is None:
                raise LookupError(f'revision not found: {rev}')
            self.commit = sha.decode().strip()
        else:
            self.commit = None

    def _git(self, *args):
        r = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True)
        return r.stdout if r.returncode == 0 else None

    def read(self, path):
        if self.rev is None:
            p = self.repo / path
            return p.read_bytes() if p.is_file() else None
        return self._git('cat-file', 'blob', f'{self.commit}:{path}')

    def has_commit(self, sha):
        return self._git('cat-file', '-e', f'{sha}^{{commit}}') is not None

    def is_ancestor(self, sha):
        if self.commit is None:
            head = self._git('rev-parse', 'HEAD')
            if head is None:
                return False
            target = head.decode().strip()
        else:
            target = self.commit
        return subprocess.run(['git', '-C', str(self.repo), 'merge-base', '--is-ancestor', sha, target],
                              capture_output=True).returncode == 0


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify(src, record):
    errors, report = [], {'selected': src.rev or 'worktree', 'commit': src.commit, 'artifacts': []}

    for key in ('canonical_path', 'reviewed_commit', 'adoption_revision', 'frozen_package', 'artifacts',
                'allowed_path_prefixes', 'forbidden_path_prefixes', 'consumers', 'procedure_owner', 'status'):
        if key not in record:
            errors.append(f'record: missing field {key}')
    if errors:
        return errors, report

    status = record['status']
    for key in STATUS_KEYS:
        if key not in status:
            errors.append(f'record: status.{key} missing (keep source verification separate from physical state)')
    for key in ('ordered', 'received', 'programmed', 'measured'):
        value = str(status.get(key, '')).upper()
        if any(w in value for w in PHYSICAL_PASS_WORDS) and 'evidence' not in status:
            errors.append(f'record: status.{key}={status[key]!r} claims physical state without status.evidence')
    report['status'] = {k: status.get(k) for k in STATUS_KEYS}

    for label in ('reviewed_commit', 'adoption_revision'):
        sha = record[label]['sha']
        if not src.has_commit(sha):
            errors.append(f'{label} {sha}: commit not present in {src.repo}')
        elif not src.is_ancestor(sha):
            errors.append(f'{label} {sha}: not an ancestor of the selected revision')

    allowed, forbidden = record['allowed_path_prefixes'], record['forbidden_path_prefixes']
    seen_roles = set()
    for art in record['artifacts']:
        path, want = art['path'], art['sha256']
        row = {'role': art['role'], 'path': path, 'expected': want}
        seen_roles.add(art['role'])
        if any(path.startswith(p) for p in forbidden):
            errors.append(f'{path}: forbidden board path for P15 (wrong board)')
            row['result'] = 'WRONG_PATH'
        elif not any(path == p or path.startswith(p) for p in allowed):
            errors.append(f'{path}: outside the P15 canonical paths')
            row['result'] = 'WRONG_PATH'
        else:
            data = src.read(path)
            if data is None:
                errors.append(f'{path}: missing at the selected revision')
                row['result'] = 'MISSING'
            else:
                row['actual'] = sha256(data)
                row['result'] = 'MATCH' if row['actual'] == want else 'MISMATCH'
                if row['result'] == 'MISMATCH':
                    errors.append(f'{path}: sha256 {row["actual"]} != recorded {want}')
        report['artifacts'].append(row)
    for role in ('pcb', 'nvm-image'):
        if role not in seen_roles:
            errors.append(f'record: no {role} artifact')

    pkg = record['frozen_package']
    base = pkg['path'].rstrip('/') + '/'
    manifest_bytes, sums_bytes = src.read(base + 'manifest.json'), src.read(base + 'SHA256SUMS')
    pkg_report = {'path': base}
    if manifest_bytes is None or sums_bytes is None:
        errors.append(f'{base}: manifest.json or SHA256SUMS missing at the selected revision')
    else:
        for name, data, want in (('manifest.json', manifest_bytes, pkg['manifest_sha256']),
                                 ('SHA256SUMS', sums_bytes, pkg['sha256sums_sha256'])):
            got = sha256(data)
            pkg_report[name] = 'MATCH' if got == want else 'MISMATCH'
            if got != want:
                errors.append(f'{base}{name}: sha256 {got} != recorded {want} (frozen package must not change)')
        entries = [l for l in sums_bytes.decode().splitlines() if l.strip()]
        pkg_report['sha256sums_entries'] = len(entries)
        if len(entries) != pkg['sha256sums_entries']:
            errors.append(f'{base}SHA256SUMS: {len(entries)} entries != recorded {pkg["sha256sums_entries"]}')
        manifest = json.loads(manifest_bytes)
        if manifest.get('git_base') != pkg['manifest_git_base']:
            errors.append(f'{base}manifest.json git_base {manifest.get("git_base")} != recorded {pkg["manifest_git_base"]}')
        boards = {b['board']: b for b in manifest.get('boards', [])}
        lock = boards.get(pkg['lock_board'], {}).get('source_hashes', {})
        by_path = {a['path']: a['sha256'] for a in record['artifacts']}
        for path in pkg['fabrication_lock_paths']:
            if lock.get(path) is None:
                errors.append(f'{path}: not in the frozen {pkg["lock_board"]} source lock')
            elif path in by_path and lock[path] != by_path[path]:
                errors.append(f'{path}: record sha256 differs from the frozen source lock')
            else:
                data = src.read(path)
                if data is None or sha256(data) != lock[path]:
                    errors.append(f'{path}: selected revision no longer matches the frozen source lock')
        drift = []
        for path, want in sorted(lock.items()):
            data = src.read(path)
            if data is None:
                drift.append({'path': path, 'result': 'MISSING'})
            elif sha256(data) != want:
                drift.append({'path': path, 'result': 'CHANGED'})
        pkg_report['source_lock'] = {'paths': len(lock), 'matching': len(lock) - len(drift),
                                     'drift_informational': drift}
    report['frozen_package'] = pkg_report
    return errors, report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument('--rev', help='commit, tag or branch to verify from the Git object store')
    sel.add_argument('--worktree', action='store_true', help='verify the checked-out files')
    ap.add_argument('--repo', default=str(ROOT))
    ap.add_argument('--record', help='record file path (default: the record at the selected source)')
    ap.add_argument('--json', help='write the report here')
    args = ap.parse_args(argv)

    try:
        src = Source(args.repo, None if args.worktree else args.rev)
    except LookupError as e:
        print(f'FAIL: {e}', file=sys.stderr)
        return 1
    raw = Path(args.record).read_bytes() if args.record else src.read(RECORD)
    if raw is None:
        print(f'FAIL: {RECORD} missing at the selected source', file=sys.stderr)
        return 1
    errors, report = verify(src, json.loads(raw))
    report['result'] = 'FAIL' if errors else 'SOURCE IDENTITY MATCH'
    report['errors'] = errors
    report['scope'] = 'byte identity only; no electrical, mechanical, programmed or physical acceptance'
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + '\n')

    for row in report['artifacts']:
        print(f'{row["result"]:<10} {row["role"]:<20} {row["path"]}')
    lock = report.get('frozen_package', {}).get('source_lock')
    if lock:
        print(f'INFO       frozen source lock: {lock["matching"]}/{lock["paths"]} paths unchanged at the selected '
              f'revision ({len(lock["drift_informational"])} later changes, expected for a fixed snapshot)')
    for k, v in report.get('status', {}).items():
        print(f'STATUS     {k}: {v}')
    for e in errors:
        print(f'FAIL       {e}', file=sys.stderr)
    print(f'{report["result"]} at {report["selected"]}' + (f' ({report["commit"]})' if report['commit'] else ''))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
