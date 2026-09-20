---
title: Bill of Materials (BOM)
sidebar_position: 4
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

Complete parts configuration for JLCPCB SMT assembly, across both boards of the
[two-board split](./two-board-plan.md).

Every reference designator, value, and LCSC number on this page is read from the two
`schgen` spec modules — `scripts/schgen/board_a_spec.py` and
`scripts/schgen/board_b_spec.py` — which are the source of truth for
`boards/board-a/board-a.kicad_sch` and `boards/board-b/board-b.kicad_sch`. Part swaps
carry the decision key from `scripts/schgen/decisions.json` that locked them.

<Note title="Stock figures were removed on purpose">

Earlier revisions of this page carried a per-line stock column dated to an unrecorded
pass. Those numbers had gone stale and there is no way to tell from the page when they
were true. **Verify stock and price at order time** — that is the standing instruction in
every wave-6 decision record. Prices below are rough JLCPCB catalog estimates and are
marked where they are an estimate rather than a dated catalog reading.

</Note>

## Stage-to-Board Map

| Stage | Function | Board |
| ----- | -------- | ----- |
| **Stage 1** | USB-PD voltage acquisition (STUSB4500 + load switch) | **Board A** |
| **Stage 2** | DC-DC converters | **Board B** |
| **Stage 3** | Linear regulators | **Board B** |
| **Stage 4** | Protection (PTC + TVS) and rail indicators | **Board B** |
| **Stage 5** | Output connectors | **Board B** |

