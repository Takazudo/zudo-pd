#!/usr/bin/env bash
set -euo pipefail

# One outer machine-wide guard covers the complete local gate. CI has no
# Codex guard installed and runs the same sequence directly.
if [[ "${ZUDO_B4PUSH_GUARDED:-0}" != "1" ]]; then
  HEAVY_GUARD="${HOME}/.codex/scripts/heavy-guard.sh"
  if [[ -x "$HEAVY_GUARD" ]]; then
    export ZUDO_B4PUSH_GUARDED=1
    exec bash "$HEAVY_GUARD" -- bash "$0"
  fi
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

pnpm circuit:check
python3 circuit/orchestration/campaigns/pd-led-20261117-integration/c5_dev_site.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261117-integration -p 'test_c5_editorial.py'
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261117-integration -p 'test_c5_catalog_navigation.py'
python3 circuit/orchestration/campaigns/pd-led-20261117-integration/c3_c5_decisions.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261117-integration -p 'test_c3_c5_decisions.py'
python3 circuit/orchestration/campaigns/pd-led-20261117-integration/c3_c5_item_review.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261117-integration -p 'test_c3_c5_item_review.py'
pnpm test:circuit
pnpm test:compatibility
bash circuit/scripts/run-python-gates.sh
pnpm check
pnpm build
pnpm check:site
pnpm circuit:check-generated
