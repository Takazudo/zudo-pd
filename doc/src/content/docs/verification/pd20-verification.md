---
title: PD20 Verification — NVM Image Status and T1–T8
sidebar_position: 2
---

Scope: **Board P r3 + B20 only**. Every physical sheet is **NOT RUN**. This index does not authorize programming,
energizing or ordering. [Current state](../project/current-state.md#pd20-board-p-r3-plus-b20) tracks status and
[release gates](../architecture/release-readiness.md) tracks acceptance.

## NVM intent is settled; no program-ready image exists

`boards/board-p/nvm/stusb4500-20v-intent.json` records the settled intent: two sink PDOs, PDO2 20 V / 5 A, and
POWER_ONLY_ABOVE_5V = 1. Both configuration choices are adopted (readiness D4, 2026-11-14):

- **TDISPAR0V = 15** at 0xCA[7:4] (0xCA = 0xFC; minimum 1.05 s, about 16 % over the 0.906 s the 2 kΩ discharge
  feed needs), as `dec-pd20-tdispar0v-15`. The position comes from the ST-authored draft note.
- **POWER_ONLY_ABOVE_5V at 0xE6 bit 3**, as `dec-pd20-nvm-power-only-gui`. Official STSW-STUSB002 1.08 S exports,
  differing only in this setting, give 0xE6 = 0x40 (off) and 0x48 (on). This is official-tool evidence, not a
  programmed-part readback.

DS12499 Rev 8 answers initial matching: a 20 V offer below 5 A does not match PDO2. See the
[evidence research](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-evidence-research.md).

These boundaries remain:

- No reviewed, program-ready 20 V binary exists. The intent record holds partial desk bytes only.
- No unit has been programmed or read back.
- The TDISPAR0V reset/reapplication interaction and transitions from an established contract (for example a source
  that re-advertises 20 V below 5 A) still need bench evidence (T8, with a programmed-part readback).

File regeneration verifies the record only. It is not a write, readback or provisioning procedure.

## Existing test sheets remain authoritative

The [dated status record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-status.md#bench-test-sheets-not-run)
owns full setups, criteria and source assumptions. Preserve those conditions rather than deriving a new recipe here.

| Sheet | Scope | State |
| --- | --- | --- |
| T1 | Output ripple at OSC continuous and transient demand; specified probe setup | NOT RUN |
| T2 | Thermal at 25 °C, 30 min, including D3 and limiter-maximum uncertainty | NOT RUN |
| T3 | Startup/re-entry, no-load exceptions and loaded limits | NOT RUN |
| T4 | 20 V image write/full power-cycle/readback. The configuration and bit mapping are settled; T4 cannot start until a reviewed program-ready image and its provisioning procedure exist | NOT RUN; BLOCKED (no reviewed image) |
| T5 | D2 sequenced fast discharge and order at zero and asymmetric load, with DIS_C drive, firing times and disconnect-before-discharge measured; WSL2512 0.5 Ω load pulse endurance | NOT RUN |
| T6 | Reverse current, unpowered and 60 °C conditions | NOT RUN |
| T7 | All-rail fault latch, re-plug recovery and recorded let-through | NOT RUN |
| T8 | PD hard reset, vSafe0V and clean restart | NOT RUN |

Nominal CAD and topology/simulation PASS rows do not execute these sheets. The [original P r3 review](https://github.com/Takazudo/zudo-pd/blob/main/boards/board-p/r3-draft/independent-review.md)
is preserved; its R1–R4 geometry findings and the final artwork have bounded dispositions from
[PR #240](https://github.com/Takazudo/zudo-pd/pull/240), while R5 (T7) and R7 (T3) remain open.
Component evidence, hot-loop EMI, thermal coupling, via/stencil process, sequencing and let-through must
remain visible until revision-specific results close them. Retain the [original review](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-b20-layout-review.md)
with its [later disposition](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-status.md).
The [D1–D3 interface diagnostics](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/interface-diagnostics.md)
(2026-11-11) are arithmetic and source binding only; they do not execute T3, T5 or T7.
