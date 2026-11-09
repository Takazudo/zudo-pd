# Package notes: Board P r3 (board-p) + Board B 20 V switcher-direct draft (board-b20-draft)

**Draft only. These notes accompany a review export, not an order.** The board-b20-draft PCB is a
four-layer development board with source-bound native checks. No export of this pair has been uploaded, quoted
or ordered. Electrical and physical qualification remain incomplete; this pair is not released for ordering. The current development review package in `corner-support-review/` is the 15 V pair
(board-p15 + Board B). This pair is not that package.

Links below resolve inside an export of this pair. Repository documents are named by their path in
[Takazudo/zudo-pd](https://github.com/Takazudo/zudo-pd).

## Open before any order

- **Board P r3 is the exported board-p (PD20).** The completed independent review is retained at
  `boards/board-p/r3-draft/independent-review.md`, with corrective work and source-bound native receipts beside it.
  Use the actual export revision's DRC/parity and layout dispositions; a historical clean DRC is not current
  acceptance. It is a two-sided board (Standard PCBA, double side).
- **PD20 electrical order hold.** Actual phase33 refinement reveals modeled no-load slope/current excursions
  beyond the adopted exceptions. Loaded asymmetric discharge, disconnect-before-discharge behavior and maximum
  delivered current including overshoot remain pre-order gates. No tracked ramp-down agreement, excess-current
  budget or lower current ceiling is adopted. PD20 NVM mapping/timing/transition decisions, repetitive discharge
  endurance, installed-capacitance bounds, shared land/paste review and thermal margins remain separate holds.
  See repository `manufacturing/prototype-order-readiness.md`; a successful development export does not close them.
- **B20 top-edge probe row.** P1/TP3–TP5 sit at Board B's positions with B20 nets (owner decision 2026-11-04): P1 =
  NC, PDOK, GND, NC (no ATT) and TP3/TP4/TP5 = P12_PRE, P5_PRE, M12_PRE. They are bare copper, outside the BOM and CPL.
  The front and back rail labels are on the board and checked against the J6/J7 pin nets. P1 ordinals and its
  ordered NC/PDOK/GND/NC legend use 1.0 mm text with 0.15 mm strokes. Current Board P J3.4/J3.5 are explicitly
  labeled VBUS/GND; these are PD20 probe labels, not a change to the frozen P15 package.
- **Independent layout review findings** (repository `manufacturing/pd20-b20-layout-review.md`, made on the board
  before the PD20 fixes). The −12 V limiter
  Kelvin blocker is fixed (RL3C now ties to the RSH3 sense pad). The −12 V output capacitors now reach U3/D3 through
  M12_RAW pours on F.Cu and B.Cu, and the FB/COMP/RT parts return through their own trace to one point on the U3 PAD.
  Both input-capacitor returns share the D3 anode pour. D3 and U3 heat now spreads into the B.Cu pour through 17
  joining vias. C43 (100 nF) now bypasses U3 pin 2 to its PAD. Still OPEN: the hot-loop area (the owner kept the SMC diode
  for its heat spreading) and the D3 junction at the limiter maximum. The source-bound desk report regenerated on 2026-11-10 JST gives
  continuous D3 TJ 92.9–111.5 °C with typical switch RDS and 99.0–120.1 °C with maximum RDS. Thus the older rounded
  93–120 °C range spans both rows, while 99–120 °C is maximum-RDS only. Maximum delivered current held indefinitely
  gives 109.0–133.4 / 118.3–146.8 °C (typ/max RDS), close to the 150 °C limit. These are conditioned steady-state
  calculations, not a measured temperature or a 20 ms transient model; require the final report's source binding.
- **Electrical behavior is unmeasured.**
  - Full-load, low-line, thermal and transient behavior: OPEN.
  - The inverter hot loop is 44.4 mm² between pad centres and 47.9–51.4 mm² along the copper. Its inductance is OPEN.
  - D3 copper temperature: UNKNOWN (desk island model only, `thermal-check.json` `inverter_island`).
- **Stack/enclosure limits.** The nominal 11.1 mm board-plane spacing passes the CAD screen; the separate 11.0 mm
  comparison has 1.36449 mm³ unintended intersection. Actual header seating and tolerances remain unverified.
  HC11 supports with the populated face toward a flat 11 mm enclosure floor are incompatible with the current
  P back plane and terminal height. The diameter-6 mm support-column screen is a PROJECT assumption; a taller
  support or deliberate floor clearance needs owner disposition. No 16 mm support substitution is adopted.
- **Current B20 population is 270 fitted components.** The 269-component export receipt is historical.
- **Prototype quantity rule is 2.** This development review does not authorize a PD20 order. The settled current
  purchase handoff is exactly two assembled P15 modules from the separate frozen P15 package.
- **Placement-preview orientation checks.** Before any order, check every polarized part against pad 1 of `cpl.csv`
  in JLC's placement preview. Start with these:
  - D1–D3 Schottky diodes. For D3 (B560C-13-F C85100, SMC), the cathode is pad 1 on C_SW.
  - The HSOP-8 and SOIC-8 converters U1–U3 and U10.
  - The VSSOP-8 amplifiers.
  - The SON-8 Q1–Q6.
  - Every SOT-23 FET.
  - Body models alone do not establish pin-1/cathode orientation or supplier placement.

## Contents of an export of this pair

- **Per-board folders.** `board-p/` and `board-b20-draft/` each hold:
  - Gerber and drill files, including In1.Cu and In2.Cu for B20;
  - `bom.csv`, `cpl.csv` and `excluded.csv`;
  - the schematic PDF;
  - a source snapshot;
  - check reports.
- **Power reports (desk drafts, not measurements):**
  - [`power-budget-b20.json`](power-budget-b20.json) holds the switcher path and the desk losses. The board loss is
    6.62 W at the limiter (let-through) maximum with maximum RDS(on); 4.29–4.79 W at the continuous contract load
    (1.7 / 1.6 / 0.3 A, 2026-11-08 load cases).
  - [`power-layout-b20.json`](power-layout-b20.json) holds the hot loops, high-current paths and filled copper.
- **[`mechanical/assembly/`](mechanical/assembly/):** the Board P + B20 stack preview from
  `scripts/pcb/board-b20/assembly-preview.py`, with its collision and mechanical reports. Nominal CAD only. The large
  `populated-stack.step` is a local-only file.
- **[`step-datum-verification.json`](step-datum-verification.json):** a model-datum and orientation screen. It is not a
  physical fit proof.

## Refill reproducibility

The B20 generator finalizes through two fresh pinned KiCad CLI refills and requires
byte-identical outputs, unchanged non-fill geometry and item identities, and the
reviewed DRC disposition. The initial filled-plane delta is retained in repository
`boards/board-b20-draft/refill-replay-adoption.json`. The exporter still requires
exact source/staged geometry equality; this is not an electrical acceptance gate.
