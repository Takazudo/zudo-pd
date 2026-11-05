---
title: JLCPCB Package Preparation
sidebar_position: 2
---

Read [current state](./current-state.md) and [per-stream gates](../architecture/release-readiness.md) before preparing
manufacturing files. An export is a local review artifact, not an order, program acceptance or release.

## Reconcile the package

BOM/CPL must describe the same exact fitted revision, including DNP/excluded bare copper, side, rotation and
through-hole assembly scope. Inspect Gerber/drill layers, outline and origin independently of KiCad. Review
unkeyed mating orientation, terminal/synth pin maps, labels and physical clearance for the selected pair.
Retain source/tool versions, source hashes, reports, blockers and assembly-preview limitations.

## Repository export and independent rendering

Use a **new development output directory** for each authorized export; do not run an export merely to edit its
instructions. The current CLI accepts these distinct pairs:

```sh
# PD15 development export
python3 scripts/pcb/export-jlcpcb.py tmp/pd15-review --boards board-p15 board-b
# PD20 development export
python3 scripts/pcb/export-jlcpcb.py tmp/pd20-review --boards board-p board-b20-draft
```

The retired `--boards board-p board-b` combination is rejected: current `board-p` is 20 V r3.
The exporter requires native KiCad tools and checks ERC/DRC, connectivity/identity and variant contracts.
The independent verifier checks layer stack, identities, coordinates, hashes and Gerber/drill parsing:

```sh
uv run --with gerbonara --with resvg-py python scripts/pcb/verify-jlcpcb.py --write tmp/pd20-review
```

`--write` is only for immediately after a fresh export: it stores renders/report and refreshes that new output's
checksums. Without `--write`, use `--out <directory>` to keep a reviewed package unchanged.
The verifier reads source hashes from the **current working tree**; it does not retrieve historical source bytes.

## Fixed P15 package and historical receipts

`manufacturing/releases/corner-support-review/` is the fixed P15+B package at manifest base `3b9821b`.
The [2026-11-03 order packet](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-decision-packet.md)
records source matches at `5a21ab9`, 151/151 checksums and full verifier PASS with original required local-only STEP.
Preserve those results and locks. They do not verify later HEAD. Historical replay requires a matching source tree
and that original STEP; a fresh clone lacks it. Do not replace this package with development exports or refresh
its checksums/source locks as part of documentation work.

The packet's two assembled P15 plan is not an executed order. Received Board B's factory BOM matches S3 at
`f25194f`; current source has later substitutions and incomplete physical identity remains explicit.
After an actual separately authorized order, retain exact submitted files through the established order/version
workflow. Export preparation alone changes neither order counters nor VERSION.
