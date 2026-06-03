---
name: l-bump-version-y
description: "Bump the Y digit of this project's X.Y.Z version — a new JLCPCB PCBA order. Use when the user says 'bump version y', 'new JLCPCB order', 'l-bump-version-y', or is placing the next PCB order. Resets Z to 0, commits, tags, and creates a GitHub release."
argument-hint: [--notes "release notes"]
allowed-tools: Bash(bash .claude/scripts/bump-version.sh *), Bash(git *), Bash(gh *), Bash(cat VERSION)
---

> **Confirm before running.** This commits, pushes, tags, and creates a public GitHub release.
> Ask the user to confirm unless they clearly already asked to bump.

# l-bump-version-y — new JLCPCB order

Bumps **Y** in the project version `X.Y.Z`. Y = the Nth JLCPCB PCBA order (lifetime counter).
See `doc/docs/inbox/versioning.md` for the full scheme.

**Effect:** `0.4.0 → 0.5.0` (resets Z to 0) → commit `chore(version): bump to 0.5.0` →
annotated tag `v0.5.0` → push → **GitHub release `v0.5.0`**.

## Steps

1. Confirm the working tree is clean (`git status`). If dirty, ask the user to `/commits` first
   — the script refuses a dirty tree by default.
2. Show the current version: `cat VERSION`.
3. Run the bump:
   ```bash
   bash .claude/scripts/bump-version.sh y
   ```
   To add release notes (recommended — summarize what changed for this order):
   ```bash
   bash .claude/scripts/bump-version.sh y --notes "4th→5th order: <key changes>"
   ```
4. Report the new version, the tag, and the GitHub release URL (`gh release view v<new>`).

## Notes

- The script handles commit + tag + push + `gh release create`. Do not do these manually.
- If there is no upstream branch, the script pushes the tag and warns; push the branch yourself.
- Idempotency: the script aborts if the target tag already exists.
