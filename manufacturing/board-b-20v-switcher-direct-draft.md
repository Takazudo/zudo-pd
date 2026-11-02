# Board B 20 V switcher-direct draft (unvalidated paper draft)

**Status: unvalidated draft. Nothing here is adopted, measured, validated or released.**
Phase 19 adds draft footprints and a placement PCB; phase 21 adds a partly routed draft of it, and phase 28 makes that draft 4-layer by owner decision (§3a). There is no BOM change and no order file. `PASS` below means
only that the arithmetic in `scripts/pcb/calculate-board-b20-draft.py` closes on its tagged inputs,
or that a named ngspice run with vendor models met the limit. A simulation is not a measurement.
`OPEN` means the gate needs data or work that does not exist yet. An `OPEN` gate is not a pass.

- Spec: `scripts/schgen/board_b20_spec.py` → `boards/board-b20-draft/board-b20-draft.kicad_sch` (generated).
- Arithmetic: `python3 scripts/pcb/calculate-board-b20-draft.py` (`--json` for every row).
- Simulation decks, analyzers and summaries: `manufacturing/sim/board-b20-phase7/` (as drawn in phase 7)
  and `manufacturing/sim/board-b20-phase9/` (phase-9 start-order clamps and shunts).
- Contract: manager `osc-pd-interface-20v.md` (2026-10-31), §0–§6.
- Evidence tags: **G** guaranteed limit from a retained primary extract, **T** typical,
  **PA** project assumption, **PROPOSED** draft value with no owner record.
- Phase 7 folds in the independent review of `bad5ddf`. Section 7 maps every finding.

## 1. Why this is a separate spec

The request was to draft the 20 V switcher-direct design in `board_b_spec.py`. That spec is the
S3 Board B ordered on 2026-09-20. Its schematic, inventory placements, integration rules and
observed forward-test runs describe that ordered board. Rewriting it in place would orphan
every one of those records. It would also make `pnpm circuit:check` describe a board that does
not exist. The draft is therefore a sibling spec. It uses the same generator, symbols and checks,
but it is not bound to the central inventory. Folding it into `board_b_spec.py` is a separate
step for whenever this design is adopted. That step needs a decision record and an as-ordered
snapshot of S3.

## 2. Architecture

```mermaid
flowchart LR
  VIN[J5 VIN 20 V from Board P] --> U1[U1 TPS54560 buck] --> F1[LC post-filter] --> P12[P12_PRE]
  VIN --> U2[U2 TPS54560 buck] --> F2[LC post-filter] --> P5[P5_PRE]
  VIN --> U3[U3 TPS54560 inverting, IC GND on M12_RAW] --> F3[LC post-filter] --> M12[M12_PRE]
  VIN --> U14[U14 AP63201 P5_SUP supervisory supply]
  P12 --> SH1[shunt + U11 INA301A3] --> SW1[Q1/Q2 tracked pair] --> O12[+12 V terminal]
  P5 --> SH2[shunt + U12 INA301A3] --> SW2[Q3/Q4 tracked pair] --> O5[+5 V terminal]
  M12 --> SH3[shunt + U9A comparator] --> SW3[Q5/Q6 tracked pair] --> OM12[-12 V terminal]
  REF[U10 REF5025 on P5_SUP] --> SERVO[OPA2187 integrators, sense at *_SH] --> FB[converter FB injection]
  REF --> RAMP[common RAMP, reset while EN_N high] --> TRK[U13 / U9B tracking amplifiers] --> SW1
  TRK --> SW2
  TRK --> SW3
  WIN[U6/U7/U8 OV/UV windows, U5B VIN UV] --> FLT[(FAULT_N latch)]
  SH1 --> FLT
  SH2 --> FLT
  SH3 --> FLT
  FLT --> EN[EN_N: gates pulled off, RAMP reset] --> DIS[hold-up discharge 100/150/33 Ohm]
```

- **Converters.** Three TPS54560DDAR run from VIN at about 557 kHz (RT 174 kΩ, T). U3 is an
  inverting buck-boost with its GND and PowerPAD on M12_RAW. Compensation is per stage:
  +12 V 10 kΩ / 6.8 nF / 47 pF, +5 V 4.02 kΩ / 27 nF / 150 pF, inverter 8.2 kΩ / 47 nF / 150 pF.
- **Supervisory supply.** U14 AP63201WU-7 C2071044 makes P5_SUP (4.93–5.04 V) from VIN. It powers
  the reference, every comparator, servo and tracking-reference amplifier, the INA301 VS pins,
  the latches and the discharge hold-up. A +5 V converter fault no longer removes its own supervision.
- **Servo.** OPA2187 integrators compare a 0.1 % divider of each `*_SH` node (after the shunt) with
  REF5025. They inject a bounded current into the converter FB node. Only the switch-pair drop is
  outside the loop. The loop time constant is about 5 ms (5.03 / 5.56 / 5.12 ms), so the rails settle
  long before the earliest enable (RDY ≥ 0.21 s).
- **Common tracking start.** RAMP rises from REF25 through 20 kΩ into 1.47 µF (CRMP 1 µF + CRMP2 470 nF,
  phase 9). A BSS138 holds it at 0 V
  while EN_N is high and for 56–108 ms after enable (RRMD 100 kΩ / CRMD 470 nF, phase 10; 12–23 ms with
  the earlier 100 nF). U13 (on VIN) closes +12 = 7.98 × RAMP
  and +5 = 3.32 × RAMP around the switch pairs; U9B closes −12 = −8.06 × RAMP. While disabled, each
  amplifier's feedback input is pre-biased through 100 kΩ and a BSS138 body diode. A 10 MΩ offset to
  M12_PRE sets a small target, so each loop brings its pair to the edge of conduction before RAMP
  moves. The integrators are 10 nF C0G; the −12 V loop adds a 10 kΩ damping zero (RT12NZ).
- **Start-order clamps (phase 9, drawn).** Each amplifier now tracks RAMP_x, which is RAMP through 1 kΩ,
  clamped by an OPA2187 and a BSS138 body diode (U15/U16, Q62–Q64, on P5_SUP / M12_PRE) to a level
  from the other rails' outputs: |−12| ≤ 1.095 × V(+12), V(+12) ≤ 1.099 × |−12| + 0.407 V and
  V(+5) ≤ 0.498 × |−12|. U15/U16 use M12_PRE as their negative rail. On a GND rail the clamp could not
  pull RAMP_x below one diode drop, about 0.4 V, which would let |−12| reach about 3 V with +12 V at 0 V.
  §5c.
- **Limiter.** +12 V and −12 V each use one 10 mΩ 0.1 % shunt (RSH1, RSH3: RESI PCSR2512BR010M6,
  distributor listing only, G-U; phase 9). +5 V keeps one 20 mΩ PE1206 shunt. +12 V and +5 V use
  INA301A3 in transparent mode on their shunts. The LIMIT dividers
  include the 79.2–80.8 µA ILIMIT source current (G). −12 V uses U9A against a divider from GND to
  M12_PRE. Every trip pulls FAULT_N. The limiter trips; it does not regulate current.
- **Reverse blocking.** Back-to-back CSD18543Q3A common-source pairs sit on every rail, with a
  BZT52C11 gate-source clamp on each pair.
- **Latch and enable.** The fault latch Q30/Q31 is held reset for 10.7–36 ms after P5_SUP rises (POR).
  The enable latch is set by RDY (PDOK valid for 0.21–0.73 s) and reset by the fault latch. Only a
  re-plug clears a fault.
- **Shutdown and discharge.** EN_N high pulls all three gates off (the −12 V gate through the Q24/Q25
  level shifter) and resets RAMP. CDH (10 µF) is charged from EN_E only while enabled. When EN_E falls,
  Q56/Q54 drive the discharge switches from CDH alone for 0.48–1.33 s.

## 3. Parts

| Part | Use | Evidence |
|---|---|---|
| TPS54560DDAR C31966 | U1–U3 | Candidate `rec-c31966`, TI SLVSBN0C (G) |
| OPA2187IDGKR C2863562 | servo, window, tracking (U4–U9, U13) | Candidate `rec-c2863562`, TI SBOS807E (G) |
| REF5025AIDR C11341 | U10 | Candidate `rec-c11341`, TI SBOS410O (G). Standard grade: 0.1 %, 8 ppm/°C |
| AP63201WU-7 C2071044 | U14 P5_SUP | Existing owner `component-ap63201-power-stage`; this draft placement is not in the inventory |
| PE1206FRF470R02L C164156 | shunts (draft default) | Candidate `rec-c164156`, YAGEO product sheet (G). JLC stock was 51 at retrieval |
| RLS12FTCR020 C163047 (TA-I) | stock alternative for the 20 mΩ shunts | Candidate `rec-c163047`. Source is an LCSC-hosted manufacturer sheet (MANUFACTURER_MIRROR); facts are **UNSOURCED** until a manufacturer-primary copy is retained. JLC stock 24,785 (read-only lookup, 2026-10-31) |
| INA301A3IDGKR C2861552 | U11, U12 | Existing candidate `rec-c2861552`, SBOS713A (G) |
| CSD18543Q3A, BSS138, DMP3036SFG-7, BZT52C11, ASPI-0630LR, 25SVPF47M, GRM32 10 µF, RT0603 0.1 % values, project 0603/0805/1206 passives | switches, logic, filters, dividers | Existing owner records |
| Values labelled `R_PROPOSED` / `C_PROPOSED` | FB tops, compensation, window dividers, servo injection, tracking network, discharge loads, hold-up | **PROPOSED**, no owner record. Phase 13: 10k 0.1 %, 4.02k 1 % and 8.2k 1 % are bound to the owned RT0603 parts (C95204, C705781, C861589). The other 70 placements resolve to distributor listings in `manufacturing/readiness/b20-identity-resolution.json` (no manufacturer document, no owner record), except 27 nF and 47 nF C0G (**UNKNOWN**, no exact 0603 listing found) |
| DW254P-2X8-L0 C4749189 | J10, J11 (phase 13) | Existing owner `component-dealon-dw254p-2x8-l0-c4749189`; pin map as on the current Board B (1/2 −12 V, 3–8 GND, 9/10 +12 V, 11/12 +5 V, 13/14 CV, 15/16 GATE) |

The new ICs are SHORTLISTED candidates in `.claude/skills/component-board-b20-draft-candidates/`.
Phase 19 drew the five former `*_DRAFT` footprints in `footprints/kicad/` (both library copies; courtyards
from `gen_courtyards.py`). None is fabrication-reviewed and none has a 3D model. Each land is recorded as a
`-land-pattern` fact in its owner bundle:

