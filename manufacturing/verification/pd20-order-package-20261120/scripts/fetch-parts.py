"""Read-only JLC catalog lookups for the PD20 package BOMs. Not a quote, cart or order.

usage: fetch-parts.py RELEASE_DIR EVIDENCE_DIR > parts-availability.json
"""
import csv, datetime, hashlib, json, subprocess, sys
from pathlib import Path

API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
release, evidence = Path(sys.argv[1]), Path(sys.argv[2])
(evidence / 'jlc').mkdir(parents=True, exist_ok=True)
out = {'_comment': __doc__.splitlines()[0], 'jlc_endpoint': API, 'boards': {}, 'parts': {}}
for board in ('board-p', 'board-b20-draft'):
    rows = []
    for r in csv.DictReader((release / board / 'bom.csv').open()):
        refs = [x.strip() for x in r['Designator'].split(',') if x.strip()]
        rows.append({'lcsc': r['JLCPCB Part #'], 'comment': r['Comment'], 'refs': refs})
    out['boards'][board] = rows
codes = sorted({r['lcsc'] for rows in out['boards'].values() for r in rows})
for code in codes:
    t = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    body = subprocess.run(['curl', '-sS', '-m', '30', '-H', 'Content-Type: application/json', '-A', 'read-only parts lookup',
                           '--data', json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 25}), API],
                          capture_output=True).stdout
    (evidence / 'jlc' / f'{code}.json').write_bytes(body)
    try:
        hit = next((x for x in json.loads(body)['data']['componentPageInfo']['list'] or [] if x.get('componentCode') == code), None)
    except Exception:
        hit = None
    if hit:
        rec = {'retrieved_utc': t, 'raw_sha256': hashlib.sha256(body).hexdigest(), 'model': hit.get('componentModelEn'),
               'brand': hit.get('componentBrandEn'), 'package': hit.get('componentSpecificationEn'),
               'library_type': hit.get('componentLibraryType'), 'stock': hit.get('stockCount'),
               'leastPatchNumber': hit.get('leastPatchNumber'), 'lossNumber': hit.get('lossNumber'),
               'minPurchaseNum': hit.get('minPurchaseNum'),
               'price_tiers_usd': [[p['startNumber'], p['endNumber'], p['productPrice']] for p in hit.get('componentPrices') or []]}
    else:
        rec = {'retrieved_utc': t, 'status': 'NOT FOUND / UNAVAILABLE'}
    out['parts'][code] = rec
print(json.dumps(out, indent=1, sort_keys=True))
