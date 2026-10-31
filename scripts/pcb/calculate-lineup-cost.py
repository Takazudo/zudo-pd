"""Phase 12: part and assembly cost of the current lineup (Board P 15 V as built + Board B) against the renewal
lineup (Board P r3 draft + B20 paper draft), from the retained JLCPCB snapshot.

usage: python3 scripts/pcb/calculate-lineup-cost.py [--json]
Inputs: manufacturing/readiness/jlc-snapshot-2026-10-31.json (catalog tiers, assembly fee table), the release BOMs
of the current boards, the r3 and B20 generator specs, and manufacturing/readiness/pad-counts.json.
A line is bought at max(quantity x lot, first tier start) at the tier price for that purchase. Parts without an LCSC
code (B20 *_PROPOSED values) are UNKNOWN and counted, never estimated. PCB fabrication, shipping and duty are UNKNOWN.
These are catalog prices on the retrieval date, not quotes.
"""
import csv, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = json.loads((ROOT / 'manufacturing/readiness/jlc-snapshot-2026-10-31.json').read_text())
PARTS = SNAP['catalog']['parts']
FEES = SNAP['assembly_fees']
PADS = json.loads((ROOT / 'manufacturing/readiness/pad-counts.json').read_text())['boards']
NOT_ASSEMBLED = ('MH', 'TP', 'H')


