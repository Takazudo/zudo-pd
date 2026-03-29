#!/usr/bin/env bash
set -euo pipefail

START_TIME=$(date +%s)
FAILURES=()
TOTAL_STEPS=3
CURRENT_STEP=0

step() {
  CURRENT_STEP=$((CURRENT_STEP + 1))
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ Step $CURRENT_STEP/$TOTAL_STEPS: $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; FAILURES+=("$1"); }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── Step 1: Type checking (astro sync + format + tsc) ──
# Runs first because astro sync generates MDX files that
# need formatting before the format check step.
step "Type checking (astro sync + tsc)"
if (cd "$ROOT_DIR" && pnpm check); then
  pass "Type checking passed"
else
  fail "Type checking"
fi

# ── Step 2: Format check (MDX) ─────────────────────────
# Must run AFTER step 1 so generated files are formatted.
step "Format check (MDX)"
if (cd "$ROOT_DIR" && pnpm run format:check:mdx); then
  pass "Format check passed"
else
  fail "Format check"
fi

# ── Step 3: Build ──────────────────────────────────────
step "Build (astro build)"
if (cd "$ROOT_DIR" && pnpm build); then
  pass "Build passed"
else
  fail "Build"
fi

# ── Summary ────────────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY (${DURATION}s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#FAILURES[@]} -eq 0 ]; then
  echo "✅ All $TOTAL_STEPS checks passed! Safe to push."
  exit 0
else
  echo "❌ ${#FAILURES[@]} check(s) failed:"
  for f in "${FAILURES[@]}"; do
    echo "   - $f"
  done
  exit 1
fi
