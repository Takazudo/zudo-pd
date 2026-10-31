# PD A/B readiness matrix: Board P r3 + B20 (unvalidated drafts)

Status words: **PASS**, **FAIL**, **BLOCKED**, **NOT RUN** (with the reason), **UNKNOWN**, **OPEN**.
No item here is validated, qualified or released. Nothing was ordered, quoted or uploaded.
Prices come from a read-only JLCPCB catalog and fee-table retrieval on 2026-10-31 and are not quotes
(`manufacturing/readiness/jlc-snapshot-2026-10-31.json`). Cost arithmetic is in
`scripts/pcb/calculate-lineup-cost.py`.

**A** is the design gate: the drawn design and its evidence close. **B** is the build gate: the parts,
cost, manufacturability and bench plan close. The user decides on a single lineup from the cost
comparison at the end.

## A gates: open on both boards; no PCB exists for B20

| Gate | Board P r3 | B20 | Evidence |
|---|---|---|---|
| Spec | **PASS** (generated spec, 29 decisions) | **PASS** (paper draft spec) | `scripts/schgen/board_p_spec.py`, `scripts/schgen/decisions.json`, `scripts/schgen/board_b20_spec.py` |
| Schematic ERC | **PASS**: 0 errors, 33 `pin_to_pin` warnings | **PASS**: 0 errors, 26 warnings (21 missing `*_DRAFT` footprints) | native KiCad 10.0.6 ERC + `verify_netlist.py` (P: 46 nets; B20: 140 nets) |
| Footprints | **PASS** (shared library) | **OPEN**: 21 `*_DRAFT` footprints do not exist | `footprints/kicad/`; B20 ERC |
| PCB DRC | **OPEN**: no copper errors; 8 unconnected (4 signals at U1, 4 GND islands) | **NOT RUN**: there is no B20 PCB | `boards/board-p/r3-draft/placement-report.json`, `routing-report.json` |
| Current capacity | **OPEN**: 5 A pours ≥ 1.85 mm against 1.82 mm (IPC-2221, 20 °C rise PA); no thermal check | **PASS (arithmetic)** converter and switch current | r3 `routing-report.json`; `calculate-board-b20-draft.py` |
| Stack and mechanics | **OPEN**: C3 over the current Board B U3 (3.31 × 4.05 mm); B.Cu parts face the floor | **OPEN**: the B20 layout must keep x 7.74–17.25, y 24.54–35.77 mm free | `boards/board-p/r3-draft/README.md` |
| Simulation rows | **OPEN**: Q1 overshoot bound rests on TYP-only TPS16630 rows | Start, re-entry and band rows **PASS (SIM)**. No-load slope rows **FAIL (SIM)**, with an owner exception requested (nom +5 V 0.94 V/ms is above the requested 0.90). Ripple, let-through, reverse current and loaded discharge order **OPEN** | `manufacturing/board-b-20v-switcher-direct-draft.md` §4–§5f; `manufacturing/sim/board-b20-phase12/results.json` |
| Component evidence | **OPEN**: strict validator PASS, but VBEN drive, Q6 RDS(on)/leakage and STUSB 28 V limits are UNSOURCED, and no 20 V / 5 A NVM image is defined | **OPEN**: 73 `*_PROPOSED` values have no exact part | `.claude/skills/component-spec-audit/scripts/validate.py --strict`; `rules.json`; `component-board-b20-draft-candidates/` |
| Independent review | **OPEN**: the observed independent run refused (both rules UNSOURCED); no PCB review | **OPEN**: review findings of `bad5ddf` recorded; no review since phase 9 | `observed-runs.json`; draft page §7 |

## B gates: BLOCKED on availability, with the renewal costing more on the priced lines alone

| Gate | Board P r3 | B20 | Evidence |
|---|---|---|---|
| BOM availability (5-unit lot) | **BLOCKED**: TVS2200DRVR C523793 had 4 in stock against 5 needed; the other 27 lines in stock | **UNKNOWN**: 73 parts have no LCSC code. The 34 priced lines were in stock | snapshot `catalog.parts[].stock` |
| Unit cost, parts | USD 12.05 (lot 1), 12.05 per board in a lot of 5 | ≥ USD 66.94 (lot 1), ≥ 53.62 per board in a lot of 5; 73 parts UNKNOWN | `calculate-lineup-cost.py` |
| 5-unit lot, parts | USD 60.26 | ≥ USD 268.08 | same |
| Assembly fee, 5-unit lot | USD 131.48: Standard PCBA, double-side (setup 51.12, stencil 16.42, 28 lines × 1.53 feeder loading, handling ≥ 14.93) | ≥ USD 92.97 (Economic, single-side assumed; 24 extended lines × 3.07) | snapshot `assembly_fees` |
| PCB fabrication | **UNKNOWN** (not retrieved) | **UNKNOWN** (no PCB) | — |
| DFM | **OPEN**: two-sided assembly forces Standard PCBA; 0603 library courtyards larger than the as-built lands; no DFM run | **NOT RUN**: no PCB | r3 `placement-report.json` |
| BOM completeness | **PASS** against the spec | **OPEN**: the B20 spec has no J10/J11 DW254P synth headers (the current Board B has both; 32 PTH joints) | `board_b20_spec.py`; current `board-b/bom.csv` |
| Bench acceptance tests | **NOT RUN**: no hardware | **NOT RUN**: no hardware | list below |

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
| Stack fit: P on B with the 18 mm legs; C3 and U3 clearance | P + B | no contact; measured gaps | NOT RUN |

## Lineup cost: the renewal costs more on the priced lines alone

Catalog parts and JLCPCB assembly fees on 2026-10-31. PCB fabrication, shipping and duty are UNKNOWN.

| Lineup | Parts, lot 1 | Parts, 5-unit lot (per set) | Assembly, 5-unit lot | Unpriced parts |
|---|---|---|---|---|
| Current: Board P 15 V (as built) + Board B | USD 43.70 | USD 206.53 (41.31) | USD 150.23 | 0 |
| Renewal: Board P r3 + B20 | ≥ USD 78.99 | ≥ USD 328.34 (≥ 65.67) | ≥ USD 224.45 | 73 (B20 `*_PROPOSED`) |

- **Per set.** The renewal's priced lines alone cost at least USD 24.36 more per set in a 5-unit lot.
  Its assembly costs at least USD 74.22 more per lot.
- **Renewal drivers.** OPA2187 × 9 (USD 76.85 per lot), the CSD18543Q3A switches, the 10 µF 50 V MLCCs,
  and the double-side Standard PCBA set-up for Board P r3.
- **Current drivers.** LT3015 and LT1963A (USD 122.67 per lot).
- **Current lineup availability.** It is also BLOCKED on stock: RT0603BRD07680RL C861519 had 0 units and
  GVT1E477M0810CNVC C2983319 had 1.
- **Not like for like.** The current Board B includes the J10/J11 synth headers, which the B20 spec lacks.
