---
title: Current Component Asset Procedure
sidebar_position: 2
---

Resolve manufacturer, complete MPN/package suffix, supplier code and placement through the exact inventory and
owner bundle before acquiring anything. [Component catalog](/docs/components/catalog/) is the generated human view;
archived BOM pages are historical evidence, not current identity sources.

## Acquire and inspect one exact asset

1. Follow `circuit/WORKFLOW.md` Workflow C/D and the component audit's `references/new-component-workflow.md`.
   Reuse retained evidence when applicable; distinguish manufacturer authority, distributor identity and availability.
2. Check the configured library roots and model paths in `circuit.config.ts`. Prefer exact vendor assets; pin an
   official KiCad library release if using it. An EasyEDA import is an inspection candidate, not a verified land pattern.
3. If the optional importer is installed, inspect its local `--help` before use. The workflow's example imports into
   `.circuit-cache/cad/<part>` with `--lcsc_id <C-number> --footprint --symbol --3d --output <path>`; substitute a resolved
   inventory identity, never an archived worked-example part.
4. Retain provider, original filename, retrieval date, hash and fidelity (`exact-vendor`, `family`, `derived`, `unavailable`)
   in a CAD receipt. Check pin/pad numbering, polarity, exposed pad, dimensions and model datums against the exact drawing.

## Integrate without replacing the shared library

Merge **only the intended symbol** into `symbols/zudo-pd.kicad_sym`. Never copy a whole downloaded multi-symbol library
over it. Keep configured master/library footprint copies byte-identical. Board-local library tables determine relative
paths; export snapshot paths must not be copied back into active boards.

Keep unavailable models/drawings explicit. Do not fabricate geometry or upgrade an illustrative envelope to exact-vendor.
Use the reviewed publication selection/asset allowlist for any deliberate publication; raw owner skills remain private
and `claudeResources: false` stays in effect.

## Verify authorized changes

Run strict identity/pin-map checks, `pnpm circuit:check`, and model/footprint parity checks. A geometry change needs the
pinned preview workflow (`pnpm previews:generate`) plus review. Run `pnpm b4push` and required built-site browser checks
when finalizing. A preview proves rendering; it does not qualify physical fit or electrical behavior.
