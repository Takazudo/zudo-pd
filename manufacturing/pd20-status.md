# PD20 status: Board P r3 + B20 (20 V / 5 A pair)

**Unvalidated draft record. Nothing here is validated, qualified, released or ordered.** It records what the PD20 stream
(Astra review 2026-11-04, PD20 and CHECKPOINT) changed, what was checked at which revision, and what stays open. Every
bench row below is a test sheet that has **not been executed**; each one needs owner approval and hardware.

Fixed decisions this stream works under:

- 20 V / 5 A is a separate product for OSC, with a 5 A e-marked cable and no degraded mode.
- OSC current contract: +12 / −12 / +5 V continuous 1.7 / 1.6 / 0.3 A; 20 ms transient 2.0 / 1.9 / 0.4 A.
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
| Layout | **Routed, unreviewed** | Committed placement kept (a re-run search did not route VREG_2V7); router seed 12 closes every signal connection; 0 detached GND clusters. Pin-corridor keep-outs forbid vias only, and the builder checks that only U1 and the protected owners touch a corridor |
| DRC with schematic parity | **PASS (DRC)** | KiCad 10.0.6: 0 errors, 0 unconnected, parity only `extra_footprint` MH1–MH3. Warnings: 69 silk overlap, 34 silk over copper, 14 text height, 2 silk edge, 3 library-footprint notes, 3 dangling fan-out items |
| STEP datum screen | **PASS (screen)** | 44 model pairs; the three r3-only boxes (HTSSOP-20 PWP, SOT-23-6 DBV, WSON-6 DRV) joined the reviewed manifest as PENDING INDEPENDENT REVIEW |
| Retired r2 + Board B records | **Kept, not exported** | `manufacturing/power-budget.json`, `boards/board-b/assembly-preview/` and the adhesive-leg check still bind the r2 PCB; rebinding the leg check to the board-p15 stack needs the local-only populated STEP (NOT RUN here) |

## B20 changes and evidence

| Item | Result | Basis |
|---|---|---|
| D3 courtyard drift (SMC_Diodes_B560C_C85100) | **Fixed** at generator level | `footprints/scripts/gen_courtyards.py`; courtyard ±3.46 mm in Y (silk ±3.21 + 0.25). B20 rebuilt; the semantic PCB diff was D3 only (#220) |
| 14 two-pin symbols with input-typed pins | **Fixed** | Pins made passive in `symbols/zudo-pd.kicad_sym`; B20 ERC pin_to_pin warnings 148 → 0 (B 54 → 18, P 33 → 27, P15 29 → 23; 0 errors) |
| PCSR2512BR010M6 (C23067428) exact evidence | **UNSOURCED, conflict recorded** | DigiKey copy of the manufacturer sheet (2024-03-24) gives 1 W / 10 A for the 10 mΩ 0.1 % row; the V8 sheet gives 2 W / 14 A. The working bound is 1 W / 10 A against a 2 A duty (0.04 W). Mirror authority only |
| C5451690 exact evidence | **Gap retained** | Re-fetched bytes are unchanged. Substitute named, not applied: YAGEO CC1206JKNPO9BN473 (C3855647). A component change needs owner approval |
| 1206 discharge resistor pulse rating | **OPEN** | Peak 1.56 / 1.02 / 0.82 W (+12 V 100 Ω, −12 V 150 Ω, +5 V 33 Ω); energy 14.0 / 13.8 / 1.6 mJ; τ ≈ 18 / 27 / 4 ms. The parts are rated 0.25 W continuous and no pulse curve is retained. A pulse-rated (anti-surge) 1206 would be a component change and is not applied |
| Four-layer stackup | **Recorded, nominal** | JLC7628 values (0.035 / 0.2 / 0.0175 / 1.065 mm) plus 0.01 mm masks sum to 1.59 mm against the declared 1.6 mm board. The stack preview takes the thickness from the PCB. Finished thickness is the fab's tolerance, not a design value |
| Front and back rail labels | **Added** | B20 builder writes the Board B rail-label contract (`boards/board-b/mechanical.json`); `scripts/pcb/board-b20/verify-mechanics.py` checks position, mirror, size and the J6/J7 pin net of each label |
| Top-edge pogo row (P1, TP3–TP5) | **OPEN** | Board B's row probes ATT, PDOK and three pre-regulator rails. B20 has no ATT and different internal rails, so which nets the row carries is a design choice that needs the owner; the verifier reports it as OPEN |
| 3D interference with Board P r3 | **Found and fixed (nominal CAD)** | The first r3 + B20 screen found B20 C1 (100 µF, 10.2 mm) 0.38 mm into r3 U2 and 0.03 mm into Q1. C1 moved to (16.48, 6.34), outside Board P's shadow; C35 and CP1 are re-placed by the generator. The rerun screen PASSES (cross-board, C5 envelope, support collars). The preview helper now accepts r3's B.Cu models. Nominal CAD only, not a physical fit |
| Independent layout review (hot loop, Kelvin sense, return path, D3 heat) | **1 blocker fixed; 3 major OPEN** | [`pd20-b20-layout-review.md`](pd20-b20-layout-review.md), a separate reviewer's desk analysis of the board before the fixes |
| −12 V limiter Kelvin (review blocker) | **Fixed** | U9A's − reference LIM12N ties to M12_PRE through RL3C, 22.6 mm up the load trunk (about 11 mΩ added, trip ≈ 0.93 A instead of 1.97 A). The router now pairs RL3C.2 (PCB R35) with the RSH3 sense pad; `loop-check.json` checks that pin instead of U9.4, the op-amp V− supply. B.Cu signal cost 0.75 closes the routing |
| −12 V output-cap path through FB/COMP parts (review major) | **OPEN** | 0.4 mm path, about 29 mΩ; about 12 mVp-p on FB (desk). Needs M12_RAW pours and a quiet control ground |
| −12 V hot loop along copper (review major) | **OPEN** | 47.9–51.4 mm² (44.4 mm² is the pad-centre polygon); CCIN2 sits on a separate island |
| D3/U3 shared island (review major) | **OPEN** | 48.1 mm², no vias at D3; D3 junction at the limiter maximum UNKNOWN (desk 120–185 °C). `thermal-check.json` has no D3 row |
| CU6D (PCB C35) far from U6 | **OPEN (pre-existing)** | The U6 decoupling capacitor sits 50+ mm from U6 at HEAD and after PD20; the greedy fill places it by net, not by IC |

## Export binding and the per-variant verifier

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
- **TDISPAR0V: UNAVAILABLE.** The field map (SparkFun library, third party) has no position for it, and no ST NVM map is
  retained. The default (9) gives at least 630 ms of discharge, too short for the 2 kΩ VBUS_VS_DISCH feed to reach
  vSafe0V; the intent is ≥ 13.
- **Capability-mismatch behaviour: UNKNOWN.** What the part does when a 20 V source offers less than 5 A is not in a
  retained document.
- The run-python gates rebuild the intent and fail if the committed record differs.

## OSC interface status (B20 draft page §4)

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
| Band-entry skew ≤ 2 ms, +5 V last | **PASS (SIM)** |
| Let-through (maximum never delivered) | **OPEN**: the limiter trips, it does not regulate current |
| +5 V ≤ 0.8 V before analog rails are "up" | **OPEN (definition)**: a question for OSC |
| Renegotiation: vSafe0V after a hard reset | **OPEN**: depends on TDISPAR0V (NVM above) and needs a bench run |
| Inrush from Board P into the B20 bulk | **OPEN**: Q1 SOA not in its bundle |

**Slope-exception owner, recorded.** The owner accepted OSC's no-load ramp-slope exceptions on 2026-11-03 (decision card
`cmsg_01Pv35emdXEU6gCRF3teSpo2GzmXCn8kfxsnNg5p6WdFzN`): no load only; +5 V ≤ 0.95 V/ms below 0.45 V at ≤ 114 mA;
−12 V ≤ 1.47 V/ms below 0.75 V at ≤ 265 mA. Loaded starts keep the 1.22 / 0.51 V/ms limits.

