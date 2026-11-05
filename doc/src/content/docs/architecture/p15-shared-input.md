---
title: P15 r1 Shared Input Module
sidebar_position: 2
---

P15 r1 is the shared STUSB4500 input module for the LED project first and PD15 afterward.
It is not a third product lineup. [Current state](../project/current-state.md#p15-r1-shared-input-module)
tracks artifacts, order plans and physical acceptance; [release gates](./release-readiness.md) define acceptance.

## Authoritative sources

- PCB: `boards/board-p15/board-p15-draft.kicad_pcb`; schematic source: `scripts/schgen/board_p15_spec.py`.
- Stable procedure: [Board P15 NVM Programming](./board-p15-programming.md), including all P15-NVM-1–7 tests.
- Revision-specific packet: [P15 order decision](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-decision-packet.md).
- Exact part behavior belongs to the [component records](/docs/components/records/), not historical docstrings.

## Accepted interface

The module is 27 × 40 mm and targets 15 V / 3 A. The same PCB, population and desk NVM image serve both loads.

| Net | Connected pins (Ref.Pin) | Value/Note |
| --- | --- | --- |
| VBUS_OUT | JOUT1.1, JOUT1.2 | Switched 15 V target; Board L J2 or PD15 Board B J5 |
| ATT | JOUT1.3 | Open-drain attach indication |
| PDOK | JOUT1.4 | Configuration-dependent contract indication; not live voltage sensing |
| GND | JOUT1.5, JOUT1.6, J2.3 | Return; verify unkeyed mating orientation |
| SCL / SDA | J2.1 / J2.2 | Board 100 kΩ pull-downs; external jig pull-ups, never from VREG_2V7 |
| RESET | U1.6, R21 | 0 Ω strap to GND; J2.4 NC, no reset pulse available |

Local VDD feed/clamp and decoupling are implemented. P15 has no downstream hardware voltage window or eFuse;
per-unit programming acceptance is the recorded prototype mitigation. A desk binary, geometric clearance or
common mechanical outline does not establish a programmed unit, transient protection or physical fit.

## Acceptance before either load

Provision from a current-limited 5 V-only source with **Board L and Board B disconnected**. Save the factory dump,
write/read back, fully power-cycle with jig sequencing, verify the reloaded image and PDO configuration, then
perform P15-NVM-6 on a current-limited PD test source also offering 20 V with no downstream board attached.
Only a module that passes the full [canonical procedure](./board-p15-programming.md) proceeds to Board L or Board B.
