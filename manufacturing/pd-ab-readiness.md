# PD A/B readiness matrix: Board P r3 + B20 (unvalidated drafts)

Status words: **PASS**, **FAIL**, **BLOCKED**, **NOT RUN** (with the reason), **UNKNOWN**, **OPEN**.
No item here is validated, qualified or released. Nothing was ordered, quoted or uploaded.
Prices come from read-only JLCPCB catalog and fee-table retrievals on 2026-10-31 and are not quotes
(`manufacturing/readiness/jlc-snapshot-2026-10-31.json`; phase 13 B20 listings in
`manufacturing/readiness/b20-identity-resolution.json`). Cost arithmetic is in
`scripts/pcb/calculate-lineup-cost.py`.

**A** is the design gate: the drawn design and its evidence close. **B** is the build gate: the parts,
cost, manufacturability and bench plan close. On 2026-11-01 the user chose separate products
(`dec-separate-products`): the current 15 V zudo-pd (Board P as built + Board B) continues, and Board P r3 +
B20 becomes a separate 20 V / 5 A unit oriented to the OSC. The STUSB4500 controller block stays common.

## A gates: open on both boards; B20 has an unrouted placement draft only

| Gate | Board P r3 | B20 | Evidence |
|---|---|---|---|
| Spec | **PASS** (generated spec, 29 decisions) | **PASS** (paper draft spec; phase 13 adds J10/J11) | `scripts/schgen/board_p_spec.py`, `scripts/schgen/decisions.json`, `scripts/schgen/board_b20_spec.py` |
| Schematic ERC | **PASS**: 0 errors, 33 `pin_to_pin` warnings | **PASS**: 0 errors, 35 `pin_to_pin` warnings on the unspecified J5/J10/J11 pins (phase 19; the 21 missing-footprint warnings are gone) | native KiCad 10.0.6 ERC + `verify_netlist.py` (P: 46 nets; B20: 142 nets) |
| Footprints | **PASS** (shared library) | **OPEN**: the 5 former `*_DRAFT` names are drawn in `footprints/kicad/` (phase 19) from TI DDA0008B / DGK0008A / D0008A drawings (primary) and RLS12 / PCSR2512 mirror sheets (UNSOURCED); no fabrication review, no 3D models | `manufacturing/board-b-20v-switcher-direct-draft.md` §3 footprint table |
| PCB DRC | **OPEN**: native DRC 0 clearance/short/courtyard errors, 5 `items_not_allowed` (owners in their own keep-outs), 0 unconnected items (3 in phase 13, 8 in phase 12); warnings: 2 `via_dangling` (SCL, ATT) and 1 `track_dangling` (CC1, 0.65 mm); `route-power.py` now finds 0 detached GND clusters, matching native DRC (its phase 14 cluster was a false positive from endpoint-only joins, fixed in phase 15); no layout review | **OPEN**: unrouted placement draft `boards/board-b20-draft/board-b20-draft.kicad_pcb` (phase 19): DRC 0 errors, 2 `lib_footprint_mismatch` warnings (J10/J11 silk clip), 0 parity issues, 499 unconnected items; no loop, thermal or return review | `boards/board-p/r3-draft/placement-report.json`, `routing-report.json` |
| Current capacity | **OPEN**: 5 A pours ≥ 1.85 mm against 1.82 mm (IPC-2221, 20 °C rise PA); no thermal check | **PASS (arithmetic)** converter and switch current | r3 `routing-report.json`; `calculate-board-b20-draft.py` |
| Stack and mechanics | **OPEN**: C3 over the current Board B U3 (3.31 × 4.05 mm); B.Cu parts face the floor | **OPEN**: the B20 draft keeps x 7.74–17.25, y 24.54–35.77 mm free with a both-side footprint rule area (`BOARD_P_R3_C3_KEEPOUT`); no B20 stack preview exists | `boards/board-p/r3-draft/README.md` |
| Simulation rows | **OPEN**: Q1 overshoot bound rests on TYP-only TPS16630 rows | Start, re-entry and band rows **PASS (SIM)**. No-load slope rows **FAIL (SIM)**, with an owner exception requested (nom +5 V 0.94 V/ms; exception wording ≤ 0.95 V/ms is with OSC). Ripple, let-through, reverse current and loaded discharge order **OPEN** | `manufacturing/board-b-20v-switcher-direct-draft.md` §4–§5f; `manufacturing/sim/board-b20-phase12/results.json` |
| Component evidence | **OPEN**: strict validator PASS, but VBEN drive, Q6 RDS(on)/leakage and STUSB 28 V limits are UNSOURCED, and no 20 V / 5 A NVM image is defined | **OPEN**: 3 values bound to owned parts; 68 placements resolved to distributor listings only (no manufacturer document, no owner record); 27 nF and 47 nF C0G **UNKNOWN**; 1206 discharge pulse rating **UNKNOWN** | `.claude/skills/component-spec-audit/scripts/validate.py --strict`; `b20-identity-resolution.json` |
| Independent review | **OPEN**: the observed independent run refused (both rules UNSOURCED); no PCB review | **OPEN**: review findings of `bad5ddf` recorded; no review since phase 9 | `observed-runs.json`; draft page §7 |

