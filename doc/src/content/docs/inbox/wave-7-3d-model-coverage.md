---
title: Wave 7 — 3D Package Model Coverage
sidebar_position: 17
description: "Coverage manifest for the wave-7 3D package model sourcing pass (issue #145) — every published footprint package's sourcing outcome, the one LCSC data-quality substitution found, and the two architecture decisions the pass made."
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

This page is the coverage manifest required by issue #145 (S7 of the
components-docs-restructure epic). It records, for every one of the 27
published footprint packages, whether a reviewed `.wrl`/`.step` 3D model pair
was sourced and from which LCSC id — the deliverable the 3D-viewer work
(#146) consumes to know which records carry a resolved model.

## Result: 27 of 27 sourced, zero unsourced

Every published package — including the 3 that previously carried no
`(model …)` line at all — now resolves to a reviewed, committed 3D model in
`footprints/kicad/zudo-pd.3dshapes/`. `easyeda2kicad` was run once per package
against the LCSC id its record[s] use in
`.claude/skills/component-spec-audit/references/inventory.json` (or, for
`scripts/schgen/board_{a,b}_spec.py`-only fields, the same LCSC number those
spec modules use). No package needed to be recorded as unsourced.

| Package (`footprintName`) | LCSC used | 3D model basename | Prior state |
| --- | --- | --- | --- |
| `QFN-24_L4.0-W4.0-P0.50-BL-EP2.8` | C2678061 | `QFN-24_L4.0-W4.0-P0.50-BL-EP2.8` | stale `${EASYEDA2KICAD}` |
| `TYPE-C-SMD_TYPE-C-6P` | C456012 | `TYPE-C-SMD_6P-L8.9-W6.8-H3.2-P1.00` | stale `${EASYEDA2KICAD}` |
| `SOT-23_L2.9-W1.3-P1.90-LS2.4-BR` | C347476 | `SOT-23-3P_L2.9-W1.3-H1.0-LS2.4-P0.95` | stale `${EASYEDA2KICAD}` |
| `D-FLAT_L4.3-W2.6-LS5.3-RD` | C571370 | `SMA_L4.2-W2.6-LS5.3-RD` | stale `${EASYEDA2KICAD}` |
| `R0603` | C25803 | `R0603` | stale `${EASYEDA2KICAD}` |
| `R0805` | C17513 | `R0805_L2.0-W1.3-H0.6` | stale `${EASYEDA2KICAD}` |
| `C1206` | C13585 | `C1206_L3.2-W1.6-H1.3` | stale `${EASYEDA2KICAD}` |
| `C0603` | C15849 | `C0603_L1.6-W0.8-H0.8` | stale `${EASYEDA2KICAD}` |
| `C0805` | C1711 | `C0805_L2.0-W1.3-H1.3` | stale `${EASYEDA2KICAD}` |
| `CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD` | **C22387780** (substituted — see below) | `CAP-SMD_BD10.0-L10.4-W10.4-LS11.2-FD` | stale `${EASYEDA2KICAD}` |
| `CAP-SMD_BD6.3-L6.6-W6.6-FD` | C335982 | `CAP-SMD_BD6.3-L6.6-W6.6-FD` | stale `${EASYEDA2KICAD}` |
| `CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD` | C970687 | `CAP-SMD_BD8.0-L8.3-W8.3-LS9.1-FD` | no `(model …)` line |
| `LED0603-RD` | C2289 | `LED0603-RD` | stale `${EASYEDA2KICAD}` |
| `CONN-TH_B6B-XH-A-6P` | C144397 | `CONN-TH_XH2.50-LI-6P` | no `(model …)` line |
| `SOD-523_L1.2-W0.8-LS1.6-RD` | C85382 | `SOD-523_L1.2-W0.8-H0.7-LS1.6` | no `(model …)` line |
| `SOD-123_L2.8-W1.8-LS3.7-RD` | C92321 | `SOD-123_L2.8-W1.8-LS3.7-RD` | stale `tmp/bzt52c11/…` |
| `TO-263-5_L10.2-W8.9-P1.70-BR` | C347423 | `TO-263-5-5P_L10.2-W8.7-H4.5-LS14.4-P1.70` | stale `${EASYEDA2KICAD}` |
| `IND-SMD_L13.8-W12.8` | C19268674 | `IND-SMD_L13.8-W12.8` | stale `${EASYEDA2KICAD}` |
| `SMA_L4.3-W2.6-LS5.2-RD` | C8678 | `SMA_L4.3-W2.6-LS5.2-RD` | stale `${EASYEDA2KICAD}` |
| `TO-263-2_L10.0-W9.1-P5.08-LS15.2-TL` | C13456 | `TO-263-2_L10.2-W8.7-H4.5_LS15.2-P2.54` | stale `${EASYEDA2KICAD}` |
| `TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW` | C86206 | `TO-263-2_L10.2-W8.7-H4.5-LS15.2-P2.54` | stale `${EASYEDA2KICAD}` |
| `TO-252-3_L6.5-W5.8-P4.58-BL` | C94173 | `TO-252-3_L6.5-W5.8-P4.58-BL` | stale `${EASYEDA2KICAD}` |
| `F1210` | C7529589 | `F1210_L3.2-W2.6-H0.6` | stale `${EASYEDA2KICAD}` |
| `F1812` | C70119 | `F1812_L4.5-W3.2-H1.0` | stale `${EASYEDA2KICAD}` |
| `F1206` | C883133 | `F1206_L3.2-W1.7-H0.6` | stale `${EASYEDA2KICAD}` |
| `CONN-TH_1217754-1` | C591344 | `CONN-TH_63951-1` | stale `${EASYEDA2KICAD}` |
| `HDR-TH_16P-P2.54-H-M-R2-C8-S2.54` | C5383092 | `HDR-TH_16P-P2.54-M-WI-2X8P` | stale `${EASYEDA2KICAD}` |

Every `.wrl` file passed the same VRML 2.0 / no-traversal / no-executable-node
/ allowed-node-set validation `references.ts`'s `validateVrml()` enforces at
generation time (checked standalone before committing, then proven again by
`pnpm test:components` against the real corpus). All 27 `.wrl` files are
individually well under the 2&nbsp;MB per-model cap
(`REFERENCE_LIMITS.modelBytes`), and the sum of all 27 is ~2.6&nbsp;MB against
the 8&nbsp;MB aggregate cap.

## The one substitution: a supplier data-quality mismatch, not a package error

<Warning title="RETRACTED — this section drew the wrong conclusion (issue #150)">

The reasoning below is **wrong** and is kept only as a record of how the error
was made. EasyEDA's `CAP-SMD_BD8.0-…` model for `C2983319` was **correct**: the
HRK datasheet states the part is a Φ8 × 10.5 mm can (`D8H10.5mm`). The supplier
data was the truth-teller, and it was overruled here to preserve a package
assignment that was itself the mistake. `C2983319` now carries
`CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD`, and C3/C11 were re-landed accordingly.

Generalizable lesson: when a supplier asset disagrees with a project package
assignment, read the manufacturer datasheet before deciding which one is wrong.
Neither side is presumptively authoritative — here the "obviously bad supplier
data" heuristic inverted the correct answer.

</Warning>

`CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD` has two inventory lines: `C2983319`
(GVT1E477M0810CNVC) and `C22387780` (EFVH035ADA471M10B0). Fetching `C2983319`
first — the natural "first line wins" choice — returns a 3D model EasyEDA
itself names `CAP-SMD_BD8.0-L8.3-W8.3-LS9.1-FD`: an **8.3&nbsp;mm** package
geometry wired to a part whose own footprint is the **10.3&nbsp;mm** BD10.0
outline. This is upstream EasyEDA/LCSC library data being wrong for that one
LCSC id (a known class of issue for electrolytic caps on LCSC, where a
part's linked 3D asset can be copied from a similar-but-different sibling) —
not a mistake in this project's package assignment. It was caught by
cross-checking the model's own reported dimensions against the footprint
name's declared dimensions before wiring anything in, and confirmed by
re-running `pnpm generate:footprint-previews` after the fact: dimension
mismatches on this scale would have been visible immediately in the rendered
silkscreen/courtyard outline sitting inside a wrongly-sized model, had the
page rendered one.

`C22387780`'s own EasyEDA data returns a correctly BD10.0-sized model
(`CAP-SMD_BD10.0-L10.4-W10.4-LS11.2-FD` — 10.4&nbsp;mm, matching within normal
manufacturer-to-manufacturer footprint tolerance), so it was used instead. The
`.kicad_mod`'s existing `(offset (xyz …))`/`(rotate (xyz …))` transform was
also replaced, not just the path, because it is specific to whichever
geometry file it is paired with, and the two LCSC ids' models are not the same
underlying geometry.

## Two architecture decisions this pass made

**Directory name: followed the code, not the issue text.** Issue #145 and the
wave-7 brief both say the target directory is
`footprints/kicad/zudo-power.3dshapes/`. The consuming code
(`doc/component-docs/adapters/circuit/paths.ts`'s `MODEL_ROOT`,
`references.ts`'s `MODEL_PREFIX`) already hard-codes
`footprints/kicad/zudo-pd.3dshapes/` from an earlier wave. Using the issue
text's name would have made every model silently unresolved (`readPackage()`
would treat the `(model …)` line as "not a reviewed local asset" even though
the file exists on disk, since the prefix check would never match) — so this
pass followed the code.

**Flipped `reference.model.*` from `DENY` to `PUBLISH`.** `matrix.ts` states
outright that these four fields "flip when their consumer lands — not
before." Sourcing the assets made `entry.model` resolve for the first time,
which made `projectFootprint()`'s previously-dead `publishRequired` branch
live — and it failed loudly exactly as designed, breaking `pnpm build`,
`pnpm generate:components`, and `pnpm test:components`. Investigating showed
the consumer already existed: `ui/component-references.tsx`'s `ModelCard` /
`ResolvedModel` (a static "Open the VRML model" link — explicitly **not** the
interactive WebGL viewer, which its own comment calls out as "a separate
port" that "needs assets that do not exist here yet") has rendered both the
resolved and unresolved states since an earlier wave. With the emitter
already in place and 27/27 packages now resolved, this pass flipped the four
fields — mirroring wave 6's identical `reference.footprint.path` flip — and
updated the two test files whose assertions described the old
zero-assets state. The interactive WebGL viewer itself remains out of this
pass's scope.

## Scope note: the other ~30 footprints in the library

`footprints/kicad/` holds footprints beyond the 27 the manifest publishes
(parts removed from the design, superseded revisions, hand-created pads,
etc.). Their `(model …)` lines were left untouched — re-sourcing them is
outside what the manifest or any published record needs, and several no
longer correspond to a current inventory line at all.