| Footprint (was) | Placements | Land source | Evidence class |
|---|---|---|---|
| `HSOP-8_TI-DDA0008B` (`HSOP-8_TPS54560DDA_DRAFT`) | 3: U1–U3 | TI DDA0008B example board layout 4214849/B (SLVSBN0C p. 49): 8 × 1.55 × 0.6 mm, 1.27 pitch, 5.4 span; thermal metal 2.95 × 4.9 mm with a 2.71 × 3.4 mm mask-defined opening; 2 × 4 vias on the 1.3 mm grid, drilled 0.3 mm (0.6 mm pad) for the Board B 0.3 mm minimum hole instead of the drawing's 0.2 mm | primary manufacturer drawing |
| `VSSOP-8_TI-DGK0008A` (`VSSOP-8_DGK_DRAFT`) | 11: U4–U9, U13, U15, U16, U11, U12 | TI DGK0008A 4214862/A (SBOS807E p. 40; SBOS713A p. 28 is text-identical): 8 × 1.4 × 0.45 mm, 0.65 pitch, 4.4 span | primary manufacturer drawing |
| `SOIC-8_TI-D0008A` (`SOIC-8_D_DRAFT`) | 1: U10 | TI D0008A 4214825/C (SBOS410O p. 47): 8 × 1.55 × 0.6 mm, 1.27 pitch, 5.4 span | primary manufacturer drawing |
| `R1206_TA-I-RLS12` (`R1206_DRAFT`) | 4: RSH2, RX12, RX5, RXN | TA-I TRLS-XXOS002B §6, RLS12 5–30 mΩ row: 2 × 1.55 × 1.8 mm, 1.6 mm gap | **UNSOURCED** (distributor mirror; no TA-I-hosted copy found). A project basis for the PE1206 shunt, whose YAGEO sheet has no land, and for the PROPOSED 1206 loads |
| `R2512_RESI-PCSR2512_Kelvin` (`R2512_DRAFT`) | 2: RSH1, RSH3 | RESI PCSR2512 sheet PCSR2512-E16009-V8, land pattern figure: current pads 1.65 × 2.0 mm with a 4.0 mm gap, sense pads 1.4 × 1.2 mm 0.5 mm away, point-symmetric; each terminal's two pads share its number | **UNSOURCED** (DigiKey-hosted copy). New candidate record `rec-c23067428` |

The RLS12 and PCSR2512 sheets were looked for on the manufacturers' own sites; neither exposes a direct
PDF, so both stay mirror evidence and their primary-specification coverage is **OPEN**.

### 3a. Draft PCB: phase 19 placement, phase 21 partial routing

`scripts/pcb/board-b20/build-draft.py` (pinned KiCad 10.0.6 pcbnew) writes
`boards/board-b20-draft/board-b20-draft.kicad_pcb`. Phase 19 placed it without routing; phase 21 routes part of it (below):

- Outline, mounting holes, fiducials and J5, J6, J7, J10, J11 come from `scripts/pcb/board_b_layout.py`
  unchanged.
- A footprint keep-out rule area covers x 7.74–17.25, y 24.54–35.77 mm on both sides for Board P r3's C3.
- The other 264 parts are packed greedily on the top side around block anchors (phase 21: the switching stages use fixed templates, below) (power stages along the
  top, rail switches toward J6/J7/J10, supervision and servo logic on the right). Loop area, thermal
  spreading, return paths and creepage are **not** reviewed. Reference designators are on F.Fab.
- The Board B design rules were copied into `board-b20-draft.kicad_pro`.

- J10/J11 front silk is clipped at local y = 11.73 mm, as `finish-board-b.py` does for the as-built Board B.
  The clip leaves two `lib_footprint_mismatch` warnings on J10/J11, which the as-built Board B DRC also carries.

Phase 19 KiCad 10.0.6 DRC of the unrouted placement (pinned image, heavy-guard then `flock`): 0 violation errors,
2 warnings (`lib_footprint_mismatch` on J10 and J11, from the silk clip), 0 parity issues and
499 unconnected items. The unconnected items are the expected result of an unrouted draft; they are not a pass.

#### Phase 21: power stages first, then the router

`scripts/pcb/board-b20/run.sh` rebuilds the draft: `build-draft.py` (placement), `dump-geom.py` (pad and rule-area
geometry), `route.py` (host grid router, 0.1 mm grid, two layers), `apply-routes.py` (tracks, vias, F.Cu and B.Cu
GND pours, fill) and `loop-check.py` (desk loop and sense self-check, `loop-check.json`). The router result is in
`routing-report.json`. The C3 keep-out rule area is unchanged and is honoured by placement and routing.

- Each TPS54560 stage is placed from one fixed template (IC, boot capacitor, input capacitor, catch diode, inductor,
  output capacitors), with the LC filter, shunt and INA301 beside it for stages A and B; stage C (−12 V) has its
  own shunt and INA301 offset. A template collision stops the build.
- Routing order: stage power pairs at 0.8 mm on F.Cu (input capacitor to VIN, SW to diode and inductor, boot
  capacitor, inductor to output capacitors, diode anode to input-capacitor return, input-capacitor return to the IC
  ground pin), then the INA301 Kelvin pairs, GND stubs, the remaining power nets, the supply nets, the signals by
  span, two rip-up rounds and GND stitching vias (3 mm pitch).
- The RESI PCSR2512 Kelvin footprint now sets `duplicate_pad_numbers_are_jumpers`, so each sense pad is joined to
  its current pad inside the footprint. Its sense pads are point-symmetric (diagonal), so the two traces of a pair
  cannot run side by side up to the resistor.
- On the 0.1 mm grid a 0.25 mm track cannot leave the middle pin of a 0.65 mm pitch row with the clearance
  margin; 0.2 mm (the board minimum) is the fallback width. All six sense traces now route.
- Copper is rasterized onto every grid cell it touches, and a track end that cannot sit inside a pad narrower than
  the track must still clear foreign copper, or the next narrower width is tried. An earlier run with a
  centre-inside raster left 7 to 11 native clearance errors of up to 0.145 mm.

Result: 2551 tracks, 737 vias (145 GND stitching), 64 router connections left open: 45 signal connections on
33 nets and 19 GND stubs. This is an incomplete draft, not a routed board.

KiCad 10.0.6 DRC with schematic parity (pinned image, heavy-guard then `flock`, Board B rules from
`board-b20-draft.kicad_pro`): 0 errors, 0 parity issues; warnings: 2 `lib_footprint_mismatch` (J10/J11 silk clip),
1 `via_dangling` (a GND stitching via), 1 `track_dangling`; **81 unconnected items** (34 GND, 47 on 33 signal nets).
The unconnected items are open work, not a pass.

Desk self-check (`loop-check.json`, pad-centre geometry and track lengths only; no field solver, nothing measured):

| Stage | Hot loop (C<sub>IN</sub> → VIN → SW → diode → C<sub>IN</sub> return) | VIN / SW / inductor branch | Diode-to-C<sub>IN</sub> return |
|---|---|---|---|
| A (U1, C3, D1) | 54.9 mm² polygon, 30.9 mm perimeter | 7.09 / 5.87 / 3.5 mm, 0.8 mm F.Cu | 2.0 mm, 0.8 mm F.Cu |
| B (U2, C7, D2) | same template: 54.9 mm², 30.9 mm | 7.09 / 5.87 / 3.5 mm | 2.0 mm F.Cu |
| C (U3, CCIN1, D3) | same template: 54.9 mm², 30.9 mm | 7.09 / 5.87 / 3.5 mm | 2.0 mm F.Cu (M12_RAW return) |

| Shunt | INA301 traces (+ / −) | Lands on | Largest pair gap |
|---|---|---|---|
| RSH1 (U11) | 3.26 mm (0.25) / 11.74 mm (0.2), F.Cu | sense pads | 3.03 mm |
| RSH2 (U12) | 3.92 mm (0.25) / 7.39 mm (0.2), F.Cu | current pads: the selected shunt is two-terminal | 2.14 mm |
| RSH3 (U9) | 6.69 mm (0.25) / 5.83 mm (0.2), F.Cu | sense pads | 5.2 mm |

The hot-loop polygon is **OPEN**: the input capacitor sits 3.4 mm left of and 8.2 mm above the IC, so the loop
encloses tens of mm²; a tighter template (input capacitor beside VIN and GND) is the next layout step. The RSH1 and
RSH3 negative traces detour around the diagonal sense pads, and the RSH1 and RSH3 pairs separate by 3.03 and 5.2 mm, so the sense
loops are **OPEN** too. Thermal spreading, creepage and the GND return under each SW node are not reviewed.

#### Phase 22: TI-style stage template, Kelvin coupling cost, wirelength pass

TI's retained TPS54560 datasheet (SLVSBN0C §10.1, Layout Guidelines) says: "Care should be taken to minimize the
loop area formed by the bypass capacitor connections, the VIN terminal, and the anode of the catch diode". Its
Figure 58 places the input bypass capacitor and the catch diode on either side of the IC with a top-side ground area
between them, and routes the boot capacitor trace on another layer to keep that ground path wide.

- **Template:** the input capacitor now sits beside VIN/GND (offset −3.6, −5.13 mm from the IC), the catch diode
  beside SW (+3.05, −5.02 mm, anode toward the capacitor return) and the inductor beyond the diode. The boot
  capacitor routes BOOT on B.Cu where it can. Hot-loop polygon (desk, pad centres): **29.6 mm², 24.7 mm perimeter**
  on all three stages, down from 54.9 mm² / 30.9 mm. Branches: VIN 4.11 mm, SW 2.75 mm, diode-to-C<sub>IN</sub>
  return 1.7 mm, inductor 1.4 mm, all 0.8 mm F.Cu.
- **Placement:** a wirelength pass moves the non-template parts toward their signal-net partners (87 parts moved;
  half-perimeter wirelength 4893 → 4206 mm).
- **Router:** the A* core is C (`astar.c`, built by `route.py` with the system compiler); the second trace of each
  Kelvin pair pays a cost for every 0.1 mm cell farther than 0.5 mm (centre) from its partner. Signal B.Cu cost
  is now 1.0 (was 1.4). Rip-up stops after the round that improves nothing (3 rounds here).
- **GND islands:** `apply-routes.py` fills both pours, finds GND fragments that do not reach the main group, and adds
  a 0.8/0.3 mm via where two fragments overlap on opposite layers (12 vias on this run).

Result: 2789 tracks, 710 vias, 53 router connections open.

KiCad 10.0.6 DRC with schematic parity (pinned image, heavy-guard then `flock`): **0 errors, 0 parity issues**;
warnings: 2 `lib_footprint_mismatch` (J10/J11 silk clip); **62 unconnected items** (17 GND, 45 signal; the largest
groups are EN_E 8, RAMP_M12 3 and ARM_GND 3). This is down from 81, but it is still open work, not a pass.

