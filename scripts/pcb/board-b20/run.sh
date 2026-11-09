#!/bin/bash
# B20 draft (unvalidated): placement with stage templates, grid routing, GND pours. Rebuilds
# boards/board-b20-draft/board-b20-draft.kicad_pcb and boards/board-b20-draft/routing-report.json from board_b20_spec.py.
# Phase 28: 4 copper layers (In1.Cu GND plane, In2.Cu routed, JLC7628 stackup); B20_LAYERS=2 rebuilds the retired 2-layer form.
# Phase 30: desk current/width (current-check.json) and thermal (thermal-check.json) screens of the routed draft.
# pcbnew steps run in the pinned KiCad image (--cpus 1, no KiCad lock); the router runs on the host.
# Native DRC is separate and runs under heavy-guard -> flock /tmp/kicad-native.lock (see the draft doc).
set -euo pipefail
export PYTHONHASHSEED=0
cd "$(dirname "$0")/../../.."
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
T=$(mktemp -d "${TMPDIR:-/tmp}/board-b20.XXXXXX")
D=scripts/pcb/board-b20
OUT=boards/board-b20-draft
# wx needs a display, so a broadway GTK backend runs inside the container
run() { docker run --rm --cpus 1 --user 0 -e PYTHONHASHSEED -v "$PWD":"$PWD" -v "$T":"$T" -w "$PWD" "$IMG" \
  bash -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec python3 "$@"' kicad-python "$@"; }
run $D/build-draft.py "$T/placed.kicad_pcb"
run $D/dump-geom.py "$T/placed.kicad_pcb" > "$T/geom.json"
uv run --python 3.12 --with numpy --with scipy python $D/route.py "$T/geom.json" "$T/routes.json"
run $D/apply-routes.py "$T/placed.kicad_pcb" "$T/routes.json" "$OUT/board-b20-draft.kicad_pcb"
# Reports describe saved native copper, including post-routing cleanup and filled-plane stitches.
run $D/dump-geom.py "$OUT/board-b20-draft.kicad_pcb" > "$T/final-geom.json"
run $D/read-routed-copper.py "$OUT/board-b20-draft.kicad_pcb" "$T/routes.json" "$T/final-geom.json" "$T/final-routes.json" "$OUT/report-input-receipt.json"
python3 $D/loop-check.py "$T/final-geom.json" "$T/final-routes.json" "$OUT/loop-check.json" > /dev/null
python3 $D/current-check.py "$T/final-geom.json" "$T/final-routes.json" "$OUT/current-check.json" > /dev/null
python3 $D/thermal-check.py "$OUT/thermal-check.json"
python3 -c "import json,sys; r=json.load(open(sys.argv[1])); n=json.load(open(sys.argv[2])); json.dump({'tracks': len(n['tracks']), 'vias': len(n['vias']), 'counts_source': 'saved native PCB after cleanup and zone stitching', 'router_tracks': len(r['tracks']), 'router_vias': len(r['vias']), 'unrouted': r['unrouted'], 'notes': r['notes']}, open(sys.argv[3], 'w'), indent=1)" "$T/routes.json" "$T/final-routes.json" "$OUT/routing-report.json"
echo "B20 draft rebuilt in $OUT"
