# PD20 status: Board P r3 + B20 (20 V / 5 A pair)

**Development review record. PD20 is not electrically qualified, released or ordered.** It records what the PD20 stream
(Astra review 2026-11-04, PD20 and CHECKPOINT) changed, what was checked at which revision, and what stays open. Every
bench row below is a test sheet that has **not been executed**; each one needs owner approval and hardware.

## 2026-11-12 JST owner decision D10 (Board P r3 C36)

`dec-p-20v-c36-x7r-1206` replaces C36 CL10A105KB8NNNC C15849 (0603 X5R) with CL31B105KBHNNNE C1848 (1206 X7R
1 µF 50 V), superseding only the C36 part of `dec-p-20v-q1-soft-start`. The Q1 closure screen at all eight corners gives
3.88–5.34 V/ms, at most 1.336 A against the 4.185 A U2 I(OL) minimum and a minimum Q1 SOA ratio of 1.67, on typical
25 °C data only. Readiness D10 is **correction adopted, verification open**: the Board P PCB is rebuilt natively for the 1206
land (Actions run 43107657333; only C36 moved, y 32.5 → 32.75 mm; DRC with parity 0 errors / 0 unconnected). The pair assembly
preview and development export are NOT RUN (selected Mac required), and bench T3 is NOT RUN.

## 2026-11-10 JST execution disposition

The [local Mac ledger](prototype-order-readiness.md) separates current source,
capability, verification and decision blockers. The earlier native/export rows
below remain dated development evidence until replaced by final-source receipts.
Current B20 has **270 fitted components**; the 269-component export is historical.
Fresh native correction, pair assembly and independently verified DEVELOPMENT REVIEW
export passed at clean `3f24a3abb43e0f24f5e0a12f739ba8ae6bbad03d`; see the
[durable package review](verification/pd20-native-20261110/development-export-review.json).
This closes local manufacturing verification, not the pre-order electrical holds below.

Six fresh startup cases at `fda0667df503aa7cdc8ec0d45920dd4c731dc56c` have complete
actual waveforms. The strengthened **1.5 V** predicate gives worst +5 V 0.6554 V
while an analog rail magnitude is below that threshold. However, adjacent-sample
analysis exposes no-load excursions hidden by the old averaged slope rows.
Actual 2 us refinements preserve the selected baseline solver variants and still
exceed the adopted no-load slope/current ceilings. See
[startup refinement](sim/board-b20-phase33/startup-refinement.md): **PRE-ORDER
HOLD**, not a measured violation or a waived limit. Small negative increments
also prevent an unqualified monotonicity claim. All eight re-entry cases now have complete actual waveforms and strengthened analysis.
The [dated full-suite receipt](sim/board-b20-phase33/execution-20261110.md) separates
the passing effective-reenable screens from off-interval sufficient-screen excursions
and unqualified installed shutdown behavior; historical PASS rows are not blanket acceptance.

