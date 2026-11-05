---
title: PD20 Verification — Blocked NVM and T1–T8
sidebar_position: 2
---

Scope: **Board P r3 + B20 only**. Every physical sheet is **NOT RUN**. This index does not authorize programming,
energizing or ordering. [Current state](../project/current-state.md#pd20-board-p-r3-plus-b20) tracks status and
[release gates](../architecture/release-readiness.md) tracks acceptance.

## NVM is blocked before provisioning

`boards/board-p/nvm/stusb4500-20v-intent.json` records intended two sink PDOs, PDO2 20 V / 5 A and
POWER_ONLY_ABOVE_5V. There is no `.bin`. The third-party map does not locate TDISPAR0V; default 9 is too short
for the 2 kΩ discharge feed and intent is at least 13. Lower-current 20 V source behavior is UNKNOWN.
File regeneration verifies the record only. It is not a write, readback or a provisioning procedure.

## Existing test sheets remain authoritative

The [dated status record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-status.md#bench-test-sheets-not-run)
owns full setups, criteria and source assumptions. Preserve those conditions rather than deriving a new recipe here.

| Sheet | Scope | State |
| --- | --- | --- |
| T1 | Output ripple at OSC continuous and transient demand; specified probe setup | NOT RUN |
| T2 | Thermal at 25 °C, 30 min, including D3 and limiter-maximum uncertainty | NOT RUN |
| T3 | Startup/re-entry, no-load exceptions and loaded limits | NOT RUN |
| T4 | 20 V image write/full power-cycle/readback only after encoding is resolved | NOT RUN; BLOCKED |
| T5 | Discharge/order at zero and asymmetric load; resistor pulse endurance | NOT RUN |
| T6 | Reverse current, unpowered and 60 °C conditions | NOT RUN |
| T7 | All-rail fault latch, re-plug recovery and recorded let-through | NOT RUN |
| T8 | PD hard reset, vSafe0V and clean restart | NOT RUN |

Nominal CAD and topology/simulation PASS rows do not execute these sheets. Independent P r3 review,
component evidence, hot-loop EMI, thermal coupling, sequencing and let-through must remain visible until
revision-specific results close them. Retain the [original review](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-b20-layout-review.md)
with its [later disposition](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-status.md).
