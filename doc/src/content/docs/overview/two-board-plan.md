---
title: Two-Board Plan (USB-PD Core + Synth Power)
sidebar_position: 19
description: Why zudo-pd is splitting from one PCBA into a reusable USB-PD core board plus a synth power conversion board, and how the two fit together.
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

The single-board zudo-pd design went through four JLCPCB orders (v1 → v4) and never
reached a working USB-PD negotiation — see the
[failure history](../inbox/current-status.md#failure-history-v1-→-v4) and the
[v4 USB-PD Failure Diagnosis](../inbox/v4-pd-failure-diagnosis.md) for the root-cause
detail. Rather than order a v5 single-board respin, the project (epic
[#86](https://github.com/Takazudo/zudo-pd/issues/86)) splits into two boards:

- **[Board A: USB-PD Core](./board-a-usb-pd-core.md)** — STUSB4500 + USB-C receptacle +
  load switch (Q1/AO3401A) + NVM programming pads (J2). A reusable "USB-PD 15V sink
  module."
- **[Board B: Synth Power](./board-b-synth-power.md)** — DC-DC converters + linear
  regulators + protection + output connectors. Everything downstream of the switched
  15V rail.

## Why split?

**The cost problem is debug-iteration cost, not unit cost.** Every JLCPCB reorder needs
the *full* BOM — DC-DC converters, LDOs, protection parts, output connectors — even
though only the USB-PD front end (STUSB4500 + CC termination + ESD/TVS strategy) has ever
been the thing under active debug across v1 → v4. Each diagnostic iteration therefore
pays to re-manufacture and re-assemble a stack of downstream parts that were never the
suspect.

Splitting removes that tax:

- **Board A is cheap to re-order in isolation.** A smaller BOM (one IC, one connector,
  one load-switch MOSFET, a handful of passives) means a faster, cheaper JLCPCB turn for
  every front-end debug iteration, instead of dragging the whole synth-power BOM along
  for the ride.
- **Board A is reusable outside this project.** Per the
  [Board A ↔ Board B interface contract](../inbox/board-split-decision.md#decision-set-b-—-board-a-↔-board-b-interface-contract),
  the inter-board connector carries only switched 15V power, ground, and two generic
  open-drain status lines — nothing synth-specific. Board A stands alone as a plain
  "USB-C PD 15V sink module" usable in other projects.
- **Board B only needs to be re-ordered once the front end is proven stable.** The DC-DC
  + LDO + protection chain has never actually been powered on real hardware (v1–v4 all
  died at the USB-PD front end before VBUS_OUT ever saw 15V) — see the
  [Board B Architecture Review](../inbox/board-b-architecture-review.md) for the
  datasheet-level review of that chain done in place of bench data. Board B's first real
  order happens once Board A is confirmed working, rather than being re-spun alongside
  every front-end debug cycle.

## How they connect

Board A and Board B join over a single 6-pin JST XH connector — see the
[Board Split Decision](../inbox/board-split-decision.md#decision-set-b-—-board-a-↔-board-b-interface-contract)
for the full pinout, current-rating math, and keying rationale. In summary: two pins of
switched +15V (paired for current sharing), two pins of GND (paired return), and two
open-drain status lines (ATTACH, POWER_OK2) that Board B or any other consumer may
ignore.

## Doc structure note

Board A and Board B **design docs** live as **flat pages under `overview/`** —
[`overview/board-a-usb-pd-core.md`](./board-a-usb-pd-core.md) and
[`overview/board-b-synth-power.md`](./board-b-synth-power.md) — alongside this page,
rather than under a new dedicated doc section. This matches the doc-structure
assumption recorded in the
[Board Split Decision](../inbox/board-split-decision.md#decision-set-c-—-doc-structure-note)
(decision set (c)) and the default used by the parallel Board A / Board B design-doc
tasks.

<Info>

This is a separate thing from the repository-root `boards/` directory (`boards/board-a/`,
`boards/board-b/`), which holds the actual generated KiCad projects (`schgen` output) —
that layout is unrelated to where the doc *pages* live, and was decided later, in the
spec-architecture epic. See `boards/README.md` and root `CLAUDE.md`.

</Info>

## Status

Design docs for both boards were written in epic #86's wave 3. Since then, the
spec-architecture epic generated both boards' schematics for real:
`boards/board-a/board-a.kicad_sch` and `boards/board-b/board-b.kicad_sch`, built by the
`schgen` toolchain from Python spec modules
(`scripts/schgen/board_a_spec.py`/`board_b_spec.py`), plus a locked wave-6 decision set
of component-level fixes on top of the original board-split fix list — see
[Spec-Architecture Review](../inbox/spec-architecture-review.md) and
`scripts/schgen/decisions.json`. **Not started:** PCB layouts or JLCPCB order files
(gerbers/BOM/CPL) for either board — that is a separate future plan, gated on the user
bench-confirming the v4 root cause using the
[bench discrimination procedure](../inbox/v4-pd-failure-diagnosis.md#bench-discrimination-procedure-dead-v4-boards-cheapest-first).

## References

- [Board Split Decision](../inbox/board-split-decision.md) — locked front-end fix list +
  Board A/B interface contract
- [v4 USB-PD Failure Diagnosis](../inbox/v4-pd-failure-diagnosis.md) — root-cause
  candidates + bench procedure
- [v4 As-Built Order Verification &amp; Footprint Geometry Audit](../inbox/v4-asbuilt-audit.md)
- [Board B Architecture Review](../inbox/board-b-architecture-review.md)
- [Spec-Architecture Review](../inbox/spec-architecture-review.md) — the evidence review
  and locked decision set behind both boards' generated schematics
- [Project Status and Plan](../inbox/current-status.md)
