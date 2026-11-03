"""P15P: read-only catalog refresh and quantity scenarios for the first P15 r1 prototype order.

usage:
  python3 scripts/pcb/p15-order-scenarios.py --refresh   # read-only JLCPCB parts search; writes the snapshot below
  python3 scripts/pcb/p15-order-scenarios.py [--json]    # price the scenarios from the retained snapshot

Reads the fixed-revision development review package (manufacturing/releases/corner-support-review/, git_base
3b9821b) BOMs and prices them with the assembly model of calculate-lineup-cost.py (board_cost), replacing only the
catalog rows with the refreshed snapshot. The assembly fee table is the 2026-10-31 extract; the fee page still read
"Last updated on Oct 22, 2026" on the refresh date. Catalog prices and stock change daily; these are not quotes.
PCB fabrication, the fabrication minimum quantity, shipping and duty are UNKNOWN and never estimated.
"""
import datetime, hashlib, importlib.util, json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / 'manufacturing/readiness/jlc-snapshot-2026-11-03-p15.json'
PACKAGE = ROOT / 'manufacturing/releases/corner-support-review'
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'

# Units needed per use (P15P decision packet). Board B counts are new boards only; reused S3 boards are not priced.
SCENARIOS = {
    'A_led_only': {'note': 'P15 for the two existing Board Ls; no new Board B', 'board-p15': 2, 'board-b': 0},
    'B_led_plus_pd_reuse_s3': {'note': '2 LED + 2 zudo-pd (paired with on-hand S3 Board Bs) + 1 spare P15; no new Board B',
                               'board-p15': 5, 'board-b': 0},
    'C_led_plus_pd_new_b2': {'note': '2 LED + 2 zudo-pd + 1 spare P15; 2 new Board Bs', 'board-p15': 5, 'board-b': 2},
    'D_old_five_sets': {'note': 'Reference only: the 2026-11-02 five-set estimate (5 P15 + 5 new Board B)',
                        'board-p15': 5, 'board-b': 5},
}


def lineup():
    s = importlib.util.spec_from_file_location('lineup', ROOT / 'scripts/pcb/calculate-lineup-cost.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def bom_codes():
    m = lineup()
    return m, {'board-p15': m.bom_board(str((PACKAGE / 'board-p15/bom.csv').relative_to(ROOT)), 'boards/board-p15/board-p15-draft.kicad_pcb'),
               'board-b': m.bom_board(str((PACKAGE / 'board-b/bom.csv').relative_to(ROOT)), 'boards/board-b/board-b.kicad_pcb')}


def refresh():
    _, boards = bom_codes()
    codes = sorted({c for b in boards.values() for c in b['lines']})
    parts, raw = {}, hashlib.sha256()
    for code in codes:
        req = urllib.request.Request(API, data=json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 25}).encode(),
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'zudo-pd read-only parts lookup'})
        body = urllib.request.urlopen(req, timeout=30).read()
        raw.update(body)
        rows = json.loads(body)['data']['componentPageInfo']['list'] or []
        hit = next((r for r in rows if r.get('componentCode') == code), None)
        if hit is None:
            parts[code] = {'status': 'NOT FOUND'}
            continue
        parts[code] = {'model': hit.get('componentModelEn'), 'brand': hit.get('componentBrandEn'), 'package': hit.get('componentSpecificationEn'),
                       'library_type': hit.get('componentLibraryType'), 'stock': hit.get('stockCount'),
                       'price_tiers_usd': [[p['startNumber'], p['endNumber'], p['productPrice']] for p in hit.get('componentPrices') or []]}
    snap = {'_comment': 'Read-only JLCPCB parts search for the P15 r1 + Board B package BOM lines. No cart, quote, upload or order. '
                        'Prices and stock are volatile catalog values, not quotes.',
            'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
            'endpoint': API, 'raw_sha256': raw.hexdigest(), 'parts': parts}
    SNAPSHOT.write_text(json.dumps(snap, indent=1) + '\n')
    print(f'wrote {SNAPSHOT.relative_to(ROOT)}: {len(parts)} lines')


def price():
    m, boards = bom_codes()
    snap = json.loads(SNAPSHOT.read_text())
    missing = [c for c, p in snap['parts'].items() if p.get('status') == 'NOT FOUND' or not p.get('price_tiers_usd')]
    if missing:
        raise SystemExit(f'unpriced lines (UNKNOWN, not estimated): {missing}')
    m.PARTS.update(snap['parts'])
    out = {'retrieved_utc': snap['retrieved_utc'], 'scenarios': {}, 'stock': {}}
    for code, p in snap['parts'].items():
        refs = {n: len(b['lines'][code]) for n, b in boards.items() if code in b['lines']}
        out['stock'][code] = {'model': p['model'], 'stock': p['stock'], 'per_board': refs}
    for name, sc in SCENARIOS.items():
        per = {b: m.board_cost(boards[b], sc[b]) for b in ('board-p15', 'board-b') if sc[b]}
        total = round(sum(v['parts_usd'] + v['assembly_usd'] for v in per.values()), 2)
        out['scenarios'][name] = {'note': sc['note'], 'assembled': {b: sc[b] for b in ('board-p15', 'board-b')},
                                  'boards': {b: {k: v[k] for k in ('parts_usd', 'assembly_usd', 'assembly_kind', 'stock_below_purchase')} for b, v in per.items()},
                                  'parts_and_assembly_usd': total,
                                  'unknown': 'PCB fabrication (and its minimum quantity), shipping and duty'}
    if '--json' in sys.argv:
        print(json.dumps(out, indent=1)); return
    print(f"catalog retrieved {snap['retrieved_utc']} (not a quote)")
    for name, r in out['scenarios'].items():
        print(f"{name}: P15 x{r['assembled']['board-p15']}, new Board B x{r['assembled']['board-b']}: USD {r['parts_and_assembly_usd']:.2f} parts+assembly")
        for b, v in r['boards'].items():
            print(f"    {b}: parts {v['parts_usd']:.2f}, {v['assembly_kind']} {v['assembly_usd']:.2f}, stock below purchase {v['stock_below_purchase']}")


if __name__ == '__main__':
    refresh() if '--refresh' in sys.argv else price()
