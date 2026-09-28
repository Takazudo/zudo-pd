---
title: Project Brief
sidebar_position: 2
description: Scope, output targets and the boundary between a design and measured hardware.
---

The supply accepts a negotiated USB-PD rail and provides three protected rails for
modular synthesizers. Separating the input module lets it be tested and replaced
independently of the conversion board.

## Electrical targets

| Interface | Design target | Evidence state |
| --- | --- | --- |
| Input | USB-PD 15 V / 3 A | Mandatory 15 V-only NVM readback; first programming at 5 V only; compatible source and verified harness |
| +12 V output | 1.2 A budget | New AP63201 + LT1963A chain; conditional headroom and thermal/load validation |
| −12 V output | 0.8 A budget | New adjustable LT3015 chain; conditional headroom and thermal/load validation |
| +5 V output | 0.5 A budget | New LT1963A chain; conditional headroom and thermal/load validation |
| Output ripple | Less than 1 mV peak-to-peak target | Unmeasured |

These are targets, not guaranteed ratings. Output budgets total 26.5 W before
conversion losses. A 45 W input contract alone does not establish converter capacity,
regulator headroom, connector heating or cooling performance. The
[integration records](/docs/components/integration/) retain conditional calculations
and unresolved evidence.

The power stage has been redesigned with these output targets retained. Current
selections are recorded in the [board contract](../architecture/board-contract.md);
they remain subject to the integration conditions, thermal and bench validation.

Board P now uses a 16 V standoff TVS. Factory 20 V negotiation is unsafe; follow
[Board P configuration](../architecture/board-p.md) before connecting a PD source.

## Renewal decisions

- Keep USB-PD negotiation on a separate reusable input board.
- Reuse the reviewed Board P design after adapting its interface and exact component
  evidence to this project.
- Replace the previous synth headers and printed guards with DEALON
  DW254P-2X8-L0, JLCPCB/LCSC C4749189.
- Make exact component records, generated schematics and PCB release checks the
  sources for current documentation.

## Hardware history

Four combined-board PCBA orders are retained as versions 0.1.0 through 0.4.0. Their
recorded USB-PD front-end failures mean those assemblies do not validate downstream
performance. The root KiCad project is the historical v0.4.0 design; renewed work
belongs under `boards/`.

Board B's screw-terminal revision retains the 110 × 85 mm outline: 10.5% less
area than the 110 × 95 mm layout and 45.8% less than the initial 150 × 115 mm layout.
It uses two copper layers and 2 oz outer copper. Board B is installed on legs with
its front/component face down. J5 is on that front face, mating to Board P with the
two component faces toward each other. P is above B in CAD and below it in the
installed device; P's own 27 × 40 mm PCB remains unchanged. P moves down to free
the fourth independent corner-support hole. All four Ø3.0 mm corner-hole centers
are 4 mm from adjacent edges; the three Ø3.2 mm PD mounting holes remain separate.

Two top-side WJ500V-5.08-2P / C8465 blocks replace the four Fastons. Their wire
entries face left, and the active board needs a plain left edge with no printed
terminal guard. The four voltage labels appear on both sides, readable from their
respective viewing side. P1 plus TP3/TP4/TP5 moves 20 mm right as one seven-contact
top-edge row. The PCB is implemented and native layout and power-path checks
pass; package reports determine CAD and export status.

The selected 18 mm printed adhesive leg addresses the earlier HC-11 support's
nominal height conflict with this front-down assembly. The PCB and JLCPCB package
are unchanged. M3 passage through the existing Ø3.0 mm holes needs a fit check. See the
[support contract](../architecture/board-contract.md#independent-corner-supports).
Physical wire fit, tightening torque, adhesive retention, connector seating and
full-load performance remain unmeasured.

Read [release readiness](../architecture/release-readiness.md) before using new
manufacturing files. Exported Gerbers and assembly tables do not replace electrical
or mechanical validation.
