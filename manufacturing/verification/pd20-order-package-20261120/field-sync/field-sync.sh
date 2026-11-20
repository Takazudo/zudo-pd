#!/bin/bash
# Local replica of .github/workflows/b20-field-sync.yml steps (same pinned image by digest).
set -euo pipefail
export PYTHONHASHSEED=0
IMAGE=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
REFS="$1"; D=scripts/pcb/board-b20; OUT=boards/board-b20-draft
T=/tmp/claude-0/campaign/native/fs; E=/tmp/claude-0/campaign/native/fs-evidence; rm -rf $T $E; mkdir -p $T $E
run() { flock /tmp/kicad-native.lock docker run --rm --pull=never --platform linux/amd64 --cpus 1 --user 0 -e PYTHONHASHSEED -v "$PWD":"$PWD" -v "$T":"$T" -w "$PWD" "$IMAGE" \
  bash -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec python3 "$@"' kicad-python "$@"; }
python3 scripts/schgen/gen_b20_components.py --check
cp "$OUT/board-b20-draft.kicad_pcb" "$T/before.kicad_pcb"
cp "$OUT/report-input-receipt.json" "$T/report-template.json"
run "$D/sync-fields.py" "$T/before.kicad_pcb" "$T/synced.kicad_pcb" "$REFS" | tee "$E/sync-fields.json"
python3 "$D/finalize_refill.py" "$T/synced.kicad_pcb" "$OUT/board-b20-draft.kicad_pcb" --project "$OUT/board-b20-draft.kicad_pro" --receipt "$OUT/refill-finalization.json"
python3 "$D/verify-field-sync.py" "$T/before.kicad_pcb" "$OUT/board-b20-draft.kicad_pcb" "$REFS" "$E/field-sync-verification.json"
run "$D/dump-geom.py" "$OUT/board-b20-draft.kicad_pcb" > "$T/final-geom.json"
run "$D/read-routed-copper.py" "$OUT/board-b20-draft.kicad_pcb" "$T/report-template.json" "$T/final-geom.json" "$T/final-routes.json" "$OUT/report-input-receipt.json"
python3 "$D/loop-check.py" "$T/final-geom.json" "$T/final-routes.json" "$OUT/loop-check.json" > /dev/null
python3 "$D/current-check.py" "$T/final-geom.json" "$T/final-routes.json" "$OUT/current-check.json" > /dev/null
python3 "$D/thermal-check.py" "$OUT/thermal-check.json"
python3 "$D/power-report.py"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); n=json.load(open(sys.argv[2])); assert (r["tracks"], r["vias"]) == (len(n["tracks"]), len(n["vias"])), "routing-report counts changed"' "$OUT/routing-report.json" "$T/final-routes.json"
echo FIELD-SYNC-PASS
