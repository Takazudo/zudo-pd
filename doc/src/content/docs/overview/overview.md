---
title: Project Overview
sidebar_position: 2
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

A compact power supply that provides ±12 V and +5 V for modular synthesizers from a
USB-C PD 15 V input. Since epic
[#86](https://github.com/Takazudo/zudo-pd/issues/86) the design is **two boards**, not
one: **Board A** negotiates and switches the 15 V rail, **Board B** converts it into the
three synth rails.

## Design Goals

### Output Specifications

| Rail     | Budget    | Final regulator | Protection            |
| -------- | --------- | --------------- | --------------------- |
| **+12 V** | **1.2 A** | U6 L7812CD2T-TR | PTC1 + TVS1           |
| **−12 V** | **0.8 A** | U8 CJ7912       | PTC3 + TVS3           |
| **+5 V**  | **0.5 A** | U7 L7805ABD2T-TR | PTC2 + TVS2          |

These are the project's **rail budgets** — what the protection chain, the thermal design,
and the PD power budget are all sized against. Older writing quoted higher numbers
(1.5 A / 1.0 A / 1.5 A) taken from the L78xx package family rather than from this
project's own evidence base; those are not this design's specification. See
[Board B — Synth Power Conversion](./board-b-synth-power.md) for the per-rail dropout and
PTC margin tables.

### Input

- **USB-C PD 15 V / 3 A** (45 W contract) — see
  [USB-PD AC Adapter](./usb-pd-adapter.md)

Total budgeted output is 14.4 W + 9.6 W + 2.5 W = **26.5 W**, so a 45 W (15 V/3 A)
adapter leaves headroom for conversion losses.

### Performance Targets

<Warning title="Targets, not measurements">

Nothing below has ever been measured on hardware. All four JLCPCB orders (0.1.0 → 0.4.0)
died at the USB-PD front end before the conversion chain was ever powered — see the
[failure history](../inbox/current-status.md#failure-history-v1-→-v4). Treat these as
design intent to be verified at bring-up.

</Warning>

- **Efficiency**: approx. 75-80% overall (estimate)
- **Ripple noise**: &lt;1 mVp-p at the final output (target)
- **Regulation**: ±1% over line and load (target)
- **Response speed**: good, by virtue of the linear output stage

## Architecture

### Two boards

- **[Board A — USB-PD Core](./board-a-usb-pd-core.md)** — STUSB4500 + USB-C receptacle +
  AO3401A load switch + NVM programming pads. A generic "negotiate 15 V over USB-PD and
  switch it" module with nothing synth-specific on it.
- **[Board B — Synth Power Conversion](./board-b-synth-power.md)** — DC-DC converters +
  linear regulators + protection + output connectors. Everything downstream of the
  switched 15 V rail.

The two join over a single 6-pin JST XH connector (J4 on Board A, J5 on Board B) carrying
switched +15 V, GND, and two open-drain status lines. The
[Two-Board Plan](./two-board-plan.md) explains why the split happened: every debug
iteration of the front end used to require re-manufacturing the entire synth-power BOM.

### 4-stage conversion chain

```
Board A                    │ Board B
                           │
USB-C 15V ──→ Q1 switch ───┼──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
                           │  │
                           │  ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
                           │  │
                           │  └─→ -13.5V (inverting DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

#### Stage 1: USB-PD (Board A)

- **U1 STUSB4500**: USB-IF certified PD sink controller, NVM-configured to request 15 V
- **Q1 AO3401A**: P-MOSFET load switch, enabled by VBEN once the contract is up
- **D8 BZT52C11**: gate-source zener clamp on Q1 (added by decision (e) — bounds Vgs on
  an unprogrammed board plugged into a 20 V-capable source)

#### Stage 2: DC-DC conversion (Board B)

- **U2/U3/U4 LM2596S-ADJ × 3**: adjustable switching regulators
  - +15 V → +13.5 V buck (feeds the +12 V rail)
  - +15 V → +7.5 V buck (feeds the +5 V rail)
  - +15 V → −13.5 V **inverting buck-boost** (feeds the −12 V rail)

There is no LM2586 and no SEPIC in this design. The −12 V rail is one LM2596S-ADJ in an
inverting buck-boost configuration — a single inductor to system GND with the catch diode
to the negative output. This wording is locked by `scripts/schgen/decisions.json`
decision (b).

#### Stage 3: Linear regulation (Board B)

- **U6 L7812**: +13.5 V → +12 V
- **U7 L7805**: +7.5 V → +5 V
- **U8 CJ7912**: −13.5 V → −12 V

The linear stage exists to strip the DC-DC switching ripple, which is why each converter
targets a voltage above its rail rather than the rail voltage directly — 1.5 V of
headroom on the ±12 V rails, 2.5 V on +5 V. Whether the +12 V headroom is enough at the
1.2 A budget is an open item; see
[Board B — Synth Power Conversion](./board-b-synth-power.md#linear-regulator-ldo-stage).

#### Stage 4: Protection (Board B)

- **PTC1/PTC2/PTC3 resettable fuses**: auto-recovering overcurrent protection, one per
  rail
- **TVS1/TVS2/TVS3**: surge and overvoltage clamps on the three outputs
- **LED indicators**: per-rail status

<Note title="PTC-only — there is no backup fuse">

Earlier revisions of this document described a two-level "PTC then SMD fuse" scheme.
That is not the design. `scripts/schgen/board_b_spec.py` places three PTCs and three TVS
diodes and no fuse of any kind, so nothing on the board is consumed by a fault and
nothing needs replacing afterwards. Note that on a hard short the regulator's **own**
current limit engages long before the PTC heats to its trip point — the cascade is worked
through in
[Board B — Synth Power Conversion](./board-b-synth-power.md#protection-stage-ptc1-and-the-l7812-current-limit-cascade).

</Note>

## Design Features

### All parts orderable from JLCPCB

Every position on both boards resolves to an exact LCSC part number, recorded in the spec
modules and cross-checked against the evidence base under `.claude/skills/component-*`.
See the [BOM](./bom.md) and the generated
[component records](/docs/components/records/).

### Low-noise by construction

The DC-DC + linear pairing is the whole point: the switcher does the heavy lifting
efficiently, and the LDO behind it rejects what the switcher leaves behind.

### Beginner-friendly protection

- **Auto-recovery**: a PTC trips on overload and resets once the load is removed
- **Visual feedback**: the rail LED going dark is the overload indication
- **No consumables**: no fuse to replace, no part to desolder after a fault

### Manufacturability

- **SMD active parts**: every IC, regulator, and passive is surface-mount and
  JLCPCB-assemblable. The connectors are the exception — J4/J5 (JST XH), Board B's
  J6-J9 Faston terminals, and the J10/J11 Eurorack headers are all through-hole
- **TO-263 / TO-252 packages**: surface-mount thermal pads rather than through-hole tabs
- **Split boards**: the front end can be re-spun without re-ordering the power stage

## Protection Circuit Operation

| Condition                    | Behavior                                                        |
| ---------------------------- | --------------------------------------------------------------- |
| Normal load (within budget)  | PTC at low resistance, rail LED lit                             |
| Overload (above PTC hold)    | PTC heats into high resistance, rail collapses, LED goes dark   |
| Fault removed                | PTC cools and resets — the rail comes back on its own           |

Exact hold and trip currents per rail, including the derating caveats that still need a
bench check, are in
[Board B — Synth Power Conversion](./board-b-synth-power.md#protection-stage).

## Current State

Four JLCPCB PCBA orders (0.1.0 through 0.4.0) have been built and none negotiated a USB-PD
contract. The v4 diagnosis is written up in
[v4 USB-PD Failure Diagnosis](../inbox/v4-pd-failure-diagnosis.md); rather than order a
fifth single-board respin, the project split into Board A and Board B.

Both boards now exist as generated KiCad projects under `boards/`, built by the `schgen`
toolchain from `scripts/schgen/board_a_spec.py` and `board_b_spec.py`. **PCB layout and
JLCPCB order files (gerbers, BOM, CPL) are not started for either board.**

## What's Next

1. **Bench-confirm the v4 root cause** on the dead v4 boards, using the
   [bench discrimination procedure](../inbox/v4-pd-failure-diagnosis.md#bench-discrimination-procedure-dead-v4-boards-cheapest-first).
   Several locked fixes are gated on this.
2. **PCB layout for Board A**, then a Board A-only order to prove the front end in
   isolation.
3. **PCB layout for Board B**, ordered once Board A is confirmed working.
4. **Performance verification** — the ripple, load-response, and thermal numbers on this
   page become measurements instead of targets.

Live status lives in [Project Status and Plan](../inbox/current-status.md).
