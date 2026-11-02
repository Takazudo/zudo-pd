# Package notes: Board P 15 V (board-p15) + Board B

**These are development review files, not an order.** This package pairs the Board P 15 V draft (`board-p15/`)
with Board B (`board-b/`). Board B carries the adopted C5455478 (R21/R27) and C696190 (C11) lines
(`dec-b-stock-gap-substitutions`). The package has not been uploaded, quoted or ordered, and nothing in it is
validated, qualified or released. Board B as ordered on 2026-09-20 is package state S3. S3 is not this package; it is
kept in the repository at commit `f25194f`.

Links below resolve inside this package. Repository documents are named by their path in
[Takazudo/zudo-pd](https://github.com/Takazudo/zudo-pd).

## Mandatory JLC placement-preview orientation checks

Neither board has been placed by JLC with these exact parts on these lands. Before ordering, check each one in
JLC's placement preview against pad 1 of `cpl.csv`.

| Ref | Part | Pad 1 | If reversed |
|---|---|---|---|
| board-p15 D5 | Littelfuse SMAJ16A C74561 (SMA) | cathode band on VBUS_IN | forward-clamps VBUS |
| board-p15 D9 | BZT52C18 C192739 (SOD-123) | cathode band on VDD_LOC | clamps VDD near 0.7 V; the STUSB4500 never powers |
| Board B C11 | Honor RVT1E471M0810 C696190 (Φ8 can) | + terminal on GND (the rail is −14.145 V) | about 14 V reverse bias on an aluminium electrolytic |

The CPL uses native KiCad rotations with a common drill/place origin. Do not negate Y. Check every other polarized
part in the same preview as well.

## Contents

- `board-p15/` and `board-b/`: each folder holds:
  - a Gerber/drill ZIP;
  - `bom.csv`, `cpl.csv` and `excluded.csv`;
  - the schematic PDF and assembly drawings;
  - a source snapshot (`source/`);
  - check reports (`checks/`: DRC with schematic parity, ERC, model checks, export validation and commands).
- Intentional DNP parts and bare test pads and holes are in `excluded.csv`, never in the BOM or CPL.
- `manifest.json`: the source revision (`git_base`) plus the source and artifact hashes. `SHA256SUMS` locks every file.
- [`power-budget-p15.json`](power-budget-p15.json), [`power-budget.md`](power-budget.md) and
  [`power-layout.json`](power-layout.json): conditioned desk calculations and filled-copper geometry. They are not
  measurements.
- [`step-datum-verification.json`](step-datum-verification.json): a model-datum and orientation screen, not a physical
  fit proof.
- [`mechanical/assembly/`](mechanical/assembly/): the P+B stack preview and its collision report. The large
  `populated-stack.step` is a local-only file.
- [`mechanical/supports/`](mechanical/supports/README.md): the retained HC-11 support evidence.

## Board P 15 V (board-p15)

- **Status:** unvalidated draft, 27 × 40 mm, two layers. The back silk reads `P15 r1`.
- **J2 pins:**
  - J2.4 is `NC`: it has no connection, because R21 straps RESET to GND (`dec-p15-reset-subset`).
  - J2.1/J2.2 (SCL/SDA) carry 100 kΩ pull-downs and no pull-ups. The programming jig supplies the pull-ups, to at
    most 4.5 V and never from J3.3 VREG_2V7.
- **NVM reload:** RESET cannot be pulsed, so only a full power cycle reloads the NVM. Accept the image only when a
  power-cycle readback equals the desk image `boards/board-p15/nvm/stusb4500-15v.bin`. The procedure is the
  repository page `doc/src/content/docs/architecture/board-p15-programming.md`.
- **First power and programming:**
  - Use a current-limited 5 V-only source, with Board B disconnected.
  - Verify the 15 V-only NVM image, its readback and its reload before connecting a PD-capable source.
  - A factory 20 V request can drive the 16 V TVS (D5, SMAJ16A) into sustained conduction. Twenty-volt operation is
    unsupported.
- **Pogo artwork:** J3.4 is `VBUS` and J3.5 is `GND`. Library-mismatch warnings keep this intentional artwork.

## Board B

- **Board:** 110 × 85 mm, three top fiducials, 0.07 mm (2 oz) outer copper. It is installed on legs with its
  component face down.
- **J10/J11:** DEALON DW254P-2X8-L0 C4749189, right-angle through-hole. Pins 1/2 carry −12 V. Confirm the wave or
  through-hole process and the footprint orientation at JLC.
- **J6/J7:** WJ500V-5.08-2P C8465, with wire entries facing left. J6.1=GND, J6.2=−12 V, J7.1=+5 V, J7.2=+12 V.
- **Top-edge contacts:** P1 and TP3–TP5 form seven contacts: ATT, PDOK, GND, NC, +13.44 V PRE, +6.519 V PRE and
  −14.145 V PRE. P1.3 is the shared probe return, and NC stays unconnected.
- **Board P stack:** J5 is on F.Cu. Board P mates face to face, at nominal Z=+11.1 mm in CAD, with
  `pd_to_board_b(x,y)=(y−0.5,x+12)`.
- **Holes:** three Ø3.2 mm PD holes, plus four Ø3.0 mm NPTH corner holes H4–H7 at (106,4), (4,81), (106,81) and
  (4,4). M3 screws have zero nominal diametral clearance in them.
- **Tabs:** the U4/U8 tabs carry the negative intermediate rail. Do not bond them to ground or to a shared heatsink.
- **Warnings:**
  - Silkscreen-over-pad warnings are retained.
  - J10/J11 silk is clipped at the straight edge on purpose.
  - Both stay in the DRC report.

## Still open

- **Board B acceptance tests:** BB-R-1..3 (R21/R27) and BB-C-1..5 (C11) are NOT RUN.
- **Bench qualification:** full-load startup, ripple, thermal coupling, low-line, surge and transient behaviour
  are NOT RUN.
- **C11 ripple share:** 256.8 mA of 342 mA (75.1 %, 120 Hz ESR ratio). The 150 kHz ESR is not printed for any bank
  part.
- **board-p15 identities:** R12 C22807 (UNI-ROYAL 0603WAF1503T5E) and C2/C35 C14663 (Yageo CC0603KRX7R9BB104) are
  now bound LCSC-to-MPN by distributor identity extracts retrieved 2026-11-01, on top of their manufacturer sheets.
  Their OPEN owner domains (pulse energy; bias, aging and ripple) remain open.
- **Mechanical fit:** the printed-leg fit, screw passage and connector seating are unmeasured.

This package prepares reviewable files. It does not place or pay for an order.
