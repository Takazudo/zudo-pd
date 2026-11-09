# B20 draft layout: independent review of hot loops, Kelvin sensing, returns and D3 heat

Reviewer: independent desk review (not the implementer). Date: 2026-11-03.
Board reviewed: `boards/board-b20-draft/board-b20-draft.kicad_pcb`, working-tree copy on branch
`claude/project-thread-9b2dt7` (uncommitted in the implementer's tree), sha256
`b2bf37e1e8a4daccfadfe9a24f20543f1d6a9233ba5f56b995db087104ad9599`. This is the same hash that
`manufacturing/power-layout-b20.json` records. Schematic source: `scripts/schgen/board_b20_spec.py`.

Status vocabulary: PASS / FAIL / OPEN / UNKNOWN / NOT RUN. This PCB is an **unvalidated draft**, and nothing
in this review is measured. All numbers come from a desk analysis of the copper geometry.

**Correction 2026-11-08 (load cases, #230; the review text below is kept as written).** Where this review says
"rated" it means 1.2 / 0.8 / 0.5 A, the PD15 Board B budget that the B20 scripts then mislabelled. It is a legacy
comparison case, not the PD20 contract. The contract is continuous 1.7 / 1.6 / 0.3 A, 20 ms transient 2.0 / 1.9 /
0.4 A and let-through maximum 2.1 / 2.0 / 0.5 A ([PD20 status](pd20-status.md)); the review's "limiter maximum" is
that let-through maximum. Against the contract, the pre-fix −12 V trip of about 0.93 A sat below the 1.6 A continuous
load, not 16 % above a 0.8 A load (that blocker is fixed). On the current board, `thermal-check.json` gives D3 TJ
93–120 °C at the continuous load and 109–147 °C at the let-through maximum (desk node model); the thermal bench rows
below apply at the continuous load and the let-through maximum, and the −12 V start-into-load row at 1.6 A.

Method: I parsed the board with `scripts/schgen/sexp.py` and extracted every pad (absolute position, size, net),
all 3241 segments, all 772 vias and the filled polygons of all 5 zones. I rasterized each copper layer at
20–50 px/mm and built copper connectivity graphs per net. Loop areas are shoelace areas of the polygon that
follows the copper. I ran no KiCad oracle and no field solver, so DRC and solver results are **NOT RUN** here.
Stackup is taken from the file: F.Cu 35 µm, 0.2 mm 7628 prepreg, In1.Cu 17.5 µm (GND), 1.065 mm core,
In2.Cu 17.5 µm (signal tracks only, **no zone**), 0.2 mm prepreg, B.Cu 35 µm. Every via is a through via.

Reference-designator mapping (spec → PCB) used below: LC → **L5**, DC → **D3**, LCF → **L6**, RCFB → **R12**,
CCHF → **C13**, RCRT → **R9**, CCCP → **C12**, RCFT → **R11**, RL3C (33 Ω) → **R35**, RL3B → **R34**.

---

## -12 V current limiter is not Kelvin: R35 taps M12_PRE 22.6 mm upstream of RSH3, so the trip falls to about half (BLOCKER)

- **Where.** U9A compares `M12_SH` (U9.3) against `LIM12N`. LIM12N = RL3A/RL3B/RL3C divider, referenced to
  `M12_PRE` through **R35.2 at (42.9, 64.9)**. Its copper is a 0.4 mm stub (42.6, 64.6)→(42.6, 63.6). The stub joins
  the 1.0 mm `M12_PRE` **load trunk** from L6.2 (35.875, 61.7) to the RSH3 current pad (59.85, 55.175).
- **Copper between the tap and the shunt.** Every load amp flows through 22.6 mm of 1.0 mm F.Cu. The route is
  (42.6, 63.2)→(46.9, 63.2)→(49.8, 60.7)→(51.6, 59.0)→(51.7, 57.0)→(55.1, 55.6)→(56.3, 54.4)→(56.7, 53.5)→
  (58.8, 53.5)→(59.2, 54.7). L6.2 has only this one track, so there is no parallel path. `current-check.json` gives
  the same trunk as 28.38 mm from L6.2 to RSH3.2.
- **Desk effect.** At 35 µm and 25 °C the run is about **11.1 mΩ**, in series with the 10 mΩ shunt inside the
  comparator's differential. The design trip is 33/20333 × 12.13 V = 19.7 mV. With the shunt alone that is 1.97 A.
  With the copper added it becomes about **0.93 A**, and about 0.87 A with the copper at +35 K. That is below the
  documented start-into-full-load floor (1.93 A) and only 16 % above the 0.8 A rated load. The added term has a
  copper TC of +0.39 %/K. If the outer copper were 2 oz (UNKNOWN, and the implementer does not rely on it), the trip
  would be about 1.27 A.
- **The implementer's check measures the wrong pin.** `loop-check.json` reports RSH3 "pin 4 lands_on sense pad". But
  U9.4 is the OPA2187 **V− supply**, not a comparator input. The 0.2 mm trace (53.9, 57.7)→(57.1, 55.8) from the RSH3
  sense pad (57.75, 55.05) feeds only the amplifier supply.
- **Fix.** Move R35.2 so that it connects only through a dedicated 0.2 mm trace to the RSH3 M12_PRE **sense pad**
  (57.75, 55.05). Route that trace as a pair with the U9.3 M12_SH sense trace, and place R34/R35 next to U9. Feed U9.4
  from the M12_PRE bus with its own trace, and put its 100 nF (C9DN) directly at the pin. Today the bypass reaches
  U9.4 only through the load trunk, the shunt terminal and the 0.2 mm sense trace, about 10 mm.

## -12 V output bank CCO1–CCO4 reaches U3/D3 only through a 0.4 mm path across the R12 (FB) and C13 (COMP) pads (MAJOR)

- **Path.** The connectivity graph has only one link from CCO1.2–CCO4.2 (`M12_RAW`, x 45.72, y 49–61) to the rest of
  `M12_RAW` (U3 PAD, D3.2, CCIN1, L6.1). Removing via (45.1, 50.9) isolates all four capacitors. The link is:
  CCO1.2 → F.Cu 0.4 mm → via (45.1, 50.9) → **In2.Cu 0.4 mm** (45.1, 50.9)→(43.7, 50.2)→(38.4, 50.2) → via
  (38.4, 50.2) → F.Cu 0.4 mm through **R12.2 (37.3, 50.45)**, the RCFB feedback-divider bottom → (36.5, 51.4)→
  (31.8, 52.6) through **C13.2 (31.45, 52.95)**, the CCHF COMP capacitor → (30.1, 51.3) → U3 PAD track.
- **Desk numbers.** In2 0.4 mm × 6.9 mm at 17.5 µm is about 16.9 mΩ. F.Cu 0.4 mm × about 8.7 mm is about 10.7 mΩ.
  Two vias add about 2 mΩ, for **about 29 mΩ** in total. With CIN referenced to M12_RAW, the CCO current is the
  inductor ripple: ΔI_L ≈ 19 V × 0.404 / (10 µH × 556.7 kHz) ≈ **1.38 A p-p** (0.40 A RMS). That gives:
  - about 40 mV p-p of triangular drop between the CCO bank and the U3 GND/PAD;
  - about 12 mV p-p at the R12.2 tap relative to U3 GND, which couples onto FB (0.8 V reference) through the 145k/10k
    divider at about 0.93×;
  - an extra series resistance on the bank, so the ripple at M12_RAW (before L6) grows by about ΔI × 29 mΩ.
- **Fix.** Make M12_RAW a power net, not a routed signal.
  - Add an M12_RAW pour on In2.Cu, and on B.Cu, under x ≈ 18–48, y ≈ 38–63. The comparator pre-routes now on In2
    there have to move. Stitch it to the CCO M12_RAW pads (≥2 vias each), to the D3 anode pour and to the U3 thermal
    vias.
  - Or move the CCO bank so that its M12_RAW pads abut the F.Cu `M12_RAW_D3` pour.
  - Return R12, C13, R9 and C12 (the RCFB, CCHF, RCRT and CCCP quiet ground) through a separate trace that carries no
    current, from U3 pin 7/PAD, as a single-point AGND.

## -12 V hot loop: the reported 44.4 mm² understates the loop, and CCIN2 is effectively outside it (MAJOR)

- **The fast loop is CCIN–U3 high-side FET–D3.** CIN is VIN→M12_RAW and the IC GND/PAD is M12_RAW, so the CCO current
  is non-pulsating (see the previous finding). The members and their pad centres are:
  CCIN1 VIN (24.88, 42.87) → 1.2 mm F.Cu (25.2, 43.7)→(25.6, 46.8)→(26.5, 47.3) → U3.2 VIN (27.3, 47.365) → package
  internal path through the die at about (30.0, 48.0) → U3.8 SW (32.7, 46.095) → 1.5 mm F.Cu (32.8, 45.8)→(37.5, 42.2)
  → D3.1 cathode (38.05, 41.25) → D3 body → D3.2 anode (31.15, 41.25) → `M12_RAW_D3` pour plus a 1.5 mm track
  (30.6, 42.2)→(28.0, 42.2) → CCIN1.2 (27.92, 42.87). Every branch is on F.Cu.
- **Independent areas.** Pad-centre polygon (the implementer's method): **44.4 mm²**, which I reproduce exactly.
  Copper-following path: **47.9 mm²**, perimeter 33.1 mm. Copper path plus the package's VIN-to-SW internal path:
  **51.4 mm²**. The 44.4 figure joins pad centres with straight chords and skips the in-package path, so it is a
  lower bound, not the true loop (about 15 % low).
- **CCIN2 is not on the same copper.** The `M12_RAW_D3` fill is two islands: 48.1 mm² (D3, CCIN1, U3 edge) and
  11.2 mm² around CCIN2.2 (21.96, 42.87), which the VIN feed cuts off. CCIN2's return runs: via (20.6, 42.1) →
  In2.Cu 0.4 mm about 6 mm → via (21.8, 47.7) → B.Cu 0.8 mm about 7.9 mm → U3 thermal vias. Its projected loop is
  about 63 mm² plus two layer transitions, so CCIN2 carries little of the HF current. CCIN1 alone, a 10 µF 50 V X7R
  1210 at about 32 V bias with UNKNOWN effective capacitance, carries about 0.66 A RMS rated and about 1.65 A RMS at
  the limiter maximum. The desk input-ripple margin assumed two capacitors.
- **The In1.Cu GND plane is continuous but perforated under the loop.** In1 is one filled polygon with no slots or
  splits. Inside the 51.4 mm² loop, **7.2 mm² is void**. The 8 U3 thermal vias on M12_RAW (pitch 1.3 mm, antipad
  about 1.1 mm, web below the 0.25 mm minimum) merge into one **2.3 × 4.9 mm void at x 28.8–31.1, y 45.5–50.4**.
  Further voids come from the VIN via (25.1, 46.8), the C_BOOT via (27.4, 45.3) and the ARM_GND signal via
  (32.3, 43.6), which sits inside the loop. The In1 plane is GND, not the loop's own net (M12_RAW). It works only as
  an eddy-current image shield, so the "ideal plane" factor in the implementer's pickup model is optimistic by an
  UNKNOWN amount.
- **Desk loop inductance (assumption, not a solver).** I assume about 0.2 nH/mm over a plane 0.2 mm away, times about
  34 mm, plus the 1210 ESL, the SMC lead frame and the package. That gives **about 10–12 nH**. At 1.34 A in 6.2 ns,
  the SW overshoot is about 2–3 V. This is OPEN until measured.
- **The SW node is larger than in the bucks.** C_SW F.Cu is **28.3 mm²** (A_SW 20.2, B_SW 17.8), because the
  2.5 × 3.3 mm SMC cathode pad is on the node. That is about 6 pF to In1 and about 30 mA peak of injected
  common-mode current at 33 V / 6 ns (desk).
- **Fix.**
  - Turn and move D3 so that its cathode sits beside U3.8 and its anode beside the CCIN M12_RAW pads and the U3 PAD
    edge. A target is ≤ 30 mm², like stages A and B.
  - Feed VIN to CCIN1/CCIN2 from outside the M12_RAW pour so that both M12 pads land on one contiguous pour.
  - Add a 0.1–1 µF 0603/0805 X7R capacitor rated ≥ 50 V straight from U3.2 to the PAD/pin 7 edge.

## +12 V (U1) and +5 V (U2) hot loops: about 20 % above the reported 29.6 mm², with continuous return and plane (MINOR)

- **U1.** C3 VIN (44.88, 5.87) → 1.2 mm (45.2, 6.7)→(45.6, 9.8) → U1.2 (47.3, 10.365) → die → U1.8 (52.7, 9.095) →
  1.5 mm → D1.1 (55.05, 5.98) → D1.2 (51.05, 5.98) → 1.5 mm GND (50.5, 5.8)→(48.0, 5.8) → C3.2 (47.92, 5.87).
  Copper path **32.1 mm²**; with the package path **35.5 mm²**, perimeter 26.2 mm.
- **U2.** Same template at x + 28 mm (C7, D2), with 0.8 mm VIN, SW and return branches. **32.9 / 36.4 mm²**.
- **Return and plane.** The diode-to-CIN return is direct F.Cu on both stages. The exposed-pad vias are GND and join
  In1, and In1 under each loop is 34.3/35.7 and 35.2/36.5 mm² covered (only signal-via antipads missing). There is
  no split. Stitching: 8 PAD vias plus 3 GND vias within 3 mm of C3/D1 (and the same for U2).
- **Gap.** Each buck has one 10 µF 1210 CIN and no small high-frequency capacitor at the pin. The U2 branches are
  0.8 mm. Fix: add 100 nF 0603 from pin 2 to the PAD on each stage. Widening the U2 branches to 1.2 mm is optional.

## Kelvin sensing: the INA301 pairs and the U9 M12_SH input land on exclusive sense pads; the only shared copper is the R35 tap above (MINOR / NOTE)

| Shunt → amp pin | Leaves from | Other copper on that pad | Path (F.Cu, 0.2 mm) | Nearest SW node |
|---|---|---|---|---|
| RSH1 P12_PRE → U11.8 | sense pad (55.45, 29.05) | none (degree 1) | (54.8, 29.8)→(51.9, 31.4), 3.3 mm | C_SW about 15 mm |
| RSH1 P12_SH → U11.7 | sense pad (57.95, 34.95) | none; touches the pad corner only | (57.3, 34.2)→(55.9, 32.3)→(51.9, 32.3), 6.5 mm | about 15 mm |
| RSH2 P5_PRE → U12.8 | current pad (84.7, 30.425), inner edge; load enters the outer edge | 0.6 mm load track | (83.8, 31.2)→(79.9, 31.4) | B_SW about 22 mm |
| RSH2 P5_SH → U12.7 | current pad (84.7, 33.575), inner corner; the load also leaves the inner corner (85.4, 33.0) | load plus the R18 servo tap | (83.8, 32.8)→(79.9, 32.3) | about 22 mm |
| RSH3 M12_SH → U9.3 | sense pad (60.25, 60.95) | none | (59.6, 60.2)→(54.7, 58.3)→(53.9, 58.3), 6.4 mm | C_SW about 20 mm |
| RSH3 M12_PRE → (LIM12N via R35) | **load trunk, 22.6 mm upstream** | load current | see the BLOCKER | — |

- **No sense trace shares copper with a switch node or with In2/B.Cu load copper.** All sense traces are on F.Cu over
  In1.
- **The pairs are not coupled.** The 0.3 mm gap target is not met (the implementer reports the same). The
  point-symmetric RESI land puts the sense pads 6.4 mm apart, which leaves sense loops of 10.6 and 12.8 mm² around
  the shunt body. The loops are fed by load-current ripple after L2/L6, so this is a NOTE.
- **RSH2 is a two-terminal 1206 land.** The pad and solder resistance sits partly inside the measurement. With the load
  exiting the same inner corner at pad 2, the error is a fraction of a mΩ against 20 mΩ: UNKNOWN, NOTE. Fix: take the
  P5_SH load from the outer pad edge, (85.4, 34.4) side, and keep the inner corner for sense only.

## Return paths: no plane split, but four antipad clusters force local detours (MINOR)

- **In1.Cu GND is a single filled polygon over the whole board, with no slots.** The largest voids are merged antipad
  clusters:
  - J10 pins 9–16, **39.9 mm²** at x 31.4–41.2, y 70.3–75.1, and J11 pins 9–16, **41.2 mm²**. Here 1.8 mm pads plus
    0.25 mm clearance on a 2.54 mm pitch leave a web below the minimum width.
  - The M12_CS / M12_OUT / M12_G via cluster at the Q5/Q6 switch pair, **16.4 mm²** at x 53.8–61.5, y 44.9–49.9.
  - The U3 thermal vias, 9.8 mm².
  The GND pins J10/J11 3–8 and J6.1 (7.0, 50.54) connect solidly (`connect_pads yes`).
- **The return from J6.1 and J10/J11 GND to C3/C7/L5/CCO crosses an unbroken In1.** The detours are around the
  clusters only. With In1 at 0.5 oz, a desk spreading resistance of about 1–1.5 mΩ from J6.1 to the top bucks is
  small next to the rail tolerances.
- **The F.Cu and B.Cu GND pours are heavily fragmented.** B.Cu is cut by the P12_OUT (1.0 mm) and M12_OUT trunks
  under the −12 V stage, so all return relies on In1.
- **Stitching near the converters is adequate in count.** L5.2 has 2 vias, each CCO GND pad 1, U1 and U2 have
  8 + 3 each.
- **Implementer's open item confirmed.** The polygon-connectivity and stitch-adequacy checks are listed as NOT RUN in
  `power-layout-b20.json`, and that is still true.
- **Fix (optional).** Shrink the via antipads in the Q5/Q6 cluster, or spread the three-via transitions so the In1
  webs survive.

## D3 heat: D3 and U3 share one 48 mm² F.Cu island with no thermal vias, and thermal-check.json does not model it (MAJOR)

**Copper connected to D3:**

| Layer | Anode (M12_RAW) | Cathode (C_SW) |
|---|---|---|
| F.Cu | `M12_RAW_D3` island **48.1 mm²** (contains the D3 anode pad, CCIN1.2 and the top of the U3 PAD). Whole connected M12_RAW F.Cu (with the U3 PAD and the 1.5 mm tracks to L6/CCIN1) is 92.3 mm² | **28.3 mm²** (pad, 1.5 mm tracks, L5.1, U3.8, C11) |
| In1.Cu | 0 (GND plane; only isolated via rings, 4.8 mm²) | 0 |
| In2.Cu | 9.3 mm² of 0.4 mm traces, none at D3 | 0 |
| B.Cu | 10.6 mm² of 0.8 mm traces (CCIN2 return), none at D3 | 0 |
| Vias at the D3 pads | **none**. The nearest M12_RAW vias are U3's 8 thermal vias, 5.5–7 mm away, and they land on **no** plane | none |

**The implementer's thermal assumptions do not match this copper:**

- **Zone area is overcounted.** `power-layout-b20.json` gives 59.3 mm² for the M12_RAW zone and the draft text gives
  55.6 mm². Both include the 11.2 mm² CCIN2 island, which is not joined to D3 on F.Cu.
- **U3 is rated on a board it does not have.** `thermal-check.json` gives U3 a TJ from the JEDEC standard-board
  θJA of 42 °C/W: 53.3 °C rated, 99.4 °C at the limiter maximum with maximum RDS(on). On that standard board the PAD
  vias reach internal planes. Here U3's PAD is M12_RAW, and its vias join nothing on In1, In2 or B.Cu.
- **D3's 0.56 W (rated) and 1.40 W (limiter maximum) never appear as a local junction or copper temperature.** They
  appear only in the board-mean rise. D3 and U3 dump their heat into the **same** island.

**Desk estimate (assumptions stated; not measured, not a solver):**

- Heat leaves the island through the 0.2 mm prepreg into In1 and then spreads. The prepreg term is
  R = t / (k·A), with k = 0.3–0.4 W/m·K and A = 48–92 mm², which gives **5.4–13.9 K/W**.
- Plane spreading is (1/(2π·k·t_eff))·ln(b/a), with a ≈ 4.5 mm, b ≈ 25 mm and k·t_eff = 0.0135–0.020 W/K. That is
  In1 0.5 oz plus 50–100 % of one fragmented 1 oz outer pour, and gives **13.6–20 K/W**.
- I add the board-mean rise from `thermal-check.json` and take D3 θJ-terminal as 10 K/W, the implementer's figure,
  which I have not checked against the datasheet.
- The model ignores D3's reverse leakage, which rises with temperature, and heat leaving through the cathode. Both
  move the result in opposite directions, so treat the ranges as order-of-magnitude.

| Case | P(D3) + P(U3) on the island | Board mean rise | Island | D3 TJ (desk) | Implementer U3 TJ |
|---|---|---|---|---|---|
| Rated, typical RDS | 0.56 + 0.32 W | 8.5–12.8 K | about 65–83 °C | **about 71–89 °C** | 53.3 °C |
| Limiter max, typical → maximum RDS | 1.40 + 0.96–1.42 W | 20.9–35.4 K | about 106–171 °C | **about 120–185 °C** | 80.2–99.4 °C |

The upper limiter-maximum range crosses the 150 °C limit, where leakage feedback starts thermal runaway. D3 and U3
margins on this copper are **UNKNOWN**, and a bench measurement decides them.

**Fix:**

- Use the In2.Cu and B.Cu M12_RAW pours from the CCO finding above as heat spreaders, which fixes both findings at
  once.
- Add ≥ 8 through vias (0.3 mm) in the `M12_RAW_D3` pour next to the D3 anode pad and between D3 and U3.
- Give U3's PAD vias a plane to land on.
- Extend `thermal-check.py` with a shared-island node for D3 and U3 instead of the JEDEC θJA.

## Implementer reports are internally stale in two places (MINOR)

- `manufacturing/board-b-20v-switcher-direct-draft.md` line 1355 (status table) still says "hot loop 29.6 mm² per
  stage". Phase 33 (line 859) and `power-layout-b20.json` say 44.4 mm² for stage C.
- `loop-check.json` `sense.RSH3.pins.4` treats the U9 supply pin as the Kelvin input (see the BLOCKER). The
  `return_branch_diode_to_cin` check for stage C reports a routed F.Cu return but does not flag that CCIN2 is
  outside it.

---

## Bench-only items for the test sheets (all NOT RUN: no hardware exists)

| Area | Item | Status |
|---|---|---|
| −12 V limiter | Trip current on −12 V versus the 1.97 A design: sweep the load at VIN 19 / 21 V, log the U9.1 (ILIM12N_CMP) edge, and record the copper temperature near RSH3 | NOT RUN |
| Startup | −12 V start into full load (0.8 A) plus the rated capacitive load: no false limiter trip. Ramp skew between rails against the 0.41 ms rule | NOT RUN |
| Startup | +12 / +5 / −12 tracking order and overshoot from PDOK; re-plug and the minimum-off interlock | NOT RUN |
| Ripple | C_SW to M12_RAW ringing and overshoot (ground spring at D3.2/CCIN1.2); A_SW and B_SW to GND likewise | NOT RUN |
| Ripple | M12_RAW ripple at CCO1.2 **and** at U3.7, and the difference between them (CCO path drop); U3 FB (C_FB) ripple relative to U3.7 | NOT RUN |
| Ripple | Output ripple and noise at J6/J7 and J10/J11 for all rails, at the PRE nodes and after the switch pairs, 20 MHz bandwidth plus full bandwidth | NOT RUN |
| Stability | Load-step response on each rail (25 → 75 % → 25 %), with and without the servo | NOT RUN |
| Thermal | D3 case, U3 case, L5 and CCIN1 temperature (thermocouple or IR camera) at the rated load and at the limiter maximum, VIN 19 / 21 V, 40 °C-equivalent ambient, until steady state | NOT RUN |
| Thermal | U1/D1, U2/D2 and RSH1/RSH3 temperature at the rated load and at the limiter maximum | NOT RUN |
| Accuracy | INA301 trip current for +12 V and +5 V, and RSH2 Kelvin error (P5 rail) | NOT RUN |
| EMI | Near-field probe pre-scan over the U3/D3 loop and the J10/J11 headers (optional) | NOT RUN |

Desk checks that are still NOT RUN in this review: KiCad 10.0.6 DRC/ERC oracle re-run, field-solver loop
inductance, polygon-connectivity / stitch-adequacy script.