## B gates: BLOCKED on availability; the renewal costs about twice the current lineup per 5-unit lot

| Gate | Board P r3 | B20 | Evidence |
|---|---|---|---|
| BOM availability (5-unit lot) | **BLOCKED**: TVS2200DRVR C523793 had 4 in stock against 5 needed; no evidenced drop-in (below) | **BLOCKED**: 8 resolved lines below the lot need (10.6k, 40.7k, 54.2k, 62.6k, 92k, 198k with 0; 221k and 806k with 4); 27 nF and 47 nF C0G **UNKNOWN** | `b20-identity-resolution.json` `catalog.parts[].stock` |
| Unit cost, parts | USD 12.05 (lot 1), 12.05 per board in a lot of 5 | USD 76.79 (lot 1), 62.58 per board in a lot of 5; 2 parts UNKNOWN | `calculate-lineup-cost.py` |
| 5-unit lot, parts | USD 60.26 | USD 312.88 | same |
| Assembly fee, 5-unit lot | USD 131.48: Standard PCBA, double-side (only class for a two-sided board: setup 51.12, stencil 16.42, 28 lines × 1.53 feeder loading, handling ≥ 14.93) | USD 187.50: Standard PCBA, single-side (82 lines × 1.53). Economic PCBA would be USD 222.60 (65 extended lines × 3.07) | snapshot `assembly_fees` |
| PCB fabrication | **UNKNOWN** (not retrieved) | **UNKNOWN** (no PCB) | — |
| DFM | **OPEN**: two-sided assembly forces Standard PCBA; 0603 library courtyards larger than the as-built lands; no DFM run | **NOT RUN**: no PCB | r3 `placement-report.json` |
| BOM completeness | **PASS** against the spec | **PASS (drawn)** for J10/J11 (phase 13). TVS1–TVS3 and the three status LEDs with ballasts are priced as adders only, not drawn: their leakage and ~10 mA loads change the no-load, discharge and reverse-current rows | `board_b20_spec.py`; `b20-identity-resolution.json` `like_for_like_adders` |
| Bench acceptance tests | **NOT RUN**: no hardware | **NOT RUN**: no hardware | list below |

### Stock gaps and evidenced alternatives (2026-11-01 listings)

| Blocked line | Need (5 sets) | Alternative | Status |
|---|---|---|---|
| TVS2200DRVR C523793 (TI), 4 in stock | 5 | C55616459 "TVS2200DRVR" from Wuxi Maxinmicro (1,264). Its V1.0 sheet is retained as an extract and hash in `readiness/tvs2200-second-source.json`: 22 V standoff and the pinout match, but the single 26.1 V clamp has no test current, limit or temperature, and Ipp × Vc (1,566 W) disagrees with the stated 1,120 W. ESTVS2200DRVR C42400188 (ElecSuper, 2,861) lists a 28.6 V clamp, above the 28 V node bound | **BLOCKED**: equivalence not established |
| RT0603BRD07680RL C861519 (current Board B R21/R27), 0 in stock | 10 | Candidate `cand-at0603brd07680rl-c5455478`: YAGEO AT0603BRD07680RL C5455478 (410–439). The hashed YAGEO sheet matches every incumbent row: 680 Ω, 0.1 %, 25 ppm/°C, 0.1 W at 70 °C, 75 V, 1.6 × 0.8 mm (AEC-Q200) | **OPEN**: shortlisted, not adopted |
| GVT1E477M0810CNVC C2983319 (current Board B C11), 1 in stock | 5 | Candidate `cand-rvt1e471m0810-c696190`: Honor RVT1E471M0810 C696190 (4,085–4,625). HONORCAP sheet: 470 µF 25 V, Φ8 × 10.2 mm on the same Φ8 land as the owned RVT1H101M0810, 228 mA at 120 Hz × 1.50 = 342 mA at 150 kHz (incumbent 312 mA), Tan δ 0.16 (ESR 0.45 Ω at 120 Hz; incumbent 0.51 Ω) | **OPEN**: shortlisted; the ESR-weighted ripple share and the LM2596 loop with the lower ESR are not measured |

