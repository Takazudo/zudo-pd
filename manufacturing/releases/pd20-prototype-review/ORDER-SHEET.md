# PD20 prototype order sheet: Board P r3 + B20

**This sheet prepares an order; it is not one.** Nothing has been uploaded, quoted, paid for or ordered. The owner
decides the quantity and places the order. Electrical acceptance of PD20 is NOT ESTABLISHED, and every bench test
(T1–T8) is NOT RUN. This file sits outside `SHA256SUMS`; everything it names is locked there.

## Files to upload

Upload one board at a time. Each board is a separate JLC PCB + PCBA order line.

| Board | Gerber/drill ZIP | BOM | CPL |
| --- | --- | --- | --- |
| Board P r3 | `board-p/board-p-gerbers.zip` `654c1011…` | `board-p/bom.csv` `82a356e2…` | `board-p/cpl.csv` `65ea1721…` |
| B20 | `board-b20-draft/board-b20-draft-gerbers.zip` `6748bfd2…` | `board-b20-draft/bom.csv` `eb4622bf…` | `board-b20-draft/cpl.csv` `6e0c04ed…` |

`manifest.json` (`f430a76a…`) binds these to their PCB, schematic, project and spec hashes. Its `git_base` is the
checkout's HEAD when the export ran; the source hashes, not `git_base`, identify
the inputs, and they match the commit that adds this package.
`excluded.csv` lists the bare-copper pads and DNP parts that are intentionally absent from the BOM and CPL. Check the
whole folder with `sha256sum -c SHA256SUMS` before uploading.

## Board settings

| Setting | Board P r3 | B20 |
| --- | --- | --- |
| Size | 27 × 40 mm | 110 × 85 mm |
| Layers | 2 | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) |
| Thickness | 1.6 mm | 1.6 mm |
| Copper (from the job file) | 1 oz outer | 1 oz outer, 0.5 oz inner |
| Assembly | Standard PCBA, **both sides** (22 top, 22 bottom) | Standard PCBA, **both sides** (268 top, 26 bottom) |
| Fitted parts / BOM lines | 44 / 27 | 294 / 88 |
| Through-hole parts | Yes; hand-soldered by JLC | Yes; hand-soldered by JLC |

Any other fabrication option (finish, colour, via handling) is the owner's choice in the order form. The design does
not ask for filled or capped vias; if the review flags via-in-pad on the SON / PowerDI lands, accept JLC's standard
handling or ask before paying, and record the answer.

## Checks to make in JLC's placement preview

The CPL uses native KiCad rotations with one drill/place origin. Do not negate Y. Body models alone do not establish
pin 1 or cathode orientation, so compare each polarized part with pad 1 of `cpl.csv`:

- **B20 top:** D1–D3 (D3 B560C-13-F, SMC: cathode is pad 1 on C_SW), U1–U3 and U10 (HSOP-8 / SOIC-8), the VSSOP-8
  amplifiers, Q1–Q6 (VSON-8) and every SOT-23 FET.
- **B20 bottom (new with D2):** D4 BZT52C11 and D5 BZT52C3V9 (SOD-123), Q51 / Q52 / Q55 CSD18543Q3A (VSON-8),
  Q8 DMP3036SFG-7 (PowerDI3333-8) and Q7 / Q9 / Q13 BSS138 (SOT-23). The bottom preview is mirrored.
- **Board P r3:** both sides; the polarized-part list is in `ORDER-NOTES.md`.
- **Stencil and paste:** confirm both sides get a stencil. The shared Q1 / Q3 land and paste on Board P keep the
  `dec-pd20-land-paste-prototype` disposition; note any DFM warning there.

## Stock to resolve first

On 2026-11-20 JLC's catalog had zero stock for two B20 lines:

| LCSC | Part | Placements | Minimum purchase |
| --- | --- | --- | --- |
| C2861552 | INA301A3IDGKR | U11, U12 | 4 |
| C861332 | RT0603BRD0733RL | R35 | 200 |

Use a JLC parts pre-order for them, or ask for a separately reviewed substitute before ordering. Every other line was
in stock on that day. Re-check stock on the order day. Evidence:
`manufacturing/verification/pd20-order-package-20261120/`.

## Quantity: undecided; estimate for two pairs

The prototype quantity is the owner's decision. The labelled estimate below is for **two** Board P r3 and **two** B20
assembled, from the retained JLC fee model and the 2026-11-20 catalog rows:

| Board | Parts (USD) | Assembly (USD) |
| --- | --- | --- |
| Board P r3 × 2 | 24.12 | 128.64 |
| B20 × 2 | 148.64 | 225.94 |
| **Total** | **172.76** | **354.58** |

USD 527.34 in all, **before** PCB fabrication (a four-layer and a two-layer board), shipping, duties and any parts
pre-order fee. It is a catalog estimate, not a quote. Two assembled sets is the PCBA minimum (owner rule
2026-11-03); the bare-PCB quantity is set in the quote and was not re-read on 2026-11-20.

## Before and after ordering

1. Decide the quantity and resolve the two stock lines.
2. Upload both boards, set both-sides assembly, and make the placement-preview checks above.
3. Read the quote and record it with the date.
4. On arrival: incoming inspection, then the PD20 bench plan T1–T8 (`doc/src/content/docs/verification/pd20-verification.md`).
   The 20 V NVM image is provisioned only after it is reviewed (T4); no program-ready binary exists yet.

The readiness ledger (`manufacturing/prototype-order-readiness.md`) lists the residuals each disposition carries
into those tests.
