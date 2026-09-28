#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: check-generated-diff.sh <generated-path> [...]" >&2
  exit 2
fi

# Include untracked output, then compare with the committed tree. Comparing the
# index with the worktree misses tracked deletions after intent-to-add stages
# them; HEAD catches edits, removals and newly generated files alike.
git add --intent-to-add -A -- "$@"
git diff --exit-code HEAD -- "$@"
