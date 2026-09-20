---
title: Project Status and Plan
sidebar_position: 3
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

Current progress and plan for the USB-PD powered modular synthesizer power supply — now in
the **2-board split era** following the v4 diagnosis (epic
[#86](https://github.com/Takazudo/zudo-pd/issues/86)), with both boards now generated
from spec-driven KiCad projects under `boards/`.

## 🎯 Project Goal

**Low-noise power module supplying ±12V/+5V for modular synths from USB-C PD 15V input**

- Protection circuit safe for modular synth beginners
- All parts available from JLCPCB (stable supply, low cost)
- Low-noise design with &lt;1mVp-p ripple
- Easy to use with USB-C PD

## 🔄 Current Phase: Spec-Driven 2-Board Architecture

The single-board zudo-pd design (v1 → v4) never reached a working USB-PD negotiation,
across four separate JLCPCB orders. Rather than order a v5 single-board respin, the
project split into two boards:

- **Board A** — a reusable USB-PD sink core (STUSB4500 + USB-C receptacle + load switch +
  NVM programming pads). Cheap to re-order in isolation while the front end is under
  debug, and reusable in other projects.
- **Board B** — the synth power conversion stage (DC-DC converters + linear regulators +
  protection + output connectors). Carries the expensive/bulky parts, only re-ordered
  once the front end is proven stable.

Both boards now exist as real, **generated** KiCad projects under `boards/board-a/` and
`boards/board-b/` — built by the `schgen` toolchain from Python spec modules
(`scripts/schgen/board_a_spec.py` / `board_b_spec.py`), not hand-drawn. A structured
evidence review (epic #86's spec-architecture wave) locked a set of component-level
fixes on top of the original board-split fix list — see
[Spec-Architecture Review](./spec-architecture-review.md) for the findings and
`scripts/schgen/decisions.json` for the machine-readable decision record.

See [Two-Board Plan](../overview/two-board-plan.md) for the full why-split rationale,
[Board A: USB-PD Core](../overview/board-a-usb-pd-core.md) and
[Board B: Synth Power](../overview/board-b-synth-power.md) for the per-board design docs,
and [Board Split Decision](./board-split-decision.md) for the locked front-end fix list
and the Board A ↔ Board B interface contract.

<Note title="What's actually done vs. not started">

Diagnosis, design docs, and both boards' generated schematics are done, including the
wave-6 decision-locked part swaps (TVS2, PTC1, C5/C7, canonical 470µF LCSC numbers) and
a new Q1 gate-source clamp (D8) on Board A. **Not started:** PCB layouts or JLCPCB order
files (gerbers/BOM/CPL) for Board A or Board B. That is the next plan, gated on the user
bench-confirming the v4 root cause on the dead v4 boards. The legacy root KiCad project
(`zudo-pd.kicad_pro` etc.) stays in place, unregenerated, as the as-built v4 reference —
see root `CLAUDE.md`.

</Note>

## Failure History (v1 → v4)

| Rev | Version | Result |
| --- | --- | --- |
| v1 | 0.1.0 | PD failed — pin 18 (VBUS_VS_DISCH) left NC, pin 22 (VSYS) shorted to VREG_2V7 |
| v2 | 0.2.0 | CC1DB believed chip-internal short → external-Rd redesign |
| v3 | 0.3.0 | CC attach worked (5V, I2C alive), pin 18 tied to GND → PD failed |
| v4 | 0.4.0 | Pin 18 fixed, NVM programmed for 15V — **still failed** (see [v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md) for the ranked root-cause candidates) |

The v4 order artifacts (schematic + JLCPCB-ready manufacturing files) were confirmed to
have actually reached a real order package — see
[v4 As-Built Order Verification &amp; Footprint Geometry Audit](./v4-asbuilt-audit.md).

## ✅ What's Done

- **Wave 1 (diagnosis):** [v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md)
  (#87), [v4 As-Built Audit](./v4-asbuilt-audit.md) (#88),
  [Board B Architecture Review](./board-b-architecture-review.md) (#89)
- **Wave 2 (decision):** [Board Split Decision](./board-split-decision.md) (#90) — locks
  the front-end fix list and the Board A ↔ Board B interface contract
- **Wave 3 (implement):** Board A design doc, Board B design doc, confirmed schematic
  fixes applied to the legacy KiCad project
- **Spec-architecture epic (waves 1–8, epic #86):** the `schgen` spec-driven generator
  toolchain ported in; `boards/board-a/board-a.kicad_sch` and
  `boards/board-b/board-b.kicad_sch` generated from `board_a_spec.py`/`board_b_spec.py`;
  a structured evidence review of both boards
  ([Spec-Architecture Review](./spec-architecture-review.md)); a wave-6 decision lock
  (`scripts/schgen/decisions.json`) covering part swaps (TVS2 → SMAJ6.5A, PTC1 →
  SMD1210P150TF/16, C5/C7 → 470µF/35V FOLLON, canonical 470µF LCSC C335982), a new Q1
  gate-source clamp (D8) on Board A, and the LM2596S-ADJ inverting-buck-boost topology
  wording (closes #46); this doc-base alignment pass (wave 8, #126)

## 📋 What's Next

- **Wave 9 and beyond:** PCB layout for Board A / Board B, then the pre-order checklist
  (gerbers, BOM, CPL — explicitly **not** started; that is a separate future plan)
- **User action:** bench-confirm the v4 root cause on the dead v4 boards using the
  [bench discrimination procedure](./v4-pd-failure-diagnosis.md#bench-discrimination-procedure-dead-v4-boards-cheapest-first) —
  this gates several of the locked fixes before the first Board A order

## Versioning

See [Versioning Scheme](./versioning.md) for the full X.Y.Z scheme, including how a
2-board JLCPCB order (Board A + Board B ordered together) is versioned going forward.

## Hardware on Hand

- **NUCLEO-F072RB** (STM32 Nucleo board, USB-to-I2C bridge for STUSB4500 NVM programming)
- **4P 2.54 mm pogo pin clip** (mates with the J2 pogo pads) — see
  [NVM Programming Setup](./nvm-programming.md)
- **PCBA v1–v4 physical boards** — retained for bodge reference and bench diagnosis (the
  [v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md) bench procedure runs on the
  dead v4 boards)
