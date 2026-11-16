#!/usr/bin/env bash
# Local credential-free gate for the documentation workspace. Mirrors the
# mandatory steps of .github/workflows/pr-checks.yml; deployment is never run.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/led-b4push-XXXXXX")"
cleanup() {
  case "$LOG_DIR" in
    */led-b4push-*) rm -rf "$LOG_DIR" ;;
    *) echo "refusing to clean an unexpected log path: $LOG_DIR" >&2 ;;
  esac
}
trap cleanup EXIT

step() { printf '\n== %s ==\n' "$1"; }

step "evidence validator, unit tests and forward tests"
pnpm circuit:project-check

step "host type check and zudo-wind audit"
pnpm --dir doc check
pnpm --dir doc check:wind

step "host script tests"
pnpm --dir doc test:scripts

step "published models and footprint previews"
pnpm --dir doc check:models
pnpm --dir doc check:footprint-previews

step "enclosure viewer geometry"
pnpm --dir doc check:enclosure-viewer

step "build (enclosure viewer, models, component pages, site)"
BUILD_LOG="$LOG_DIR/doc-build.log"
if ! pnpm build >"$BUILD_LOG" 2>&1; then
  cat "$BUILD_LOG"
  exit 1
fi
grep -v 'zfb warn: ' "$BUILD_LOG" | tail -20 || true

step "hand-authored links (zfb warning gate)"
bash doc/scripts/check-zfb-link-warnings.sh "$BUILD_LOG"

step "built site: component references, publication scan, images, anchors, Mermaid"
pnpm check:site

step "component generation is deterministic (second run, read-only)"
pnpm --dir doc check:components

step "docs-to-agent corpus scan"
pnpm --dir doc scan:doc-skill

step "generated output is committed"
git add --intent-to-add -A -- doc/src/content/docs circuit/generated/preflight.json doc/public/assets/component-previews
if ! git diff --quiet -- doc/src/content/docs circuit/generated/preflight.json doc/public/assets/component-previews; then
  git diff --stat -- doc/src/content/docs circuit/generated/preflight.json doc/public/assets/component-previews
  echo "generated output differs from the committed tree; commit the regenerated files" >&2
  exit 1
fi

echo
echo "b4push: all credential-free gates passed (browser smoke runs separately: pnpm test:browser)"