### Current lineup reorder (Board P 15 V + Board B): BLOCKED on 2 stock lines, then OPEN on source parity

The ordered revision is `manufacturing/releases/corner-support-review/` (BOM, CPL and Gerbers for both boards).
A full stock refresh on 2026-11-01 of its 53 lines against 5 sets finds:

| Item | Status |
|---|---|
| C861519 (R21/R27) 0 in stock, C2983319 (C11) 1 in stock | **BLOCKED** until a candidate above is adopted through `board_b_spec.py`, regeneration and a refreshed package |
| C861332 RT0603BRD0733RL (R24) 10 in stock against 5 | **OPEN**: in stock, no margin |
| Board P 15 V source parity | **PASS (phase 15)**: `scripts/schgen/board_p15_spec.py` reproduced the as-built netlist pin for pin (baseline, as-built PCB pads, package BOM identity) before the RESET subset; the draft PCB `boards/board-p15/board-p15-draft.kicad_pcb` matches the spec pin for pin |
| Any BOM change on Board B | **OPEN**: needs a new package from one revision with ERC, DRC and BOM/CPL parity; the existing package stays the ordered revision |
| Electrical qualification (full-load start, ripple, thermal, fuse hold, surge, low input) and mechanical fit (wire, torque, retention, seating, printed leg, M3 in the 3.0 mm holes) | **OPEN**, as listed in `ORDER-NOTES.md`; not reorder blockers by themselves |
| First power procedure: 5 V-only current-limited source, Board B disconnected, verify the 15 V NVM image and readback | Required at bring-up (`ORDER-NOTES.md`) |
| PCB fabrication, shipping and duty | **UNKNOWN** (not retrieved) |
| Controller block on the 15 V Board P | **Working direction: RESET subset plus phases 17–18** (`dec-p15-reset-subset`, `dec-p15-i2c-pulldowns`, `dec-p15-vdd-local-clamp`, `dec-p15-vdd-decoupling`). Spec, ERC (0 errors) and draft PCB exist: DRC 0 errors, 0 unconnected, schematic parity `extra_footprint` only (MH1–MH3); RESET ≥ 1.353 mm from VBUS-class copper on its layer. Silk classes equal the as-built board (phase 18). Phase 20, after the board-p15 layout review: D9 stays BZT52C18, because BZT52C20 leaves 4.959 V (< 5 V) to the 28 V VDD maximum and its 105 °C VZ maximum exceeds the 22 V operating row (`boards/board-p15/d9-zener-choice.json`); the cold window above 15.75 V stays +0.01 V (OPEN); the back mark reads `P15 r1`. An order package is OPEN (`boards/board-p15/README.md`) |
| 15 V NVM image and jig procedure | **OPEN (NOT RUN)**: desk image `boards/board-p15/nvm/stusb4500-15v.bin` (sha256 `76622e14…`) and procedure `doc/src/content/docs/architecture/board-p15-programming.md`; never written or read back |

### Current Board P controller block: stay as is only with the #144 RESET geometry accepted; the RESET subset costs nothing in parts

The as-built 15 V Board P predates the common block. A pcbnew clearance scan of `boards/board-p/board-p.kicad_pcb`
(sha256 `407f6349…`, unchanged) finds the RESET track passing between the R13 pads at 0.222 mm (VBUS_OUT and DISCH)
and 0.325 mm from a VBUS_VS_DISCH via. Those are the distances of the ordered LED Board P, whose RESET read 0.93 V
(VIL max 0.35 V) in the #144 desk analysis (`manufacturing/readiness/board-p-15v-reset-clearance.json`,
`scripts/pcb/board-p-reset-clearance.py`). Other differences from the r3 block:

- R21 is a 10 kΩ pull-down, not a 0 Ω strap;
- RESET is on the J2.4 pogo pad;
- R15/R16 pull SCL/SDA up to VREG_2V7;
- VDD (U1.24) sits directly on VBUS_IN with D5 SMAJ16A. That gives +2.00 V to the 28 V pin limit at the
  26.0 V, 10/1000 µs, 25 °C point only, and −0.6 V at the TYP-based 28.6 V hot estimate
  (`input-clamp-fix.md`). The phase 17 draft replaces this with the R29/R30 + D9 feed (below).

