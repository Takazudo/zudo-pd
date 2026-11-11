"""Apply a value-only spec change to the saved B20 PCB (pinned KiCad 10.0.6 pcbnew).

usage: sync-fields.py IN.kicad_pcb OUT.kicad_pcb EXPECTED_REFS
EXPECTED_REFS is a comma-separated list of reference designators.
For every footprint owned by board_b20_components.py, this sets the Value and LCSC fields to the
generated projection. It fails without saving if:
- a footprint identity or the footprint set differs;
- a board-only footprint is not a fiducial or a mounting hole;
- the changed set is not exactly EXPECTED_REFS.
Placement, pads, copper and fills are not touched. Fills are redone by finalize_refill.py, and
verify-field-sync.py proves the rest of the board is unchanged.
"""
import json
from pathlib import Path
import re
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from board_b20_components import COMPONENTS  # noqa: E402

BOARD_ONLY = re.compile(r'^(FID|H)[0-9]+$')

source, output, expected = sys.argv[1], sys.argv[2], set(filter(None, sys.argv[3].split(',')))
board = pcbnew.LoadBoard(source)
seen, changes = set(), {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in COMPONENTS:
        if not BOARD_ONLY.match(ref):
            raise SystemExit(f'Footprint {ref} is not owned by the B20 components projection')
        continue
    if ref in seen:
        raise SystemExit(f'Duplicate footprint {ref}')
    seen.add(ref)
    _mpn, value, lcsc, lib_id, *_ = COMPONENTS[ref]
    if str(fp.GetFPID().Format()) != lib_id:
        raise SystemExit(f'{ref}: footprint {fp.GetFPID().Format()} differs from {lib_id}; not a value-only change')
    fields = [item for item in fp.GetFields() if item.GetName() == 'LCSC']
    if len(fields) != 1:
        raise SystemExit(f'{ref}: expected exactly one LCSC field')
    field = fields[0]
    before = (fp.GetValue(), field.GetText())
    if before != (value, lcsc):
        changes[ref] = {'before': list(before), 'after': [value, lcsc]}
        fp.SetValue(value)
        field.SetText(lcsc)
if seen != set(COMPONENTS):
    raise SystemExit(f'Footprints missing from the PCB: {sorted(set(COMPONENTS) - seen)}')
if set(changes) != expected:
    raise SystemExit(f'Changed set {sorted(changes)} differs from expected {sorted(expected)}')
board.Save(output)
print(json.dumps({'changes': changes}, indent=1, sort_keys=True))
