#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

GENERATED_PATHS=(
  doc/src/content/docs/components
  circuit/generated/preflight.json
  doc/public/assets/component-previews
)

check_against_git() {
  bash circuit/scripts/check-generated-diff.sh "${GENERATED_PATHS[@]}"
}

# `build` performs the first projection. Re-run the complete configured
# preparation twice so the committed pages, preflight report and selected
# models are current and the second projection is byte-identical.
pnpm circuit:prepare
check_against_git
pnpm circuit:prepare
check_against_git

echo "generated output: committed and deterministic across two preparations"