## Bench test sheets (NOT RUN)

None of these has been executed. Each needs owner approval and the two prototype sets.

| Sheet | Procedure | Pass criterion | Basis |
|---|---|---|---|
| T1 Output ripple | 20 V / 5 A e-marked source; each rail at the OSC continuous load (1.7 / 1.6 / 0.3 A) and at 20 ms transient peaks; 20 MHz-limited probe with a tip-and-barrel ground at J10 | < 1 mVp-p at load on each rail | OSC contract §0; the averaged model gives 22.6 / 13.4 / 43.6 µVp-p, not a switching simulation |
| T2 Thermal | 25 °C ambient, continuous load for 30 min; thermocouples on D3, U4, the 10 mΩ shunts and Board P Q1 | D3 and every IC inside its rated junction limit with the measured θ; no part above its derated limit | D3 copper temperature UNKNOWN; desk loss 6.62 W at the limiter maximum |
| T3 Startup and re-entry | Scope all three rails and EN_N at no load and at transient load; repeat with 6 ms and 18.6 ms off times | Every §5 row of the draft page, with the owner-accepted no-load exceptions | Phase 9–12 simulations |
| T4 NVM readback | Write the 20 V image only after TDISPAR0V is located; power-cycle, read back 40 bytes | Readback equals the image; PDO2 = 20 V / 5 A | NVM status BLOCKED |
| T5 Discharge and order | Disconnect at zero load and at an asymmetric OSC load | ≤ 100 ms; \|−12 V\| ≤ 6 V while +12 V is low; 1206 discharge resistors without visible damage after 100 cycles | Discharge rows above; pulse rating OPEN |
| T6 Reverse current | Back-drive each output from a bench supply with the board unpowered and at 60 °C | ≤ 1 mA per rail | Reverse current OPEN |
| T7 Fault latch | Short each rail through a current-limited load | All rails off and latched until re-plug; let-through charge recorded | Latch PASS (topology); let-through OPEN |
| T8 Hard reset | Force a PD hard reset from a source analyser | VBUS reaches vSafe0V within the PD timing; B20 latches off and restarts cleanly | Renegotiation OPEN |
