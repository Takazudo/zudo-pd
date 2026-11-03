#!/bin/bash
# Board P r3 draft (unvalidated; power-path pours, ground pours and grid-routed signals). Rebuilds boards/board-p/r3-draft/ from board_p_spec.py.
# The as-built boards/board-p/board-p.kicad_pcb is only read. Every step is pcbnew python (--cpus 1, no KiCad lock); only the native DRC below takes the lock.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$(dirname "$0")/../../.."
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
T=$(mktemp -d "${TMPDIR:-/tmp}/board-p-r3.XXXXXX")
D=scripts/pcb/board-p-r3-draft
OUT=boards/board-p/r3-draft
mkdir -p "$OUT"
NAMES=$(python3 -c "
import importlib.util;s=importlib.util.spec_from_file_location('s','scripts/schgen/board_p_spec.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(' '.join(sorted({c[3].split(':')[1] for c in m.COMPONENTS.values()})))")
run() { docker run --rm --cpus 1 --user 0 -v "$PWD":/w -v "$T":/t -w /w "$IMG" "$@"; }
run python3 /w/$D/dump-asbuilt.py boards/board-p/board-p.kicad_pcb > "$T/asbuilt.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));json.dump({r['ref']:[r['x'],r['y'],r['rot']] for r in d},open(sys.argv[2],'w'))" "$T/asbuilt.json" "$T/asbuilt-pos.json"
run python3 /w/$D/footprint-sizes.py footprints/kicad/zudo-power.pretty $NAMES > "$T/fpsize.json"
python3 $D/strip-asbuilt.py boards/board-p/board-p.kicad_pcb "$T/asbuilt-stripped.kicad_pcb"
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-top-only.json" top 25 "$OUT/floorplan.json" 2>/dev/null
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-two-sided.json" both 25 "$OUT/floorplan.json" 2>/dev/null
run python3 /w/$D/build-draft.py /w /w/$OUT/board-p-r3-draft.kicad_pcb /w/$OUT/placement-report.json /t/asbuilt-stripped.kicad_pcb /t/asbuilt-pos.json /w/$OUT/search-two-sided.json
docker run --rm --cpus 1 --user 0 -v "$PWD":/w -w /w "$IMG" python3 /w/$D/dump-geom.py $OUT/board-p-r3-draft.kicad_pcb > "$T/geom.json"
cp "$OUT/board-p-r3-draft.kicad_pcb" "$T/placed.kicad_pcb"
# the router is deterministic per seed (canonical pad order, PYTHONHASHSEED=0); run the pass-shuffle seeds four at a
# time and keep the result with the fewest open signal connections (ties: lowest seed)
SEEDS="${R3_SEEDS:-12 14 16 20}"   # phase 13 tried 12-20; none closes every connection, 16 and 20 leave one
set -- $SEEDS
while [ $# -gt 0 ]; do
  batch=""; for k in 1 2 3 4; do [ $# -gt 0 ] && { batch="$batch $1"; shift; }; done
  for seed in $batch; do R3_SEED=$seed python3 $D/route-signals.py "$T/geom.json" "$OUT/pours.json" "$T/routes-$seed.json" 20 60 > "$T/route-$seed.log" 2>&1 & done
  wait
  best=$(python3 -c "import json,sys; r=[(len(json.load(open(sys.argv[1]+'/routes-'+s+'.json'))['report']['unrouted']),int(s)) for s in sys.argv[2:]]; print(min(r)[0], min(r)[1])" "$T" $(ls "$T" | sed -n 's/^routes-\([0-9]*\)\.json$/\1/p'))
  [ "${best%% *}" = 0 ] && break
done
cp "$T/routes-${best##* }.json" "$OUT/routes.json"
echo "router: seed ${best##* }, ${best%% *} open signal connections"
# phase 13: pours, then join any GND cluster the fills left detached and rebuild from the placed board (at most 4 joins)
for i in 1 2 3 4 5; do
  cp "$T/placed.kicad_pcb" "$OUT/board-p-r3-draft.kicad_pcb"
  docker run --rm --cpus 1 --user 0 -v "$PWD":/w -w /w "$IMG" sh -c "python3 /w/$D/apply-tracks.py $OUT/board-p-r3-draft.kicad_pcb $OUT/routes.json && python3 /w/$D/route-power.py $OUT/board-p-r3-draft.kicad_pcb $OUT/routing-report.json $OUT/pours.json"
  python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))['gnd_clusters_detached'] else 1)" "$OUT/routing-report.json" || break
  [ "$i" = 5 ] && break
  R3_JOIN_REPORT="$OUT/routing-report.json" R3_JOIN_ROUTES="$OUT/routes.json" python3 $D/route-signals.py "$T/geom.json" "$OUT/pours.json" "$T/routes-join.json" 20 60
  mv "$T/routes-join.json" "$OUT/routes.json"
done
python3 $D/annotate-fit.py "$OUT"
# DRC (native, under the lock): kicad-cli pcb drc --format json --severity-all on $OUT/board-p-r3-draft.kicad_pcb
cp boards/board-p/fp-lib-table "$OUT/fp-lib-table" && sed -i "s#\${KIPRJMOD}/../../footprints#\${KIPRJMOD}/../../../footprints#" "$OUT/fp-lib-table"
