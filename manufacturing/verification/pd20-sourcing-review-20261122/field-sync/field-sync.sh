#!/bin/bash
# Local replica of .github/workflows/b20-field-sync.yml steps (same pinned image by digest), preceded by the
# geometry-identical footprint-identity rebind of the four B20 zeners (sync-footprint-identity.py).
# usage: field-sync.sh WORKDIR  (run from the repository root on the pre-adoption PCB)
set -euo pipefail
export PYTHONHASHSEED=0
IMAGE=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
REFS=C10,C13,CI12,CI5,D4,DZ1,DZ2,DZ3,R16,R17,R21,R22,R23,R31,R33,R35,R42,R6,RDG12,RDG5,RLM2,RLV1,RVX1,U11,U12
ZENERS=D4,DZ1,DZ2,DZ3
D=scripts/pcb/board-b20; OUT=boards/board-b20-draft; E=manufacturing/verification/pd20-sourcing-review-20261122/field-sync
T="$1"; mkdir -p "$T"
run() { docker run --rm --pull=never --platform linux/amd64 --cpus 1 --user 0 -e PYTHONHASHSEED -v "$PWD":"$PWD" -v "$T":"$T" -w "$PWD" "$IMAGE" \
  bash -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec python3 "$@"' kicad-python "$@"; }
python3 scripts/schgen/gen_b20_components.py --check
cp "$OUT/board-b20-draft.kicad_pcb" "$T/original.kicad_pcb"
cp "$OUT/report-input-receipt.json" "$T/report-template.json"
python3 "$D/sync-footprint-identity.py" "$T/original.kicad_pcb" "$T/before.kicad_pcb" \
  zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD zudo-pd:SOD-123_Pad0.90x0.95mm_P3.15mm "$ZENERS" "$E/footprint-identity.json" > /dev/null
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
