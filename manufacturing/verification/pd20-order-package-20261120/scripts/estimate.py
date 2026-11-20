"""Two-pair PD20 catalog estimate from the retained JLC fee model. Not a supplier quote.

usage: estimate.py RELEASE_DIR PARTS_AVAILABILITY.json LOT
"""
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
release, snap, lot = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), int(sys.argv[3])
s = importlib.util.spec_from_file_location('lineup', ROOT / 'scripts/pcb/calculate-lineup-cost.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
missing = sorted(c for c, r in snap['parts'].items() if 'price_tiers_usd' not in r or not r['price_tiers_usd'])
m.PARTS.update({c: {'model': r['model'], 'library_type': r['library_type'], 'stock': r['stock'],
                    'price_tiers_usd': r['price_tiers_usd']} for c, r in snap['parts'].items() if c not in missing})
pcbs = {'board-p': 'boards/board-p/board-p.kicad_pcb', 'board-b20-draft': 'boards/board-b20-draft/board-b20-draft.kicad_pcb'}
out = {'basis': 'catalog estimate, not a supplier quote: scripts/pcb/calculate-lineup-cost.py board_cost() with its retained '
                 'fee table and the dated JLC catalog rows; PCB fabrication and shipping are not included',
       'lot': lot, 'unpriced_lines': missing, 'boards': {}}
for board, pcb in pcbs.items():
    b = m.bom_board(str((release / board / 'bom.csv').relative_to(ROOT)) if release.is_absolute() else str(release / board / 'bom.csv'), pcb)
    if missing:
        b['lines'] = {c: r for c, r in b['lines'].items() if c not in missing}
    res = m.board_cost(b, lot)
    out['boards'][board] = {'joints_per_board': b['joints'], 'double_sided': b['double_sided'],
                            **{k: res[k] for k in ('parts_usd', 'assembly_usd', 'assembly_kind', 'assembly_classes_usd', 'lines',
                                                   'extended_lines', 'stock_below_purchase')}}
out['total_parts_and_assembly_usd'] = round(sum(v['parts_usd'] + v['assembly_usd'] for v in out['boards'].values()), 2)
print(json.dumps(out, indent=1, sort_keys=True))