| Shunt | INA301 traces (+ / −) | Coupled length within 0.3 mm edge gap | Status |
|---|---|---|---|
| RSH1 (U11) | 3.31 / 6.48 mm, 0.2 mm F.Cu | 0 mm | **OPEN** |
| RSH2 (U12) | 3.91 / 4.11 mm, 0.2 mm F.Cu | 0 mm | **OPEN** |
| RSH3 (U9) | 3.72 / 6.41 mm, 0.2 mm F.Cu | 0 mm | **OPEN** |

The Kelvin traces are shorter: the longest was 11.74 mm and is now 6.48 mm. The 0.3 mm gap target is **not met**. Two
0.2 mm traces leaving adjacent INA301 pins at 0.65 mm pitch already start 0.45 mm apart. The PCSR2512 sense pads sit
diagonally at opposite ends of the resistor, so the pair must split over the resistor's length whatever its
rotation. Getting below 0.3 mm would need a neck-down to 0.15 mm beside the pins, below the board's 0.2 mm minimum.
Thermal spreading, creepage and the GND return under each SW node are still not reviewed.

#### Phase 24: router trials, sense-pair geometry limit and pickup estimate

- **Spec:** the RP680 library entry in `board_b20_spec.py` is the adopted AT0603BRD07680RL / C5455478 line
  (`dec-b-stock-gap-substitutions`). RP680 is not placed on B20, so the generated schematic is unchanged.
- **Router trials, none adopted.** Each ran on the phase 22 placement. KiCad 10.0.6 DRC with schematic parity
  (pinned image, heavy-guard then `flock`) ran where the router result was competitive:

  | Trial | Router connections open | DRC unconnected |
  |---|---|---|
  | Phase 22 (kept) | 53 | **62** (17 GND, 45 signal) |
  | GND stubs try 2.5 then 6.0 mm, land on existing GND copper, run before stitching | 51 (44 signal, 7 GND) | 64 (19 GND, 45 signal) |
  | Plus a pin-escape halo (soft F.Cu cost within 0.75 mm of another net's pad), cost 1.5 | 77 (46 signal, 31 GND) | NOT RUN (router result worse) |
  | Halo cost 4 | 77 (46 signal, 31 GND) | NOT RUN (router result worse) |

  The halo runs also routed a GND track tree, which added 24 GND failures. No trial lowered the DRC count, so the
  board, `route.py`, `routing-report.json` and the DRC result stay at phase 22.
- **Why 0 is not reached:** the signal failures are fine-pitch pins boxed in by other nets, on a board whose
  courtyards cover 55 % of the area (75 % with a 0.8 mm keep-out halo). The GND items are pour fragments that the
  fill leaves apart. Closing them needs placement changes (more room around U6 and the EN_E, RAMP_M12 and ARM_GND
  pin groups), not router cost tuning. The **62 unconnected items are OPEN**.

**Sense-pair geometry limit.** A pair coupled within a 0.3 mm edge gap over its length is not reachable with
these parts, and the phase 22 note that a neck-down would fix it was wrong (narrower traces widen the gap):

| Quantity | Value |
|---|---|
| INA301 (VSSOP-8) pin pitch; edge gap of two 0.2 mm traces at the pins | 0.65 mm; 0.45 mm |
| Edge gap the traces could close to past the pins (board clearance) | 0.2 mm |
| PCSR2512 sense-pad separation (diagonal, opposite resistor ends) | 6.41 mm (RSH1, RSH3); RSH2 lands on current pads 3.15 mm apart |
| Routed trace lengths | 3.31–6.48 mm |

The far ends of each pair are 6.41 mm apart, as far apart as the traces are long, so the two traces diverge from
the amplifier pins and no parallel stretch exists; the router's coupling cost found 0 mm on every pair. Forcing a
coupled stretch would lengthen the traces and enlarge the loop. Under the dipole model below, pickup scales with
the enclosed loop area, so that is the figure carried:

| Shunt | Traces (+ / −) | Sense loop | Differential pickup at input | Capacitive CM at input | Amplifier output |
|---|---|---|---|---|---|
| RSH1 (U11, INA301A3) | 3.31 / 6.48 mm | 10.55 mm² | 0.727 mV peak | 0.20 / 0.77 mV peak | 0.64 mV (differential, BW-limited); 0.043 mV (CM via CMRR) |
| RSH2 (U12, INA301A3) | 3.91 / 4.11 mm | 6.71 mm² | 0.183 mV peak | 0.27 / 0.29 mV peak | 0.16 mV; 0.016 mV |
| RSH3 (U9, OPA2187) | 3.72 / 6.41 mm | 12.75 mm² | 0.341 mV peak | 0.24 / 0.64 mV peak | not modelled (not an INA301) |

Model and assumptions (desk estimate, not a measurement): 20 V input, 6.2 ns SW rise (SLVSBN0C, VIN×0.16 ns/V + 3 ns),
switched currents A 1.2 A, B 0.5 A, C 1.28 A; a magnetic dipole between each stage's hot-loop polygon and the sense
loop; two-wire capacitance to the nearest SW track (nearest SW centre 17.7–23.2 mm) with εeff 2.7 and 1 nH/mm
trace inductance; INA301A3 gain 100 V/V, 450 kHz bandwidth, 65 dB CMRR at 1 MHz (SBOS713A Figure 9, typical; the
guaranteed 110 dB is at DC only). The common-mode term is small next to the differential term because the SW nodes
are 18–23 mm away. Every number is in `boards/board-b20-draft/loop-check.json` (`geometry_and_pickup`,
`pickup_assumptions`). It is OPEN until a bench measurement exists.

#### Phase 26: placement spacing trials, B.Cu signal cost 0.7

The aim was to unbox the blocked pins by spreading the placement, then reroute toward 0 unconnected. Every row below
ran on the same spec. DRC is KiCad 10.0.6 with schematic parity (pinned image, heavy-guard then `flock`); "NOT RUN"
rows were dropped on their router result.

| Trial | Placement | Router open | DRC unconnected |
|---|---|---|---|
| Phase 22 | 0.8 mm courtyard clearance | 53 | 62 (17 GND) |
| Extra 0.6 mm keep-out around the VSSOP/SOIC/TSOT ICs (`B20_ICHALO=0.6`) | spread | 70 | 84 (24 GND) |
| IC keep-out 1.2 mm | does not fit: 9 parts unplaced | — | — |
| 1.0 mm clearance for every part (`B20_CLEAR=1.0`) | does not fit: 11 parts unplaced | — | — |
| 0.6 mm clearance + 0.6 mm IC keep-out, B.Cu cost 0.8 | fits | 65 | 67 (19 GND) |
| Same placement, B.Cu cost 0.6 | fits | 55 | NOT RUN |
| Phase 22 placement, gate-drive nets (EN_E, P5_G, P12_G, M12_G, EN_N, FAULT_N) routed before power nets | phase 22 | 60 | 68 (20 GND) |
| Phase 22 placement, EN_E only first / EN_E grown from RE1 | phase 22 | 71 / 61 | NOT RUN |
| Phase 22 placement, no copper between fine-pitch IC pin rows | phase 22 | 73 | NOT RUN |
| Phase 22 placement, signals longest-first | phase 22 | 60 | NOT RUN |
| Phase 22 placement, B.Cu signal cost 0.8 / 0.6 / 0.5 | phase 22 | 52 / 54 / 50 | 60 / 58 / 57 |
| **Phase 22 placement, B.Cu signal cost 0.7 (adopted)** | phase 22 | **49** (39 signal, 10 GND stubs) | **55 (16 GND, 39 signal)** |

Adopted result: 0 errors, 0 parity issues; warnings 2 `lib_footprint_mismatch` (J10/J11 silk clip), 3
`via_dangling`, 1 `track_dangling`; **55 unconnected items** (16 GND, 39 signal; EN_E 8, TRK12 3, ARM_GND 3).

**Findings:**
- **Placement is at its density limit.** With the stage templates and fixed hardware, the greedy packer cannot raise
  the clearance anywhere without leaving parts unplaced (1.0 mm all round, or 1.2 mm around the ICs). Every spread
  placement that does fit routed worse, because it lengthens the nets that the wirelength pass had shortened.
- **The remaining failures are not one cause.** EN_E (8 items) fails because its first pad, the Q24 gate, sits in a
  pocket of the Q24 source copper. Growing EN_E from RE1 routes 8 of its 9 pads, but the copper it takes strands more
  pins elsewhere (61 open).
- **Results are noisy.** The B.Cu cost sweep moves the count by ±4 with no trend. The adopted 0.7 is the best of the
  sweep, not a tuned optimum. Rip-up stops at round 6 with no gain; 12 rounds give the identical result.
- **Unchanged:** the sense pairs, hot loops and pickup estimate are identical to phase 24
  (`boards/board-b20-draft/loop-check.json`).

Closing the remaining items needs more board area for this part count: parts on B.Cu, a larger outline, or fewer
parts. Those are design decisions, not router settings. **The unconnected items are OPEN.** The trial knobs stay in
`build-draft.py` (`B20_CLEAR`, `B20_ICHALO`, defaults 0.8 and 0, which reproduce the phase 22 placement).

#### Phase 27: 4-layer trial and outline fit study (not adopted)

The 2-layer phase 26 board stays the committed draft. These trials ran on scratch copies of the phase 22 placement
with the same spec, router and KiCad 10.0.6 DRC with schematic parity (heavy-guard then `flock`).

**4-layer trial.** `B20_LAYERS=4` gives the router a third layer, In2.Cu, for signal and power. In1.Cu carries a full GND
pour and is not routed. `apply-routes.py` writes a 4-layer stackup when the routes use In2.Cu. Its dielectric
thicknesses are placeholders until a stackup is chosen; they do not enter DRC. `B20_STUBREACH` widens the search window
for GND pad stubs.

| Trial | Router open | DRC unconnected |
|---|---|---|
| 2-layer, phase 26 (committed) | 49 (39 signal, 10 GND stubs) | 55 (16 GND, 39 signal) |
| 4-layer, B.Cu/In2.Cu cost 0.7 | 26 (14 signal, 12 GND stubs) | NOT RUN (superseded) |
| **4-layer, GND stub reach 6 mm** | **24** (14 signal, 10 GND stubs) | **22 (8 GND, 14 signal)**; 0 errors, 0 parity issues |
| 4-layer, reach 6 mm, cost 0.5 | 27 | NOT RUN (router result worse) |
| 4-layer, reach 6 mm, 12 rip-up rounds | 24 (identical) | NOT RUN (same routes) |

The best 4-layer board has 2407 track segments (F.Cu 1419, In2.Cu 483, B.Cu 505) and 738 vias. Its open signal
items are one pin each on 13 nets (UV12_DIV has 2). EN_E, which had 8 open items on 2 layers, routes completely. The
inner layer removes 60 % of the open items, but not all of them. **The 4-layer result is OPEN, not 0.** Its first DRC
also found a tool defect: GND island-stitch vias were placed only against F.Cu/B.Cu copper, so 4 of them landed on In2.Cu
signal tracks. `apply-routes.py` now keeps those vias clear of In2.Cu tracks; the 2-layer output is unaffected.

**Outline fit study.** `B20_GROW_X` widens the packing area to the right and moves the right-hand corner holes and
fiducial with the edge. The drawn outline is unchanged, so this is a placement-feasibility result at 1.0 mm courtyard
clearance, not a routed layout.

| Width | 1.0 mm clearance placement |
|---|---|
| 110 mm (current) | does not fit: 11 parts unplaced |
| 112 mm | does not fit: 8 parts unplaced |
| 113 mm | does not fit: 6 parts unplaced |
| 114 mm | does not fit: 3 parts unplaced (CP1, RP1, RP2) |
| **115 mm** | **fits: smallest whole-millimetre width** |
| 120 mm / 130 mm | fits |

The 2-layer router has not been run on a wider placement. A wider board would move the right-hand corner holes, its
legs and the right fiducial by the same amount. J6/J7 on the left edge, J10/J11, J5 with Board P, and the P1/TP row keep
their positions.

#### Phase 28: 4-layer B20 adopted, JLC7628 stackup, 5 unconnected

**Decision (owner, project decision card answered 2026-11-02 15:40Z, relayed by the coordinator):** B20 grows to
4 copper layers rather than bottom-side placement or a larger outline. The phase 27 comparison is the basis. This
draft decision is recorded here and not in `scripts/schgen/decisions.json`: that registry covers the Board P/A/B wave-6
specs, accepts no `board_b20_spec` target, and requires component fact evidence, but a stackup has no component owner. The
4-layer board replaces the 2-layer phase 26 board in `boards/board-b20-draft/board-b20-draft.kicad_pcb`. Under the
latest-only rule, the 2-layer board is retired to Git history (`e0738a3`). `route.py` rebuilds it with `B20_LAYERS=2`;
that run still reproduces the phase 26 routes exactly.

**Stackup.** The stackup is JLC's published 4-layer "JLC7628" impedance-control stackup from the jlcpcb.com Help Center
"PCB Stackup" page, read 2026-11-02:

| Layer | Thickness |
|---|---|
| F.Cu | 0.035 mm |
| 7628 prepreg | 0.2 mm, Er 4.6 |
| In1.Cu (GND plane) | 0.0175 mm |
| Core | 1.065 mm |
| In2.Cu | 0.0175 mm |
| 7628 prepreg | 0.2 mm, Er 4.6 |
| B.Cu | 0.035 mm |

The page lists 0.8–2.0 mm finished thicknesses but does not tie these layer values to one of them; they sum to about
1.57 mm. It gives no core Er, so the core reuses 4.6. Loss tangent and mask thickness are KiCad defaults. **2 oz outer
copper on 4 layers is UNKNOWN:** the page does not mention it. The 2-layer draft assumed 2 oz, so the copper-width and
current checks at 0.035 mm outer copper are OPEN.

**Router changes, 4-layer only.** The 2-layer output is unchanged.

- Every GND surface pad gets its own via to the In1.Cu plane before any signal is routed.
- A `fanout` pass lays a short escape stub and via on 49 pins (`FANOUT_4L`) before the power and signal nets. The
  pins are the ones earlier runs left boxed in, plus the fine-pitch signal pins of U5, U7, U8, U13 and U16. Rip-up
  keeps these escapes.

| Trial (phase 22 placement unless named) | Router open | DRC unconnected |
|---|---|---|
| Phase 27 best (stub reach 6 mm) | 24 | 22 (8 GND, 14 signal) |
| Phase 26 spread placements (0.6/0.6, IC halo 0.6) on 4 layers | 25 / 32 | NOT RUN (router result worse) |
| GND pads first | 18 (0 GND) | NOT RUN (superseded by fanout) |
| + fanout of the 18 failed pins | 6 | 7 (0 GND) |
| + fanout of every fine-pitch pin of nine ICs (64 pins) | 10 | NOT RUN (router result worse) |
| Iterated fanout lists, B.Cu/In2.Cu cost 0.6 / 0.7 / 0.8, 12 rip-up rounds | 5–7 | 6 for the best |
| **Adopted: 49-pin fanout list** | **5** | **5 (0 GND, 5 signal)** |

Adopted board, KiCad 10.0.6 DRC with schematic parity run in place (heavy-guard then `flock`):

- 0 errors and 0 parity issues.
- Warnings: 7 `via_dangling` and 2 `lib_footprint_mismatch` (J10/J11 silk clip).
- **5 unconnected items, all signal:** U7.2 REF25, U7.6 UV5_DIV, U16.8 P5_SUP, U15.5 LVL12 and Q46.1–U8.1 OVN_CMP.
  Each is one pad short of a routed fragment.
- The board has 2821 track segments and 759 vias. **The 5 unconnected items are OPEN.**

**Hot loop and sense geometry with In1.Cu under F.Cu (desk numbers, nothing measured).** The stage templates are
unchanged. Each hot loop is still a 29.6 mm² polygon on F.Cu. The six sense traces are unchanged: 3.31–6.48 mm on F.Cu,
loop areas 10.55 / 6.71 / 12.75 mm². What changes is the return path: In1.Cu now lies 0.2 mm under every F.Cu loop. The
2-layer draft's nearest continuous return was the B.Cu pour, 1.5 mm down.

| Quantity | Free-space model (phase 24) | Ideal plane 0.2175 mm below |
|---|---|---|
| Hot-loop inductance, trace-equivalent | about 11 nH (circular loop of equal area, 0.8 mm trace) | about 5 nH (0.19 nH/mm microstrip × 24.7 mm perimeter) |
| Magnetic coupling hot loop → sense loop | ×1 | ×0.0016–0.0026 at the 18–23 mm stage distances |
| Differential pickup at the amplifier inputs (RSH1 / RSH2 / RSH3) | 0.727 / 0.183 / 0.341 mV peak | 0.85 / 0.17 / 0.27 µV peak |
| Capacitive common-mode at the inputs | 0.20–0.77 mV peak | 0.02–0.12 µV peak |

Model: `loop-check.py` now applies the plane by default to 4-layer routes. A loop parallel to an ideal plane gets an
image with opposite current 2h below it, so the magnetic coupling falls by
|1 + (3cos²θ − 1)(r/R)³|, with R = √(r² + 4h²) and cos θ = 2h/R. Trace-to-trace capacitive coupling is scaled by
1/(1 + (d/h)²), a two-microstrip crosstalk rule of thumb.

These are **ideal-plane lower bounds**. They do not cover:

- the plane's finite 0.0175 mm thickness (about 1.9 skin depths at the 51 MHz edge frequency, but thinner than one skin
  depth below about 14 MHz);
