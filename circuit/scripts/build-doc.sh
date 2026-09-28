#!/usr/bin/env bash
set -euo pipefail
mkdir -p .circuit-cache
pnpm --dir doc build 2>&1 | tee "${ZUDO_DOC_BUILD_LOG:-.circuit-cache/doc-build.log}"