Costs are for a 5-unit lot from `scripts/pcb/calculate-lineup-cost.py` (`p15_*` rows). They cover catalog parts
plus assembly. PCB fabrication and any new-revision NRE are UNKNOWN.

| Option | Changes | Lot cost (per set) | Risk |
|---|---|---|---|
| Stay as is | None; reorder the `corner-support-review` package unchanged | USD 48.06 (9.61) | **OPEN, inherited**: RESET geometry identical to #144; RESET on a bare pad; VREG_2V7 loading (R1.3); VDD hot margin negative on the TYP estimate. No new layout risk |
| R1.1–R1.3 subset | R21 becomes a 0 Ω strap at U1.6, routed away from VBUS / VBUS_VS_DISCH / DISCH / VBEN; J2.4 becomes NC; R15/R16 move to the jig | USD 48.00 (9.60); 12 lines, 5 extended | Needs a re-routed PCB, ERC/DRC and a new package. I2C idle without pull-ups is not stated by ST (OPEN). VDD clamp margin is unchanged |
| Full common block, top only | Subset plus D9–D12, Q6 cascode, R28–R32, C38; R13 4.7 kΩ, R14 2 × 1 kΩ; SMAJ16A and AO3401A stay | USD 60.00 (12.00); 17 lines, 8 extended (+3) | Top-only fit on the 27 × 40 mm outline is **NOT RUN**: no placement search was made for this variant. VDD bound about 20.8 V (r3 arithmetic at the 28.35 V row, not redone at 28.6 V). Adds the r3 OPEN items: TDISPAR0V ≥ 13 in the 15 V NVM image, VBEN/Q6 ratings UNSOURCED, attach headroom with the operating IDD unknown |
| Full common block, two-sided | As above, if top only does not fit | USD 134.21 (26.84) | Standard double-side PCBA: +USD 86.15 per lot over as built; same OPEN items |

Phase 15: the coordinator took the R1.1–R1.3 subset as the working direction (`dec-p15-reset-subset`). Phase 14 recommendation, kept for the record: take the R1.1–R1.3 subset as the floor. Its part and assembly cost is
neutral, and it removes the one layout defect with a recorded failure. Add the full block only if a top-only
placement fits. That would close the VDD clamp margin for about USD 2.40 per set more. In every changed
option the 15 V board needs its own spec source: `board_p_spec.py` now describes r3, and the 15 V schematic
exists only in history.

Phase 17 (draft `boards/board-p15/`, sha256 `c7767cb8…`): the coordinator added three items to the subset.

- **SCL/SDA pull-downs:** R22/R23 100 kΩ C25803 to GND, so the pins no longer float. Jig pull-ups to 3.3 V
  through 967 Ω to 3.39 kΩ meet VOL and tr ≤ 300 ns at 100 pF with them present.
- **VDD feed and clamp, top side:** R29 1 kΩ C21190 + R30 470 Ω C23179 (1470 Ω) from VBUS_IN, with D9
  BZT52C18 C192739 at U1.24/C2. It fits without moving any other part. Desk margin to the 28 V VDD limit is
  +7.198 V at the 28.6 V hot estimate (was −0.6 V) and +7.279 V at 26.0 V. Attach headroom at 4.72 V in is
  +0.273 V over 4.1 V at the idle IDD maximum; IDD during communication is UNKNOWN.
- **R21** carries the `LCSC Part` field.

Cost (`p15_phase17_draft` row): USD 51.86 per 5-unit lot (parts 18.32, Economic PCBA 33.54), 14 lines,
6 extended; +USD 3.86 per lot over the RESET subset. With the current Board B and the candidate stock rows the
lineup is USD 357.98 per lot. PCB fabrication is excluded: Board P has a published USD 2.00 floor, Board B is UNKNOWN.

Phase 18 (draft sha256 `ccfe3229…`, commits `07f8590`…`1d622fa`): a scratch dry run of
`export-jlcpcb.py --boards board-p15 board-b` passes every exporter gate at `1d622fa`.

