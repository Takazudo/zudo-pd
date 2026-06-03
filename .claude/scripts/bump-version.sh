#!/usr/bin/env bash
# Bump the project version in VERSION, commit, tag, and (for x/y) make a GitHub release.
#
# Usage: bump-version.sh <x|y|z> [--notes "release notes body"]
#
# Version scheme X.Y.Z (see doc/docs/inbox/versioning.md):
#   X = product release (resets Z; KEEPS Y — Y is a lifetime JLCPCB-order counter)
#   Y = Nth JLCPCB order (resets Z; tag + GitHub release)
#   Z = local checkpoint tag (tag only, no GitHub release)
#
# Runs from anywhere inside the repo. Refuses to run with a dirty tree unless --allow-dirty.
set -euo pipefail

PART="${1:-}"
shift || true

NOTES=""
ALLOW_DIRTY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --notes) NOTES="${2:-}"; shift 2 ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

case "$PART" in
  x|y|z) ;;
  *) echo "Usage: bump-version.sh <x|y|z> [--notes \"...\"]" >&2; exit 2 ;;
esac

# Locate repo root and VERSION file.
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
VERSION_FILE="$ROOT/VERSION"

if [ ! -f "$VERSION_FILE" ]; then
  echo "ERROR: $VERSION_FILE not found. Create it with a baseline (e.g. 0.4.0) first." >&2
  exit 1
fi

CUR="$(tr -d '[:space:]' < "$VERSION_FILE")"
if ! printf '%s' "$CUR" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: VERSION '$CUR' is not X.Y.Z" >&2
  exit 1
fi

X="${CUR%%.*}"
REST="${CUR#*.}"
Y="${REST%%.*}"
Z="${REST#*.}"

case "$PART" in
  x) X=$((X+1)); Z=0 ;;          # product release; Y kept on purpose
  y) Y=$((Y+1)); Z=0 ;;          # new JLCPCB order
  z) Z=$((Z+1)) ;;               # local checkpoint
esac

NEW="${X}.${Y}.${Z}"
TAG="v${NEW}"

if [ "$ALLOW_DIRTY" -ne 1 ]; then
  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: working tree is dirty. Commit/stash first, or pass --allow-dirty." >&2
    git status --short >&2
    exit 1
  fi
fi

if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
  echo "ERROR: tag ${TAG} already exists." >&2
  exit 1
fi

echo "Bumping ${CUR} -> ${NEW} (part: ${PART})"

printf '%s\n' "$NEW" > "$VERSION_FILE"
git add "$VERSION_FILE"
git commit -m "chore(version): bump to ${NEW}"

# Annotated tag.
DEFAULT_MSG="${TAG}"
case "$PART" in
  y) DEFAULT_MSG="${TAG} — JLCPCB order #${Y}" ;;
  x) DEFAULT_MSG="${TAG} — product release ${X}.x" ;;
  z) DEFAULT_MSG="${TAG} — local checkpoint" ;;
esac
git tag -a "$TAG" -m "$DEFAULT_MSG"

# Push commit + tag (best-effort; report if no upstream).
if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  git push && git push origin "$TAG"
else
  echo "WARN: no upstream tracking branch; pushing tag only."
  git push origin "$TAG" || echo "WARN: tag push failed; push manually."
fi

# GitHub release for x and y only.
if [ "$PART" = "x" ] || [ "$PART" = "y" ]; then
  if command -v gh >/dev/null 2>&1; then
    BODY="${NOTES:-$DEFAULT_MSG}"
    gh release create "$TAG" --title "$TAG" --notes "$BODY" \
      && echo "GitHub release ${TAG} created." \
      || echo "WARN: gh release failed; create manually: gh release create ${TAG}"
  else
    echo "WARN: gh CLI not found; skipped GitHub release for ${TAG}."
  fi
else
  echo "Z bump: git tag only, no GitHub release (by design)."
fi

echo "Done: ${NEW} (tag ${TAG})."
