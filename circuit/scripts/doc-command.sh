#!/usr/bin/env bash
set -euo pipefail

CIRCUIT_DOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../doc" && pwd)"
cd "$CIRCUIT_DOC_ROOT"
# A root pnpm lifecycle leaves INIT_CWD pointing at the workspace root. The
# history CLI resolves relative content paths there before checking cwd.
# Start a fresh doc lifecycle so history uses this host's content directory.
unset INIT_CWD
exec pnpm "$@"
