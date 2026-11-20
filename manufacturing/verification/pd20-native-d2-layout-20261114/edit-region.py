"""Write the verifier's own D2 edit region (courtyard circles of new and replaced parts, old and new, plus every changed
copper item) as [{a, b, r}] for fill-slit-check.py. usage: edit-region.py BEFORE.kicad_pcb verification.json out.json"""
import importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('vip', ROOT / 'scripts/pcb/board-b20/verify-insert-parts.py')
vip = importlib.util.module_from_spec(spec); spec.loader.exec_module(vip)
before = vip.parse(vip.tokenize(Path(sys.argv[1]).read_text()))
result = json.load(open(sys.argv[2]))
after = vip.parse(vip.tokenize((ROOT / 'boards/board-b20-draft/board-b20-draft.kicad_pcb').read_text()))
old, new = vip.footprints(before), vip.footprints(after)
region = [vip.courtyard(new[r]) for r in result['added_parts']]
region += [vip.courtyard(fp[r]) for r in result['replaced_parts'] for fp in (old, new)]
region += [vip.reach(i) for i in result['removed_copper'] + result['added_copper']]
Path(sys.argv[3]).write_text(json.dumps([{'a': a, 'b': b, 'r': r} for a, b, r in region]) + '\n')
print(len(region), 'region capsules')
