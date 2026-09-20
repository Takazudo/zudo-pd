#!/usr/bin/env bash
# Export a kicad-cli netlist for a board and diff it against the board spec's
# expected net table via verify_netlist.py.
#
# Usage: scripts/schgen/verify.sh <board-a|board-b|board-p>
#
# Exit codes:
#   0  PASS, or kicad-cli is not installed (prints a SKIPPED marker and
#      degrades gracefully — this is a local-only check, CI has no KiCad)
#   1  FAIL: netlist mismatch, missing schematic, or bad usage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

board="${1:-}"
case "$board" in
  board-a|board-b|board-p) ;;
  *)
    echo "Usage: $(basename "$0") <board-a|board-b|board-p>" >&2
    exit 1
    ;;
esac

# Check kicad-cli availability before the schematic file even exists — this
# check must degrade to SKIPPED regardless of whether the board has been
# created yet (Board A / Board B are ported as their own sub-issues; this
# toolchain must still behave sanely against a not-yet-existing board).
if ! command -v kicad-cli >/dev/null 2>&1; then
  echo "SKIPPED: kicad-cli not found on PATH — install KiCad to run the netlist-verify" \
       "step locally (see scripts/schgen/README.md); CI never runs this check."
  exit 0
fi

spec_module="${board//-/_}_spec"
sch_file="$REPO_ROOT/boards/$board/$board.kicad_sch"

if [[ ! -f "$sch_file" ]]; then
  echo "FAIL: no schematic at $sch_file" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
netlist_file="$tmp_dir/$board.net"

echo "exporting netlist for $board via kicad-cli..."
kicad-cli sch export netlist --format kicadsexpr --output "$netlist_file" "$sch_file"

python3 "$SCRIPT_DIR/verify_netlist.py" "$spec_module" "$netlist_file"