**2026-11-12 owner decisions** (the campaign manager, under Takazudo's delegation): readiness D11 raises the B20
RDY resistors to 2 × 150k C22807. The calculated servo-settle project screen now passes at 1.22 × with X5R TCC included.
The pinned-KiCad field sync and the STEP-datum proof ran on the new PCB bytes; the pair assembly preview
and development export are NOT RUN (they need the local-only assembled STEP files on the selected Mac).
Readiness D10 (Board P r3 C36) is tracked separately. Nothing here is measured.

Loaded asymmetric discharge, shutdown/re-entry and maximum delivered current
including overshoot remain **pre-order** interface gates. The contract requires
output disconnection before discharge. A tracked ramp-down before disconnection
is only proposed and requires explicit agreement; no excess-current charge/time
budget is adopted. T1–T8 remain NOT RUN and do not replace these obligations.

Fixed decisions this stream works under:

- 20 V / 5 A is a separate product for OSC, with a 5 A e-marked cable and no degraded mode.
- OSC current contract: +12 / −12 / +5 V continuous 1.7 / 1.6 / 0.3 A; 20 ms transient 2.0 / 1.9 / 0.4 A; let-through maximum 2.1 / 2.0 / 0.5 A including tolerance. OSC canonical +12 V demand is 1.6 A after its S2b switch; the 1.7 A contract is unchanged.
- STUSB4500 common controller block; B20 is a four-layer board (JLC7628 stackup).
- Every prototype order is **quantity 2** (owner rule: JLCPCB PCBA needs at least two assembled sets).

## P15 package is a fixed-revision snapshot

`manufacturing/releases/corner-support-review/` (board-p15 + Board B) was exported and checked at git base `3b9821b`;
its sources were unchanged through `6cb02c8`. PD20 changes files that its manifest's `source_hashes` lock: the evidence
tree under `.claude/skills/`, `symbols/zudo-pd.kicad_sym` and `footprints/kicad/step-datum-verification.json`. The
package is therefore a snapshot of that revision. It is **not** verified at the current HEAD, and PD20 does not touch
the package, its manifest or its checksums.

## Board P r3 is the exported board-p

The routed r3 draft is now `boards/board-p/board-p.kicad_pcb`, so the exporter's `board-p` is Board P r3. It pairs only
with `board-b20-draft`; the 15 V Board B pairs with `board-p15`. The routed 15 V as-built module it replaced stays in git
at `6cb02c8`, and `scripts/pcb/board-p-r3-draft/run.sh` reads its outline, connectors and holes from there.

| Step | Result | Basis |
|---|---|---|
| Spec → PCB identity | **PASS** | The builder writes the LCSC field of all 44 fitted parts, marks bare copper exclude-from-BOM/CPL and names the 14 no-connect pin nets `unconnected-(ref-pin-Pad)` |
| Layout | **Corrected; independently reviewed with retained residuals** | Committed placement is the default. R1–R4 and functional probe/polarity artwork are corrected at PCB `56cbe0ab…`; all default routing seeds close, and deterministic route/fill and later artwork-only replays are separately retained. Pin-corridor constraints remain enforced |
| DRC with schematic parity | **PASS (DRC)** | KiCad 10.0.6: 0 errors, 0 unconnected, parity only `extra_footprint` MH1–MH3. Current warnings: 57 silk overlap, 30 silk over copper, 3 artwork-only library mismatches, 3 unavailable global MountingHole library notes and 2 electrically necessary front-annulus fan-out items. All 95 have individual dispositions in `boards/board-p/r3-draft/warning-disposition.json` |
| STEP datum screen | **PASS, current native pair** | 45 model pairs, zero translations, current PCB hashes in `footprints/kicad/step-datum-verification.json`. R3-only body models were independently reviewed; U2/U3 known lead/flash omissions require separate PROJECT envelopes with explicit TYP limits. Full final assembly remains a separate check |
| Independent review (2026-11-08 baseline; 2026-11-10 correction) | **R1–R4 corrected; native evidence independently reviewed** | Historical [findings](../boards/board-p/r3-draft/independent-review.md) are preserved. Four U2, four Q1 and three Q3 thermal vias plus connected B.Cu islands and bounded C30/C34 supply/return geometry are now verified. [Correction record](../boards/board-p/r3-draft/layout-corrections.md) retains via-process, shared land/paste, R5/R7 and installed-thermal limitations |
| Retired r2 + Board B records | **Kept, not exported** | `manufacturing/power-budget.json`, `boards/board-b/assembly-preview/` and the adhesive-leg check still bind the r2 PCB; rebinding the leg check to the board-p15 stack needs the local-only populated STEP (NOT RUN here) |

## B20 changes and evidence

| Item | Result | Basis |
|---|---|---|
| D3 courtyard drift (SMC_Diodes_B560C_C85100) | **Fixed** at generator level | `footprints/scripts/gen_courtyards.py`; courtyard ±3.46 mm in Y (silk ±3.21 + 0.25). B20 rebuilt; the semantic PCB diff was D3 only (#220) |
| 14 two-pin symbols with input-typed pins | **Fixed** | Pins made passive in `symbols/zudo-pd.kicad_sym`; B20 ERC pin_to_pin warnings 148 → 0 (B 54 → 18, P 33 → 27, P15 29 → 23; 0 errors) |
| PCSR2512BR010M6 (C23067428) exact evidence | **Primary revision history acquired; lot applicability OPEN** | RESI E16009 V9 (2026-04-28) records the V5 1 W → 2 W change for 5–10 mΩ. The supplier lot revision is unknown, so retain the historical 1 W / 10 A working bound. The manufacturer +20 °C reference is applied to the existing 5–45 °C interval. This does not qualify pulse endurance or fault let-through |
| C5451690 exact evidence | **Exact HolyStone HCN primary evidence acquired; no substitution** | Exact C1206N473J050T/C5451690: 47 nF, ±5%, 50 V, C0G; bounded terminal/model dimensions and ±5% AC corners are retained. The new 3.5 × 1.8 × 1.8 mm derived envelope preserves pads/courtyard. The AC model is conditioned evidence, not full converter stability or a guaranteed installed loop margin |
| 1206 discharge resistor pulse rating | **Single event inside the manufacturer test envelope; repetition UNSOURCED** | Peak 1.56 / 1.02 / 0.82 W (+12 V 100 Ω, −12 V 150 Ω, +5 V 33 Ω); energy 14.0 / 13.8 / 1.6 mJ; τ ≈ 18 / 27 / 4 ms. UNI-ROYAL V.7 short-time overload (2.5 × RCWV for 5 s) covers one event, including an inlet held for the whole 1.33 s window. +12 V peaks at 99.8 % of that test voltage, and no repetitive-pulse curve is published ([`pd20-evidence-research.md`](pd20-evidence-research.md)). A pulse-rated (anti-surge) 1206 would be a component change and is not applied |
| Four-layer stackup | **Recorded, nominal** | JLC7628 values (0.035 / 0.2 / 0.0175 / 1.065 mm) plus 0.01 mm masks sum to 1.59 mm against the declared 1.6 mm board. The stack preview takes the thickness from the PCB. Finished thickness is the fab's tolerance, not a design value |
| Front and back rail labels | **Added** | B20 builder writes the Board B rail-label contract (`boards/board-b/mechanical.json`); `scripts/pcb/board-b20/verify-mechanics.py` checks position, mirror, size and the J6/J7 pin net of each label |
| Top-edge pogo row (P1, TP3–TP5) | **Added (owner decision 2026-11-04)** | Board B's seven contacts at its fixed positions (x 56.19–71.43 mm, y 1.8 mm, 2.54 mm pitch): P1 = NC, PDOK, GND (shared probe ground P1.3), NC; TP3/TP4/TP5 = P12_PRE, P5_PRE, M12_PRE. B20 has no ATT. Bare F.Cu/F.Mask copper, out of BOM/CPL (inventory exclusions). To clear the row, L1 with CAO1/CAO2 drops 1.3 mm as one group (the U1 SW node gains about 1.3 mm), RJ12, RE1, R65 and RJ5 move by 0.6 mm or less. The router joins the probe pads last with signal-width tracks. `verify-mechanics.py` checks positions, pitch, edge gap, layers and nets against `boards/board-b/mechanical.json` |
| Historical 3D interference with Board P r3 | **Found and fixed on the earlier pair (nominal CAD)** | The first r3 + B20 screen found B20 C1 (100 µF, 10.2 mm) 0.38 mm into r3 U2 and 0.03 mm into Q1. C1 moved to (16.48, 6.34), outside Board P's shadow; C35 and CP1 are re-placed by the generator. The earlier rerun screen passed (cross-board, C5 envelope, support collars); this is historical intermediate-pair evidence, not acceptance of the final `56cbe0ab…` / `7dd3cc43…` pair. Its fresh assembly result is tracked in the [current ledger](prototype-order-readiness.md). The preview helper now accepts r3's B.Cu models. Nominal CAD only, not a physical fit |
| Independent layout review (hot loop, Kelvin sense, return path, D3 heat) | **1 blocker fixed; 3 majors addressed, 2 parts OPEN** | [`pd20-b20-layout-review.md`](pd20-b20-layout-review.md), a separate reviewer's desk analysis of the board before the fixes |
| −12 V limiter Kelvin (review blocker) | **Fixed** | U9A's − reference LIM12N ties to M12_PRE through RL3C, 22.6 mm up the load trunk (about 11 mΩ added, trip ≈ 0.93 A instead of 1.97 A). The router now pairs RL3C.2 (PCB R35) with the RSH3 sense pad; `loop-check.json` checks that pin instead of U9.4, the op-amp V− supply. B.Cu signal cost 0.75 closed the routing then; 0.7 after the M12_RAW pours below |
| −12 V output-cap path through FB/COMP parts (review major) | **Fixed (desk)** | M12_RAW is now pour, not a routed net. `M12_RAW_B` (B.Cu, 191.6 mm² filled with the C43 tongue) runs from the U3 PAD vias above U3, under D3 and L5, down the CCO column; `M12_RAW_CCO` (F.Cu) joins CCO1–CCO4 to 10 vias between their pads. Desk path about 3 mΩ instead of about 29 mΩ. RCFB, CCHF, RCRT and CCCP (R12, C13, R9, C12) return through their own trace to one point on the U3 PAD's lower edge; with that stub removed they are isolated from the rest of M12_RAW (pcbnew connectivity check) |
| −12 V hot loop: CCIN2 return (review major) | **Fixed** | CCIN2 stacks above CCIN1, so both M12_RAW returns sit in one column on the `M12_RAW_D3` pour with D3's anode, and VIN reaches both VIN pads from outside it (`loop-check.json` `input_cap_returns_in_one_pour`). RRDY2 and RCEN2 moved to the freed site |
| −12 V hot loop: area (review major) | **OPEN** | Pad-centre polygon still 44.4 mm² (copper path about 48–51 mm²). A search of D3 and CCIN placements (four rotations, 0.25–0.5 mm grid, courtyard-clear of U3 and C11, short VIN and SW branches) found nothing below the current site: the SMC part's 6.9 mm pad pitch sets the loop. Reaching ≤ 30 mm² needs a smaller diode package. Owner decision 2026-11-04: keep the SMC B560C, because a smaller package loses heat spreading while D3 already reaches 109–147 °C at the limiter maximum; the area stays OPEN for the bench EMI check |
| U3 pin-2 high-frequency bypass (review suggestion) | **Added (owner decision 2026-11-04)** | C43, 100 nF 50 V X7R 0603 (CC0603KRX7R9BB104 / C14663, an existing B20 line), from U3 pin 2 (VIN) to the PAD's M12_RAW. It sits left of U3 between CCIN1 and R11; pad 2 joins the 1.2 mm VIN feed about 2.7 mm from pin 2, pad 1 sits on a small M12_RAW F.Cu pour with a via into a new M12_RAW_B tongue under U3's left pins. It sees about 33 V DC (37.6 V worst case), so its effective capacitance is well below 100 nF (the exact Yageo manufacturer simulation is retained as typical evidence, not a guaranteed installed minimum). Its loop inductance is not computed; the CCIN1/D3 hot-loop polygon is unchanged |
| D3/U3 shared island (review major) | **Improved; limiter maximum OPEN** | Vias beside and below the D3 anode and U3's 8 PAD vias now land on `M12_RAW_B`. `thermal-check.json` `inverter_island` is a desk node model of the shared island (F.Cu 61.3 mm², B.Cu 191.6 mm², 17 joining vias after the C43 bypass re-route; was 62.2 / 179.6 mm² and 20). Fresh regenerated D3 junction: 92.9–111.5 °C with typical RDS and 99.0–120.1 °C with maximum RDS at the continuous contract load (1.7 / 1.6 / 0.3 A; 2026-11-08 load cases, #230), 104.7–127.6 / 113.2–139.7 °C (typ/max RDS) at the 20 ms transient held steady (not a transient model), 109.0–133.4 / 118.3–146.8 °C (typ/max RDS) at the maximum delivered current held steady. The 67–79 °C first recorded here as "rated" is the legacy PD15 1.2 / 0.8 / 0.5 A comparison case (the same model gives 76–93 / 132–188 °C on the board before the fix, close to the review's 71–89 / 120–185 °C). The worst case sits 3 K under the 150 °C limit, so owner disposition of the modeled limiter-maximum margin remains a pre-order decision. T2 is the separate post-arrival measured check and remains NOT RUN. U3 gets only the PAD temperature (82–109 °C continuous, 95–133 °C at the let-through maximum; legacy comparison 61–73 °C), because its junction-to-PAD resistance is not retained |
| Router settings after the M12_RAW pours | **Fully routed** | The pours displaced B.Cu routes across the inverter. B.Cu signal cost 0.7 (trials 0.58–0.8 left 1–10 connections open), ARM_GND joins the In2.Cu pre-routes, and R29.2, R30.1, RCP1.1, U15.2, U15.5 and Q48.3 get pin escapes; U3 pins 3–6 and RCFT.2 escape before the quiet return is laid. The D3-to-L6 M12_RAW trunk now drops to B.Cu and returns through 2 vias near L6: `current-check.json` gave 1.5 K rated and 12.3 K at the limiter maximum for that transition (desk). Correction 2026-11-08: the committed report puts 4 and 3 vias on the two transitions and gives 3.0 K continuous, 4.4 K at the 20 ms transient held steady and 5.0 K at the let-through maximum (legacy 1.2 / 0.8 / 0.5 A comparison 0.6 K) |
| CU6D (PCB C35) far from U6 | **Corrected and native-verified, 2026-11-10 JST** | The historical 52.3/57.2 mm placement is superseded by the U6-bound placement at (78.5,56.15). Actual supply path is 4.607 mm; local returns are 0.700/0.600 mm into the same filled In1 GND plane. C43 remains separate and unchanged. See [current native review](../boards/board-b20-draft/u6-bypass-review.md) for exact source/PCB hashes and invariants |

## Historical export binding and per-variant verification

The retained 269-part scratch-export observations below predate the current 270-part B20.
They do not accept the final corrected pair. Its fresh DEVELOPMENT REVIEW export remains
pending in the [current ledger](prototype-order-readiness.md).

`scripts/pcb/verify-jlcpcb.py` now carries a per-variant contract (spec, copper stack, outline) for board-p, board-p15,
board-b and board-b20-draft. It accepts at most one Board P and one Board B variant, requires the manifest's
`copper_layers` to equal the variant stack, exactly one Gerber per copper layer (In1.Cu and In2.Cu for B20) and no stray
inner-layer Gerber. The 2-layer checks are unchanged, and the results schema is unchanged.

| Check | Result | Basis |
|---|---|---|
| Scratch export of Board P r3 + B20 (same revision) | **PASS** | `export-jlcpcb.py --boards board-p board-b20-draft` into a gitignored scratch folder; nothing under `manufacturing/releases/`, no upload, quote or order. board-p: 44 fitted, 26 BOM lines, DRC 0 errors / 0 unconnected, ERC 0 errors. board-b20-draft: 269 fitted, 87 BOM lines, four copper layers, DRC 0 errors / 0 unconnected, parity 0, ERC 0 errors and 0 warnings |
| Independent verifier on that export | **PASS** | Checksums, identities, coordinates, Gerber/drill stack (4 copper layers for B20) and outline |
| Verifier on the P15 package (2-layer regression) | **NOT RUN** | The package's `populated-stack.step` is a local-only file absent from this checkout, so its checksum gate stops first (as it does for the unchanged verifier) |
| Verifier negative case (missing inner layer) | **NOT RUN** | No mutated package was built |
| Exporter fix found by the export | **Fixed** | Library SOD-123 footprints carried a stale `LCSC Part` C92321; the r3 builder now sets every supplier alias to the spec's LCSC |

## 20 V / 5 A NVM is BLOCKED

`scripts/pcb/board-p/nvm-intent-20v.py` writes `boards/board-p/nvm/stusb4500-20v-intent.json` and never a `.bin`:

- Intent: SNK_PDO_NUMB 2, PDO2 20.00 V / 5.00 A (V code 400, I code 15), POWER_ONLY_ABOVE_5V 1; the rest stays at the
  DS12499 Rev 7 defaults. Partial desk bytes differ from the base in s3b2, s3b4, s4b1 and s4b6.
- **TDISPAR0V: LOCATED, value not set.** An ST-authored draft technical note (TNxxx, attached by an ST moderator on ST
  Community) puts it at NVM 0xCA = sector 1 byte 2, bits [7:4], default 0x9C. 13 gives 0.4 % margin over the 0.906 s
  need; 14 (0xEC) or 15 (0xFC) give 8 % or 16 %. The value is an owner choice ([`pd20-evidence-research.md`](pd20-evidence-research.md)).
- **Capability mismatch: ANSWERED (DS12499 Rev 8, sections 3.3.2 and 6.1.2).** A PDO match needs
  I(SNK) ≤ I(SRC), so a 20 V offer below 5 A gives a 5 V contract, and POWER_ONLY_ABOVE_5V keeps VBUS_EN_SNK Hi-Z.
- **POWER_ONLY_ABOVE_5V position: CONFLICT.** The ST note marks 0xE6 bits [3:0] reserved; bit 3 rests on the
  third-party map and a non-ST GUI diff. The P15 image uses the same bit.
- The run-python gates rebuild the intent and fail if the committed record differs.

## Historical OSC interface status (B20 draft page §4)

The table and original exception discussion below preserve the earlier phase33 assessment.
They are **not current acceptance**: the 2026-11-10 execution disposition above and
[source-bound full-suite receipt](sim/board-b20-phase33/execution-20261110.md) supersede
the old 1.45 V screen, averaged slope conclusions and treatment of loaded ramp-down.
In particular, discharge/shutdown and maximum delivered current remain pre-order gates.

| Contract item | Status |
|---|---|
| Any trip → all-rail latched shutdown, re-plug only | **PASS (topology)**: FAULT_N shared, no retry path; limiter comparators not simulated |
| Reverse blocking on all rails | **PASS (topology)**: back-to-back NFET pairs |
| Reverse current ≤ 1 mA | **OPEN**: divider currents 0.23 / 0.50 / 0.12 mA (calculated); FET leakage at temperature not guaranteed |
| Discharge time ≤ 100 ms, zero load | **PASS**: 57.9 / 81.7 / 8.6 ms at ceiling capacitance |
| Discharge order, zero load | **PASS** |
| Discharge order under load | **OPEN**: an asymmetric OSC load reorders the rails; a tracked ramp-down is proposed, not drawn |
| Disconnect skew ≤ 1 ms | **PASS (SIM)**: 4 µs |
| Startup ramp and slope limits | **PASS (SIM)** loaded; no-load +5 V and −12 V slopes accepted by the owner (below) |
| Start skew ≤ 0.41 ms | Voltage form **PASS (SIM)**; time form **FAIL (SIM)** |
| Band-entry skew ≤ 2 ms (all rails in band) | **PASS (SIM)**: 0.73 ms in the phase-33 re-entry runs. +5 V entering last is a PD design choice that avoids the one-rail case, not an OSC rule |
| Let-through maximum 2100 / 2000 / 500 mA (+12 / −12 / +5 V, including tolerance and let-through) | **OPEN**: the limiter trips, it does not regulate current; let-through not simulated or measured |
| +5 V ≤ 0.8 V until both analog rails exceed about 1.5 V magnitude (OSC Definition 1, answered) | **PASS (SIM)** at startup: worst 0.637 V while the lower analog rail is below 1.45 V (phase-33 start runs). The 1.45 V analysis threshold is slightly below OSC's "about 1.5 V"; re-running at 1.5 V is NOT RUN. Ramp-down is covered by T5, not by this row |
| Renegotiation: vSafe0V after a hard reset | **OPEN**: TDISPAR0V is located but its value is not chosen (NVM above); needs a bench run |
| Inrush from Board P into the B20 bulk | **PASS (desk, graph read)**: 41 mJ, ≤ 39 W peak for 2.1 ms against about 87 W allowed on DS37038 Fig. 12 (2.2× at 25 °C, 1.6× at 60 °C); bench T3 |

**Slope-exception owner, recorded.** The owner accepted OSC's no-load ramp-slope exceptions on 2026-11-03 (decision card
`cmsg_01Pv35emdXEU6gCRF3teSpo2GzmXCn8kfxsnNg5p6WdFzN`): no load only; +5 V ≤ 0.95 V/ms below 0.45 V at ≤ 114 mA;
−12 V ≤ 1.47 V/ms below 0.75 V at ≤ 265 mA. Loaded starts keep the 1.22 / 0.51 V/ms limits.

