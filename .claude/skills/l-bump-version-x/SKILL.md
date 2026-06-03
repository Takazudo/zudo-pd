---
name: l-bump-version-x
description: "Bump the X digit of this project's X.Y.Z version — a real product release. Use when the user says 'bump version x', 'product release', 'l-bump-version-x'. Resets Z to 0, KEEPS Y (lifetime JLCPCB-order counter), commits, tags, and creates a GitHub release."
argument-hint: [--notes "release notes"]
allowed-tools: Bash(bash .claude/scripts/bump-version.sh *), Bash(git *), Bash(gh *), Bash(cat VERSION)
---

> **Confirm before running.** This is a product-level release: commits, pushes, tags, and
> creates a public GitHub release. Always confirm with the user first.

# l-bump-version-x — product release

Bumps **X** in the project version `X.Y.Z`. X = the product's own release version (currently 0
— nothing shipped yet). See `doc/docs/inbox/versioning.md`.

**Effect:** e.g. `0.5.2 → 1.5.0` — increments X, resets Z to 0, and **keeps Y** (Y is a
lifetime JLCPCB-order counter and does not reset). Then commit → annotated tag `v1.5.0` →
push → **GitHub release `v1.5.0`**.

:::note Y is intentionally kept
Unlike standard semver, an X bump does NOT reset Y here, because Y means "Nth JLCPCB order
ever." If the user wants Y to reset on a product release, edit `.claude/scripts/bump-version.sh`.
:::

## Steps

1. Confirm the working tree is clean (`git status`). If dirty, ask the user to `/commits` first.
2. Show the current version: `cat VERSION`.
3. Confirm with the user that this is a real product release (X bumps are rare).
4. Run the bump:
   ```bash
   bash .claude/scripts/bump-version.sh x --notes "Product release: <summary>"
   ```
5. Report the new version, tag, and GitHub release URL (`gh release view v<new>`).
