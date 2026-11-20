import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; E=Path(__import__('os').environ.get('P15_EVIDENCE_DIR', 'tmp/p15-order-refresh'))
s=importlib.util.spec_from_file_location('lineup',ROOT/'scripts/pcb/calculate-lineup-cost.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
snap=json.loads((E/'parts-availability-2026-11-20.json').read_text())
parts={c:{'model':r['jlc']['model'],'library_type':r['jlc']['library_type'],'stock':r['jlc']['stock'],'price_tiers_usd':r['jlc']['price_tiers_usd']} for c,r in snap['parts'].items()}
m.PARTS.update(parts)
b=m.bom_board('manufacturing/releases/corner-support-review/board-p15/bom.csv','boards/board-p15/board-p15-draft.kicad_pcb')
res=m.board_cost(b,2)
# conservative attrition variant: JLC fields leastPatchNumber/lossNumber (semantics not documented publicly; treated as min-buy and attrition)
cons=0.0; crow=[]
for code,refs in sorted(b['lines'].items()):
    j=snap['parts'][code]['jlc']; need=len(refs)*2
    buy=max(need+(j['lossNumber'] or 0), j['leastPatchNumber'] or 0, j['minPurchaseNum'] or 1)
    _,p=m.tier_price(code,buy); cons+=buy*p; crow.append({'lcsc':code,'need':need,'buy':buy,'unit_usd':p,'line_usd':round(buy*p,4)})
out={'basis':'catalog estimate, not a supplier quote; retained fee model scripts/pcb/calculate-lineup-cost.py board_cost() with fee table from jlc-snapshot-2026-10-31 (page still Last updated Oct 22, 2026 on 2026-11-20) and the 2026-11-20 JLC catalog rows',
     'lot':2,'joints_per_board':b['joints'],'double_sided':b['double_sided'],
     'model':{k:res[k] for k in ('parts_usd','assembly_usd','assembly_kind','assembly_classes_usd','lines','extended_lines','stock_below_purchase')},'model_rows':res['rows'],
     'conservative_attrition_parts_usd':round(cons,2),'conservative_rows':crow}
print(json.dumps(out,indent=1))