## Bench test sheets (NOT RUN)

None of these has been executed. Each needs owner approval and the two prototype sets.

| Sheet | Procedure | Pass criterion | Basis |
|---|---|---|---|
| T1 Output ripple | 20 V / 5 A e-marked source; each rail at the OSC continuous load (1.7 / 1.6 / 0.3 A) and at 20 ms transient peaks; 20 MHz-limited probe with a tip-and-barrel ground at J10 | < 1 mVp-p at load on each rail | OSC contract §0; the averaged model gives 22.6 / 13.4 / 43.6 µVp-p, not a switching simulation |
| T2 Thermal | 25 °C ambient, continuous load for 30 min; thermocouples on D3, U4, the 10 mΩ shunts and Board P Q1 | D3 and every IC inside its rated junction limit with the measured θ; no part above its derated limit | D3 copper temperature UNKNOWN; desk loss 4.29–4.79 W at the continuous load, 6.62 W at the let-through maximum |
| T3 Startup and re-entry | Scope all three rails and EN_N at no load and at transient load; repeat with 6 ms and 18.6 ms off times | Every §5 row of the draft page, with the owner-accepted no-load exceptions | Phase 9–12 simulations |
| T4 NVM readback | Write the 20 V image only after the TDISPAR0V value is chosen, the POWER_ONLY_ABOVE_5V position is confirmed and the image is reviewed; power-cycle, read back 40 bytes | Readback equals the image; PDO2 = 20 V / 5 A | NVM status BLOCKED |
| T5 Discharge and order | Disconnect at zero load and at an asymmetric OSC load | ≤ 100 ms; \|−12 V\| ≤ 6 V while +12 V is low; +12 V ≤ 0.5 V while −12 V is absent; +5 V ≤ 0.8 V by the time the first analog rail leaves; 1206 discharge resistors without visible damage after 100 cycles | Discharge rows above; pulse rating OPEN |
| T6 Reverse current | Back-drive each output from a bench supply with the board unpowered and at 60 °C | ≤ 1 mA per rail | Reverse current OPEN |
| T7 Fault latch | Short each rail through a current-limited load | All rails off and latched until re-plug; let-through charge recorded | Latch PASS (topology); let-through OPEN |
| T8 Hard reset | Force a PD hard reset from a source analyser | VBUS reaches vSafe0V within the PD timing; B20 latches off and restarts cleanly | Renegotiation OPEN |
