"""Verify the LED consumer reference to zudo-pd's shared P15 r1 record.

usage: python3 scripts/checks/verify-p15-reference.py --pd-repo PATH [--pd-rev REV] [--json OUT]
       python3 scripts/checks/verify-p15-reference.py --local-only

--pd-repo names an explicit zudo-pd checkout; inputs are read from its Git object store at --pd-rev
(default: the record_commit pinned in boards/p15-r1-reference.json). A missing checkout or commit is a
failure, not a skip. --local-only checks only this repository's side (record shape, the preserved
historical Board P bytes, and that no LED board path is used as P15).

The check proves byte identity only, never electrical, mechanical, programmed or physical acceptance.
Exit 0 = match; 1 = mismatch or missing input; 2 = usage error.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / 'boards/p15-r1-reference.json'
STATUS_KEYS = ('source_verification', 'ordered', 'received', 'programmed', 'measured')
PASS_WORDS = ('PASS', 'ACCEPTED', 'QUALIFIED', 'VALIDATED', 'RELEASED')
P15_PREFIX = 'boards/board-p15/'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(repo, rev, path):
    r = subprocess.run(['git', '-C', str(repo), 'cat-file', 'blob', f'{rev}:{path}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def git_commit(repo, rev):
    r = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '--quiet', f'{rev}^{{commit}}'],
                       capture_output=True)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def check_local(record, root=ROOT):
    errors = []
    for key in ('owner', 'adoption', 'pinned_artifacts', 'led_side', 'historical_board_p', 'status'):
        if key not in record:
            errors.append(f'record: missing field {key}')
    if errors:
        return errors
    for key in STATUS_KEYS:
        if key not in record['status']:
            errors.append(f'record: status.{key} missing')
    for key in ('ordered', 'received', 'programmed', 'measured'):
        value = str(record['status'].get(key, '')).upper()
        if any(w in value for w in PASS_WORDS) and 'evidence' not in record['status']:
            errors.append(f'record: status.{key} claims physical state without status.evidence')
    roles = set()
    for art in record['pinned_artifacts']:
        roles.add(art['role'])
        if not art['path'].startswith(P15_PREFIX):
            errors.append(f'{art["path"]}: not a zudo-pd P15 path (wrong board)')
    for role in ('pcb', 'nvm-image'):
        if role not in roles:
            errors.append(f'record: no {role} artifact')
    hist = record['historical_board_p']
    p = root / hist['path']
    if not p.is_file():
        errors.append(f'{hist["path"]}: historical LED Board P missing (bytes must be preserved)')
    else:
        got = sha256(p.read_bytes())
        if got != hist['sha256']:
            errors.append(f'{hist["path"]}: sha256 {got} != recorded {hist["sha256"]} (historical bytes changed)')
        if any(got == a['sha256'] for a in record['pinned_artifacts']):
            errors.append(f'{hist["path"]}: historical LED Board P bytes equal a P15 artifact')
    return errors


def check_owner(record, pd_repo, pd_rev):
    errors = []
    commit = git_commit(pd_repo, pd_rev)
    if commit is None:
        return [f'zudo-pd revision {pd_rev} not found in {pd_repo}'], None
    owner = record['owner']
    raw = git_blob(pd_repo, commit, owner['record_path'])
    if raw is None:
        return [f'zudo-pd {owner["record_path"]} missing at {commit}'], commit
    pd_record = json.loads(raw)
    pd_hashes = {a['path']: a['sha256'] for a in pd_record.get('artifacts', [])}
    for art in record['pinned_artifacts']:
        if pd_hashes.get(art['path']) != art['sha256']:
            errors.append(f'{art["path"]}: LED pin {art["sha256"]} != zudo-pd record {pd_hashes.get(art["path"])}')
        data = git_blob(pd_repo, commit, art['path'])
        if data is None:
            errors.append(f'{art["path"]}: missing in zudo-pd at {commit}')
        elif sha256(data) != art['sha256']:
            errors.append(f'{art["path"]}: zudo-pd bytes at {commit} have sha256 {sha256(data)}')
    adopted = record['adoption']['zudo_pd_commit']
    if pd_record.get('adoption_revision', {}).get('sha') != adopted:
        errors.append(f'adoption commit {adopted} != zudo-pd record adoption_revision')
    if git_commit(pd_repo, adopted) is None:
        errors.append(f'adoption commit {adopted} not present in {pd_repo}')
    return errors, commit


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pd-repo', help='explicit zudo-pd checkout')
    mode.add_argument('--local-only', action='store_true')
    ap.add_argument('--pd-rev', help='zudo-pd revision (default: owner.record_commit)')
    ap.add_argument('--record', default=str(RECORD))
    ap.add_argument('--json')
    args = ap.parse_args(argv)
    record = json.loads(Path(args.record).read_text())

    errors = check_local(record)
    pd_commit = None
    if args.pd_repo and not errors:
        pd_rev = args.pd_rev or record['owner']['record_commit']
        owner_errors, pd_commit = check_owner(record, Path(args.pd_repo), pd_rev)
        errors += owner_errors
    scope = 'local side only' if args.local_only else f'zudo-pd at {pd_commit}'
    result = 'FAIL' if errors else 'SOURCE IDENTITY MATCH'
    if args.json:
        Path(args.json).write_text(json.dumps({'result': result, 'scope': scope, 'errors': errors,
                                               'status': record.get('status')}, indent=2) + '\n')
    for k in STATUS_KEYS:
        print(f'STATUS     {k}: {record.get("status", {}).get(k)}')
    for e in errors:
        print(f'FAIL       {e}', file=sys.stderr)
    print(f'{result} ({scope}; byte identity only)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
