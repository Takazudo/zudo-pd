#!/usr/bin/env bash
set -euo pipefail

# Scan the docs-to-agent skill output for denied evidence values.
#
# `setup:doc-skill` exposes this site's content to Claude Code and Codex as a
# lookup skill. That makes it a publication surface: whatever the generated
# component pages contain is what an agent reads back, and it reads it as
# reference material rather than as a web page.
#
# The script writes to `$HOME/.claude/skills` and `$HOME/.codex/skills` by
# design. This harness therefore runs it with HOME pointed at a throwaway
# directory, and verifies afterwards that the real ones were not touched — an
# epic acceptance criterion and a hard safety rule. It never passes --target
# auto, because auto probes $HOME.
#
# The isolated corpus is assembled here rather than scanned through the skill's
# own `docs` symlink: that symlink resolves to the MAIN worktree by design (so
# it survives worktree removal), and what needs scanning is the content of the
# checkout being tested.

DOC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

real_home_state() {
  # Listing, not content: enough to prove nothing was created, removed or
  # repointed, without reading anything inside the user's own skills.
  { ls -la "$HOME/.claude/skills" 2>/dev/null || echo "(absent)"; } | sort
  { ls -la "$HOME/.codex/skills" 2>/dev/null || echo "(absent)"; } | sort
}

BEFORE="$(real_home_state)"

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/component-docs-doc-skill-XXXXXX")"

# Guarded because the cleanup is a recursive delete of a variable: an empty or
# reassigned SANDBOX would take the whole of $TMPDIR with it.
cleanup() {
  case "$SANDBOX" in
    */component-docs-doc-skill-*) rm -rf "$SANDBOX" ;;
    *) echo "refusing to clean an unexpected sandbox path: $SANDBOX" >&2 ;;
  esac
}
trap cleanup EXIT

mkdir -p "$SANDBOX/home"

echo "== running setup:doc-skill with HOME=$SANDBOX/home =="
HOME="$SANDBOX/home" bash "$DOC_ROOT/scripts/setup-doc-skill.sh" --silent --target claude \
  >"$SANDBOX/setup.log" 2>&1 || {
  echo "setup:doc-skill failed:" >&2
  cat "$SANDBOX/setup.log" >&2
  exit 1
}

SKILL_DIR="$SANDBOX/home/.claude/skills/doc-wisdom"
if [ ! -e "$SKILL_DIR/SKILL.md" ]; then
  echo "expected a generated SKILL.md under the sandbox HOME, found none" >&2
  exit 1
fi

AFTER="$(real_home_state)"
if [ "$BEFORE" != "$AFTER" ]; then
  echo "setup:doc-skill modified the real user-global skill directories" >&2
  diff <(printf '%s\n' "$BEFORE") <(printf '%s\n' "$AFTER") >&2 || true
  exit 1
fi
echo "== real \$HOME/.claude/skills and \$HOME/.codex/skills unchanged =="

# The corpus an agent would actually read: the generated skill definition plus
# this checkout's content tree.
CORPUS="$SANDBOX/corpus"
mkdir -p "$CORPUS"
cp "$SKILL_DIR/SKILL.md" "$CORPUS/SKILL.md"
cp -r "$DOC_ROOT/src/content/docs" "$CORPUS/docs"

echo "== scanning the isolated corpus =="
"$DOC_ROOT/node_modules/.bin/zudo-circuit-doc" scan \
  --config "$DOC_ROOT/../circuit.config.ts" --agent-skill "$CORPUS"