def spec(name):
    s = importlib.util.spec_from_file_location(name, ROOT / f'scripts/schgen/{name}.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def spec_board(name, pcb=None):
    m = spec(name)
    lines, unknown, joints = {}, [], {'smd': 0, 'th': 0}
    pins = {}
    for n, ps in m.NETS.items():
        for p in ps:
            pins[p.split('.')[0]] = pins.get(p.split('.')[0], 0) + 1
    for p in getattr(m, 'NO_CONNECT', []):
        pins[p.split('.')[0]] = pins.get(p.split('.')[0], 0) + 1
    for ref, c in m.COMPONENTS.items():
        if c[0].startswith(('PogoPad', 'Conn_1x')) and not c[2]:
            continue
        if not c[2]:
            unknown.append(f'{ref} {c[1]}')
            continue
        lines.setdefault(c[2], []).append(ref)
        pc = PADS.get(pcb, {}).get(ref) if pcb else None
        if pc:
            joints['smd'] += pc['smd']; joints['th'] += pc['th']
        else:
            th = c[3].split(':')[1].startswith(('HDR-TH', 'WJ500V'))
            joints['th' if th else 'smd'] += pins.get(ref, 0)
    sides = {PADS[pcb][r]['side'] for r in PADS.get(pcb, {}) if not r.startswith(NOT_ASSEMBLED)} if pcb else {'F'}
    return {'lines': lines, 'unknown': unknown, 'joints': joints, 'double_sided': 'B' in sides}


def bom_board(path, pcb):
    lines, joints = {}, {'smd': 0, 'th': 0}
    for r in csv.DictReader(open(ROOT / path)):
        refs = [x.strip() for x in r['Designator'].split(',') if x.strip()]
        lines.setdefault(r['JLCPCB Part #'], []).extend(refs)
        for ref in refs:
            pc = PADS[pcb].get(ref, {'smd': 0, 'th': 0})
            joints['smd'] += pc['smd']; joints['th'] += pc['th']
    sides = {PADS[pcb][r]['side'] for rs in lines.values() for r in rs if r in PADS[pcb]}
    return {'lines': lines, 'unknown': [], 'joints': joints, 'double_sided': 'B' in sides}


def tier_price(code, qty):
    tiers = PARTS[code]['price_tiers_usd']
    buy = max(qty, tiers[0][0])
    for lo, hi, p in tiers:
        if buy >= lo and (hi == -1 or buy <= hi):
            return buy, p
    return buy, tiers[-1][2]


def board_cost(b, lot):
    parts = 0.0
    ext = 0
    rows = []
    for code, refs in sorted(b['lines'].items()):
        buy, p = tier_price(code, len(refs) * lot)
        parts += buy * p
        ext += PARTS[code]['library_type'] != 'base'
        rows.append({'lcsc': code, 'model': PARTS[code]['model'], 'qty_per_board': len(refs), 'buy': buy, 'unit_usd': p,
                     'line_usd': round(buy * p, 4), 'library': PARTS[code]['library_type'], 'stock': PARTS[code]['stock']})
    j = b['joints']
    if b['double_sided']:
        f = FEES['standard']
        asm = (f['setup_double'] + f['stencil_double'] + f['feeder_loading_each'] * len(b['lines']) + f['confirm_parts_placement']
               + j['smd'] * lot * f['smt_per_joint'] + j['th'] * lot * f['manual_per_joint'] + (f['hand_soldering_labor_per_order'] if j['th'] else 0))
        asm = max(asm, 0) + f['handling_min'] + (f['single_board_surcharge'] if lot == 1 else 0)
        kind = 'Standard PCBA, double-side'
    else:
        f = FEES['economic']
        asm = (f['setup'] + f['stencil'] + f['feeder_loading_extended_each'] * ext + f['confirm_parts_placement']
               + j['smd'] * lot * f['smt_per_joint'] + j['th'] * lot * f['manual_per_joint'] + (f['hand_soldering_labor_per_order'] if j['th'] else 0))
        kind = 'Economic PCBA, single-side'
    low_stock = [r['lcsc'] for r in rows if r['stock'] < r['buy']]
    return {'parts_usd': round(parts, 2), 'assembly_usd': round(asm, 2), 'assembly_kind': kind, 'lines': len(rows), 'extended_lines': ext,
            'unknown_parts': len(b['unknown']), 'joints_per_board': j, 'stock_below_purchase': low_stock, 'rows': rows}


BOARDS = {
    'current': {'Board P 15 V (as built)': bom_board('manufacturing/releases/corner-support-review/board-p/bom.csv', 'boards/board-p/board-p.kicad_pcb'),
                'Board B (current)': bom_board('manufacturing/releases/corner-support-review/board-b/bom.csv', 'boards/board-b/board-b.kicad_pcb')},
    'renewal': {'Board P r3 draft': spec_board('board_p_spec', 'boards/board-p/r3-draft/board-p-r3-draft.kicad_pcb'),
                'B20 paper draft': spec_board('board_b20_spec')},
}


def main():
    res = {}
    for lineup, boards in BOARDS.items():
        res[lineup] = {}
        for lot in (1, 5):
            per = {n: board_cost(b, lot) for n, b in boards.items()}
            res[lineup][f'lot_{lot}'] = {'boards': per, 'parts_usd': round(sum(p['parts_usd'] for p in per.values()), 2),
                                         'assembly_usd': round(sum(p['assembly_usd'] for p in per.values()), 2),
                                         'unknown_parts': sum(p['unknown_parts'] for p in per.values())}
        res[lineup]['unknown_list'] = {n: b['unknown'] for n, b in boards.items() if b['unknown']}
    if '--json' in sys.argv:
        print(json.dumps(res, indent=1)); return
    for lineup in res:
        for lot in (1, 5):
            r = res[lineup][f'lot_{lot}']
            print(f"{lineup:8s} lot {lot}: parts ${r['parts_usd']:.2f} (per set ${r['parts_usd'] / lot:.2f}), assembly ${r['assembly_usd']:.2f}, "
                  f"UNKNOWN parts {r['unknown_parts']}; PCB fabrication UNKNOWN")
            for n, b in r['boards'].items():
                print(f"    {n}: parts ${b['parts_usd']:.2f}, {b['lines']} lines ({b['extended_lines']} extended), {b['assembly_kind']} ${b['assembly_usd']:.2f}, "
                      f"joints {b['joints_per_board']}, stock below purchase {b['stock_below_purchase']}")


if __name__ == '__main__':
    main()
