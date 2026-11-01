# PD A/B readiness matrix: Board P r3 + B20 (unvalidated drafts)

Status words: **PASS**, **FAIL**, **BLOCKED**, **NOT RUN** (with the reason), **UNKNOWN**, **OPEN**.
No item here is validated, qualified or released. Nothing was ordered, quoted or uploaded.
Prices come from read-only JLCPCB catalog and fee-table retrievals on 2026-10-31 and are not quotes
(`manufacturing/readiness/jlc-snapshot-2026-10-31.json`; phase 13 B20 listings in
`manufacturing/readiness/b20-identity-resolution.json`). Cost arithmetic is in
`scripts/pcb/calculate-lineup-cost.py`.

**A** is the design gate: the drawn design and its evidence close. **B** is the build gate: the parts,
cost, manufacturability and bench plan close. The user decides on a single lineup from the cost
comparison at the end.

## A gates: open on both boards; no PCB exists for B20

| Gate | Board P r3 | B20 | Evidence |
|---|---|---|---|
| Spec | **PASS** (generated spec, 29 decisions) | **PASS** (paper draft spec; phase 13 adds J10/J11) | `scripts/schgen/board_p_spec.py`, `scripts/schgen/decisions.json`, `scripts/schgen/board_b20_spec.py` |
| Schematic ERC | **PASS**: 0 errors, 33 `pin_to_pin` warnings | **PASS**: 0 errors, 56 warnings (21 missing `*_DRAFT` footprints; 35 `pin_to_pin` on the unspecified J5/J10/J11 pins) | native KiCad 10.0.6 ERC + `verify_netlist.py` (P: 46 nets; B20: 142 nets) |
| Footprints | **PASS** (shared library) | **OPEN**: 21 placements on 5 `*_DRAFT` names, none in `footprints/kicad/`; stock KiCad candidates listed, land patterns not compared | `manufacturing/board-b-20v-switcher-direct-draft.md` §3 footprint table |
| PCB DRC | **OPEN**: native DRC 0 clearance/short/courtyard errors, 5 `items_not_allowed` (owners in their own keep-outs), 3 unconnected items (CC2 at U1.4; 2 GND zone items) against 8 in phase 12 | **NOT RUN**: there is no B20 PCB | `boards/board-p/r3-draft/placement-report.json`, `routing-report.json` |
| Current capacity | **OPEN**: 5 A pours ≥ 1.9 mm against 1.82 mm (IPC-2221, 20 °C rise PA); no thermal check | **PASS (arithmetic)** converter and switch current | r3 `routing-report.json`; `calculate-board-b20-draft.py` |
| Stack and mechanics | **OPEN**: C3 over the current Board B U3 (3.31 × 4.05 mm); B.Cu parts face the floor | **OPEN**: the B20 layout must keep x 7.74–17.25, y 24.54–35.77 mm free | `boards/board-p/r3-draft/README.md` |
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

### Stock gaps and evidenced alternatives (2026-10-31 listings)

| Blocked line | Need (5 sets) | In-stock listing | Status |
|---|---|---|---|
| TVS2200DRVR C523793 (TI), 4 in stock | 5 | C55616459 "TVS2200DRVR" from Wuxi Maxinmicro (1,264): same number, other maker, no datasheet read. ESTVS2200DRVR C42400188 ElecSuper (2,866): listing clamp 28.6 V, above the 28 V node bound that only the TI clamp holds | **BLOCKED**: no evidenced drop-in |
| RT0603BRD07680RL C861519 (current Board B R21/R27), 0 in stock | 10 | AT0603BRD07680RL C5455478 (Yageo, 0.1 %, 25 ppm/°C, 439); TNPW0603680RBEEA C2079059 (Vishay, 0.1 %, 25 ppm/°C, 5,141); RT0603BRE07680RL C705871 (50 ppm/°C, 4,764) | **OPEN**: same class in stock; listing facts only, no owner record |
| GVT1E477M0810CNVC C2983319 (current Board B C11), 1 in stock | 5 | RVT1E471M0810 C696190 (Honor, 470 µF 25 V, D8 × L10.2, 4,625), the maker of the owned RVT1H101M0810 on the same 8 mm footprint | **OPEN**: ESR and ripple not in the listing; no owner record |

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