- **Exporter gates:** power budget (`power-budget-p15.json`, its own binding), STEP datums, assembly preview
  (`boards/board-b/assembly-preview-p15`, cross-board collision PASS), DRC 0 errors / 0 unconnected / parity
  `extra_footprint` only, ERC 0 errors, BOM/CPL parity (board-p15 23 = 23, 14 lines; Board B 75 = 75, 39 lines).
  The fabrication outputs were deleted from scratch after hashing; nothing was written under `manufacturing/releases/`.
- **Silk:** the silk warning classes now equal the as-built board. The phase 17 clipping came from visible
  supplier fields, not D9's library silk.
- **C38:** the 1 µF C15849 fits top-side without moving parts. board-p15 is USD 51.95 per 5-unit lot; the lineup
  with the candidate rows is USD 358.07.
- **Still BLOCKED for an order:** the dry run exported Board B with the incumbent C861519/C2983319 lines (0 and 1 in
  stock). The SOD-123 STEP datum translation (`4347b80`) awaits independent review. No layout review exists.

### Board B stock-gap candidate rows: not adopted; acceptance tests NOT RUN

`manufacturing/readiness/board-b-stock-gap-candidate-rows.json` lists both candidate rows beside their incumbents.
It is not a BOM or an order file. Adopting either part needs four things: the owner decision, a `board_b_spec.py`
edit, regeneration, and a new package. Each package must come from one revision and pass ERC, DRC and BOM/CPL parity.

| Refs | Candidate (incumbent) | Acceptance tests | Status |
|---|---|---|---|
| R21, R27 | AT0603BRD07680RL C5455478 (RT0603BRD07680RL C861519) | BB-R-1 incoming 4-wire 679.32–680.68 Ω; BB-R-2 +12 V / −12 V set points at no load and at budget, within 0.2 % of an incumbent board; BB-R-3 30 min warm drift | NOT RUN |
| C11 | RVT1E471M0810 C696190 (GVT1E477M0810CNVC C2983319) | BB-C-1 fit and polarity on the Φ8 land; BB-C-2 −14.145 V PRE ripple no worse than an incumbent board; BB-C-3 −12 V load step with no sustained oscillation; BB-C-4 C11 ripple ≤ 342 mA rms; BB-C-5 case temperature after 30 min | NOT RUN |

### Residual risks

| Risk | Status |
|---|---|
| Q1 gate clamps D8 and D13 both open: −27.49 V at the 28.35 V row, beyond VGSS 25 V | OPEN (double fault) |
| VBEN drive and sink rating, Q6 RDS(on) and hot leakage | UNSOURCED |
| No 20 V / 5 A NVM image defined or read back | OPEN |
| C3 height tolerance and the stack conflict with Board B U3 | UNKNOWN / OPEN |
| B20 no-load start slope (+5 V 0.94 V/ms, −12 V 1.47 V/ms) | FAIL (SIM), owner exception requested |
| B20 ripple (no switching simulation), let-through, reverse current ≤ 1 mA, loaded discharge order | OPEN |
| B20 minimum-off interlock: Q66 VGS(th) minimum is PA (0.5 V); CHO effective capacitance range is PA | OPEN |
| B20 passives: listing-only identities; 8 lines out of stock; 27 nF / 47 nF C0G without a listing | OPEN / BLOCKED / UNKNOWN |
| TVS2200DRVR single-source stock (4 units on 2026-10-31) | BLOCKED for a 5-unit lot |
| HC-11 / printed-leg support height against the P envelope | OPEN (see `3dp-files/adhesive-leg/README.md`) |

### Bench acceptance tests (planned; none run)

| Test | Board | Pass criterion | Status |
|---|---|---|---|
| Unpowered resistance and short check per rail | P, B20 | no rail-to-GND short; values against the net table | NOT RUN |
| PD contract at 20 V / 5 A with the defined NVM image; read back the NVM | P | requested PDO selected; NVM matches the image | NOT RUN |
| Q1 gate–source voltage across VBUS 5–20 V, and with D8 lifted | P | \|VGS\| ≤ 20 V normal, ≤ 25 V with D8 lifted | NOT RUN |
| Hot-plug overshoot and TPS16630 OV trip | P | VBUS_OUT peak within the contract; trip window | NOT RUN |
| 5 A thermal soak, 30 min | P | copper and Q1/Q3 temperature rise within the assumed 20 °C | NOT RUN |
| Rail band, ripple < 1 mVp-p at load | B20 | contract §0 | NOT RUN |
| Start order, slopes and band entry at no load and at I_TRANSIENT_MIN | B20 | contract §5 rows | NOT RUN |
| Disable and re-enable at 6–20 ms off time | B20 | re-enable no sooner than the hold; §5 rows hold | NOT RUN |
| Limiter trip and latched shutdown on each rail | B20 | contract §1 window; re-plug only | NOT RUN |
| Discharge time and order under load | B20 | ≤ 100 ms; contract §3 order | NOT RUN |
| J10/J11 pin map against a keyed synth cable (pins 1/2 −12 V) | B20 | each pin at its rail | NOT RUN |
| Stack fit: P on B with the 18 mm legs; C3 and U3 clearance | P + B | no contact; measured gaps | NOT RUN |

