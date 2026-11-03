# Package notes: Board P r3 (board-p) + Board B 20 V switcher-direct draft (board-b20-draft)

**Draft only. These notes accompany a review export, not an order.** The board-b20-draft PCB is an unvalidated
four-layer draft. No export of this pair has been uploaded, quoted or ordered, and nothing in it is validated,
qualified or released. The current development review package in `corner-support-review/` is the 15 V pair
(board-p15 + Board B). This pair is not that package.

Links below resolve inside an export of this pair. Repository documents are named by their path in
[Takazudo/zudo-pd](https://github.com/Takazudo/zudo-pd).

## Open before any order

- **Board P r3 is not bound to the exporter.** `board-p` exports `boards/board-p/board-p.kicad_pcb`. The r3 front end
  draft (`boards/board-p/r3-draft/`) still has identity, DRC and BOM/CPL failures.
- **Missing B20 front-edge features.** B20 has no top-edge pogo row (P1, TP3–TP5) and no front or back rail labels.
  Board B requires both.
- **Electrical behavior is unmeasured.**
  - Full-load, low-line, thermal and transient behavior: OPEN.
  - The inverter hot loop is 44.4 mm². Its inductance is OPEN.
  - D3 copper temperature: UNKNOWN.
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