- 759 via antipads and the GND-plane cut-outs around them;
- current crowding at the loop ends.

The real pickup lies between the two columns. A field solver or a bench measurement would be needed to place it, so it
is **OPEN**.

## 4. Gate table against the OSC–PD contract

| Contract item | Result | Basis |
|---|---|---|
| Source band, ripple excluded (§0) | **PASS** | +12: 12.042–12.196 V; −12: 12.017–12.182 V; +5: 5.0543–5.0981 V. With hot RDS(on) (×1.25, PA) the minimums are 12.026 / 12.001 / 5.0504 V |
| Ripple at load < 1 mVp-p (§0) | **OPEN (averaged + ripple injection, not a switching simulation)** | The vendor TPS54560 transient model still aborts after the phase-8 retry (§5). Injecting the switching current into the linear filter network gives 22.6 / 13.4 / 43.6 µVp-p at the output, with PA ESL and no SRF, coupling or ground-return terms. §5 |
| Limiter trip window (§1) | **PASS (+12 V and −12 V shunt evidence G-U)** | +12: 2.0418–2.0847 A; +5: 0.4369–0.4608 A; −12: 1.9423–1.9953 A, including ILIMIT × R_TH (review finding 1). Phase 9 draws the 10 mΩ shunts, LIMIT 649 Ω / 2.74 kΩ and the 20.3 kΩ / 33 Ω −12 V divider |
| No trip on the startup ramp (§1, §5) | **PASS (drawn, shunt evidence G-U)** | Start into the full transient load peaks at I_min × V_terminal,max / V_nom: 2.0327 / 1.9289 / 0.4078 A, against trip minimums of 2.0418 / 1.9423 / 0.4369 A. The phase-9 `*R` runs peak at 2.013 / 0.403 / 1.91 A (SIM; limiter comparators not in the decks). §5a, §5c |
| Maximum never delivered (let-through) (§1) | **OPEN** | The limiter trips; it does not regulate current. A series inductor that holds a hard short below I_MAX for an illustrative 2 µs switch-off needs 1.6 / 5.2 / 0.26 mH, which is infeasible at 2 A; switch-off time has no guaranteed figure. The contract needs let-through stated as charge or time above I_MAX. §5a |
| Any trip → all-rail latched shutdown, re-plug only (§1) | **PASS (topology)** | FAULT_N is shared; the latch has no retry path. The limiter comparators are not in the simulation |
| Reverse blocking on all rails (§2) | **PASS (topology)** | Back-to-back NFET pairs on all three rails |
| Reverse current ≤ 1 mA (§2) | **OPEN** | Divider currents are 0.23 / 0.50 / 0.12 mA (CALCULATED). FET and BSS138 leakage at temperature is not retained as a guaranteed value |
| Discharge time ≤ 100 ms (§3) | **PASS at zero load** | 57.9 / 81.7 / 8.6 ms at ceiling capacitance; the hold-up drives the switches for 0.48–1.33 s |
| Discharge order at zero load (§3) | **PASS** | +5 V at 0.8 V after 7.4 ms; +12 V absent at 57.9 ms; −12 V at 81.7 ms with \|−12\| = 1.45 V (≤ 6 V). C+/C− window 0.337–1.411 |
| Discharge order under load (§3) | **OPEN** | After disconnect each rail falls at I/C into its own load (2.0 A on 180 µF is 11 V/ms). An asymmetric OSC load reorders the rails. Guaranteeing the order needs a tracked ramp-down (RAMP falling while the pairs stay in tracking): a contract change, proposed but not drawn |
| Discharge resistor pulse rating | **OPEN** | The PROPOSED 1206 loads have no owner record or pulse curve |
| Disconnect skew ≤ 1 ms (§3) | **PASS (SIM)** | Run `disR`: source current below 10 mA at 21.4 / 20.0 / 24.0 µs after EN_N; skew 4 µs. Gate below 1 V at 15.9 / 16.5 µs |
| Monotonic common ramp ≥ 10 ms, slope limits (§5) | **PASS (SIM) at the I_TRANSIENT_MIN load; FAIL (SIM) at no load: owner exception requested** | Arithmetic: 0.754 / 0.314 / 0.762 V/ms unclamped and 0.845 / 0.425 / 0.834 V/ms clamped, PASS. Phase 10 (§5d, CRMD 470 nF): 0.322 / 0.134 / 0.322 V/ms in all four completed loaded runs. At no load +5 V reaches 0.85–0.90 V/ms (limit 0.51) and −12 V 1.21–1.47 V/ms (limit 1.22, `adv` fails). Phase 9 failed +5 V in every run |
| Re-enable inside the RAMP reset window (§5, interrupted ramp) | **PASS (SIM, phase-12 interlock)** | Phase 12 (§5f): the minimum-off interlock holds every re-enable for 18.6–121 ms (arithmetic). All eight re-entry runs at the shortest hold pass every §5 row. Phase 11 (§5e), without the interlock, failed the slope rows at 6 ms off from steady state |
| Start skew ≤ 0.41 ms (§5) | **Voltage form PASS (SIM, drawn clamps); time form FAIL (SIM)** | Phase 10 (§5d), six completed runs: voltage forms held (worst +12 V 0.433 V while \|−12\| < 0.1 V; \|−12\| 0.523 V while +12 V ≤ 0.5 V); ramp start skew 2.24–3.93 ms. Phase 9 (§5c), ten completed runs: +12 V ≤ 0.408 V while \|−12\| < 0.1 V (limit 0.5 V); \|−12\| ≤ 0.72 V while +12 V ≤ 0.5 V (limit 6 V). Ramp start skew is 1.16–2.42 ms. The 0.41 ms row is the time form of the +12 V-alone limit at the fastest slope; the clamps meet the voltage form without it. Arithmetic: ≤ 0.411 V and ≤ 0.553 V |
| Band-entry skew ≤ 2 ms; +5 V up last (§5) | **PASS (SIM)** | Phase 10: 0.79–0.88 ms, +5 V last in every completed run. Phase 9: 0.74–0.83 ms; +5 V last in every completed run. Arithmetic: 1.500 ms |
| +12 V lead over \|−12 V\| ≤ 0.5 V (review finding 5) | **PASS (SIM)** | Phase 10: at most 0.36 V; \|−12\| leads by up to 0.29 V. Phase 9: at most 0.33 V; \|−12\| leads +12 by up to 0.31 V |
| P59-A: \|−12\| ≤ 6 V until +12 V ≥ 5.2 V | **PASS (SIM)** | At most 5.452 V (arithmetic 5.749 V) |
| +5 V ≤ 0.8 V before both analog rails are "up" | **OPEN (definition)** | As drawn, +5 V ≤ 0.69 V (SIM) while either analog rail is below 1.45 V, and reaches 3.39 V by the time both reach 8 V. Which level means "up" is a question for OSC (§5c) |
| OV/UV windows (§6) | **PASS** | All three rails fit, using actual E192 resistor values |
| VIN undervoltage (§6) | **PASS** | Trips at 16.86–17.04 V, below 19 V (PA). The U5B input is 1.86 V at the Board P overshoot bound |
| Contract detect before enable (§6) | **PASS (topology), polarity G-U** | RDY needs PDOK valid for 0.21–0.73 s; POR ends at 36 ms at most. PDOK low = PDO2 explicit contract (POWER_OK_CFG 10b, DS12499 Rev 7 Table 4, mirror authority) |
| Servo settled before enable (review finding 2) | **PASS** | Loop time constants 5.03 / 5.56 / 5.12 ms against RDY ≥ 0.21 s |
| P5_SUP independence (review finding 7) | **PASS (topology), single-fault OPEN** | U14 is separate from the +5 V output chain. A U14 failure still removes all supervision; that single fault is OPEN |
| U4 40 V margin | **PASS** | The inverter IC sees VIN + \|Vout\| ≤ 37.6 V against 60 V operating and 65 V absolute (G) |
| Converter current | **PASS** | Switch peaks 2.73 / 0.90 / 4.01 A against a 6.3 A minimum current limit (G) |
| Switch VGS | **PASS** | +12 V pair 13.2 V maximum, +5 V clamped at 11.6 V, Q25 11.1 V, against 20 V (G). +12 V minimum 4.5 V at VIN UV |
| Servo trim authority | **PASS** | Required FB current is covered on all three rails across TPS54560 VREF 0.792–0.808 V (G) |
| OPA2187 input range (5 V amplifiers) | **PASS** | Worst input 2.503 V against (V+) − 2 V = 3.07 V |
| Converter loop stability | **PASS (SIM, average model)** | §5. Phase margin ≥ 82° (+12), ≥ 88° (+5), ≥ 58° (−12 at light load, 21 V); gain margin ≥ 13.4 dB |
| Inrush from Board P into the B20 input bulk | **OPEN** | Board P now slews its Q1 closure (Board P soft-start draft, 3.1–10 V/ms, ≤ 2.5 A into 250 µF); Q1 SOA is not in its bundle |

