"""Phase 12/13 (p15 rows: phases 14 and 17): part and assembly cost of the current lineup (Board P 15 V as built + Board B) against the renewal
lineup (Board P r3 draft + B20 paper draft), from the retained JLCPCB snapshot.

usage: python3 scripts/pcb/calculate-lineup-cost.py [--json]
Phase 33: the current lineup reads the current development review package (board-p15 + Board B under
manufacturing/releases/corner-support-review/). The as-built Board P BOM left that package in 658b377; the phase 14/17
board-p15 desk scenarios still start from it and read it from git history (AS_BUILT_P_BOM). Pads of a board missing
from pad-counts.json are counted from its PCB file (SMD / through-hole pads per footprint).
Inputs: manufacturing/readiness/jlc-snapshot-2026-10-31.json (catalog tiers, assembly fee table), the phase 13 B20
resolution manufacturing/readiness/b20-identity-resolution.json (distributor listings for the unbound *_PROPOSED values
and the like-for-like adders), the release BOMs of the current boards, the r3 and B20 generator specs, and
manufacturing/readiness/pad-counts.json.
A line is bought at max(quantity x lot, first tier start) at the tier price for that purchase. Parts without an LCSC
code and no resolved listing are UNKNOWN and counted, never estimated.
Assembly class (phase 13): a two-sided board can only use Standard PCBA (double-side rows); a one-sided board is priced
in both classes and the cheaper one is used, with both totals reported. Economic PCBA charges feeder loading only for
extended lines, Standard PCBA for every line. PCB fabrication, shipping and duty are UNKNOWN.
These are catalog prices on the retrieval date, not quotes.
"""
import csv, importlib.util, io, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = json.loads((ROOT / 'manufacturing/readiness/jlc-snapshot-2026-10-31.json').read_text())
PARTS = SNAP['catalog']['parts']
FEES = SNAP['assembly_fees']
RES = json.loads((ROOT / 'manufacturing/readiness/b20-identity-resolution.json').read_text())
PARTS = {**RES['catalog_phase33']['parts'], **RES['catalog']['parts'], **PARTS}
RESOLVED = {v: e['lcsc'] for v, e in RES['values'].items() if e['status'] == 'RESOLVED'}
PADS = json.loads((ROOT / 'manufacturing/readiness/pad-counts.json').read_text())['boards']
NOT_ASSEMBLED = ('MH', 'TP', 'H')


