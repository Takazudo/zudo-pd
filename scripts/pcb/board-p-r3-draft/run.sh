#!/bin/bash
# Board P r3 draft (unvalidated; power-path pours, ground pours and grid-routed signals). Rebuilds the Board P PCB
# boards/board-p/board-p.kicad_pcb (PD20 binding: the exported board-p) and the reports in boards/board-p/r3-draft/ from
# board_p_spec.py. The outline, connectors and holes come from the routed 15 V as-built PCB, read from git history at
# AS_BUILT_REV. Invoke the entire workflow under the heavy guard and native lock; see README.md.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$(dirname "$0")/../../.."
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
T=$(mktemp -d "${TMPDIR:-/tmp}/board-p-r3.XXXXXX")
D=scripts/pcb/board-p-r3-draft
OUT=boards/board-p/r3-draft
mkdir -p "$OUT"
# the last commit whose boards/board-p/board-p.kicad_pcb is the routed 15 V as-built module (PD20 replaced it with r3)
AS_BUILT_REV=6cb02c8
git show "$AS_BUILT_REV:boards/board-p/board-p.kicad_pcb" > "$T/asbuilt.kicad_pcb"
NAMES=$(python3 -c "
import importlib.util;s=importlib.util.spec_from_file_location('s','scripts/schgen/board_p_spec.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(' '.join(sorted({c[3].split(':')[1] for c in m.COMPONENTS.values()})))")
# wx needs a display (finish_details.py), so a broadway GTK backend runs inside the container, as in board-b20/run.sh
run() { docker run --rm --cpus 1 --user 0 -v "$PWD":/w -v "$T":/t -w /w "$IMG" \
  bash -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec "$@"' run "$@"; }
# Mandatory focused regressions in the same pinned native workflow. No tool skip is a pass.
run python3 /w/$D/test-native-connectivity.py
python3 $D/test-routing-fixed-groups.py
python3 $D/test-correction-contract.py
run python3 /w/$D/dump-asbuilt.py /t/asbuilt.kicad_pcb > "$T/asbuilt.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));json.dump({r['ref']:[r['x'],r['y'],r['rot']] for r in d},open(sys.argv[2],'w'))" "$T/asbuilt.json" "$T/asbuilt-pos.json"
run python3 /w/$D/footprint-sizes.py footprints/kicad/zudo-power.pretty $NAMES > "$T/fpsize.json"
python3 $D/strip-asbuilt.py "$T/asbuilt.kicad_pcb" "$T/asbuilt-stripped.kicad_pcb"
# The committed search results are the placement of record: a library courtyard refresh re-runs the heuristic search into
# a different placement that the router may not close (PD20: VREG_2V7 at U1.23 stayed open on 16 seeds). Re-run the
# search only on request (R3_SEARCH=1); build-draft.py and DRC then check the fixed placement against current footprints.
if [ "${R3_SEARCH:-0}" = 1 ] || [ ! -f "$OUT/search-two-sided.json" ]; then
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-top-only.json" top 25 "$OUT/floorplan.json" 2>/dev/null
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-two-sided.json" both 25 "$OUT/floorplan.json" 2>/dev/null
fi
# Never inherit an untracked/default project when pcbnew loads and fills the
# generated board. Both native load basenames use the canonical project rules.
cp boards/board-p/board-p.kicad_pro "$T/asbuilt-stripped.kicad_pro"
cp boards/board-p/board-p.kicad_pro "$OUT/board-p-r3-draft.kicad_pro"
run python3 /w/$D/build-draft.py /w /w/$OUT/board-p-r3-draft.kicad_pcb /w/$OUT/placement-report.json /t/asbuilt-stripped.kicad_pcb /t/asbuilt-pos.json /w/$OUT/search-two-sided.json
docker run --rm --cpus 1 --user 0 -v "$PWD":/w -w /w "$IMG" python3 /w/$D/dump-geom.py $OUT/board-p-r3-draft.kicad_pcb > "$T/geom.json"
cp "$OUT/board-p-r3-draft.kicad_pcb" "$T/placed.kicad_pcb"
# the router is deterministic per seed (canonical pad order, PYTHONHASHSEED=0); run the pass-shuffle seeds four at a
# time and keep the result with the fewest open signal connections (ties: lowest seed)
SEEDS="${R3_SEEDS:-12 14 16 20}"   # retained historical seed set; current completion is measured below
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
# A completed process is not a routed board. Keep the candidate local on failure;
# never replace the canonical Board P with an incomplete result.
python3 - "$OUT/routes.json" "$OUT/routing-report.json" <<'PY_CHECK'
import json, sys
routes, power = (json.load(open(path)) for path in sys.argv[1:])
if routes['report']['unrouted']: raise ValueError(routes['report']['unrouted'])
if power['gnd_clusters_detached']: raise ValueError(power['gnd_clusters_detached'])
PY_CHECK
# Board-specific probe legends are a reviewed final artwork stage. Preserve
# filled copper and compare all non-artwork serialization before promotion.
run python3 /w/$D/test-finish-details.py /w/$OUT/board-p-r3-draft.kicad_pcb
run python3 /w/$D/finish_details.py /w/$OUT/board-p-r3-draft.kicad_pcb /w/$OUT/board-p-r3-finished.kicad_pcb
mv "$OUT/board-p-r3-finished.kicad_pcb" "$OUT/board-p-r3-draft.kicad_pcb"
mv "$OUT/board-p-r3-finished.proposal.json" "$OUT/probe-silk-check.json"
python3 $D/annotate-fit.py "$OUT"
# PD20: the routed draft becomes the Board P PCB; boards/board-p/board-p.kicad_pro keeps the project's rules and the
# schematic pairing, so the draft-local project files are not kept
mv "$OUT/board-p-r3-draft.kicad_pcb" boards/board-p/board-p.kicad_pcb
rm -f "$OUT/board-p-r3-draft.kicad_pro" "$OUT/board-p-r3-draft.kicad_prl" "$OUT/fp-lib-table"
# DRC (native, under the lock): kicad-cli pcb drc --schematic-parity --format json --severity-all on boards/board-p/board-p.kicad_pcb
