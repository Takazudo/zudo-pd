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
pnpm test:circuit
pnpm test:compatibility
python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
pnpm check
pnpm build
pnpm check:site
pnpm circuit:check-generated
