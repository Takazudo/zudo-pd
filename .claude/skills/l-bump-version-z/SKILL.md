---
name: l-bump-version-z
description: "Bump the Z digit of this project's X.Y.Z version — a local checkpoint tag. Use when the user says 'bump version z', 'tag a checkpoint', 'l-bump-version-z'. Commits and creates a git tag ONLY (no GitHub release)."
argument-hint: ""
allowed-tools: Bash(bash .claude/scripts/bump-version.sh *), Bash(git *), Bash(cat VERSION)
---

> **Confirm before running.** This commits, pushes, and creates a git tag. Confirm with the
> user unless they clearly asked to bump.

# l-bump-version-z — local checkpoint

Bumps **Z** in the project version `X.Y.Z`. Z = an ad-hoc local checkpoint, tagged whenever a
point in the work is worth marking. See `doc/docs/inbox/versioning.md`.

**Effect:** `0.4.0 → 0.4.1` → commit `chore(version): bump to 0.4.1` → annotated tag
`v0.4.1` → push. **No GitHub release** (git tag only, by design — that's what separates Z from
X/Y bumps).

## Steps

1. Confirm the working tree is clean (`git status`). If dirty, ask the user to `/commits` first.
2. Show the current version: `cat VERSION`.
3. Run the bump:
   ```bash
   bash .claude/scripts/bump-version.sh z
   ```
4. Report the new version and tag (`git tag --list 'v*' --sort=-v:refname | head -1`).

## Notes

- Z tag only — intentionally no `gh release`. Use `/l-bump-version-y` for a JLCPCB order or
  `/l-bump-version-x` for a product release when you want a GitHub release.
