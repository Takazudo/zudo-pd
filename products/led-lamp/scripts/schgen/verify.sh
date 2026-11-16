#!/usr/bin/env bash
# Export a kicad-cli netlist for a board and diff it against the board spec's
# expected net table via verify_netlist.py.
#
# Usage: scripts/schgen/verify.sh <board-p|board-l|swd-adapter>
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
  board-p|board-l|swd-adapter) ;;
  *)
    echo "Usage: $(basename "$0") <board-p|board-l|swd-adapter>" >&2
    exit 1
    ;;
esac

spec_module="${board//-/_}_spec"
sch_file="$REPO_ROOT/boards/$board/$board.kicad_sch"

if [[ ! -f "$sch_file" ]]; then
  echo "FAIL: no schematic at $sch_file" >&2
  exit 1
fi

if ! command -v kicad-cli >/dev/null 2>&1; then
  echo "SKIPPED: kicad-cli not found on PATH — install KiCad to run the netlist-verify" \
       "step locally (see scripts/schgen/README.md); CI never runs this check."
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
netlist_file="$tmp_dir/$board.net"

echo "exporting netlist for $board via kicad-cli..."
kicad-cli sch export netlist --format kicadsexpr --output "$netlist_file" "$sch_file"

python3 "$SCRIPT_DIR/verify_netlist.py" "$spec_module" "$netlist_file"

# The fitted switch is present in the normal PCB netlist.
if [[ "$board" == "board-l" ]]; then
  python3 "$SCRIPT_DIR/verify_power_switch.py" --netlist "$netlist_file"
fi