## 5. Simulation (ngspice in the pinned KiCad 10.0.6 image)

All runs use `ngspice -b` from `kicad/kicad@sha256:18693567…dd3ec`, with `set ngbehavior=psa`.
The vendor models were downloaded from TI's model pages on 2026-10-31 and are not retained.

| Model | TI package | SHA-256 of the download |
|---|---|---|
| TPS54560 average model (`AVG.LIB`) | SLVMCU2 | `e74a8842728963360a0342e940ac96ee93b8ec8d21b65005a2b8152202550597` |
| TPS54560 transient model | SLVMCU1 | `e7dbf0f2b5026f18936790dedee28f479eb724ccf19dc7466cf95717a8735883` |
| OPAx187 | SBOMAB6 | `50c3c188a17bca04f2760feac9c5e6350561eb12a1e25d5a2c19b08dcc2b3930` |
| CSD18543Q3A | SLPM286 | `fbf5e0b576e11f2e0a1a65b0b2c589f86a182ae9ef5c412a0b0b98cd8c569715` |

The CSD18543Q3A library needed a syntax-only copy for ngspice: five `.PARAM name value` lines became
`name=value`. The original library file hashes to `fa4ef721…ba170`. No vendor BSS138, DMP3036 or
BZT52 model was obtained (the Diodes site refused the download). Those parts appear as ideal or
generic elements in the decks, and their results are therefore tagged PA.

### Converter loop stability (average model)

The average model's COMP node is referenced to absolute ground, so the inverter is simulated with the
simulator ground on the IC GND (M12_RAW) and system ground as a separate node. Four corners per rail:
VIN 19 / 21 V × full / light load.

| Rail | Crossover | Phase margin | Gain margin |
|---|---|---|---|
| +12 V | 5.2–5.3 kHz | 82–93° | ≥ 13.8 dB |
| +5 V | 5.0 kHz | 88–94° | ≥ 13.4 dB |
| −12 V, Cc 47 nF | 0.63–3.1 kHz | 58–93° (58° at light load, 21 V) | ≥ 16 dB |

With the earlier 12 nF Cc the inverter had 33° at light load and 21 V. That run is why Cc is 47 nF.
The servo integrators are outside this loop; their 5 ms time constant is three decades below crossover.

### Ripple

**Switching model: still NOT RUN.** Phase 8 retried the vendor transient model once with a changed
input: the `FAST=1` model variant and a 1.2 ms deck. It stopped at 0.14 ms with "timestep too small"
at node `x1.u3_n16532327`; the earlier failures were at 0.92 ms on `x1.isw`.

**Averaged + ripple injection (labelled; not a switching simulation).** `ripple_injection()` in
`scripts/pcb/calculate-board-b20-draft.py` replaces each converter by its averaged operating point
plus an injected periodic current at the minimum switching frequency (501 kHz, typ −10 %). It then
takes the periodic steady state of the linear filter network by harmonic superposition. A linear ngspice
transient of the same network was also tried; it stopped with "timestep too small" at a node with no
switching element, so the frequency-domain form is used.

| Rail | Injected current | Stage-1 bank | Output | Limit |
|---|---|---:|---:|---:|
| +12 V | buck triangle 1.256 App at VIN 25.21 V | 27.9 mVp-p | 22.6 µVp-p | 1 mVp-p |
| +5 V | buck triangle 0.809 App | 17.7 mVp-p | 13.4 µVp-p | 1 mVp-p |
| −12 V | inverter diode current, IL 3.27 A, 20 ns edges (PA) | 77.1 mVp-p | 43.6 µVp-p | 1 mVp-p |

The network is the GRM32 stage-1 bank (3 mΩ, 0.5 nH ESL PA per part), the 10 µH post filter at its
68 mΩ DCR maximum, then 25SVPF47M (30 mΩ, 1 nH PA) plus one GRM32, into the I_MAX load. The status
stays **OPEN**: ESL, inductor self-resonance, switch-node coupling, the ground return and the
measurement bandwidth are PA or unsourced, and they set the high-frequency content that a real
measurement would see.

### Tracking start and disconnect

The decks model the converters as stiff sources behind 20 mΩ (PA). They include the shunts, the
tracking amplifiers (vendor OPAx187), the switch pairs (vendor CSD18543Q3A) and the contract maximum
load capacitance. Enable is at 40 ms; `disR` disables at 85 ms. Cases:
`nom`, `adv` (+12/+5 thresholds −0.5 V, −12 +0.5 V), `rev` (opposite), and each again with resistive
loads at I_TRANSIENT_MIN (`*R`). The solver ladder (`run_ladder.sh`) records the variant used.
`disR` stops at 90.3 ms ("timestep too small" in the −12 V FET after switch-off); its disconnect data is complete.

| Run | Ramp start skew | Band entry (ms after enable) +12 / +5 / −12 | Max slope V/ms +12 / +5 / −12 | Peak source A |
|---|---|---|---|---|
| nom | 0.81 ms | 42.98 / 43.13 / 42.09 | 0.71 / 0.48 / 0.83 | 0.13 / 0.06 / 0.15 |
| adv | 1.07 ms | 42.98 / 43.13 / 42.09 | 0.71 / 0.30 / **1.55** | 0.13 / 0.04 / 0.28 |
| rev | 2.26 ms | 42.98 / 43.14 / 42.10 | 0.86 / **0.75** / 0.72 | 0.16 / 0.09 / 0.13 |
| nomR | 0.55 ms | 43.42 / 43.77 / 42.79 | 0.71 / 0.30 / 0.78 | 2.02 / 0.41 / 1.92 |
| advR | 1.01 ms | 43.42 / 43.77 / 42.79 | 0.71 / 0.30 / **1.46** | 2.02 / 0.41 / 1.92 |
| revR | 2.04 ms | 43.42 / 43.77 / 42.79 | 0.79 / **0.56** / 0.73 | 2.02 / 0.41 / 1.92 |
| disR | 0.56 ms | 43.43 / 43.77 / 42.79 | 0.71 / 0.30 / 0.78 | 2.02 / 0.41 / 1.92 |

