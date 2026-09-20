---
title: Board Split Decision — Fix List + A/B Interface Contract
sidebar_position: 15
description: Locked decisions from the wave-2 decision pass (#90) - the front-end fix list for the existing KiCad project / Board A, the Board A to Board B interface contract with current-rating math, and the doc-structure assumption.
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

This page is the **single source of truth** for the three decision sets locked by the
board-split decision task (epic #86, sub-issue #90). It consumes the three wave-1
analysis artifacts:

- [v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md) (#87) — ranked root
  causes + bench discrimination procedure
- [v4 As-Built Order Verification &amp; Footprint Geometry Audit](./v4-asbuilt-audit.md) (#88)
  — as-built and footprint verdicts
- [Board B Architecture Review](./board-b-architecture-review.md) (#89) — DC-DC/LDO/protection
  review with 3 blockers

<Note>

Everything marked **LOCKED** below is the implementable spec for the wave-3 tasks
(#91 Board A doc, #92 Board B doc, #93 KiCad fixes). Items marked
**bench-confirm-first** are gated on the bench procedure in
[v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md) and must NOT be
implemented before their stated gate passes.

</Note>

## Decision set (a) — front-end fix list

### A1. CCDB topology — LOCKED: restore `CC1DB↔CC1` / `CC2DB↔CC2`, external Rd to DNP

**Decision.** Return to the ST reference wiring for a VBUS-only sink:

- `CC1DB` (U1 pin 1) joined to the CC1 line, and `CC2DB` (U1 pin 5) joined to the CC2
  line, each **through a 0 Ω link** — implemented by repurposing the existing R19/R20
  (0 Ω, LCSC C21189): their GND-side ends move from `GND` to the CC1/CC2 nets. The 0 Ω
  links double as fallback jumpers: removing them isolates the DB pins again for rework.
- R17/R18 (external 5.1 kΩ Rd, LCSC C23186) become **DNP** (footprints stay as rework
  insurance; excluded from BOM/CPL so JLCPCB never populates them).

**Justification.** Per the #87 diagnosis: DS12499 Rev 4 §7.3 Table 22 gives the
STUSB4500 a non-disableable internal Rd of 5.1 kΩ ±10% whenever it is powered, so the
v2→v4 topology (external 5.1 kΩ Rd + grounded DB pins) presents **2.55 kΩ effective the
moment U1 boots** — below the USB Type-C sink window (5.1 kΩ ±20%), landing the
source-seen CC voltage inside or below the Ra/Rd undefined band (0.84 V at 3 A Rp).
DS12499 §3.5 states dead-battery mode "is also used in systems that are powered through
the VBUS only" — i.e. `CCxDB↔CCx` with **no** external Rd is ST's intended topology for
exactly this board (also used by the SparkFun breakout and STEVAL-ISC005V1). The v2
"CC1DB chip-internal short" evidence that motivated the external-Rd redesign was
re-examined in #87 and found inconclusive, while the redesign itself is a provable spec
violation on every powered attach.

**Fallback insurance.** If bench test C2/C3 ever rehabilitates the bad-CCDB theory for
a specific chip batch: remove R19/R20 (isolates the DB pins), fit R17/R18, and bodge the
DB-side R19/R20 pads to GND — restoring the v4 topology without a board respin.

### A2. VBUS ESD/TVS strategy — LOCKED: remove D4; SMAJ20A on VBUS; CC ESD provision DNP

**Decision on D4 (USBLC6-2SC6, LCSC C7519): remove entirely** (not relocate, not keep).
Its two roles are re-covered separately:

1. **VBUS clamp → SMAJ20A** (SMA/DO-214AC, unidirectional): new part on `VBUS_IN` to
   GND, cathode on `VBUS_IN`. Primary pick: **LCSC C571370** ("High Diode" brand — the
   same family and SMA footprint as the project's existing SMAJ15A / C571368 used for
   TVS1/TVS3, so the library symbol/footprint pattern is cloned, not invented).
   Alternate if C571370 is out of stock at order time: STMicroelectronics SMAJ20A-TR,
   **LCSC C1973455**. Stock was confirmed listed at LCSC on 2026-07-05; **re-verify
   stock at order time**.
   - Ratings: VRWM 20 V, VBR 22.2–24.5 V, clamping ≤32.4 V (10/1000 µs).
   - Why a 20 V standoff: the rail is 15 V by contract, so a 15 V-standoff part would
     sit at 0% margin (the exact mistake #89 flagged for TVS2/SD05 on the +5 V rail);
     20 V standoff gives 33% margin at 15 V **and** stays non-conducting through the
     20 V mis-contract edge case #89 guards against, while the ≤32.4 V clamp stays
     inside the LM2596S abs-max (40 V).
   - Residual (accepted): a hard surge clamp can momentarily exceed Q1/AO3401A's
     −30 V VDS rating; this is transient-only, far better than v4's 6 V zener on the
     15 V rail, and Board A's layout phase may upgrade to an SMBJ20A if desired.
2. **CC-line ESD → U1's integrated protection, plus a DNP provision.** DS12499 rates
   the STUSB4500's CC pins for 22 V short-to-VBUS with integrated ESD structures — ST's
   own reference designs put nothing between the receptacle CC pins and the chip. The
   fitted Board A build therefore has **no external CC ESD part** (minimum parts between
   connector and chip, which is also what kills root-cause candidate 3 permanently —
   see A4). The Board A **layout** provisions two DNP footprints, one per CC line to
   GND: **Nexperia PESD24VS1UB** (SOD-523, unidirectional, VRWM 24 V, low capacitance),
   **LCSC C85382** (stock confirmed listed 2026-07-05; re-verify at order time). VRWM
   24 V is chosen deliberately **above** U1's 22 V CC fault rating so a fitted part
   never becomes the weakest link during a CC-short-to-VBUS fault; a 5 V-class USB ESD
   array on a PD CC line would repeat the D4 mistake. Fit them only for
   enclosed/production builds.

**Why removal beats relocation.** Keeping USBLC6-2 anywhere on this board is wrong by
datasheet: its VBUS pin is a 6 V (min) zener, and its only remaining value — CC ESD —
is already integrated in U1 at a higher fault rating (22 V vs the USBLC6's 5 V-class
lines). Removal also converts the CC path from "two-pin nets joined inside a package"
(candidate 3's silent-failure class) into plain copper.

### A3. Pin-18 network — LOCKED: keep `VBUS_IN → R14 (470 Ω) → pin 18` unchanged

DS12499 Rev 4 Table 1 specifies pin 18 (VBUS_VS_DISCH) as "From VBUS, receptacle side",
and Table 22 (IDISUSB) specifies discharge "through external resistor connected to
VBUS_VS_DISCH pin" at 50 mA max. With R14 = 470 Ω: 15 V / 470 Ω ≈ 32 mA, and even the
20 V edge case gives 20 V / 470 Ω ≈ 43 mA — both inside the 50 mA rating. #87
re-confirmed the network as-wired against the netlist, and #88 confirmed it reached the
manufactured-package stage. **No divider variant**: pin 18 is simultaneously the
receptacle-side discharge path and the VBUS presence sense; a divider would mis-scale
the sense point and break the discharge function ST specifies through a single series
resistor. Keep exactly as-is.

### A4. Per-candidate disposition: fix-now vs bench-confirm-first

"Fix-now" = design-provable from datasheets, goes into the #93 KiCad edit regardless of
which candidate actually killed v4. "Bench-confirm-first" = no design change until the
stated gate from the
[#87 bench procedure](./v4-pd-failure-diagnosis.md#bench-discrimination-procedure-dead-v4-boards-cheapest-first)
resolves.

| # | v4 root-cause candidate | Disposition | Design change | Gate |
|---|---|---|---|---|
| 1 | External Rd ∥ internal Rd (2.55 kΩ, out of spec) | **Fix-now** | A1: CCxDB↔CCx via R19/R20 links, R17/R18 DNP | None needed to justify the change (DS12499-provable). Bench C2 additionally validates it as the operative v4 blocker — recommended on a dead v4 board before the first Board A order, but not blocking |
| 2 | D4 VBUS pin (6 V zener) on the 15 V rail | **Fix-now** | A2: delete D4, add SMAJ20A | None (abs-max violation is provable). Bench A2 is forensic only: a shorted D4 on a dead board is evidence a 15 V contract once completed |
| 3 | CC continuity via D4's internal flow-through | **Fix-now by construction** | Eliminated as a class by D4 removal (CC becomes one copper net per line) | Bench A1 remains for diagnosing the existing dead v4 boards only |
| 4 | NVM content on the failed boards | **Bench-confirm-first** | None | Gate: bench B2 — full NVM read-back diff vs target (`SNK_PDO_NUMB = 2`, PDO2 = 15 V/3 A, monitor coefficients default) on a dead board. Only a confirmed diff triggers action (rewrite + retest), and it is a programming action, not a schematic change |

### A5. #89's three Board-B blockers — explicit calls

| # | Blocker | Call | Detail |
|---|---|---|---|
| 1 | L7812 dropout margin (13.5 V → 12 V @ 1.2 A; 1.5 V available vs 2.0 V typ at only 1 A) | **Defer to the Board B design plan, bench-gated** | Not a simple provable one-wire fix: the correction is either raising the +13.5 V intermediate rail (e.g. R1 10 kΩ → 11 kΩ gives 14.76 V, but LDO dissipation rises from ~1.8 W to ~3.3 W — a thermal/layout tradeoff) or a low-dropout regulator swap. **Gate:** bench-measure a real L7812 (a dead v4 board's U6, or a bare part) at 1.2 A from a 13.5 V source; lock the numeric setpoint (preferred direction: raise the rail) during Board B layout with its thermal budget on the table |
| 2 | U8 −12 V decoupling network missing its GND node (`Net-(C16-Pad2)` floating) | **Fix-now-in-KiCad (#93)** | A genuinely missing GND tie, netlist-provable: the mirrored +12 V/+5 V networks connect the same-position cap plates individually to GND. Fix: merge `Net-(C16-Pad2)` into `GND` (C16.2, C24.1, C19.2, C25.1 all to GND). Also removes the C25 sustained-reverse-bias risk |
| 3 | C9 (100 µF **25 V**) bridging +15 V to −13.5 V = 28.5 V nominal, 33.5 V @ 20 V edge | **Fix-now-in-KiCad (#93)** | Rating math is provable from the LCSC datasheet; topology is correct, only the rating is wrong. Replace with a 50 V part: **DMBJ RVT1H101M0810** (100 µF 50 V, D8×L10.2 mm SMD), **LCSC C970687** (listed in stock 2026-07-05; re-verify at order time; alternate: Semtech CK1H101M-CRF10, LCSC C129420). Note: the physical can grows from 6.3×7.7 mm to 8×10.2 mm — the schematic footprint field changes now, and the resulting sch↔pcb mismatch on the *existing* single-board layout is accepted (layout rework is a later plan; Board B gets a fresh layout anyway) |

Two #89 leads (not blockers) also get dispositions for the record:

- **TVS2 (SD05, VRWM 5 V) at 0% standoff on the +5 V rail** — defer to the Board B
  design phase; direction: replace with a ≥6 V-standoff part so the L7805's legal
  4.8–5.2 V output never sits at/above the TVS standoff. Not in #93.
- **C4/C22/C23 Value field says "16V" but C335982 is a 10 V part** — **fix-now in #93**
  as a Value-field-only correction (`470uF 16V` → `470uF 10V`). Netlist-neutral,
  prevents a future reviewer trusting the wrong label. (10 V remains electrically safe
  on the 7.5 V/5 V nets per #89.)

### A6. Exact #93 KiCad change list (the locked spec)

All edits in `usb-pd-input.kicad_sch` unless noted. No `zudo-pd.kicad_pcb` edits.

| # | Action | Refs | Net effect (expected netlist diff) |
|---|---|---|---|
| 1 | Delete D4 (USBLC6-2SC6, C7519) | D4 | `Net-(J1-CC1)` + `Net-(U1-CC1)` merge into one CC1 net: `J1.A5 U1.2 R17.1 (+R19.2, D5 per below)`. Same for CC2: `J1.B5 U1.4 R18.1 (+R20.2)`. D4.2 leaves `GND`, D4.5 leaves `VBUS_IN` |
| 2 | Set R17, R18 DNP + exclude-from-BOM/CPL | R17 R18 | No net change (pins stay on CC1/CC2 and GND) |
| 3 | Rewire R19: pin 2 from `GND` to the CC1 net | R19 | `CC1DB` unchanged (`U1.1 R19.1 J3.1`); R19.2 appears on CC1; R19.2 leaves `GND`. Keep 0 Ω / C21189, fitted |
| 4 | Rewire R20: pin 2 from `GND` to the CC2 net | R20 | `CC2DB` unchanged (`U1.5 R20.1 J3.2`); R20.2 appears on CC2; R20.2 leaves `GND` |
| 5 | Add D5 = SMAJ20A (C571370; alt C1973455), SMA | D5 (new) | D5 cathode on `VBUS_IN`, anode on `GND`. Clone the `zudo-pd:SMAJ15A_C571368` symbol+footprint pattern (as used by TVS1/TVS3) into an `SMAJ20A_C571370` entry in `symbols/zudo-pd.kicad_sym`; verify pin→cathode mapping against the cloned symbol |
| 6 | Merge `Net-(C16-Pad2)` into `GND` (`linear-regulation.kicad_sch`) | C16 C19 C24 C25 | C16.2, C24.1, C19.2, C25.1 all become `GND` members; `Net-(C16-Pad2)` disappears |
| 7 | C9 part swap: RVT1E101M0607/C22383804 → RVT1H101M0810/C970687 (100 µF 50 V), update Value/LCSC/Datasheet/footprint fields (`dc-dc-conversion.kicad_sch`) | C9 | No net change |
| 8 | Value-field fix: `470uF 16V` → `470uF 10V` | C4 C22 C23 | No net change |

**Explicitly NOT in #93:** L7812 dropout rework (A5#1, bench-gated); TVS2 swap (Board B
phase); PESD24VS1UB DNP footprints D6/D7 (Board A layout phase — adding never-fitted
symbols to the legacy schematic is geometry risk with no payoff); any PCB edit.

<Warning>

Do not "fix" more than this list. In particular, do not touch the pin-18 network (A3),
the Q1 gate network, or the U4 inverting-topology referencing — all were re-confirmed
correct by #87/#89.

</Warning>

## Decision set (b) — Board A ↔ Board B interface contract

### Connector — LOCKED: JST XH, 6 pins, one per board

- **Board-side part (both boards): JST B6B-XH-A(LF)(SN)**, 6-pin top-entry shrouded
  through-hole header, 2.5 mm pitch — **LCSC C144397** (genuine JST; ~42k stock listed
  at LCSC on 2026-07-05; re-verify at order time). Rated 3 A AC/DC per contact with
  AWG #22, 250 V.
- **Cable:** commodity pre-crimped 6-way XH↔XH lead, AWG 22, 80–150 mm; or build from
  JST XHP-6 housings + SXH-001T-P0.6 contacts (verify stock at order time — cable-side
  parts are not on the PCBA BOM).
- Why XH: polarized/shrouded housing (foolproof insertion), the de-facto synth-DIY
  standard, genuine-JST parts in JLCPCB's library, through-hole anchoring for a power
  connector, and cheap on both boards.

### Pinout — LOCKED

| Pin | Signal | Direction | Notes |
|-----|--------|-----------|-------|
| 1 | +15V | A → B | Board A `VBUS_OUT` (post Q1 load switch), PD-contract 15 V |
| 2 | +15V | A → B | Paired with pin 1 (current sharing) |
| 3 | ATT | A → B, open-drain, active-low | STUSB4500 pin 11 (ATTACH). No pull-up on Board A; Board B (or any host) pulls up 10–100 kΩ to a local rail ≤5 V if used. May be left unconnected |
| 4 | PDOK | A → B, open-drain, active-low | STUSB4500 pin 20 (POWER_OK2): asserts when the PDO2 (15 V) contract is live. Same pull-up rule as ATT. May be left unconnected |
| 5 | GND | — | Paired return |
| 6 | GND | — | Paired return |

Nothing synth-specific is on the connector: 15 V power, ground, and two generic
open-drain status lines — Board A stays reusable as a plain "USB-PD 15 V sink module"
in any other project (a consumer that ignores pins 3–4 just gets switched 15 V).

### Current-rating math (3 A+ continuous)

Load basis — worst case is the **PD contract cap of 3.0 A at 15 V**, not the computed
draw:

- Rated output budget: 12 V×1.2 A + 12 V×0.8 A + 5 V×0.5 A = **26.5 W**.
- Estimated input at rated load: buck ≈85%, inverting ≈80% efficiency, LDO stage scales
  by Vout/Vin → per-rail input ≈ 19.1 W + 4.4 W + 13.5 W ≈ **37 W** → 37 W / 15 V ≈
  **2.5 A steady**. The contract cap (3.0 A) is the design number.

| Quantity | Value |
|---|---|
| XH contact nameplate rating | 3.0 A per contact (JST, AWG #22) |
| Continuous derating applied (80%) | 2.4 A per contact |
| +15V contacts | 2 → 4.8 A derated (6.0 A nameplate) capacity |
| Worst-case continuous load | 3.0 A (PD contract cap; ≈2.5 A computed steady draw) |
| Per-contact current at 3.0 A | 1.5 A = 50% of nameplate, 62.5% of derated |
| **Margin** | **4.8 / 3.0 = 1.6× derated; 6.0 / 3.0 = 2.0× nameplate** |

GND uses the identical 2-contact math (symmetric return). 1.6× derated margin satisfies
the project's 150%+ safety-margin convention. Cable drop is negligible: two paralleled
AWG 22 conductors per leg at 100 mm ≈ 2.7 mΩ/leg → ≈16 mV round trip at 3 A.

### Keying / foolproofing — LOCKED

- The XH shrouded housing is mechanically polarized — reversed insertion is blocked.
- **Uniqueness rule:** the 6-pin XH is the ONLY 6-position XH on either board, so the
  A↔B cable cannot land on a wrong header. (Board B's Eurorack outputs are 2×8 shrouded
  IDC; Faston tabs are physically incompatible.)
- Pin 1 is marked on silkscreen on both boards.
- The pinout is deliberately non-symmetric under pin reversal (+15V on 1–2, GND on 5–6)
  only behind the housing key; the key is the protection, the silkscreen is the audit.

### Mechanical combination — LOCKED: side-by-side, cable-linked

- **Side-by-side** placement joined by the 6-way XH cable; **stacking is rejected**
  because: the USB-C receptacle must reach the enclosure wall on its own edge; Board
  A's J2 pogo pads must stay face-accessible for the NVM programming rig; Board B's
  three TO-263 regulators need top-side copper and airflow that a stacked board would
  blanket; and a stack fixes the relative orientation, hurting Board A reuse.
- Mounting: each board carries its own **4× M3 (3.2 mm) corner holes** and mounts
  independently. Board A's hole pattern is chosen at layout time for Board A alone (no
  shared-pattern coupling to Board B). An optional shared 3D-printed tray can come
  later in `3dp-files/` — explicitly out of scope for this plan.

## Decision set (c) — doc structure note

**Assumption stated for reconciliation:** the Board A / Board B pages go under
**`overview/`** as flat pages, matching the wave-3 issue defaults —
`overview/board-a-usb-pd-core.md`, `overview/board-b-synth-power.md`, plus the
housekeeping task's `overview/two-board-plan.md`. No dedicated `boards/` section is
created by this decision. If the housekeeping task (#94) instead creates a section, its
PR description records that choice and the wave-4 confirm pass (#95) reconciles the
paths (this page's links, the issue bodies, and the interface-table cross-references).

## References

- [v4 USB-PD Failure Diagnosis](./v4-pd-failure-diagnosis.md) — candidates, DS12499
  citations, bench procedure (gates referenced above)
- [v4 As-Built Order Verification &amp; Footprint Geometry Audit](./v4-asbuilt-audit.md) —
  footprint verdicts; v0.4.0 order-status caveat
- [Board B Architecture Review](./board-b-architecture-review.md) — the three blockers
  dispositioned in A5
- [PCBA v2 Debug Report](./pcba-v2-debug.md) — origin of the external-Rd topology
  reversed by A1
- [NVM Programming Setup](./nvm-programming.md) — read-back procedure behind the
  candidate-4 gate
- [STUSB4500 pinout guide](./stusb4500-pinout.md) — ATT (pin 11) / POWER_OK2 (pin 20)
  roles used in the interface contract
- ST DS12499 Rev 4 (STUSB4500), ST USBLC6-2 datasheet, JST XH series datasheet,
  SMAJ series TVS datasheet — part-level claims above