## 15 V prototype order: decision inputs (desk only; no order, quote or package exists)

This section collects what an owner needs to decide on a 5-unit zudo-pd 15 V prototype lot: board-p15 on the
current Board B. It is not an order file. Every board here is an unvalidated draft, and no package has been
exported for this pair outside scratch dry runs.

### Revisions an order package would have to be built from

| Board | File | sha256 | Last change |
|---|---|---|---|
| board-p15 | `boards/board-p15/board-p15-draft.kicad_pcb` | `97acc5f4c712f0be01dbc5d6809a5bd17ecdceb97f3e6a831bef94500117d065` | `d6d3efc` (phase 20, back mark `P15 r1`) |
| board-p15 | `boards/board-p15/board-p15.kicad_sch` | `416c56a7bd5bfb74c2b15b56081c619239063d4cce58ef06373b8ea9c7f5393f` | `07f8590` (phase 18) |
| board-p15 | `scripts/schgen/board_p15_spec.py` | `c20281447c89f32e4ed7b7bcd86e9b5bc36df7b24fe522f8f2860a07870cd713` | phase 18 |
| board-p15 | `boards/board-p15/nvm/stusb4500-15v.bin` | `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` | desk image, never written |
| Board B | `boards/board-b/board-b.kicad_pcb` | `c8f83fcdba4daa06bfcce6b998bc2c3ab0400a0c12d4b13e1ba391a72553fc2f` | `194707a` (on main) |
| Board B | `boards/board-b/board-b.kicad_sch` | `d3c395d151bcec7ab440a24b28f8dc01183cf10fb29b65b2149ab6077692e9e3` | `194707a` |
| Board B | `scripts/schgen/board_b_spec.py` | `12814d07a8318bc16ab0259ff6baddfd67af3abe01b8824feb5b0885608cff49` | — |

- The package of record, `manufacturing/releases/corner-support-review/`, carries Board B source
  `cd3677c9…`, not the active `c8f83fcd…`. An order needs a new package from one revision of both boards.
- The phase 20 scratch dry run (`export-jlcpcb.py --boards board-p15 board-b`) passed every exporter gate on these
  files. It still exported the incumbent Board B stock lines below.
- The stack proof `boards/board-b/assembly-preview-p15` binds this board-p15 and Board B pair: collision PASS.
  Its 159 MB STEP is local-only.

### Two Board B stock substitutions need owner adoption

Neither candidate is adopted. Adopting one means a `board_b_spec.py` edit, regeneration, a new package and the
acceptance tests in `readiness/board-b-stock-gap-candidate-rows.json`.

| Refs | Incumbent (stock 2026-11-01, need for 5 sets) | Candidate (stock) | Desk match | Acceptance tests |
|---|---|---|---|---|
| R21, R27 | YAGEO RT0603BRD07680RL C861519 (0, need 10) | YAGEO AT0603BRD07680RL C5455478 (410–439) | every recorded row matches: 680 Ω, 0.1 %, 25 ppm/°C | BB-R-1 to BB-R-3: NOT RUN |
| C11 | HRK GVT1E477M0810CNVC C2983319 (1, need 5) | Honor RVT1E471M0810 C696190 (4,085–4,625) | 470 µF 25 V on the same Φ8 land; 342 mA ripple rating against 312 mA; lower ESR changes the LM2596 loop (not measured) | BB-C-1 to BB-C-5: NOT RUN |

### Bench tests still NOT RUN for this pair

No hardware exists, so every row is NOT RUN.