Ramp start is the first time a rail rises 0.1 V above its pre-bias plateau after RAMP release.
Band entry uses the source-band floor (12.00 / 5.05 / 12.00 V).

**What the runs changed.** The first drawn network (1 nF integrators) limit-cycled at no load:
−12 V rose in steps at up to 6.9 V/ms with 1.2–1.6 A pulses into the load capacitance. Those runs are
kept in `tracking-1nf-archive/`. Raising the integrators to 10 nF and adding the 10 kΩ zero on the
−12 V loop removed the stepping. Two slope rows still fail with the threshold shifts. Start skew still
fails everywhere. Both need a different start scheme; a shared gate-drive reference is one candidate,
and nothing like it is drawn.

**The test load is at the trip edge.** I_TRANSIENT_MIN loads at 12 V become 2.013 A at the 12.05 V
terminal, which is above the +12 V trip minimum. The limiter comparators are not in these decks.

### 5a. Phase 8: start into the full load and let-through (arithmetic)

A resistive load sized at I_TRANSIENT_MIN at the nominal rail draws I_min × V_terminal,max / V_nom
once the rail is up: 2.0327 / 1.9289 / 0.4078 A (`limiter_startup()`). The ramp does not add to that
peak: the load RC (180 µF × 6 Ω = 1.08 ms) is shorter than the servo time constant (about 5 ms), so
V + RC·dV/dt stays below the final V. Judged on peaks, the drawn trip minimums fail on +12 V and −12 V.

| Rail | Startup floor | Drawn trip | Proposed trip (not drawn) | Result |
|---|---:|---:|---:|---|
| +12 V | 2.0327 A | 2.0032–2.0898 A | 2.0418–2.0847 A (1 × 10 mΩ 0.1 %, LIMIT 649 Ω / 2.74 kΩ) | PASS (PROPOSED) |
| −12 V | 1.9289 A | 1.9025–1.9967 A | 1.9423–1.9953 A (1 × 10 mΩ 0.1 %, 10.2k + 10.1k / 33 Ω) | PASS (PROPOSED) |
| +5 V | 0.4078 A | 0.4369–0.4608 A | unchanged | PASS |

The 10 mΩ shunt (RESI PCSR2512BR010M6, C23067428) and its 20 mΩ sibling (PCSR2512BR020M6,
C19690158) were known only from a read-only JLC listing (G-U). Phase 19: the RESI sheet (V8) was read from a
DigiKey-hosted copy (10 mΩ ±0.1 %, ±15 ppm/°C, 2 W, 14 A), recorded as candidate `rec-c23067428`; its
facts stay UNSOURCED until a manufacturer-hosted copy is retained, so the G-U tag stands.

Let-through stays **OPEN**. The limiter is a trip, not a regulator. Bounding a hard short below I_MAX
with a series inductor needs L ≥ V × t_off / (I_MAX − trip_max): 1.6 mH (+12 V), 5.2 mH (−12 V) and
0.26 mH (+5 V) at an illustrative 2 µs, and no retained source guarantees t_off.

### 5b. Phase 8: +12 V-first start sequence by construction (proposal; drawn and simulated in §5c)

Each tracking target becomes the minimum of its RAMP term and a clamp derived from the other rails'
actual terminals (`start_sequence_proposal()`). Followers only lag their targets, and the contract
excludes overshoot, so each inequality holds on the outputs regardless of FET thresholds:

- |−12| ≤ 1.10 × V(+12): −12 V cannot start or lead before +12 V.
- V(+12) ≤ 1.10 × |−12| + 0.40 V: +12 V alone stays below the 0.5 V one-rail limit.
- V(+5) ≤ 0.55 × (min(V(+12), |−12|) − OFF_P5), with OFF_P5 = 0 (unconditional) or 1.5 V (P59-A).
- RAMP C rises from 1 µF to 1.5 µF so that every clamped slope stays inside the contract.

Clamp-amplifier and diode errors are taken as 1 % (PA).

| Row | Limit | Construction | Margin |
|---|---|---|---|
| Unconditional: +12 V alone | ≤ 0.5 V | ≤ 0.404 V | 0.096 V |
| Unconditional: −12 V alone | ≤ 6 V | ≤ 0.556 V while +12 V ≤ 0.5 V | 5.44 V |
| Unconditional start skew (time form of the row above) | ≤ 0.41 ms | voltage form met directly | n/a |
| P59-A: −12 V magnitude until +12 V ≥ 5.2 V | ≤ 6 V | ≤ 5.777 V | 0.223 V |
| P59-A: −12 V lead (time form, 0.069 × ramp time) | ≤ 1.15 ms on this ramp | 0.81 ms at 6 V | 0.34 ms |
| P59-A: +12 V lead | no R-VEE limit; ≤ 6.50 ms with +5 V present | single analog rail ≤ 0.404 V | n/a |
| Slopes | 1.23 / 0.51 / 1.22 V/ms | 0.829 / 0.461 / 0.821 V/ms | PASS |
| First band entry / band-entry skew | ≥ 10 ms / ≤ 2 ms | 28.2 ms / 1.53 ms | PASS |
| Pair overdrive at the end of the ramp | > 0 | +12 0.69 V, −12 0.41 V, +5 0.94 / 0.13 V | PASS |

With OFF_P5 = 0, +5 V stays at or below 0.8 V until both analog rails reach 1.47 V, and it starts with
them. With OFF_P5 = 1.5 V (P59-A), the hold extends until both analog rails reach 2.97 V, and +5 V starts
1.81 ms later. That lag breaks the literal "all ramps start within 0.41 ms" row, whose basis is the
+12 V-leading case only.

Holding +5 V ≤ 0.8 V until both analog rails are inside their source bands is not compatible with the
contract. +5 V then needs ≥ 8.33 ms at 0.51 V/ms after analog band entry, against the 2 ms band-entry
skew (PROPOSED) and the one-common-ramp shape (CONTRACT). OSC has to define the level that "both analog
rails up" means.

The 28 ms first band entry is inside the 20–50 ms range that the contract lists only as candidate
PWR-C1; OSC tolerance of slower ramps is unverified.

### 5c. Phase 9: start-order clamps and shunts drawn and simulated

`board_b20_spec.py` now draws the §5a shunts and the §5b construction, with these values:

| Clamp | Network | Bound (arithmetic, 1 % clamp error PA) |
|---|---|---|
| −12 V target | U16A: LVLM12 = P12_OUT × 10.2k / (64.9k + 10.2k) against RAMP_M12 | \|−12\| ≤ 1.0947 × V(+12) |
| +12 V target | U15A: MABS = 0.15 × \|−12\| (100k / 15k); U15B: LVL12 from MABS (8.87k / 92k) and REF25 (30.1k / 10k) | V(+12) ≤ 1.0990 × \|−12\| + 0.407 V |
| +5 V target | U16B: MABS against RAMP_P5 | V(+5) ≤ 0.498 × \|−12\| |
| Common | RCP1–RCP3 1 kΩ from RAMP; Q62–Q64 BSS138 body diodes; U15/U16 on P5_SUP / M12_PRE; RAMP C 1.47 µF | first band entry ≥ 27.65 ms, band-entry skew ≤ 1.50 ms |

Arithmetic (`start_sequence_proposal()`): +12 V alone ≤ 0.411 V (0.089 V margin to 0.5 V); \|−12\|
≤ 0.553 V while +12 V ≤ 0.5 V; \|−12\| ≤ 5.749 V at +12 V = 5.2 V (P59-A, 0.251 V margin); +5 V ≤ 0.8 V
until \|−12\| ≥ 1.623 V (+12 V ≥ 1.468 V).

**Decks.** `manufacturing/sim/board-b20-phase9/gen_tracking.py` writes the phase-7 decks with the
clamps, the 10 mΩ shunts and 1.47 µF. `run_ladder.sh` records the solver variant. Two start modes are
kept. In `tracking/`, stiff sources start from initial conditions (`uic`), as in phase 7. In
`tracking-ramp/`, every source rises from 0 V over 2 ms from a DC operating point.