The JST B6B-XH-A interface connector appears on both boards — `J4` on Board A, `J5` on
Board B. See the
[A↔B interface contract](./board-a-usb-pd-core.md#a↔b-interface-contract-locked-—-copied-verbatim-from-90).

## Power Supply Specifications

**Rail budgets** (the currents this design is sized for, per `CLAUDE.md`):

| Rail | Design budget | Regulator | PTC hold / trip |
| ---- | ------------- | --------- | --------------- |
| **+12V** | 1.2 A | U6 L7812CD2T | 1.5 A / 3.0 A (PTC1) |
| **+5V** | 0.5 A | U7 L7805ABD2T | 1.1 A / 2.2 A (PTC2) |
| **-12V** | 0.8 A | U8 CJ7912 | 1.5 A / 3.0 A (PTC3) |

Total output budget: 12 V × 1.2 A + 5 V × 0.5 A + 12 V × 0.8 A = **26.5 W**.

- **Input**: USB-C PD 15 V, 3 A contract
- **Efficiency**: ~75-80% — a design estimate, not a measurement

<Warning title="1.5 A is a package capability, not a rail budget">

The L78xx family's 1.5 A rating is a property of the package, not of these rails. The
+5 V rail is budgeted at 0.5 A and its L7805ABD2T evidence bundle records `iout-rating`
as 0.5 A; PTC2 holds at 1.1 A, well under 1.5 A. Sizing a load against "1.5 A per rail"
would exceed both the PTC hold currents and the 26.5 W output budget. See
[Board B → PTC2 hold-current rationale](./board-b-synth-power.md#protection-stage-ptc2-hold-current-rationale-on-the-5-v-rail).

</Warning>

<Note title="Performance figures below are design targets, not measurements">

No rail on this design has yet been energized from a negotiated PD contract — all four
JLCPCB orders (v1-v4) failed at USB-PD negotiation. The efficiency and ripple figures on
this page are design intent for the DC-DC + linear topology, and become measurements only
after Board A bring-up. See [Project Status and Plan](../inbox/current-status.md).

</Note>

## Stage 1: USB-PD Voltage Acquisition (Board A)

Source: `scripts/schgen/board_a_spec.py`. The full design rationale for this stage is on
the [Board A: USB-PD Core](./board-a-usb-pd-core.md) page; the table below is the parts
list only.

### Main ICs, connector, and protection

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application | Reference |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | --------- |
| **U1** | **[C2678061](https://jlcpcb.com/partdetail/C2678061)** | **STUSB4500QTR** | USB-IF certified PD sink | QFN-24 | **$2.50** | PD negotiation (15 V) | [Board A](./board-a-usb-pd-core.md#component-list-lcsc-parts-and-rough-cost) |
| **Q1** | **[C347476](https://jlcpcb.com/partdetail/C347476)** | **AO3401A** (UMW) | P-channel MOSFET -30 V -4 A | SOT-23 | **$0.02** | Load switch (high-side) | [Board A](./board-a-usb-pd-core.md#load-switch-q1-gate-network-and-soft-start) |
| **J1** | **[C456012](https://jlcpcb.com/partdetail/C456012)** | **USB-TYPE-C-009** | 6P Type-C female | SMD | **$0.05** | USB-C input | [Board A](./board-a-usb-pd-core.md#component-list-lcsc-parts-and-rough-cost-j1-substitution-options) |
| **D5** | **[C571370](https://jlcpcb.com/partdetail/C571370)** | **SMAJ20A** | 20 V unidirectional TVS | SMA | **~$0.15** (est.) | VBUS clamp — cathode `VBUS_IN`, anode `GND` | [Board A](./board-a-usb-pd-core.md#deltas-vs-the-current-single-board-circuit) |
| **D8** | **[C92321](https://jlcpcb.com/partdetail/C92321)** | **BZT52C11-7-F** (Diodes Inc.) | Zener, Vz 10.4-11.6 V | SOD-123 | **$0.054** | Q1 gate-source clamp — cathode `VBUS_IN`, anode `Net-(Q1-G)` | [Board A](./board-a-usb-pd-core.md#programming-order-and-the-d8-gate-clamp) |
| **J4** | **[C144397](https://jlcpcb.com/partdetail/C144397)** | **B6B-XH-A(LF)(SN)** (JST) | 6-pin shrouded header, 2.5 mm | THT | **~$0.08** (est.) | Board A → Board B interface | [Board A](./board-a-usb-pd-core.md#a↔b-interface-contract-locked-—-copied-verbatim-from-90) |

<Warning title="D4 (USBLC6-2SC6) is gone, not optional">

Older revisions of this page listed `D4` (USBLC6-2SC6, C7519) under an "ESD Protection
(Recommended)" heading. It was **deleted from the design**, not downgraded: its VBUS-clamp
role was a hard absolute-maximum violation (a 6 V-rated zener on a 15 V rail), and its
CC-ESD role duplicated U1's own integrated 22 V protection while routing CC continuity
through a part-internal flow-through — a silent-failure path that was a live candidate in
the v4 diagnosis. CC1/CC2 now run as direct copper from J1 to U1. See
[Board A → Deltas](./board-a-usb-pd-core.md#deltas-vs-the-current-single-board-circuit).

</Warning>

### Capacitors

| Symbol | Part Number | Specification | Package | Price | Application |
| ------ | ----------- | ------------- | ------- | ----- | ----------- |
| **C1** | **[C13585](https://jlcpcb.com/partdetail/C13585)** | 10 µF 50 V (CL31A106KBHNNNE) | 1206 | **$0.024** | VBUS bulk filter |
| **C2** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | 100 nF 50 V X7R | 0805 | **$0.0021** | VDD HF decoupling |
| **C30** | **[C15849](https://jlcpcb.com/partdetail/C15849)** | 1 µF 50 V (CL10A105KB8NNNC) | 0603 | **$0.001** | VREG_2V7 decoupling |
| **C34** | **[C15849](https://jlcpcb.com/partdetail/C15849)** | 1 µF 50 V (CL10A105KB8NNNC) | 0603 | **$0.001** | VREG_1V2 decoupling |
| **C35** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | 100 nF 50 V X7R | 0805 | **$0.0021** | Gate soft-start |

### Resistors

| Symbol | Part Number | Value | Description | Package | Price | Application |
| ------ | ----------- | ----- | ----------- | ------- | ----- | ----------- |
| **R11** | **[C25803](https://jlcpcb.com/partdetail/C25803)** | 100 kΩ | ±1% 100 mW | 0603 | **$0.0005** | Gate pull-up (default OFF) |
| **R12** | **[C23206](https://jlcpcb.com/partdetail/C23206)** | 56 kΩ | ±1% 100 mW | 0603 | **$0.0005** | Gate series resistor from `VBEN` |
| **R13** | **[C23179](https://jlcpcb.com/partdetail/C23179)** | 470 Ω | ±1% 100 mW | 0603 | **$0.0005** | DISCH (U1.9) to `VBUS_OUT` |
| **R14** | **[C23179](https://jlcpcb.com/partdetail/C23179)** | 470 Ω | ±1% 100 mW | 0603 | **$0.0005** | Pin-18 (`VBUS_VS_DISCH`) series R — the v3 fix |
| **R15** | **[C23162](https://jlcpcb.com/partdetail/C23162)** | 4.7 kΩ | ±1% 100 mW | 0603 | **$0.0005** | I2C SCL pull-up (to VREG_2V7) |
| **R16** | **[C23162](https://jlcpcb.com/partdetail/C23162)** | 4.7 kΩ | ±1% 100 mW | 0603 | **$0.0005** | I2C SDA pull-up (to VREG_2V7) |
| **R19** | **[C21189](https://jlcpcb.com/partdetail/C21189)** | 0 Ω | ±1% 100 mW | 0603 | **$0.0005** | CC1DB↔CC1 link (dead-battery termination) |
| **R20** | **[C21189](https://jlcpcb.com/partdetail/C21189)** | 0 Ω | ±1% 100 mW | 0603 | **$0.0005** | CC2DB↔CC2 link (dead-battery termination) |

### DNP provisions (footprint placed, not populated, excluded from BOM/CPL)

| Symbol | Part Number | Value / Part | Package | Why it is DNP |
| ------ | ----------- | ------------ | ------- | ------------- |
| **R17, R18** | **[C23186](https://jlcpcb.com/partdetail/C23186)** | 5.1 kΩ external Rd | 0603 | Rework insurance only. Fitted, they parallel U1's own always-on internal 5.1 kΩ Rd and put CC termination outside the USB Type-C sink window (2.55 kΩ effective) the moment U1 powers up — the v4 blocker |
| **D6, D7** | **[C85382](https://jlcpcb.com/partdetail/C85382)** | PESD24VS1UB (Nexperia) | SOD-523 | CC-line ESD provision, one per CC line to GND. Fit for enclosed/production builds, not for the bring-up/debug build |

### Zero-cost pads

| Symbol | Form | Purpose |
| ------ | ---- | ------- |
| **J2** | Pogo pads, 1×4, 2.54 mm (bare copper) | NVM I2C programming — see [NVM Programming Setup](../inbox/nvm-programming.md) |
| **J3** | Pogo pads, 1×8, 2.54 mm (bare copper) | Debug pads |
| **TP1, TP2, TP6** | Test pads, D1.5 mm | `VBUS_OUT` / `GND` / `VBUS_VS_DISCH` probes |

**Stage 1 subtotal: ~$2.90** (fitted parts only, J4 included). U1 alone is ~86% of it.
Matches the itemized figure on
[Board A → Component list](./board-a-usb-pd-core.md#component-list-lcsc-parts-and-rough-cost).

**Key features (STUSB4500 vs the v1.0 CH224D design):**

| Feature | CH224D (v1.0) | STUSB4500 (current) |
| ------- | ------------- | ------------------- |
| **USB-IF certified** | No | **Yes** |
| **Charger compatibility** | ~33% | **~95%+** |
| **Error recovery** | None | **Built-in retry** |
| **Power sequencing** | None | **VBUS_EN_SNK pin** |
| **CC protection** | 8 V | **22 V** |
| **Configuration** | Resistor | **NVM + I2C** |

**Critical notes:**

- **Load switch (Q1)** controls the power path — it only conducts after successful PD negotiation
- **VBUS_EN_SNK** (U1.16, active-low, open-drain) pulls LOW on success, turning Q1 ON
- **Soft-start** via C35 limits inrush: τ = R12 × C35 = 56 kΩ × 100 nF = 5.6 ms
- **NVM programming** is required to configure the 15 V PDO (one-time setup), and must be done **before** first attach to a 20 V-capable source. D8 is the hardware guard for the case where it is not — see [Board A → Programming order and the D8 gate clamp](./board-a-usb-pd-core.md#programming-order-and-the-d8-gate-clamp)

## Stage 2: DC-DC Converters (Board B)

Three LM2596S-ADJ: U2 and U3 as buck converters, U4 in an **inverting buck-boost**
configuration. There is no LM2586 and no SEPIC anywhere in this design — decision (b) in
`scripts/schgen/decisions.json` locks that wording against the schematic.

### Main ICs

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application | Diagram |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | ------- |
| **U2** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](./board-b-synth-power.md#dc-dc-conversion-stage)** | Adjustable 3 A buck | TO-263-5 | **$0.266** | +15 V → +13.5 V | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **U3** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](./board-b-synth-power.md#dc-dc-conversion-stage)** | Adjustable 3 A buck | TO-263-5 | **$0.266** | +15 V → +7.5 V | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **U4** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](./board-b-synth-power.md#dc-dc-conversion-stage)** | Same IC, inverting buck-boost | TO-263-5 | **$0.266** | +15 V → -13.5 V | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

### Inductors

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application | Diagram |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | ------- |
| **L1** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH** | 100 µH 4.5 A | SMD, 13.8×12.8 mm | **$0.378** | U2 energy storage | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **L2** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH** | 100 µH 4.5 A | SMD, 13.8×12.8 mm | **$0.378** | U3 energy storage | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **L3** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH** | 100 µH 4.5 A | SMD, 13.8×12.8 mm | **$0.378** | U4 energy storage (`L3.2` on system GND) | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

### Diodes

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application | Diagram |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | ------- |
| **D1** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34** | 3 A 40 V Schottky | SMA | **$0.012** | U2 freewheeling (cathode to switch node, anode to GND) | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **D2** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34** | 3 A 40 V Schottky | SMA | **$0.012** | U3 freewheeling (cathode to switch node, anode to GND) | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **D3** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34** | 3 A 40 V Schottky | SMA | **$0.012** | U4 catch diode (cathode to switch node, anode to -13.5 V) | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

All three catch/freewheeling positions are the **same** SS34, LCSC C8678. An "SS36, 60 V"
figure circulated for D3 in older revisions of the circuit-diagram page; the fitted part is
the 40 V SS34 at every position.

### Feedback resistors

| Symbol | Part Number | Value | Description | Package | Price | Application | Diagram |
| ------ | ----------- | ----- | ----------- | ------- | ----- | ----------- | ------- |
| **R1** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | **10 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U2 FB upper | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **R2** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U2 FB lower | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **R3** | **[C23186](https://jlcpcb.com/partdetail/C23186)** | **5.1 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U3 FB upper | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **R4** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U3 FB lower | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **R5** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | **10 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U4 FB upper | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |
| **R6** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1 kΩ** | ±1% 100 mW | 0603 | **$0.0005** | U4 FB lower | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

R1 stays 10 kΩ by decision (f): the +13.5 V setpoint's dropout margin against U6 is
recorded as an open bench item, **not** changed on paper.

### Electrolytic capacitors

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **C3** | **[C2983319](https://jlcpcb.com/partdetail/C2983319)** | **470 µF 25 V** (GVT1E477M0810CNVC) | D8 | **$0.04** | U2 output filter | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **C4** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470 µF 10 V** (ROQANG RVT1A471M0607) | D6.3 | **$0.05** | U3 output filter | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **C5** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** (FOLLON EFVH035ADA471M10B0) | D10 | **$0.04** | U2 input bulk | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **C7** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** (FOLLON EFVH035ADA471M10B0) | D10 | **$0.04** | U3 input bulk | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **C9** | **[C970687](https://jlcpcb.com/partdetail/C970687)** | **100 µF 50 V** (DMBJ RVT1H101M0810) | D8 | **~$0.05** (est.) | U4 input bulk — bridges +15 V to -13.5 V, 28.5 V of stress | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |
| **C11** | **[C2983319](https://jlcpcb.com/partdetail/C2983319)** | **470 µF 25 V** (GVT1E477M0810CNVC) | D8 | **$0.04** | U4 output filter | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |
| **C12** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** (FOLLON EFVH035ADA471M10B0) | D10 | **$0.04** | U4 output filter, added in parallel with C11 (decision `neg-rail-cap-bank`, resolves the BB-7 ripple over-rating) | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

<Info title="Three wave-6 electrolytic corrections land in this table">

- **C5 / C7** were 100 µF / 25 V (ACMECON C22383804). Decision (d) swapped them to the
  470 µF / 35 V FOLLON line already fitted at five other positions. The 25 V part held
  only 5 V of margin at the 20 V mis-contract edge and was exceeded by 7.4 V at the D5
  clamp table point; the 35 V part makes every exposure positive (+2.6 V at that clamp
  point). It also raises total input bulk from 200 µF to 940 µF. **Package consequence:**
  these two positions move from a D6.3 can to a D10 can.
- **C4** (with C22/C23 in Stage 3) carried LCSC **C22383803** and a "470 µF 16 V" value.
  Decision (c) canonicalizes them on **C335982**, the 10 V ROQANG part that matches the
  drawn symbol; C22383803 is recorded as the alias and is in fact a 16 V listing. 10 V is
  safe on the 7.5 V and 5 V nets these sit on.
- **C9** is the DMBJ RVT1H101M0810 (C970687) 100 µF **50 V** part fixed in #93 — the
  original 25 V part was under-rated for the 28.5 V this position bridges.

</Info>

### Ceramic capacitors (DC-DC stage)

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **C6** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U2 input decoupling | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **C8** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U3 input decoupling | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **C10** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U4 input decoupling | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |
| **C31** | **[C1729](https://jlcpcb.com/partdetail/C1729)** | **22 nF** (CL21B223KBANNNC) | 0805 | **$0.002** | U2 feedback compensation | [D2](./circuit-diagrams.mdx#diagram2-usb-pd-15v-→-13-5v-buck-converter-lm2596s-adj-1) |
| **C32** | **[C1729](https://jlcpcb.com/partdetail/C1729)** | **22 nF** (CL21B223KBANNNC) | 0805 | **$0.002** | U3 feedback compensation | [D3](./circuit-diagrams.mdx#diagram3-15v-→-7-5v-buck-converter-lm2596s-adj-2-u3) |
| **C33** | **[C1729](https://jlcpcb.com/partdetail/C1729)** | **22 nF** (CL21B223KBANNNC) | 0805 | **$0.002** | U4 feedback compensation | [D4](./circuit-diagrams.mdx#diagram4-15v-→--13-5v-inverting-buck-boost-lm2596s-adj-u4) |

**Stage 2 subtotal: ~$2.28** (includes the C9 estimate and C12, added by decision
`neg-rail-cap-bank`).

## Stage 3: Linear Regulators (Board B)

### Regulator ICs

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application | Diagram |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | ------- |
| **U6** | **[C13456](https://jlcpcb.com/partdetail/C13456)** | **[L7812CD2T](./board-b-synth-power.md#linear-regulator-ldo-stage)** | +12 V positive LDO | TO-263-2 | **$0.11** | +12 V output | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **U7** | **[C86206](https://jlcpcb.com/partdetail/C86206)** | **[L7805ABD2T](./board-b-synth-power.md#linear-regulator-ldo-stage)** | +5 V positive LDO | TO-263-2 | **$0.11** | +5 V output | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **U8** | **[C94173](https://jlcpcb.com/partdetail/C94173)** | **[CJ7912](./board-b-synth-power.md#linear-regulator-ldo-stage)** | -12 V negative LDO (79xx pinout) | TO-252-3 | **$0.11** | -12 V output | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

### Ceramic input capacitors (470 nF)

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **C15** | **[C1623](https://jlcpcb.com/partdetail/C1623)** | **470 nF** (CL10B474KA8NNNC) | 0603 | **$0.0036** | U7 input filter | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **C16** | **[C1623](https://jlcpcb.com/partdetail/C1623)** | **470 nF** (CL10B474KA8NNNC) | 0603 | **$0.0036** | U8 input filter | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

U6 has **no** 470 nF ceramic on its input, unlike U7 and U8. The bypass parts
`board_b_spec.py` places on the `+13.5V OUT` net alongside `U6.1` are `C14.1` and `C20.1`
— two 470 µF / 35 V electrolytics — with the rest of that net being U2's own output filter
(`C3.1`), the feedback network (`R1.2`, `C31.2`), and the `TP3` test pad. That asymmetry
against U7/U8 is real, not a documentation gap.

### Ceramic output capacitors (100 nF)

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **C17** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U6 output filter | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **C18** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U7 output filter | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **C19** | **[C1711](https://jlcpcb.com/partdetail/C1711)** | **100 nF 50 V X7R** | 0805 | **$0.0021** | U8 output filter | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

### Large electrolytic capacitors (LDO stage)

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **C14** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** | D10 | **$0.04** | U6 input | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **C20** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** | D10 | **$0.04** | U6 input | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **C21** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** | D10 | **$0.04** | U6 output | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **C22** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470 µF 10 V** | D6.3 | **$0.05** | U7 input | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **C23** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470 µF 10 V** | D6.3 | **$0.05** | U7 output | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **C24** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** | D10 | **$0.04** | U8 input (polarity reversed: − to -13.5 V, + to GND) | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |
| **C25** | **[C22387780](https://jlcpcb.com/partdetail/C22387780)** | **470 µF 35 V** | D10 | **$0.04** | U8 output (polarity reversed: − to -12 V, + to GND) | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

**Stage 3 subtotal: ~$0.64.** Earlier revisions of this page quoted **$0.37** here; that
figure counted the three regulators and left the seven bulk electrolytics out.

<Warning title="U6's dropout margin is an open bench item">

13.5 V in, 12 V out leaves **1.5 V** against the L7812's 2.0 V *typical* dropout at 1 A,
and DS0422 states no dropout figure at all at this rail's 1.2 A load. Decision (f) records
the arithmetic and makes **no spec change**: R1 stays 10 kΩ and the setpoint stays 13.5 V
until bench measurement shows whether the part actually drops out under real load. Do not
read the 13.5 V rail as proven headroom.

</Warning>

## Stage 4: Protection and Rail Indicators (Board B)

### PTC resettable fuses

| Symbol | Part Number | Manufacturer Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------------------ | ------------- | ------- | ----- | ----------- | ------- |
| **PTC1** | **[C7529589](https://jlcpcb.com/partdetail/C7529589)** | **[SMD1210P150TF/16](./board-b-synth-power.md#protection-stage)** (RUILON) | **1.5 A hold / 3.0 A trip, Vmax 16 V** | 1210 | **$0.095** | +12 V rail protection | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **PTC2** | **[C70119](https://jlcpcb.com/partdetail/C70119)** | **[mSMD110-33V](./board-b-synth-power.md#protection-stage)** | **1.1 A hold / 2.2 A trip, Vmax 33 V** | 1812 | **$0.10** | +5 V rail protection | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **PTC3** | **[C883133](https://jlcpcb.com/partdetail/C883133)** | **[BSMD1206-150-16V](./board-b-synth-power.md#protection-stage)** | **1.5 A hold / 3.0 A trip, Vmax 16 V** | 1206 | **$0.14** | -12 V rail protection | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

<Warning title="PTC1 is a wave-6 replacement — do not order the C20808 part">

`SMD1210P200TF` (C20808) was the fitted PTC1 through v4. Its primary-sourced **Vmax is
6 VDC** — a deterministic blocker on a +12 V rail (finding BB-1). Decision (g) replaces it
with the 16 V `SMD1210P150TF/16` (C7529589). The trade is hold-current margin: 1.5 A hold
against the 1.2 A budget instead of 2.0 A. No 16 V part exists at the 2 A hold rating in a
1210 package; `SMD1812P200TF16` (C20812) is the recorded fallback if the 1.5 A part
nuisance-trips at elevated ambient, at the cost of a footprint change.

</Warning>

**Protection philosophy:**

- **PTC-only design** — no backup fuses (traditional fuses are not available on JLCPCB assembly)
- **Linear regulators act first**: their current limiting is electronic and near-instant, while a PTC is thermal and takes seconds to trip. PTC1/2/3 are backstops for the case where the regulator's own protection is bypassed or defeated
- **Four layers**: USB-PD source → DC-DC → linear regulator → PTC
- **Auto-reset**: 30-60 s cooling, no manual fuse replacement

<Warning title="The regulators' own limit thresholds are not in this project's evidence base">

Figures such as "≈2.2 A current limit" and "150 °C thermal shutdown" appeared in earlier
revisions of this page. The L7812CD2T bundle retains **no** current-limit figure and **no**
thermal-shutdown temperature — only a `TJ` range of 0-125 °C. The *ordering* of the cascade
above is sound and is why the design works; the regulator-side numbers must come from
DS0422 or a bench measurement before anyone designs against them. See
[Board B → PTC1 and the L7812 current-limit cascade](./board-b-synth-power.md#protection-stage-ptc1-and-the-l7812-current-limit-cascade).

</Warning>

### TVS diodes

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Orientation | Diagram |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- | ------- |
| **TVS1** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **[SMAJ15A](./board-b-synth-power.md#protection-stage)** | 15 V unidirectional, VC 24.4 V | SMA | **$0.15** | Cathode → +12 V rail, anode → GND | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **TVS2** | **[C87267](https://jlcpcb.com/partdetail/C87267)** | **[SMAJ6.5A](./board-b-synth-power.md#protection-stage)** (Brightking) | VRWM 6.5 V, breakdown ≥7.22 V, VC 11.2 V | SMA | **~$0.15** (est.) | Cathode → +5 V rail, anode → GND | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **TVS3** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **[SMAJ15A](./board-b-synth-power.md#protection-stage)** | 15 V unidirectional, VC 24.4 V | SMA | **$0.15** | **Cathode → GND, anode → -12 V rail** (reversed) | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

<Warning title="TVS2 is a wave-6 replacement, and TVS3's orientation is a locked spec point">

`SD05` (C502527) was the fitted TVS2. Its 5 V standoff sits exactly at the +5 V rail's
nominal and **below** the L7805's guaranteed 5.2 V band top, so it could conduct during
normal regulation (finding BB-2). Decision (a) replaces it with the SMA-package
`SMAJ6.5A` (C87267), which keeps the D-FLAT footprint family shared by TVS1/TVS3/D5.

TVS3 is unidirectional and **reversed** relative to TVS1/TVS2. Fitted the other way round
it is forward-biased at -12 V — a dead short through one diode drop, from power-on.
Decision `tvs3-orientation` requires `board_b_spec.py` to carry it as explicit pin-to-net
rows (`TVS3.1` on `GND`, `TVS3.2` on `-12V rail`), which it does.

</Warning>

### Status indicator LEDs

| Symbol | Part Number | Specification | Package | Price | Application | Diagram |
| ------ | ----------- | ------------- | ------- | ----- | ----------- | ------- |
| **LED2** | **[C2289](https://jlcpcb.com/partdetail/C2289)** | **KT-0603YG green** (pin 1 = anode) | 0603 | **$0.01** | +12 V status | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **LED3** | **[C2288](https://jlcpcb.com/partdetail/C2288)** | **KT-0603B blue** (pin 1 = cathode) | 0603 | **$0.01** | +5 V status | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **LED4** | **[C2286](https://jlcpcb.com/partdetail/C2286)** | **KT-0603R red** (pin 1 = cathode) | 0603 | **$0.01** | -12 V status (conducts from GND into the rail) | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |
| **R7** | **[C17513](https://jlcpcb.com/partdetail/C17513)** | **1 kΩ** (0805W8F1001T5E) | 0805 | **$0.001** | LED2 current limit (~10 mA) | [D5](./circuit-diagrams.mdx#diagram5-13-5v-→-12v-linear-regulator-l7812-u6) |
| **R8** | **[C17513](https://jlcpcb.com/partdetail/C17513)** | **1 kΩ** (0805W8F1001T5E) | 0805 | **$0.001** | LED3 current limit (~2.2 mA) | [D6](./circuit-diagrams.mdx#diagram6-7-5v-→-5v-linear-regulator-l7805-u7) |
| **R9** | **[C17513](https://jlcpcb.com/partdetail/C17513)** | **1 kΩ** (0805W8F1001T5E) | 0805 | **$0.001** | LED4 current limit (~10 mA) | [D7](./circuit-diagrams.mdx#diagram7--13-5v-→--12v-linear-regulator-cj7912-u8) |

All three indicator resistors are **1 kΩ**. A "330 Ω for R8" figure appeared in older
revisions of the circuit-diagram page; `board_b_spec.py` fits the same 1 kΩ 0805 line
(C17513) at R7, R8 and R9. The +5 V indicator is therefore the dim one — ~2.2 mA against
~10 mA on the ±12 V rails.

**Stage 4 subtotal: ~$0.82.**

## Stage 5: Output Connectors and Interface (Board B)

### Eurorack power connectors (16-pin)

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- |
| **J10, J11** | **[C5383092](https://jlcpcb.com/partdetail/C5383092)** | **2541WR-2X08P** | 2×8P pin header, 2.54 mm | Through-hole | **$0.08 × 2** | Eurorack power output |

**Connector type:** standard 2×8 pin header (male, through-hole, 2.54 mm pitch).

**Note:** these are plain pin headers. For box/shrouded connectors (common in Eurorack),
source the mating female box header separately — Tayda Electronics, Mouser/Digikey, or
another distributor.

**Eurorack 16-pin pinout (flipped for a bottom-facing PCB):**

```
  GATE  [ 1]  [ 2]  GATE
  CV    [ 3]  [ 4]  CV
  +5V   [ 5]  [ 6]  +5V
  +12V  [ 7]  [ 8]  +12V
  GND   [ 9]  [10]  GND
  GND   [11]  [12]  GND
  GND   [13]  [14]  GND
  -12V  [15]  [16]  -12V   ← Red stripe side
```

Pins 9-14 are the GND moat, per `board_b_spec.py`'s `GND` net (`J10.9`-`J10.14`,
`J11.9`-`J11.14`) — six ground contacts per header, not the "n/c" pairs older revisions of
this page showed.

**Design note:** the pinout is vertically flipped from the standard Eurorack orientation
because the PCB mounts facing downward. Viewed from the module side (looking up at the
PCB), the red stripe (-12 V) is at the bottom as expected.

**Note:** the GATE (pins 1-2) and CV (pins 3-4) rails are carried through to both headers
but are not driven by this supply — they exist so a bus board sees a complete Eurorack
header.

### Individual power terminals

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Price | Application |
| ------ | ----------- | ------------------------ | ----------- | ------- | ----- | ----------- |
| **J6-J9** | **[C591344](https://jlcpcb.com/partdetail/C591344)** | **[63951-1](./board-b-synth-power.md#output-connectors)** (×4) | FASTON 250 PCB tab, 6.35 mm | Through-hole | **~$0.26 × 4** | Individual power output |

| Terminal | Signal | Rating |
| -------- | ------ | ------ |
| **J6** | -12 V | 7 A (connector rating) |
| **J7** | +12 V | 7 A (connector rating) |
| **J8** | +5 V | 7 A (connector rating) |
| **J9** | GND | 7 A (connector rating) |

**Purpose:** direct wire or busboard connection. FASTON 250 terminals take thick-gauge
wire for low-resistance, low-noise delivery. Requires matching FASTON receptacles.
Combined GND return is ~2.5 A max — well inside the 7 A connector rating.

### Interface, provisions, and test pads

| Symbol | Part Number | Description | Package | Price | Application |
| ------ | ----------- | ----------- | ------- | ----- | ----------- |
| **J5** | **[C144397](https://jlcpcb.com/partdetail/C144397)** | **B6B-XH-A(LF)(SN)** (JST), 6-pin, 2.5 mm | THT | **~$0.08** (est.) | Board A → Board B interface (mates with Board A's J4) |
| **P1** | — (bare pads) | Pogo pads, 1×4, 2.54 mm | Custom SMD | **$0** | ATT/PDOK probe: 1 = ATT (`J5.3`), 2 = PDOK (`J5.4`), 3 = GND return, 4 = no-connect |
| **TP3, TP4, TP5** | — | Test pads, D1.5 mm | Custom SMD | **$0** | +13.5 V / +7.5 V / -13.5 V rail probes |

P1 is placed as **bare pads** (`in_bom = no`, `on_board = yes`) per decision `p1-form` —
the library carries no 2-pin test symbol, so the epic's "2-pin provision" resolves to a
single 1×4 pad row with a probe ground return at zero BOM cost. ATT and PDOK are
open-drain with **no on-board pull-up on either board**; any consumer wired to P1 must
supply its own pull-up to its own logic rail.

**Stage 5 subtotal: ~$1.28** (headers $0.16 + FASTON ~$1.04 + J5 ~$0.08).

## Component Heights

Full height table and enclosure implications: **[Mechanical Design](./mechanical-design.md)**.

The tallest parts are the 470 µF electrolytics, then the FASTON terminals at 8.89 mm.
Total board height is ~12 mm including the 1.6 mm PCB. The exact can height is stated
once, in [Mechanical Design](./mechanical-design.md) — do not restate it here, so the
two pages cannot drift apart again. Note that
decision (d)'s C5/C7 swap moved those two positions from a D6.3 can to a D10 can, and
decision `neg-rail-cap-bank` then added a new D10 can, C12, in parallel with C11 on the
−13.5 V output. Board B now carries **eight** D10 electrolytics (C5, C7, C12, C14, C20,
C21, C24, C25 are D10; C3, C9, C11 are D8; C4, C22, C23 are D6.3). C3/C11 were counted
as D10 until issue #150: the fitted part there (C2983319, GVT1E477M0810CNVC) is a
Φ8 × 10.5 mm can per its datasheet, and had simply been assigned the Φ10 land by
mistake; C12 is a different, freshly-added position and was never subject to that
mistake — it is a genuine Φ10 × 10.5 mm FOLLON can from the start.

## Total Cost Summary

| Stage | Description | Board | Subtotal |
| ----- | ----------- | ----- | -------- |
| **Stage 1** | USB-PD voltage acquisition (incl. J4) | A | **~$2.90** |
| **Stage 2** | DC-DC converters | B | **~$2.28** |
| **Stage 3** | Linear regulators | B | **~$0.64** |
| **Stage 4** | Protection + indicators | B | **~$0.82** |
| **Stage 5** | Output connectors + J5/P1/test pads | B | **~$1.28** |
| | **Board A total** (Stage 1) | A | **~$2.90** |
| | **Board B total** (Stages 2-5) | B | **~$5.02** |
| | **Both boards, components only** | | **~$7.92** |

<Note title="These totals are recomputed, and they are larger than the figures this page used to show">

The old summary quoted **$3.96** for the whole design. That number was built on three
subtotals that did not match their own tables: Stage 1 was listed as $0.45 while its table
contained a $2.50 STUSB4500; Stage 3 was $0.37 with seven bulk electrolytics uncounted;
Stage 5 was $0.28 against a FASTON line that alone comes to ~$1.04. The figures above are
summed directly from the tables on this page. Two lines carry an explicit estimate (C9,
TVS2) and one carries a dated LCSC reading (PTC1, $0.0946 @ 5 pcs, 2026-08-14) — re-verify
everything at order time.

</Note>

**Notes:**

- Prices are estimates from the JLCPCB part catalog and exclude PCB fabrication and assembly fees
- The PTC-only protection design removes the fuse line items entirely

## JLCPCB Assembly Cost Structure

The component prices above are only part of the total PCBA cost. JLCPCB charges additional
fees. The figures in this section describe the **v4 single combined board** — the design
that was actually ordered four times. Board A and Board B have no layout or order files
yet, so no split figures exist.

### Fee Types

| Fee | Description | Typical Cost |
| --- | ----------- | ------------ |
| **PCB Fabrication** | Board manufacturing | ¥500-1,000 |
| **Setup Fee** | One-time assembly setup | ~¥1,250 |
| **Stencil** | Solder paste stencil | ~¥235 |
| **SMT Assembly** | Per-placement fee | ~¥145 |
| **Extended Parts Fee** | Per unique Extended part | **¥470 each** |
| **Hand-soldering** | THT components | ~¥550 |

### Basic vs Extended Parts

JLCPCB classifies components into two categories:

- **Basic Parts**: common resistors, MLCCs, some diodes — **no extra fee**
- **Extended Parts**: specialty ICs, electrolytic caps, LEDs, inductors, connectors — **¥470 per unique part number**

The v4 single board used ~20 Extended parts, adding ~¥9,400 to the assembly cost. This is
the number the split is designed to attack: Board A carries roughly 3-4 unique Extended
parts, so a USB-PD-only debug iteration no longer re-pays for inductors, LDOs,
electrolytics, and connectors that were never the failing part.

### Cost Per Board (v4 single board, reference: January 2025)

| Quantity | Total Cost | Per Board |
| -------- | ---------- | --------- |
| 1 board | ~¥16,500 | ¥16,500 |
| 5 boards | ~¥21,000 | ¥4,200 |
| 10 boards | ~¥26,000 | **¥2,600** |

**Key insight**: Extended fees are **one-time setup costs**, not per-board. Ordering more
boards significantly reduces the per-unit cost.

### Cost Optimization Tips

1. **Order in batches of 5-10** to amortize setup fees
2. **Hand-solder large components** (electrolytic caps, connectors) to reduce Extended fees
3. **Use Basic parts** where possible (resistors, MLCCs are usually Basic)
4. **Consolidate part numbers** — fewer unique Extended parts = lower fees. Decision (d)'s
   C5/C7 swap onto the already-fitted 470 µF/35 V line is an instance of exactly this

## Protection Circuit Operation

### Normal operation (current below the PTC hold rating)

- PTC in its low-resistance state, minimal voltage drop
- Linear regulator in normal regulation
- Rail LED lit

PTC series resistance is a budget item, not free protection. The fitted `SMD1210P150TF/16`
has **no retained resistance figure** in this project's evidence base — the C20808
sibling's numbers belong to a different part and must not be substituted. The drop is a
bench measurement against a ≤50 mV project budget at 1.2 A; see
[Board B → PTC1 voltage drop and acceptance testing](./board-b-synth-power.md#protection-stage-ptc1-voltage-drop-and-acceptance-testing).

### Overload (current above the PTC hold rating)

1. PTC heats and its resistance rises
2. LED dims or goes out — the visible fault signal
3. PTC trips within seconds; rail current collapses
4. **User action**: reduce the load
5. **Auto-recovery**: 30-60 s to cool, then the rail returns

### Short circuit (output shorted to GND)

1. **Immediate**: the linear regulator's own current limiting engages — electronic, essentially instant
2. **Seconds**: the PTC warms and trips under the limited current
3. **Sustained**: the regulator's thermal shutdown follows as its die heats
4. **LED**: off (fault indication)
5. **Recovery**: PTC and regulator both auto-reset after cooling

**Key insight:** the regulator limits current long before the PTC can react, which is what
makes PTC-only protection adequate here. The PTC exists for the case where the regulator's
own protection is bypassed — a shorted pass element, or a fault that does not route through
the regulator at all.

## Design Features

### 1. JLCPCB-sourceable

- Heavy use of Basic parts (resistors, MLCCs) — no per-part Extended fee
- Stock and price must be re-verified at order time for every line; several wave-6 picks were made against dated 2026-08-14 readings
- **USB-PD IC**: STUSB4500, USB-IF certified, 15 V support

### 2. Low-noise topology

- **Two-stage**: DC-DC for efficient conversion, linear regulator for the final low-noise output
- **Target ripple**: `<1 mVp-p` at the outputs (design intent, not yet measured)

### 3. Multi-layer protection

- **Four layers**: USB-PD source → DC-DC → linear regulator → PTC
- **Auto-reset**: no fuse replacement, 30-60 s recovery
- **Visual feedback**: per-rail status LEDs
- **Board A additions**: D5 clamps VBUS; D8 clamps Q1's gate-source against the unprogrammed-NVM 20 V case

### 4. Implementation

- **SMD-first**: compatible with automated PCBA assembly; the FASTON tabs and 2×8 headers are the THT exceptions
- **Separated design**: DC-DC and linear stages physically separated, and now the USB-PD front end is a separate board entirely
