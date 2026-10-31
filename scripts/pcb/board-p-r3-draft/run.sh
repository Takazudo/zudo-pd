#!/bin/bash
# Board P r3 draft (unvalidated; power-path pours and ground only, signals unrouted). Rebuilds boards/board-p/r3-draft/ from board_p_spec.py.
# The as-built boards/board-p/board-p.kicad_pcb is only read. Serialise the KiCad steps through the shared lock.
set -euo pipefail
cd "$(dirname "$0")/../../.."
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
T=$(mktemp -d "${TMPDIR:-/tmp}/board-p-r3.XXXXXX")
D=scripts/pcb/board-p-r3-draft
OUT=boards/board-p/r3-draft
mkdir -p "$OUT"
NAMES=$(python3 -c "
import importlib.util;s=importlib.util.spec_from_file_location('s','scripts/schgen/board_p_spec.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(' '.join(sorted({c[3].split(':')[1] for c in m.COMPONENTS.values()})))")
run() { flock /tmp/kicad-native.lock docker run --rm --user 0 -v "$PWD":/w -v "$T":/t -w /w "$IMG" "$@"; }
run python3 /w/$D/dump-asbuilt.py boards/board-p/board-p.kicad_pcb > "$T/asbuilt.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));json.dump({r['ref']:[r['x'],r['y'],r['rot']] for r in d},open(sys.argv[2],'w'))" "$T/asbuilt.json" "$T/asbuilt-pos.json"
run python3 /w/$D/footprint-sizes.py footprints/kicad/zudo-power.pretty $NAMES > "$T/fpsize.json"
python3 $D/strip-asbuilt.py boards/board-p/board-p.kicad_pcb "$T/asbuilt-stripped.kicad_pcb"
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-top-only.json" top 25 "$OUT/floorplan.json" 2>/dev/null
python3 $D/search-placement.py . "$T/fpsize.json" "$T/asbuilt.json" "$OUT/search-two-sided.json" both 25 "$OUT/floorplan.json" 2>/dev/null
run python3 /w/$D/build-draft.py /w /w/$OUT/board-p-r3-draft.kicad_pcb /w/$OUT/placement-report.json /t/asbuilt-stripped.kicad_pcb /t/asbuilt-pos.json /w/$OUT/search-two-sided.json
docker run --rm --cpus 1 --user 0 -v "$PWD":/w -w /w "$IMG" python3 /w/$D/route-power.py /w/$OUT/board-p-r3-draft.kicad_pcb /w/$OUT/routing-report.json
python3 $D/annotate-fit.py "$OUT"
# DRC (native, under the lock): kicad-cli pcb drc --format json --severity-all on $OUT/board-p-r3-draft.kicad_pcb
cp boards/board-p/fp-lib-table "$OUT/fp-lib-table" && sed -i "s#\${KIPRJMOD}/../../footprints#\${KIPRJMOD}/../../../footprints#" "$OUT/fp-lib-table"
