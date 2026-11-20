#!/bin/bash
# usage: drc.sh board.kicad_pcb  -> stage dir tmp/d2s, report tmp/d2s/drc.json
set -e
S=tmp/d2s; rm -rf $S; mkdir -p $S
cp "$1" $S/board-b20-draft.kicad_pcb
for f in board-b20-draft.kicad_pro board-b20-draft.kicad_sch fp-lib-table sym-lib-table; do cp boards/board-b20-draft/$f $S/; done
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
docker run --rm --platform linux/amd64 --cpus 2 --user 0 -v "$PWD":"$PWD" -w "$PWD" --entrypoint /bin/bash $IMG -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec kicad-cli "$@"' kicad-cli pcb drc --refill-zones --save-board --schematic-parity --format json --severity-all -o $S/drc.json $S/board-b20-draft.kicad_pcb > $S/drc.log 2>&1 || true
tail -3 $S/drc.log
python3 - <<'PY'
import json,collections
r=json.load(open('tmp/d2s/drc.json'))
print('violations',len(r['violations']),'unconnected',len(r['unconnected_items']),'parity',len(r['schematic_parity']))
c=collections.Counter((v['severity'],v['type']) for v in r['violations']); print(c)
for v in r['violations'][:60]:
    if v['type']!='lib_footprint_mismatch': print(v['type'],v['severity'],[ (i['description'][:70],i['pos']) for i in v['items']])
for v in r['unconnected_items'][:20]: print('UNC',[(i['description'][:60],i['pos']) for i in v['items']])
for v in r['schematic_parity'][:20]: print('PAR',v['type'],[i['description'][:80] for i in v['items']])
PY