| Test | Board | Pass criterion |
|---|---|---|
| P15-NVM-1 to P15-NVM-7: jig levels, pre-write dump, power-cycle readback, PDO registers, first attach, VDD at 4.75 V in | board-p15 | `board-p15-programming.md` table; readback equals `76622e14…`; 15 V contract; VDD ≥ 4.1 V |
| D9 clamp at the cold corner: leakage at a 15.75 V input, −40 °C | board-p15 | no VDD sag at the 15 V contract (guaranteed window is only +0.01 V) |
| RESET strap leakage | board-p15 | RESET stays low |
| BB-R-1 to BB-R-3, BB-C-1 to BB-C-5 | Board B | the candidate-row table above |
| Full-load start, ripple, thermal, fuse hold, surge and low-input rows of `ORDER-NOTES.md` | Board B on board-p15 | as listed there |
| Stack fit: board-p15 on Board B with the 18 mm printed legs, M3 in the 3.0 mm holes | P + B | no contact; measured gaps; screw passes |

### Residual risks of a 15 V lot

| Risk | Status |
|---|---|
| D9 guaranteed cold window over a 15.75 V input is +0.01 V | OPEN; BZT52C20 fails the 5 V margin to 28 V (`d9-zener-choice.json`) |
| VDD IDD during PD communication, so attach headroom | UNKNOWN |
| R29/R30 derating above 70 °C (77.1 / 36.2 mW at the surge row) | UNKNOWN |
| SCL/SDA idle states without pull-ups; RESET strap leakage | UNVERIFIED (Rev 8 not re-read) / OPEN |
| 15 V NVM image never written or read back | OPEN |
| Board B package of record is not the active Board B revision | OPEN: a new package is required |
| Board B electrical qualification and the printed-leg mechanical fit | OPEN; the adhesive-leg fit check is stale |
| C861332 (R24) 10 in stock against 5 | OPEN: no margin |

### 5-unit lot cost: USD 358.07 for parts and assembly; Board B PCB fabrication UNKNOWN

From `calculate-lineup-cost.py` on the 2026-10-31 snapshot, with the two candidate rows priced in. These are desk
figures; no quote was requested.

| Item | Parts | Assembly | Subtotal |
|---|---|---|---|
| board-p15 (phase 18 BOM: 14 lines, Economic PCBA) | USD 18.39 | USD 33.56 | USD 51.95 |
| Board B with the two candidate rows (39 lines, Standard PCBA; USD 0.07 over the incumbent rows, phase 17 desk figure) | USD 188.96 | USD 117.16 | USD 306.12 |
| Parts and assembly, 5 sets | | | **USD 358.07** (USD 71.61 per set) |
| PCB fabrication | board-p15: published USD 2.00 floor (not quoted); Board B: **UNKNOWN** | | — |
| Shipping and duty | **UNKNOWN** | | — |

## Lineup cost: the renewal costs about twice the current lineup per 5-unit lot

Catalog parts and JLCPCB assembly fees on 2026-10-31. PCB fabrication, shipping and duty are UNKNOWN. A
one-sided board uses the cheaper of Economic and Standard PCBA; a two-sided board can only use Standard.

| Lineup | Parts, lot 1 | Parts, 5-unit lot (per set) | Assembly, 5-unit lot | Lot total (per set) | Unpriced parts |
|---|---|---|---|---|---|
| Current: Board P 15 V (as built, Economic) + Board B (Standard) | USD 43.70 | USD 206.53 (41.31) | USD 147.58 | USD 354.11 (70.82) | 0 |
| Renewal as drawn: Board P r3 (Standard, two-sided) + B20 with J10/J11 (Standard) | USD 88.84 | USD 373.14 (74.63) | USD 318.98 | USD 692.12 (138.42) | 2 (27 nF, 47 nF C0G) |
| Renewal like for like: as drawn + B20 adders (3 TVS, 3 LEDs, 3 ballasts) | USD 89.00 | USD 373.94 (74.79) | USD 328.30 | USD 702.24 (140.45) | 2 |
| Lever check: Board P r3 one-sided (Economic) + like-for-like B20 | USD 89.00 | USD 373.94 (74.79) | USD 267.96 | USD 641.90 (128.38) | 2; **not available**: the top-only placement leaves 20 parts unplaced |

- **Difference.** Like for like, the renewal costs USD 348.13 more per 5-unit lot (USD 69.63 per set):
  USD 167.41 in parts and USD 180.72 in assembly. Most of the assembly gap is Board P r3's double-side
  Standard PCBA (USD 131.48 against 30.42 for the as-built Economic board) and the 88 B20 feeder lines.
