"""Compare a saved-placement/routes native replay, ignoring only generated UUIDs."""
import hashlib
import json
from pathlib import Path
import re
import sys

original, replay, output = map(Path, sys.argv[1:])
def normalize(path):
    text = path.read_text()
    ids = re.findall(r'\(uuid "([0-9a-fA-F-]{36})"\)', text)
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate native object UUIDs: {path}')
    return re.sub(r'\(uuid "[0-9a-fA-F-]{36}"\)', '(uuid "GENERATED")', text).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

first, second = normalize(original), normalize(replay)
report = {'original': str(original), 'replay': str(replay),
          'original_sha256': sha(original.read_bytes()), 'replay_sha256': sha(replay.read_bytes()),
          'original_normalized_sha256': sha(first), 'replay_normalized_sha256': sha(second),
          'equal_ignoring_generated_uuids': first == second,
          'scope': 'Entire serialized PCB comparison after replacing only UUID values; no geometry, nets, footprints, masks, layers, fills or settings are removed. The comparison itself does not regenerate a board or rerun routing; caller provenance must identify fresh-builder or saved-placement scope.'}
output.write_text(json.dumps(report, indent=2)+'\n')
if first != second:
    raise SystemExit('FAIL: replay differs beyond generated UUIDs; inspect before acceptance')
print('PASS: complete saved-owner replay matches, ignoring only generated UUIDs')
