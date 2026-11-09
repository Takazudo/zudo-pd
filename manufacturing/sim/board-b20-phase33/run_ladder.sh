#!/bin/bash
# Run isolated solver attempts; source decks are never modified, including on interruption.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/run_ladder.py" "$@"