- **Renewal drivers.** OPA2187 × 9 (USD 76.85 per lot), CSD18543Q3A × 6 (31.99), GRM32 10 µF × 19 (29.90),
  the two 10 mΩ 2512 shunts (25.39) and INA301 × 2 (24.03). The 68 resolved passives add USD 42.09 per lot
  in parts, plus their feeder lines.
- **Current drivers.** LT3015 and LT1963A (USD 122.67 per lot).
- **Lever: one-sided Board P r3.** It would save USD 60.34 per lot, but it is not available: the top-only
  search leaves 20 small parts unplaced, and those parts are the STUSB4500 local clamps and dividers that
  must sit within 2.5 mm of their pins, so they cannot move to Board B either. Its margin cost would be the
  D9–D12 / R21 pin-distance rule.
- **No-cost lever already applied.** B20 and the current Board B use Standard PCBA, which is cheaper than
  Economic once a board has many extended lines (B20: USD 187.50 against 222.60 per lot).
- **Availability.** Both lineups are BLOCKED for a 5-unit lot on 2026-10-31 (renewal: TVS2200DRVR plus
  8 B20 lines; current: C861519 and C2983319, with in-stock same-class listings above).

## B20 cost levers (desk only): line count and the protection/servo blocks dominate; none is free

These figures are for one 5-unit lot of the like-for-like renewal (USD 702.24), from `calculate-lineup-cost.py --json`. B20 assembly is
Standard single-side, USD 196.82:

| Assembly item | USD |
|---|---|
| 88 feeder lines × 1.53 | 134.64 |
| Setup and stencil | 33.77 |
| Handling | 14.93 |
| Hand-soldering labour | 3.58 |
| 751 SMD joints × 5 boards | 6.01 |
| 42 TH joints × 5 boards | 3.44 |

Economic PCBA is USD 235.02 (69 extended lines × 3.07). It only becomes cheaper below 57 extended lines.
No schematic was changed for this table.

| # | Contributor (lot of 5) | Lever | Saves (lot of 5) | Breaks or costs |
|---|---|---|---|---|
| 1 | B20 unique lines: 88 × USD 1.53 feeder loading = 134.64. 55 of the lines are resistors (USD 46.84 in parts) | Collapse the 0.1 % divider values to about 20 shared values (ratio-matched pairs, series pairs) | Up to about 53.55 in feeder fees (−35 lines) plus up to about 30 in minimum-buy parts | Every set point and threshold moves: rail dividers, window and tracking comparators, LIMIT dividers. The §5 band, start-order and slope simulations must be re-run. Series pairs add placements |
| 2 | Board P r3 two-sided: Standard double only, USD 131.48 | Single-sided Board P (Economic) | 60.34 (Standard single-side would save 33.77) | Not available: the top-only search leaves 20 parts unplaced, and those are the STUSB4500 pin-local clamps and dividers (D9–D12, R21 within 2.5 mm). Moving them breaks that rule |
| 3 | OPA2187 × 9 (servo, window and tracking amplifiers): USD 76.85, plus REF5025 at 4.54 | Drop the post-shunt servo and regulate at the converter feedback; keep only the window and tracking amplifiers | Up to about 81 in parts plus their R/C lines | The terminal-accuracy and ripple contract loses its shunt and switch-drop correction. Band entry and tracking rows need re-simulation. Another zero-drift dual would need an evidenced part; its price is UNKNOWN |
| 4 | Interface limiter: INA301 × 2 (24.03) + PCSR2512 shunts × 2 (25.39) = 49.42 | Fuse-style PTC protection, as on the current Board B | About 48 in parts and 2–4 lines | The §1 interface-maximum trip window and latched shutdown are lost. PTC hold/trip spread and slow response replace a defined limit |
| 5 | Reverse blocking, CSD18543Q3A × 6: 31.99. Output bank, GRM32ER71H106KA12L × 19: 29.90 | One FET per rail instead of back-to-back pairs. GRM32 to basic 1206 CL31A106KBHNNNE | Up to 16 (FETs). 9.80 (capacitors), and 3.07 per line only under Economic | Single FETs lose reverse-current blocking (the ≤ 1 mA row) and the tracked-pair discharge order. X5R 1206 effective capacitance at bias drops, so the ripple rows reopen |

Combining levers 1, 3 and 4 would cut roughly USD 210 per lot. That still leaves the like-for-like renewal at
about USD 490 against 354.11 for the current lineup. Each of those levers removes a contract row that the renewal
was drawn to meet.