def spec(name):
    s = importlib.util.spec_from_file_location(name, ROOT / f'scripts/schgen/{name}.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def spec_board(name, pcb=None, resolve=False, adders=False):
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
        code = c[2] or (RESOLVED.get(c[1]) if resolve else None)
        if not code:
            unknown.append(f'{ref} {c[1]}')
            continue
        lines.setdefault(code, []).append(ref)
        pc = PADS.get(pcb, {}).get(ref) if pcb else None
        if pc:
            joints['smd'] += pc['smd']; joints['th'] += pc['th']
        else:
            th = c[3].split(':')[1].startswith(('HDR-TH', 'WJ500V', 'IDC-TH'))
            joints['th' if th else 'smd'] += pins.get(ref, 0)
    if adders:
        cur = PADS['boards/board-b/board-b.kicad_pcb']
        for a in RES['like_for_like_adders']['lines']:
            refs = [r.strip() for r in a['ref'].split(',')]
            lines.setdefault(a['lcsc'], []).extend(f'ADD-{r}' for r in refs)
            for r in refs:
                joints['smd'] += cur[r]['smd']; joints['th'] += cur[r]['th']
    sides = {PADS[pcb][r]['side'] for r in PADS.get(pcb, {}) if not r.startswith(NOT_ASSEMBLED)} if pcb else {'F'}
    return {'lines': lines, 'unknown': unknown, 'joints': joints, 'double_sided': 'B' in sides}


AS_BUILT_P_BOM = ('658b377^', 'manufacturing/releases/corner-support-review/board-p/bom.csv')


def pcb_pads(pcb):
    sys.path.insert(0, str(ROOT / 'scripts/schgen'))
    from sexp import atom, find_all, load
    out = {}
    for fp in find_all(load(ROOT / pcb), 'footprint'):
        ref = next(atom(p[2]) for p in find_all(fp, 'property') if atom(p[1]) == 'Reference')
        kinds = [atom(pad[2]) for pad in find_all(fp, 'pad')]
        layer = atom(find_all(fp, 'layer')[0][1])
        out[ref] = {'smd': kinds.count('smd'), 'th': kinds.count('thru_hole'), 'side': layer[0]}
    return out


def bom_board(path, pcb):
    lines, joints = {}, {'smd': 0, 'th': 0}
    if pcb not in PADS:
        PADS[pcb] = pcb_pads(pcb)
    if isinstance(path, tuple):
        text = subprocess.run(['git', 'show', f'{path[0]}:{path[1]}'], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    else:
        text = (ROOT / path).read_text()
    for r in csv.DictReader(io.StringIO(text)):
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
    nl = len(b['lines'])
    th = j['th'] * lot * FEES['standard']['manual_per_joint'] + (FEES['standard']['hand_soldering_labor_per_order'] if j['th'] else 0)
    f = FEES['standard']
    sides = 'double' if b['double_sided'] else 'single'
    std = (f[f'setup_{sides}'] + f[f'stencil_{sides}'] + f['feeder_loading_each'] * nl + f['confirm_parts_placement']
           + j['smd'] * lot * f['smt_per_joint'] + th + f['handling_min'] + (f['single_board_surcharge'] if lot == 1 else 0))
    classes = {f'Standard PCBA, {sides}-side': round(std, 2)}
    if not b['double_sided']:
        e = FEES['economic']
        classes['Economic PCBA, single-side'] = round(e['setup'] + e['stencil'] + e['feeder_loading_extended_each'] * ext
                                                      + e['confirm_parts_placement'] + j['smd'] * lot * e['smt_per_joint'] + th, 2)
    kind = min(classes, key=classes.get)
    asm = classes[kind]
    low_stock = [r['lcsc'] for r in rows if r['stock'] < r['buy']]
    return {'parts_usd': round(parts, 2), 'assembly_usd': round(asm, 2), 'assembly_kind': kind, 'assembly_classes_usd': classes, 'lines': len(rows), 'extended_lines': ext,
            'unknown_parts': len(b['unknown']), 'joints_per_board': j, 'stock_below_purchase': low_stock, 'rows': rows}


BOARDS = {
    'current': {'Board P 15 V (board-p15 package)': bom_board('manufacturing/releases/corner-support-review/board-p15/bom.csv', 'boards/board-p15/board-p15-draft.kicad_pcb'),
                'Board B (current)': bom_board('manufacturing/releases/corner-support-review/board-b/bom.csv', 'boards/board-b/board-b.kicad_pcb')},
    'renewal': {'Board P r3 draft': spec_board('board_p_spec', 'boards/board-p/r3-draft/board-p-r3-draft.kicad_pcb'),
                'B20 paper draft': spec_board('board_b20_spec', resolve=True)},
    'renewal_like_for_like': {'Board P r3 draft': spec_board('board_p_spec', 'boards/board-p/r3-draft/board-p-r3-draft.kicad_pcb'),
                              'B20 + current-Board-B adders': spec_board('board_b20_spec', resolve=True, adders=True)},
}
# lever check (phase 13): Board P r3 one-sided would allow Economic PCBA, but the top-only placement leaves 20 parts
# unplaced (boards/board-p/r3-draft/search-top-only.json); this row prices that infeasible board for the saving only
_p1 = dict(BOARDS['renewal']['Board P r3 draft'], double_sided=False)
AS_BUILT_P = bom_board(AS_BUILT_P_BOM, 'boards/board-p/board-p.kicad_pcb')
BOARDS['lever_board_p_r3_one_sided_infeasible'] = {'Board P r3 one-sided (does not fit)': _p1,
                                                    'B20 + current-Board-B adders': BOARDS['renewal_like_for_like']['B20 + current-Board-B adders']}


def p15_variant(full_block, double_sided=False):
    # phase 14 desk scenarios for the separate 15 V product; refs and LCSC codes follow board_p_spec.py (r3 controller block)
    b = AS_BUILT_P
    lines = {k: list(v) for k, v in b['lines'].items()}
    joints = dict(b['joints'])
    lines.pop('C23162')                              # R15/R16 I2C pull-ups move to the jig (R1.3)
    joints['smd'] -= 4
    lines['C17414'].remove('R21'); lines.pop('C17414')
    lines['C21189'].append('R21')                    # R21 becomes the 0R RESET strap (R1.1)
    if full_block:
        add = {'C23162': ['R13'], 'C21190': ['R14', 'R28', 'R29'], 'C25803': ['R31', 'R32'], 'C15849': ['C38'],
               'C192739': ['D9', 'D11', 'D12'], 'C260890': ['D10'], 'C40912': ['Q6']}
        lines['C23179'] = ['R30']
        for code, refs in add.items():
            lines.setdefault(code, []).extend(refs)
        joints['smd'] += 2 * 10 + 3                  # ten two-terminal parts and the SOT-23 cascode
    return {'lines': lines, 'unknown': [], 'joints': joints, 'double_sided': double_sided}


def p15_phase17():
    # phase 17/18 draft (board_p15_spec.py): the RESET subset, R22/R23 100k SCL/SDA pull-downs, the R29/R30 + D9 VDD feed and C38
    b = p15_variant(False)
    for code, refs in {'C25803': ['R22', 'R23'], 'C21190': ['R29'], 'C23179': ['R30'], 'C192739': ['D9'], 'C15849': ['C38']}.items():
        b['lines'].setdefault(code, []).extend(refs)
    b['joints']['smd'] += 2 * 6   # phase 18 adds C38 on the existing C15849 line
    return b


BOARDS['p15_as_built'] = {'Board P 15 V (as built)': AS_BUILT_P}
BOARDS['p15_reset_subset'] = {'Board P 15 V + R1.1-R1.3 RESET/I2C subset': p15_variant(False)}
BOARDS['p15_full_block_one_sided'] = {'Board P 15 V + full controller block, top only (fit NOT RUN)': p15_variant(True)}
BOARDS['p15_full_block_two_sided'] = {'Board P 15 V + full controller block, two-sided': p15_variant(True, True)}
BOARDS['p15_phase17_draft'] = {'Board P 15 V phase 17 draft (RESET subset + I2C pull-downs + VDD feed)': p15_phase17()}
BOARDS['current_p15_phase17'] = {'Board P 15 V phase 17 draft': p15_phase17(),
                                 'Board B (current)': BOARDS['current']['Board B (current)']}

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
