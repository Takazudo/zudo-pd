"""Flag PD20 BOM lines whose JLC catalog row may not cover an order. Reads retained lookups only; no network.

usage: stock-review.py AVAILABILITY_JSON [PAIRS]   (PAIRS defaults to 2)

A line is flagged when stock is zero, below PAIRS x placements + the row's `lossNumber`, or below the row's
`minPurchaseNum` or `leastPatchNumber`. JLC does not publicly document `lossNumber` / `leastPatchNumber`, and
whether `minPurchaseNum` binds a standard-PCBA order is not established; the flags are prompts for the owner's quote
review, not shortages proven by the supplier.
"""
import json, sys

data = json.load(open(sys.argv[1]))
pairs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
lines = {}
for board, rows in data['boards'].items():
    for r in rows:
        line = lines.setdefault(r['lcsc'], {'comment': r['comment'], 'placements': []})
        line['placements'] += [f'{board}:{ref}' for ref in r['refs']]
flagged = []
for code, line in sorted(lines.items()):
    row = data['parts'][code]
    if 'stock' not in row:
        flagged.append({'lcsc': code, 'comment': line['comment'], 'reasons': ['lookup returned no exact row']})
        continue
    per_set = len(line['placements'])
    need = pairs * per_set + (row.get('lossNumber') or 0)
    reasons = []
    if not row['stock']:
        reasons.append('zero stock')
    elif row['stock'] < need:
        reasons.append(f'stock below {pairs} x placements + lossNumber')
    for field in ('minPurchaseNum', 'leastPatchNumber'):
        if row['stock'] and (row.get(field) or 0) > row['stock']:
            reasons.append(f'stock below {field}')
    if reasons:
        flagged.append({'lcsc': code, 'comment': line['comment'], 'model': row.get('model'), 'placements': line['placements'],
                        'stock': row['stock'], 'need_for_pairs': need, 'lossNumber': row.get('lossNumber'),
                        'minPurchaseNum': row.get('minPurchaseNum'), 'leastPatchNumber': row.get('leastPatchNumber'),
                        'retrieved_utc': row['retrieved_utc'], 'reasons': reasons})
print(json.dumps({'_comment': __doc__.splitlines()[0], 'pairs': pairs, 'lines_checked': len(lines),
                  'flagged': flagged}, indent=1))