The clamp amplifiers made the vendor CSD18543Q3A and OPAx187 models fragile in the first
microseconds. A 100 MΩ resistor across Q5 (RCV1) is a simulation-only convergence aid and not a board
part. With it, 10 of 14 runs completed: the `ramp` set has six of seven, and the `uic` set has
`nom`, `adv`, `nomR` and `revR`. `disR` aborts in both modes and in eight extra variants (50 µs and 5 µs
disable edges, gear and trap). The furthest runs fail during the disable edge, before switch-off ("timestep
too small" in a CSD18543Q3A). Its start portion matches
`nomR`. The disconnect path (EN_N to the gates) is unchanged from phase 7, so the phase-7 disconnect row
stands and is not re-simulated. The retained results are in `manufacturing/sim/board-b20-phase9/results.json`.

| Run (mode) | Start skew | Band entry +12 / +5 / −12 (ms after enable) | Max slope V/ms +12 / +5 / −12 | Peak source A |
|---|---|---|---|---|
| nom (ramp) | 1.70 ms | 53.25 / 53.68 / 52.86 | 0.54 / **0.86** / **1.54** | 0.10 / 0.11 / 0.28 |
| adv (ramp) | 2.42 ms | 53.00 / 53.42 / 52.60 | 0.53 / **0.60** / **1.40** | 0.10 / 0.07 / 0.26 |
| rev (ramp) | 1.42 ms | 53.58 / 54.01 / 53.19 | 0.54 / **1.03** / 1.14 | 0.10 / 0.13 / 0.21 |
| nomR (ramp) | 1.42 ms | 53.83 / 54.46 / 53.72 | 0.53 / **0.70** / 1.06 | 2.01 / 0.40 / 1.91 |
| advR (ramp) | 2.12 ms | 53.59 / 54.22 / 53.48 | 0.53 / **0.53** / 1.10 | 2.01 / 0.40 / 1.91 |
| revR (ramp) | 1.16 ms | 54.19 / 54.82 / 54.08 | 0.54 / **0.82** / 0.84 | 2.01 / 0.40 / 1.91 |
| nom (uic) | 1.59 ms | 52.98 / 53.41 / 52.59 | 0.54 / **0.90** / 1.20 | 0.10 / 0.11 / 0.22 |
| adv (uic) | 2.15 ms | 52.76 / 53.19 / 52.37 | 0.53 / **0.61** / 1.20 | 0.10 / 0.07 / 0.22 |
| nomR (uic) | 1.43 ms | 53.69 / 54.31 / 53.57 | 0.53 / **0.72** / 1.09 | 2.01 / 0.40 / 1.91 |
| revR (uic) | 1.18 ms | 54.03 / 54.66 / 53.92 | 0.54 / **0.84** / 0.85 | 2.01 / 0.40 / 1.91 |

| Voltage-form row (contract §5) | Limit | Worst over the 10 runs | Result |
|---|---|---|---|
| +12 V while \|−12\| < 0.1 V | ≤ 0.5 V | 0.408 V | **PASS (SIM)** |
| \|−12\| while +12 V ≤ 0.5 V | ≤ 6 V | 0.722 V | **PASS (SIM)** |
| P59-A: \|−12\| while +12 V < 5.2 V | ≤ 6 V | 5.452 V | **PASS (SIM)** |
| +12 V − \|−12\| | ≤ 0.5 V | +0.333 / −0.309 V | **PASS (SIM)** |
| +5 V while either analog rail < 1.45 V | ≤ 0.8 V | 0.691 V | **PASS (SIM)** |
| +5 V while either analog rail < 8 V | not defined (see the OSC question) | 3.389 V | OPEN |
| Band-entry skew; +5 V last | ≤ 2 ms | 0.74–0.83 ms; +5 V last in all runs | **PASS (SIM)** |
| Slopes | 1.23 / 0.51 / 1.22 V/ms | +5 V exceeds in every run; −12 V in `nom` and `adv` (ramp) | **FAIL (SIM)** |

**What the runs show.** The clamps hold every voltage-form start row in every completed run,
including the threshold-shifted cases, without depending on FET thresholds. The time-form start skew
(1.16–2.42 ms) is no longer the binding test, because the voltage limits it was derived from are met
directly. The slope rows fail. While a target is pinned by its clamp, its pass pair does not stay at the
edge of conduction. When the clamp releases, the loop catches up in a short step: −12 V moves 0.03 → 0.7 V
at up to 1.54 V/ms in `nom` (ramp), and +5 V moves 0.01 → 0.4 V at up to 1.03 V/ms in `rev`. Both steps
are below 0.7 V and carry under 0.3 A of charging current, but they exceed the slope rows as written.
Candidate fixes are not drawn: a small positive offset on each clamped target so the pair stays
biased, or slew-limiting each RAMP_x node directly. Phase 10 (§5d) traces the steps to the start instead and draws a longer RAMP reset delay.

**OSC question: what does "both analog rails up" mean for the +5 V hold?** The contract has three
statements. R-ADG forbids +5 V above 0.8 V with one analog rail absent and the other at 8 V or more.
Row 137 says to bring +5 V up last. The P59-A row says no OSC limit applies "if +5 V stays ≤ 0.8 V until
both analog rails are present". As drawn, +5 V stays ≤ 0.8 V only until both analog rails pass about
1.5 V; it reaches 3.39 V by the time both reach 8 V. The three possible definitions behave differently:

1. **"Present" = above about 1.5 V (as drawn).** One common ramp, start-skew voltage form, band-entry
   skew ≤ 2 ms and +5 V last are all met (SIM). Since the analog rails track within about 10 % of each
   other, the R-ADG state (one absent, the other ≥ 8 V) cannot occur. ADG5412F IN is not guaranteed
   low below the ±5 V supply minimum, so OSC #59 (load-side inhibited enables) still has to cover it.
2. **"Present" = ±5 V, the ADG5412F minimum supply.** +5 V would need its own later ramp. That breaks
   the one-common-ramp shape and the 0.41 ms start-skew row. Band-entry skew ≤ 2 ms would be a new
   design target that has not been shown.
3. **"Present" = inside the source band (12.00 V).** +5 V then needs at least 8.33 ms at 0.51 V/ms after
   analog band entry. That breaks the 2 ms band-entry skew (PROPOSED) and the common-ramp shape
   (CONTRACT).

The question for OSC: does the +5 V hold require definition 1, 2 or 3? If 2 or 3, which of the
common-ramp, start-skew and band-entry-skew rows is OSC prepared to relax?

### 5d. Phase 10: RAMP reset delay lengthened (CRMD 470 nF)

**Mechanism, corrected from §5c.** The phase-9 waveforms show the steps come from the start, not from a
clamp release. At enable every tracking integrator leaves its rail at about 1.2 µA / 10 nF
(|M12_PRE| through the 10 MΩ offset into CT), 0.12 V/ms at the gate. With 100 nF, RAMP was released
about 16 ms after enable (12–23 ms over the Q12 threshold range). The gates were then still about 2 V
from conduction, so each pair started late and caught up in a step.

**Change (drawn).** CRMD rises from 100 nF to 470 nF (C1623, already in the B20 parts list). The release
moves to 56.4–108.1 ms after enable. The gates can then climb at least 6.70 V before the earliest
release (`calculate-board-b20-draft.py`). CSD18543Q3A VGS(th) is not in its bundle, so the climb is
stated rather than compared with a threshold (UNSOURCED). There is no slowest-ramp limit in the
contract. Band entry now comes about 140 ms after enable instead of 53 ms. RDY (≥ 0.21 s) gates enable
and is unaffected. The common ramp now takes about 53 ms from first rise to band entry, beyond the 20–50 ms
PWR-C1 candidate. Part of the lower slope comes from the generic Q12 switch model releasing gradually
as its gate falls slowly (PA). After a disable, RAMP is reset 5.0–16.8 ms later instead of 1.1–3.6 ms. A
re-enable inside that window is the contract's separate interrupted-ramp case; phase 11 (§5e) simulates it.

**Decks.** `manufacturing/sim/board-b20-phase10/` holds the same decks with CDLY 470 nF, disable at
235 ms and stop at 250 ms. The retained results are in `results.json`. ngspice ran without the KiCad
lock, one CPU per run.

| Run (ramp mode) | Solver | Start skew | Band entry +12 / +5 / −12 (ms after enable) | Max slope V/ms +12 / +5 / −12 | Pre-bias plateau V |
|---|---|---|---|---|---|
| nomR / advR / revR | trap | 3.65 ms | 140.60 / 141.30 / 140.51 | 0.32 / 0.13 / 0.32 | 0.088 / 0.030 / 0.055 |
| disR (start portion) | gear; stops at the disable edge | 3.65 ms | 140.61 / 141.31 / 140.52 | 0.32 / 0.13 / 0.32 | same |
| rev (no load) | trap | 3.93 ms | 140.09 / 140.59 / 139.72 | 0.45 / **0.90** / 1.21 | 0.145 / 0.052 / 0.096 |
| adv (no load) | trap, rshunt 1e9 | 2.24 ms | 140.05 / 140.56 / 139.68 | 0.32 / **0.85** / **1.47** | 0.144 / 0.051 / 0.097 |
| nom (no load) | FAILED all seven variants at 0.85 ms, before enable | — | — | — | — |

The three loaded runs are identical, so the ±0.5 V threshold shifts no longer change the start. Every
loop reaches its pre-bias plateau before RAMP moves. The `uic` set failed to converge in every case
(stops between 8 µs and 162 ms) and gives no phase-10 evidence. The phase-9 `uic` rows are not
carried forward as phase-10 results.

| Voltage-form row (contract §5) | Limit | Worst over the six runs | Result |
|---|---|---|---|
| +12 V while \|−12\| < 0.1 V | ≤ 0.5 V | 0.433 V (adv) | **PASS (SIM)** |
| \|−12\| while +12 V ≤ 0.5 V | ≤ 6 V | 0.523 V | **PASS (SIM)** |
| P59-A: \|−12\| while +12 V < 5.2 V | ≤ 6 V | 5.361 V | **PASS (SIM)** |
| +12 V − \|−12\| | ≤ 0.5 V | +0.364 / −0.293 V | **PASS (SIM)** |
| +5 V while either analog rail < 1.45 V | ≤ 0.8 V | 0.637 V | **PASS (SIM)** (definition 1, accepted by OSC) |
| Band-entry skew; +5 V last | ≤ 2 ms | 0.79–0.88 ms; +5 V last in all runs | **PASS (SIM)** |
| Slopes at the I_TRANSIENT_MIN load | 1.23 / 0.51 / 1.22 V/ms | 0.32 / 0.13 / 0.32 V/ms | **PASS (SIM)** |
| Slopes at no load | 1.23 / 0.51 / 1.22 V/ms | 0.45 / 0.90 / 1.47 V/ms | **FAIL (SIM)**: owner exception requested |

**Why no load still steps.** With no load, each source-only pair overshoots its pre-bias target, to
0.14 / 0.05 / 0.10 V. It cannot pull the output back down, so the integrator winds to its rail again
before RAMP moves. The fast part of each step lies between 0.08 and 0.45 V on +5 V and between 0.26 and 0.73 V on −12 V. A bleed that
discharges 180 µF within the reset delay would need well under 300 Ω, a permanent 40 mA or more at
12 V. That is not cheap, so this residual is not fixed in B20.

**Requested owner exception (OSC).** OSC accepted definition 1 for the +5 V hold. It found that no
OSC part limits the +5 V step: at most 120 µF × 1.03 V/ms = 124 mA, inside the 400 mA transient
minimum and 500 mA maximum. The phase-10 no-load +5 V step is lower, at most 0.90 V/ms (108 mA). The
request is a contract exception for the no-load start only: a +5 V excursion of ≤ 0.90 V/ms below
0.45 V, and a −12 V excursion of ≤ 1.47 V/ms below 0.75 V (≤ 265 mA into 180 µF). The −12 V part has
no OSC evaluation yet. Loaded starts meet the slope rows.

### 5e. Phase 11: re-enable inside the RAMP reset window (loaded, nominal)

**Decks.** `manufacturing/sim/board-b20-phase11/` starts the loaded nominal case as in §5d (enable at
40 ms, CRMD 470 nF), disables EN_N and re-enables it 6, 10, 14 or 20 ms later. `reR*` disables at
150 ms, mid-ramp with the rails near 4 V. `reB*` disables at 200 ms, with the rails in band. The phase-9/10
decks never passed the disable edge, so these decks soften it for simulation only: 1 ms EN_N edges, and
the three gate pulldown switches (B10, B11, B25) at 1/35 S instead of 1/3.5 S. Disconnect timing is
therefore not evaluated here. All seven runs completed; `results.json` holds them with the solver variant
of each. The rows below are evaluated from the re-enable to the end of the run.

| Run (re-enable after disable) | RAMP at re-enable | Max slope V/ms +12 / +5 / −12 | +12 V while \|−12\| < 0.1 V | +12 − \|−12\| | Band-entry skew; +5 V last | Result |
|---|---|---|---|---|---|---|
| reR6 / reR10 / reR14 / reR20 | 0.0011 / 0.0004 V | 0.32 / ≤ 0.42 / ≤ 0.71 | ≤ 0.300 V | −0.162 / +0.257 V | 0.79–0.80 ms; yes | **PASS (SIM)** |
| reB10 / reB14 | 0.0006 / 0.0004 V | 0.32 / ≤ 0.27 / ≤ 0.51 | ≤ 0.248 V | −0.162 / +0.200 V | 0.79 ms; yes | **PASS (SIM)** |
| reB6 | 0.049 V | 0.32 / **1.02** / **1.31** | 0.471 V | −0.182 / +0.446 V | 0.79 ms; yes | **FAIL (SIM)**: slope rows |

In every run |−12| stays ≤ 0.53 V while +12 V ≤ 0.5 V, ≤ 5.36 V while +12 V < 5.2 V (P59-A), and +5 V
≤ 0.637 V while either analog rail is below 1.45 V. All rails return to the §5d steady values.

**What breaks.** Only a re-enable 6 ms after a disable from steady state breaks a contract row. At that
point the rails have not discharged (0.07 / 0.12 / 0.09 V) and RAMP is at 0.049 V. +5 V then steps at
1.02 V/ms between 0.02 and 0.40 V, and −12 V at 1.31 V/ms between 0.18 and 0.50 V. The +5 V step is
above the 0.90 V/ms no-load exception requested in §5d. The −12 V step is inside the requested 1.47 V/ms
bound. The rails sit above their pre-bias targets at re-enable, so the steps are likely the §5d no-load
mechanism (inference, not traced). Mid-ramp disables do not break any row at any delay. Phase 12 (§5f) closes the case on the PD side with a
minimum-off interlock instead of an OSC timing rule. During the off interval itself the rails
fall at up to 11 V/ms and leave the start rows: +5 V reaches 1.14 V while an analog rail is below
1.45 V, and +12 − |−12| reaches −0.67 V. That interval belongs to the OPEN discharge-order row.

### 5f. Phase 12: minimum-off interlock (PD side)

**Change (drawn).** The enable latch can no longer be set until a hold-off has run after any disable
or P5_SUP return. Q65 (BSS138, gate EN_E) holds EN_HO at GND while enabled. After a disable, EN_HO
charges from P5_SUP through RHO1 + RHO2 (2 × 150k, C22807) into CHO (1 µF, C15849). Q66 (BSS138) sits in
series with Q38 in the RDY set path and closes only once EN_HO passes its VGS(th). The latch holds through
Q33 / Q34 as before, so Q65 resetting EN_HO does not drop an enable. A P5_SUP brownout leaves EN_HO at
GND (it was held there while enabled), so the hold runs again when P5_SUP returns.

**Arithmetic** (`calculate-board-b20-draft.py`, PASS on tagged inputs). The hold is 18.6–121 ms. The short
end uses VGS(th) 0.5 V (PA minimum; the bundle has only the 1.5 V maximum), CHO at 0.6 µF effective (−40 %,
DC bias and tolerance PA) and P5_SUP high. The long end uses 1.5 V, 1.1 µF and P5_SUP low. The RAMP reset
is engaged by 17.1 ms at the latest, so every re-enable lands after it. 121 ms is below the earliest RDY
(214 ms), so the first start is not delayed. Cost: +2 × C22807, +1 × C15849, +2 × C40912. That is
USD 0.11 per board at the 2026-10-31 catalog tiers, and adds no new BOM line.

**Simulation** (`manufacturing/sim/board-b20-phase12/`, 14 runs, all completed). The decks use the shortest
hold (0.5 V, 0.6 µF: 19 ms) and a behavioural model of the latch.

| Runs | Effective re-enable after disable | Max slope V/ms +12 / +5 / −12 | +12 V while \|−12\| < 0.1 V | +12 − \|−12\| | Band-entry skew; +5 V last | Result |
|---|---|---|---|---|---|---|
| reB6 / reB10 / reB14 / reB20 (in-band disable) | 19.1 / 19.1 / 19.2 / 21.2 ms | 0.32 / 0.13 / 0.32 | ≤ 0.126 V | −0.162 / +0.035 V | 0.79–0.80 ms; yes | **PASS (SIM)** |
| reR6 / reR10 / reR14 / reR20 (mid-ramp disable) | 19.1 / 19.1 / 19.2 / 21.2 ms | 0.32 / 0.13 / 0.32 | ≤ 0.126 V | −0.162 / +0.035 V | 0.79–0.80 ms; yes | **PASS (SIM)** |
| nomR / advR / revR (loaded start) | enable at 40.5 ms (hold already run) | 0.32 / 0.13 / 0.32 | ≤ 0.126 V | −0.162 / +0.089 V | 0.79 ms; yes | **PASS (SIM)**, same as §5d |
| adv / rev (no-load start) | same | 0.32–0.45 / 0.85–0.90 / 1.21–1.47 | ≤ 0.433 V | −0.293 / +0.364 V | 0.87–0.88 ms; yes | **FAIL (SIM)** slope rows, same as §5d |
| nom (no-load start; failed in phase 10, completes now with rshunt 1e9) | same | 0.35 / **0.94** / 0.84 | 0.144 V | −0.197 / +0.100 V | 0.88 ms; yes | **FAIL (SIM)** +5 V slope |

In every run |−12| stays ≤ 0.60 V while +12 V ≤ 0.5 V, ≤ 5.36 V while +12 V < 5.2 V, and +5 V
≤ 0.637 V while an analog rail is below 1.45 V. The phase-11 failure (re-enable 6 ms after an in-band
disable) no longer occurs: the request waits for the hold. **New finding:** the `nom` no-load start,
which phase 10 could not complete, gives +5 V 0.94 V/ms. That is above the 0.90 V/ms bound of the
requested no-load exception (§5d). The exception would have to state ≤ 0.95 V/ms, or the no-load step
needs a fix. This is an OSC question.

## 6. Checks run on this draft

| Check | Result |
|---|---|
| `gen_schematic.py` | PASS: 269 components, 779 pin specs (phase 13: J10/J11 and three owned bindings) |
| `verify_geometry.py` | PASS: 772 spec pins matched (phase 13) |
| KiCad 10.0.6 native ERC (pinned image; phase 10 serialised through `flock`) | exit 0. 0 errors and 35 warnings (phase 19; the 21 missing `*_DRAFT` footprint warnings of phase 13 are gone): 35 `pin_to_pin` warnings on the unspecified pins of J5 (5) and J10/J11 (30, the same symbol pin type as on the current Board B). Two `power_pin_not_driven` errors on U14 were closed with PWR_FLAGs on VIN and GND |
| KiCad 10.0.6 native netlist + `verify_netlist.py` | PASS: 142 nets, 779 nodes (phase 13) |
| `calculate-board-b20-draft.py` | FAIL (SIM) start skew (time form); OPEN let-through, ripple, loaded discharge order; ramp slope PASS (SIM) loaded / FAIL (SIM) no load; everything else PASS. Phase 10 uses CRMD 470 nF |
| ngspice AC and tracking runs | As in §5 |
| PCB DRC + schematic parity (phase 28, 4 layers, partly routed) | 0 errors, 0 parity issues; 2 `lib_footprint_mismatch`, 7 `via_dangling` warnings; 5 unconnected items (0 GND, 5 signal), so **OPEN**, not a pass (2-layer phase 26: 55; phase 22: 62; phase 21: 81; phase 19 placement: 499) |
| Routing | **OPEN**: 4 layers with an In1.Cu GND plane (phase 28, JLC7628 stackup; 2 oz outer UNKNOWN); power stages and all six sense traces routed; 5 router connections open; hot loop 29.6 mm² per stage; Kelvin pairs not coupled within 0.3 mm, a geometry limit (pads 6.41 mm apart); desk pickup 0.18–0.73 mV peak differential in free space, 0.17–0.85 µV peak over an ideal In1.Cu plane, real value between (§3a, phases 24 and 28); self-check in `boards/board-b20-draft/loop-check.json` |
| BOM/CPL | NOT RUN: no export |

## 7. Independent review findings (review of `bad5ddf`)

| Finding | Severity | Phase-7 state |
|---|---|---|
| 1. INA301 LIMIT ~80 µA source current omitted | HIGH | **Fixed.** LIMIT dividers recomputed with ILIMIT 79.2–80.8 µA (G): windows above |
| 2. Servo time constants 3.5–19.6 s vs enable at 26–53 ms | HIGH | **Fixed.** Servo senses at `*_SH`, tau about 5 ms; RDY now 0.21–0.73 s |
| 3. No inrush limit from Board P C3 when Q1 closes | HIGH | **Fixed on paper (Board P draft).** Miller soft start C36/Q5/R27: 3.1–10 V/ms, ≤ 2.5 A. Q1 SOA OPEN |
| 4. +2.9 V margin to 28 V rests on typical figures | HIGH | **OPEN.** L7 stays BLOCKING; only the TVS2200 clamp bounds the node (`manufacturing/input-protection-20v.md`) |
| 5. Rail lead 0.51–0.90 V vs ≤ 0.5 V | MEDIUM | **Fixed (SIM).** Common tracking start: +12 leads \|−12\| by at most 0.24 V |
| 6. Zener knee / VGS assumption | MEDIUM | **Fixed.** Gates driven through 10 kΩ; clamp current < 1 mA; the 4.5 V RDS(on) row is used everywhere |
| 7. +5 V buck powering its own supervision | MEDIUM | **Fixed (topology).** U14 P5_SUP. A U14 single fault is OPEN |
| 8. Discharge hold-up | MEDIUM | **Fixed.** CDH charged only while enabled; 0.48–1.33 s window |
| 9. STUSB4500 VBUS sense behind the eFuse | MEDIUM | **OPEN.** Needs DS12499 behaviour with VBUS_P lagging VBUS_IN, or a bench check |
| 10. Timing and margin claims | LOW | **Partly fixed.** RDY is 0.21–0.73 s and POR ends by 36 ms, so they no longer overlap. R14 + R28 = 940 Ω gives 26.7 mA at 25.1 V. Q55 VGS is 11.2 V. The OVP `node_rows` use the fitted 22.57 V. **OPEN:** the 20 mV UVLO margin to vSafe5V (unchanged, trade-off against the OVP divider), the VBEN 3.15 mA sink rating, and the C3 polarity confirmation |
| 11. Shared compensation; OPA2187 input diodes load REF25 | LOW | **Fixed.** Per-stage compensation, verified in §5. The REF5025 load budget is 3.0 mA, including the comparator input-diode current |
