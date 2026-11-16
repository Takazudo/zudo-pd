#!/usr/bin/env bash
set -euo pipefail

# ── setup-doc-skill.sh ─────────────────────────────────
# Creates an agent skill that exposes your zudo-doc
# documentation as a knowledge base, then symlinks it into
# the user-scope skills directory (~/.claude/skills/ and/or
# ~/.codex/skills/).
# ────────────────────────────────────────────────────────

TARGET_MODE="auto"

# Accept --silent (alias -y) for parity with the consuming-site convention:
# scaffolded sites expose `setup:doc-skill-silent` = `bash scripts/setup-doc-skill.sh
# --silent`. This script is already non-interactive (the skill name is deterministic
# — see below), so the flag is a no-op here; it is consumed only so it is never
# mistaken for the positional skill-name override (`$1`).
while [ $# -gt 0 ]; do
  case "$1" in
    --silent|-y) shift ;;
    --target)
      shift
      if [ $# -eq 0 ]; then
        echo "Error: --target requires one of: auto, claude, codex, both" >&2
        exit 1
      fi
      TARGET_MODE="$1"
      shift
      ;;
    --target=*)
      TARGET_MODE="${1#--target=}"
      shift
      ;;
    --) shift; break ;;
    -*) echo "Error: unknown flag '$1'" >&2; exit 1 ;;
    *) break ;;
  esac
done

case "$TARGET_MODE" in
  auto|claude|codex|both) ;;
  *)
    echo "Error: --target must be one of: auto, claude, codex, both" >&2
    exit 1
    ;;
esac

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Read project name from package.json
PROJECT_NAME=$(node -e "console.log(require('$ROOT_DIR/package.json').name || 'my-project')")
DEFAULT_SKILL_NAME="${PROJECT_NAME}-wisdom"

echo ""
echo "=== zudo-doc Skill Setup ==="
echo ""

# Skill name is DETERMINISTIC: always `<projectName>-wisdom`. The scaffolded
# .gitignore (emitted by create-zudo-doc) hard-codes this exact name, so the
# generated skill directory must match it — an interactive prompt would let the
# name drift from the gitignore entry and leave the skill showing as untracked
# (zudolab/zudo-doc#2173). An explicit override is still allowed via the first
# CLI arg or the SKILL_NAME env var (consumers who override must also update
# their .gitignore), but never via an interactive prompt.
SKILL_NAME="${1:-${SKILL_NAME:-$DEFAULT_SKILL_NAME}}"

