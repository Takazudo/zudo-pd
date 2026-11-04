# Package notes: Board P r3 (board-p) + Board B 20 V switcher-direct draft (board-b20-draft)

**Draft only. These notes accompany a review export, not an order.** The board-b20-draft PCB is an unvalidated
four-layer draft. No export of this pair has been uploaded, quoted or ordered, and nothing in it is validated,
qualified or released. The current development review package in `corner-support-review/` is the 15 V pair
(board-p15 + Board B). This pair is not that package.

Links below resolve inside an export of this pair. Repository documents are named by their path in
[Takazudo/zudo-pd](https://github.com/Takazudo/zudo-pd).

## Open before any order

- **Board P r3 is the exported board-p (PD20).** It routes with 0 open connections and passes native DRC with
  schematic parity (0 errors; parity only the mechanical MH1–MH3). No layout review exists for it, and it is a
  two-sided board (Standard PCBA, double side).
- **B20 top-edge probe row.** P1/TP3–TP5 sit at Board B's positions with B20 nets (owner decision 2026-11-04): P1 =
  NC, PDOK, GND, NC (no ATT) and TP3/TP4/TP5 = P12_PRE, P5_PRE, M12_PRE. They are bare copper, outside the BOM and CPL.
  The front and back rail labels are on the board and checked against the J6/J7 pin nets.
- **Independent layout review findings** (repository `manufacturing/pd20-b20-layout-review.md`, made on the board
  before the PD20 fixes). The −12 V limiter
  Kelvin blocker is fixed (RL3C now ties to the RSH3 sense pad). The −12 V output capacitors now reach U3/D3 through
  M12_RAW pours on F.Cu and B.Cu, and the FB/COMP/RT parts return through their own trace to one point on the U3 PAD.
  Both input-capacitor returns share the D3 anode pour. D3 and U3 heat now spreads into the B.Cu pour through 18
  vias. Still OPEN: the hot-loop area (unchanged; it needs a smaller diode package) and the D3 junction at the
  limiter maximum (desk 109–147 °C against a 150 °C limit).
- **Electrical behavior is unmeasured.**
  - Full-load, low-line, thermal and transient behavior: OPEN.
  - The inverter hot loop is 44.4 mm² between pad centres and 47.9–51.4 mm² along the copper. Its inductance is OPEN.
  - D3 copper temperature: UNKNOWN (desk island model only, `thermal-check.json` `inverter_island`).
- **Prototype quantity is 2** (JLCPCB PCBA needs at least two assembled sets).
- **Placement-preview orientation checks.** Before any order, check every polarized part against pad 1 of `cpl.csv`
  in JLC's placement preview. Start with these:
  - D1–D3 Schottky diodes. For D3 (B560C-13-F C85100, SMC), the cathode is pad 1 on C_SW.
  - The HSOP-8 and SOIC-8 converters U1–U3 and U10.
  - The VSSOP-8 amplifiers.
  - The SON-8 Q1–Q6.
  - The 35 SOT-23 FETs.
  - The 3D body models carry no pin-1 or cathode cue.

## Contents of an export of this pair

- **Per-board folders.** `board-p/` and `board-b20-draft/` each hold:
  - Gerber and drill files, including In1.Cu and In2.Cu for B20;
  - `bom.csv`, `cpl.csv` and `excluded.csv`;
  - the schematic PDF;
  - a source snapshot;
  - check reports.
- **Power reports (desk drafts, not measurements):**
  - [`power-budget-b20.json`](power-budget-b20.json) holds the switcher path and the desk losses. The board loss is
    6.62 W at the limiter maximum with maximum RDS(on).
  - [`power-layout-b20.json`](power-layout-b20.json) holds the hot loops, high-current paths and filled copper.
- **[`mechanical/assembly/`](mechanical/assembly/):** the Board P + B20 stack preview from
  `scripts/pcb/board-b20/assembly-preview.py`, with its collision and mechanical reports. Nominal CAD only. The large
  `populated-stack.step` is a local-only file.
- **[`step-datum-verification.json`](step-datum-verification.json):** a model-datum and orientation screen. It is not a
  physical fit proof.
