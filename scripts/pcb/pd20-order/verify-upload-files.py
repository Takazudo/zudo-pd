"""Check the six PD20 supplier upload files against the frozen package's own locks. Read-only.

usage: python3 scripts/pcb/pd20-order/verify-upload-files.py [--release DIR]

Scope: UPLOAD FILE INTEGRITY only. It proves that the Board P r3 and B20 Gerber ZIP, BOM and CPL bytes in the
release folder equal the bytes the package locked in SHA256SUMS and manifest.json. It does not replay the export,
re-check source locks, parse Gerbers, run DRC/ERC or native KiCad, and says nothing about electrical, mechanical or
supplier acceptance. Complete historical replay is the unmodified scripts/pcb/verify-jlcpcb.py with every recorded
source hash and the original local-only populated-stack STEP; this checker never substitutes for it.

Order of checks: strict SHA256SUMS parse (no duplicate or unsafe path), manifest.json against its checksum and, for
the default release, against the pinned manifest hash of the 2026-11-20 export, the
verified manifest's artifact hashes against SHA256SUMS for all six files, then the six files' actual bytes.
Exit 0 = all six match; 1 = any refusal; 2 = usage error. Nothing is written.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RELEASE = ROOT / 'manufacturing/releases/pd20-prototype-review'
# manifest.json of the 2026-11-20 PD20 package (ORDER-SHEET.md); anchors the default check to that exact export
EXPECTED_MANIFEST_SHA256 = 'f430a76ac01ff77359a5c67112b429c45807afac7ac70cae73d1566c57b62607'
BOARDS = ('board-p', 'board-b20-draft')
UPLOAD_FILES = tuple(f'{b}/{name}' for b in BOARDS for name in (f'{b}-gerbers.zip', 'bom.csv', 'cpl.csv'))
MANIFEST = 'manifest.json'
LINE = re.compile(r'^([0-9a-f]{64})  (.+)$')
SCOPE = ('scope: the six supplier upload files equal the package locks (SHA256SUMS + manifest.json). '
         'NOT a complete engineering replay, native KiCad validation or electrical qualification.')


class Refusal(Exception):
    pass


def safe_relative(relative):
    p = PurePosixPath(relative)
    return (relative == str(p) and not p.is_absolute() and '..' not in p.parts and '\\' not in relative
            and relative.strip() == relative and bool(p.parts))


def parse_sums(text):
    entries = {}
    for number, line in enumerate(text.splitlines(), 1):
        m = LINE.match(line)
        if not m:
            raise Refusal(f'SHA256SUMS line {number} is not "<sha256>  <path>"')
        sha, relative = m.groups()
        if not safe_relative(relative):
            raise Refusal(f'SHA256SUMS line {number} has an invalid path: {relative!r}')
        if relative in entries:
            raise Refusal(f'SHA256SUMS lists {relative} more than once')
        entries[relative] = sha
    return entries


def file_sha256(release, relative):
    path = release / relative
    resolved = path.resolve()
    if not resolved.is_relative_to(release.resolve()):
        raise Refusal(f'{relative} resolves outside the release folder')
    if not path.is_file():
        raise Refusal(f'missing file: {relative}')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(release, expected_manifest=None):
    """Return [(relative, sha256)] for the six upload files, or raise Refusal."""
    release = Path(release)
    sums_path = release / 'SHA256SUMS'
    if sums_path.is_symlink() or not sums_path.is_file():
        raise Refusal('missing SHA256SUMS (or it is a symlink)')
    sums = parse_sums(sums_path.read_text())
    for relative in (MANIFEST, *UPLOAD_FILES):
        if relative not in sums:
            raise Refusal(f'SHA256SUMS has no entry for {relative}')

    manifest_sha = file_sha256(release, MANIFEST)
    if manifest_sha != sums[MANIFEST]:
        raise Refusal('manifest.json does not match its SHA256SUMS entry')
    if expected_manifest and manifest_sha != expected_manifest:
        raise Refusal(f'manifest.json is not the expected export ({expected_manifest[:8]}…)')
    manifest = json.loads((release / MANIFEST).read_text())
    if not isinstance(manifest, dict) or not isinstance(manifest.get('boards'), list) \
            or not isinstance(manifest.get('artifact_hashes'), dict) \
            or not all(isinstance(r, dict) and isinstance(r.get('board'), str) for r in manifest['boards']):
        raise Refusal('manifest.json does not have the expected boards / artifact_hashes structure')
    boards = [r['board'] for r in manifest['boards']]
    if sorted(boards) != sorted(BOARDS):
        raise Refusal(f'manifest boards are {boards}, expected exactly {list(BOARDS)}')
    locks = manifest['artifact_hashes']
    for relative in UPLOAD_FILES:
        if relative not in locks:
            raise Refusal(f'manifest artifact_hashes has no entry for {relative}')
        if locks[relative] != sums[relative]:
            raise Refusal(f'manifest and SHA256SUMS disagree for {relative}')

    results = []
    for relative in UPLOAD_FILES:
        actual = file_sha256(release, relative)
        if actual != sums[relative]:
            raise Refusal(f'bytes differ from the package lock: {relative}')
        results.append((relative, actual))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--release', type=Path, default=DEFAULT_RELEASE)
    args = parser.parse_args(argv)
    try:
        default = args.release.resolve() == DEFAULT_RELEASE.resolve()
        results = check(args.release, EXPECTED_MANIFEST_SHA256 if default else None)
    except (Refusal, ValueError, OSError) as error:
        print(f'UPLOAD FILE INTEGRITY: FAIL: {error}', file=sys.stderr)
        print(SCOPE, file=sys.stderr)
        return 1
    for relative, sha in results:
        print(f'OK  {sha}  {relative}')
    anchor = 'pinned manifest f430a76a… matched' if default else 'no pinned manifest for a non-default release'
    print(f'UPLOAD FILE INTEGRITY: PASS (6/6 upload files; manifest.json and SHA256SUMS agree; {anchor}) in {args.release}')
    print(SCOPE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