# Validate skill name (allow only alphanumeric, hyphens, underscores)
if [[ ! "$SKILL_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "Error: Skill name may only contain letters, numbers, hyphens, and underscores."
  exit 1
fi

# Resolve the main repo root (handles git worktrees correctly)
# Use the main worktree path so symlinks survive worktree removal
REPO_ROOT="$(git -C "$ROOT_DIR" worktree list | head -1 | awk '{print $1}')"

# Path from the repository root to the project directory: "" at the repo
# root, "doc/" (trailing slash) when the project lives in a subdirectory
# (nested layout, #2918). `rev-parse --show-prefix` is relative to the
# CURRENT worktree's top level, so combining it with REPO_ROOT (the MAIN
# worktree root, above) reconstructs the equivalent path there even when
# running from inside a different worktree.
PROJECT_PREFIX="$(git -C "$ROOT_DIR" rev-parse --show-prefix)"
MAIN_PROJECT_DIR="$REPO_ROOT/${PROJECT_PREFIX}"
MAIN_PROJECT_DIR="${MAIN_PROJECT_DIR%/}"
REPO_DOCS_DIR="$REPO_ROOT/${PROJECT_PREFIX}src/content/docs"
REPO_DOCS_JA_DIR="$REPO_ROOT/${PROJECT_PREFIX}src/content/docs-ja"

DOCS_DIR="$ROOT_DIR/src/content/docs"

# Validate docs directory exists
if [ ! -d "$DOCS_DIR" ]; then
  echo "Error: Documentation directory not found at $DOCS_DIR"
  exit 1
fi

# Helper: replace a symlink or file at the given path
ensure_symlink() {
  local link_path="$1"
  local target="$2"
  if [ -L "$link_path" ] || [ -e "$link_path" ]; then
    rm -rf "$link_path"
  fi
  ln -s "$target" "$link_path"
}

DOCS_JA_DIR="$ROOT_DIR/src/content/docs-ja"
HAS_JA=""
if [ -d "$DOCS_JA_DIR" ]; then
  HAS_JA="true"
fi

# Discover top-level doc categories dynamically
DOC_TREE=""
for dir in "$DOCS_DIR"/*/; do
  [ -d "$dir" ] || continue
  dirname="$(basename "$dir")"
  DOC_TREE="${DOC_TREE}- ${dirname}/
"
done

# The SKILL.md "Format"/"Verify" steps must only reference commands that
# actually exist on the running project's package.json — a fresh
# create-zudo-doc scaffold has no format script at all, while this repo's own
# showcase exposes `format` (there is no `format:md` script anywhere, #2918).
# `format:md` is checked too in case a downstream project defines its own
# script under that literal name.
FORMAT_SCRIPT="$(node -e "
const scripts = (require('$ROOT_DIR/package.json').scripts) || {};
console.log(
  scripts.format ? 'format'
  : scripts['format:mdx'] ? 'format:mdx'
  : scripts['format:md'] ? 'format:md'
  : ''
);
")"
if [ -n "$FORMAT_SCRIPT" ]; then
  FORMAT_STEP="Run \`pnpm $FORMAT_SCRIPT\` to format the new/changed MDX files."
else
  FORMAT_STEP="No format script is configured for this project; formatting is optional."
fi

# Name the project directory explicitly so the instruction resolves correctly
# even when the project is nested inside a larger git repo (running `pnpm
# build` from the outer repo root would otherwise invoke the wrong
# package.json, #2918).
VERIFY_STEP="Run \`pnpm build\` from \`$MAIN_PROJECT_DIR\` to confirm the site builds correctly."

resolve_targets() {
  case "$TARGET_MODE" in
    claude) echo "claude" ;;
    codex) echo "codex" ;;
    both) echo "claude codex" ;;
    auto)
      local has_claude=""
      local has_codex=""
      [ -d "$HOME/.claude" ] && has_claude="true"
      [ -d "$HOME/.codex" ] && has_codex="true"

      if [ "$has_claude" = "true" ] && [ "$has_codex" = "true" ]; then
        echo "claude codex"
      elif [ "$has_codex" = "true" ]; then
        echo "codex"
      else
        # Preserve the historical default for fresh machines and test homes.
        echo "claude"
      fi
      ;;
  esac
}

generate_skill() {
  local target="$1"
  local project_skills_dir="$ROOT_DIR/.$target/skills"
  local skill_dir="$project_skills_dir/$SKILL_NAME"
  local global_skills_dir="$HOME/.$target/skills"
  local assistant_label

  case "$target" in
    claude) assistant_label="Claude Code" ;;
    codex) assistant_label="Codex" ;;
    *) echo "Error: unknown target '$target'" >&2; exit 1 ;;
  esac

  mkdir -p "$skill_dir"

  ensure_symlink "$skill_dir/docs" "$REPO_DOCS_DIR"
  echo "  [$target] Created docs symlink -> $REPO_DOCS_DIR"

  if [ "$HAS_JA" = "true" ]; then
    ensure_symlink "$skill_dir/docs-ja" "$REPO_DOCS_JA_DIR"
    echo "  [$target] Created docs-ja symlink -> $REPO_DOCS_JA_DIR"
  fi

  cat > "$skill_dir/SKILL.md" << SKILLEOF
---
name: $SKILL_NAME
description: >-
  Search and reference documentation from the $PROJECT_NAME project.
  Use when answering questions about $PROJECT_NAME features, configuration,
  components, or usage patterns.
user-invocable: true
argument-hint: "[-u|--update] [topic keyword, e.g., 'configuration', 'sidebar', 'i18n']"
---

# $PROJECT_NAME Documentation Reference

Look up documentation from the $PROJECT_NAME project for $assistant_label.
Documentation base path: \`src/content/docs\` (relative to the project root: \`$MAIN_PROJECT_DIR\`)

## Mode Detection

Parse the argument string for flags:

- If args start with \`-u\` or \`--update\`: enter **Update mode** (see below)
- Otherwise: enter **Lookup mode** (default)

Strip the flag from the remaining argument to get the topic keyword.

## Lookup Mode (default)

1. Find the relevant article(s) from the \`docs/\` directory based on the topic
2. Read ONLY the specific article(s) you need — do NOT load all articles at once
3. Apply the information from the article when answering the user's question
4. Mention the source article path so the user can find it for further reading

## Update Mode (\`-u\` / \`--update\`)

The user has new information and wants to add or update documentation in this repo.

### Workflow

1. **Understand the new info**: Ask the user what they learned or want to
   document. The topic keyword (if provided) hints at the subject area.
2. **Find existing docs**: Search the \`docs/\` directory for articles related to
   the topic. Read them to understand what is already covered.
3. **Decide create vs update**: If an existing article covers the topic, update
   it. Otherwise, create a new \`.mdx\` file in the appropriate subdirectory.
4. **Write the content**: Follow the doc-authoring rules in this project's CLAUDE.md (\`$MAIN_PROJECT_DIR/CLAUDE.md\`):
   - Required frontmatter: \`title\` (string). Always set \`sidebar_position\`.
     Optional: \`description\`, \`sidebar_label\`, \`tags\`, etc.
   - Do NOT use \`# h1\` in content — the frontmatter \`title\` renders as h1.
     Start with \`## h2\` headings.
   - Use available MDX components (\`<Note>\`, \`<Tip>\`, \`<Info>\`, \`<Warning>\`,
     \`<Danger>\`, \`<HtmlPreview>\`) where appropriate.
   - For live demos, use \`<HtmlPreview>\` with \`js\`/\`displayJs\` props.
   - Link to other docs using relative paths with \`.mdx\` extension.
5. **Update Japanese docs**: Create or update the corresponding file under
   \`docs-ja/\` mirroring the English directory structure. Keep code blocks,
   Mermaid diagrams, and \`<HtmlPreview>\` blocks identical — only translate
   surrounding prose. Exception: pages with \`generated: true\` skip translation.
6. **Format**: ${FORMAT_STEP}
7. **Verify**: ${VERIFY_STEP}

## Documentation Structure

The documentation is organized in MDX files under \`docs/\`:

\`\`\`
${DOC_TREE}\`\`\`

Browse the \`docs/\` directory to discover available articles. Each \`.mdx\` file
has YAML frontmatter with \`title\` and \`description\` fields that help identify
the right article to read.
SKILLEOF

  if [ "$HAS_JA" = "true" ]; then
    cat >> "$skill_dir/SKILL.md" << JAEOF

## Japanese Documentation

Japanese translations are available under \`docs-ja/\`. When the user is working
in Japanese or asks for Japanese content, prefer articles from \`docs-ja/\`.
JAEOF
  fi

  echo "  [$target] Generated SKILL.md"

  mkdir -p "$global_skills_dir"
  ensure_symlink "$global_skills_dir/$SKILL_NAME" "$skill_dir"

  echo "  [$target] Project skill: $skill_dir"
  echo "  [$target] Global symlink: $global_skills_dir/$SKILL_NAME"
}

read -r -a TARGETS <<< "$(resolve_targets)"
echo "Target: $TARGET_MODE -> ${TARGETS[*]}"
echo ""

for target in "${TARGETS[@]}"; do
  generate_skill "$target"
done

echo ""
echo "Done! Skill '$SKILL_NAME' is ready."
echo ""
echo "Use --target claude, --target codex, or --target both to override auto-detection."
echo "In Claude Code, use: /$SKILL_NAME <topic>"
echo "In Codex, mention the skill by name when asking about this documentation."
echo ""
