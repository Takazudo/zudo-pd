# P15 r1 prototype order: owner handoff (2026-11-20)

This is the order-day checklist for the owner. It is desk preparation only. Nothing has been ordered, quoted,
uploaded, programmed or energized, and no file below is validated, qualified or released. The full reasoning is in
the [2026-11-03 decision packet](p15-order-decision-packet.md); this page does not repeat or replace it.

## Upload exactly these P15 files from the fixed package

Package: `manufacturing/releases/corner-support-review/`. Its manifest `git_base` is
`3b9821b48cf4c77e8512ce653cada3db962d2c88`. `manifest.json` has SHA-256 `7afcef99…`, and `SHA256SUMS` has SHA-256
`a72dedec…` with 151 entries. Only the `board-p15/` files are needed for this order. Do not use zudo-pd
`boards/board-p/` (20 V Board P r3) or the LED repository's historical `boards/board-p/`.

| File | Use | SHA-256 |
| --- | --- | --- |
| `board-p15/board-p15-gerbers.zip` | PCB upload | `e68a133e2a3fa610758ed0e183fb9c4e77e4a4bfff7a9a6bac5cd1ab7f8c14ae` |
| `board-p15/bom.csv` | Assembly BOM | `23d6e2902307ce3920c405abe3296600610bcd5b54f0cca67ee0a8291ecfd59f` |
| `board-p15/cpl.csv` | Assembly CPL | `a9116d1b9f1d7f092531173a7c8f4d49f4a4c282b9a88f449a89b0da3e030ce6` |
| `board-p15/excluded.csv` | Review only, not uploaded: DNP D6/D7/R17/R18, bare pads J2/J3 | `16d6146bd3ca6f3fbca8adbc4ddcddb176659dcd5d016a27a699b41467e9f616` |
| `boards/board-p15/nvm/stusb4500-15v.bin` | Not uploaded; NVM desk image for bench provisioning | `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` |

Run from the repository root:

```sh
python3 scripts/pcb/board-p15/verify-shared-reference.py --rev HEAD   # or the exact commit you order from
(cd manufacturing/releases/corner-support-review && sha256sum -c SHA256SUMS)
```

The first command confirms that the P15 PCB, spec, NVM image and population files at that revision match
[`boards/board-p15/shared-reference.json`](../boards/board-p15/shared-reference.json). It is a byte-identity check
only. Its frozen-lock line reports later repository changes as information. The fabrication paths (PCB, spec, NVM)
must match. In a **shallow clone**, the adoption-ancestry line can print FAIL because Git cannot see the history.
Check that line in a full clone, or with `gh api repos/Takazudo/zudo-pd/compare/4a0741f...<commit>`
(`status: ahead`, `behind_by: 0`).

In a working tree without the local-only STEP, `sha256sum -c` passes 150 of 151 entries. The 151st is
`mechanical/assembly/populated-stack.step` (158,591,651 bytes, SHA-256
`b2d5d8da200c4f4e989e33d4190912054475fb17d601f2f76c0b347ab3508167`), which cannot be read. The P15 upload check
does not need that file. Full historical replay (151/151 plus the unmodified `verify-jlcpcb.py` with its source locks)
requires the original STEP and a tree matching the frozen locks. Without them, report it as **NOT RUN**. Do not
regenerate a replacement or refresh the locks.

## Set the JLC order to these values

| Setting | Value | Source |
| --- | --- | --- |
| Layers | 2 | Gerber job `LayerNumber`, manifest `copper_layers` |
| Size | 27 × 40 mm (Gerber outline 27.05 × 40.05) | Package notes, Gerber job |
| Material, thickness | FR-4, 1.6 mm | Gerber job `BoardThickness` |
| Outer copper | 35 µm (1 oz) | Gerber job stackup |
| Solder mask colour | **Black** (owner preference). Check that the quote keeps it, and record any price or lead-time change | Owner preference; not in the package |
| Surface finish, silk colour | Not fixed by the package; choose in the quote | Gerber job `Finish: None` |
| Assembly | **Top side only**, 2 assembled sets (PCBA minimum, owner rule 2026-11-03); 23 placements per board | `cpl.csv` (all Top) |
| Through-hole | JOUT1 (PZ254V-11-06P) needs through-hole soldering. J1 has 4 THT shell tabs | PCB pads |
| Bare-PCB quantity | Set in the quote. The quote's minimum was not re-read on 2026-11-20 | — |
| CPL handling | Native KiCad rotations with a common origin. Do not negate Y | Package notes |

## Check the placement preview against the polarity list

The full per-part list (BOM lines, CPL rows, pad nets) is in [`placement-checklist.md`](verification/p15-order-refresh-20261120/placement-checklist.md). JLC places parts
with its own library footprints, so local agreement does not prove the placed orientation.

| Ref | Part | Must show |
| --- | --- | --- |
| **D5** | SMAJ16A C74561 | Cathode stripe on the VBUS_IN pad (pad 1, x = 20.45, smaller X) |
| **D9** | BZT52C18 C192739 | Cathode band on the VDD_LOC pad (pad 1, x = 17.325, smaller X) |
| U1 | STUSB4500QTR C2678061, rotation 180 | Pin-1 mark at the upper-right corner (toward J1, larger X) |
| Q1 | AO3401A C347476, rotation 90 | Gate and source leads toward J1; the single drain lead away from J1 |
| J1 | TYPE-C-31-M-17 C283540, rotation 180 | Receptacle opening at the board edge |
| JOUT1 | PZ254V-11-06P C492405, rotation 0 | Top side; pin 1 (VBUS_OUT) at the left (smaller X) |

If D5 or D9 is reversed, stop and correct it in JLC's tool. Do not edit the frozen package. Also confirm the following:

- No DNP part from `excluded.csv` is added.
- Every BOM line is matched to the exact LCSC code, with no substitutes.
- The final quote total is recorded.

## Parts are in stock on 2026-11-20; re-check on the order day

The data comes from a read-only lookup of each exact code, retrieved 2026-11-20 between 09:57:03Z and 09:57:20Z. It
used the JLC parts search endpoint
`https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` and LCSC
`https://www.lcsc.com/product-detail/<code>.html`. Unit prices are the lowest-quantity tier in USD. No line is below
the purchase quantity, and every model matches its BOM comment. None is flagged JLC "preferred".

| LCSC | Part | Qty for 2 boards | JLC library | JLC stock | JLC unit | LCSC stock | LCSC min buy | LCSC unit |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| C21189 | 0603WAF0000T5E | 6 | Basic | 15,694,342 | 0.0021 | 6,674,100 | 100 | 0.0021 |
| C21190 | 0603WAF1001T5E | 2 | Basic | 29,838,292 | 0.0016 | 4,178,500 | 100 | 0.0016 |
| C25803 | 0603WAF1003T5E | 6 | Basic | 13,173,279 | 0.0029 | 4,049,900 | 100 | 0.003 |
| C22807 | 0603WAF1503T5E | 2 | Basic | 800,782 | 0.0017 | 291,700 | 100 | 0.0017 |
| C23179 | 0603WAF4700T5E | 6 | Basic | 4,115,437 | 0.0019 | 1,424,200 | 100 | 0.002 |
| C14663 | CC0603KRX7R9BB104 | 4 | Basic | 53,624,762 | 0.0055 | 674,000 | 100 | 0.0055 |
| C15849 | CL10A105KB8NNNC | 6 | Basic | 11,753,651 | 0.0092 | 483,400 | 50 | 0.0093 |
| C13585 | CL31A106KBHNNNE | 2 | Basic | 4,072,626 | 0.1223 | 429,840 | 10 | 0.1238 |
| C347476 | AO3401A | 2 | Extended | 1,160,858 | 0.0317 | 1,138,100 | 20 | 0.0321 |
| C192739 | BZT52C18-7-F | 2 | Extended | 6,328 | 0.1292 | 6,255 | 5 | 0.1306 |
| C492405 | PZ254V-11-06P | 2 | Extended | 70,725 | 0.043 | 70,500 | 20 | 0.0435 |
| C74561 | SMAJ16A | 2 | Extended | 4,492 | 0.1461 | 4,195 | 5 | 0.1468 |
| C2678061 | STUSB4500QTR | 2 | Extended | 6,249 | 2.8335 | 6,001 | 1 | 2.8672 |
| C283540 | TYPE-C-31-M-17 | 2 | Extended | 9,403 | 0.1987 | 8,960 | 5 | 0.201 |

The table has 14 lines: 8 Basic and 6 Extended.

## Catalog estimate: about USD 40–43 for parts and assembly; PCB fabrication and shipping are unknown

This is a **catalog estimate, not a supplier quote**. It uses the retained fee model (`board_cost()` in
`scripts/pcb/calculate-lineup-cost.py`) with the 2026-11-20 catalog rows. The fee table is the retained
2026-10-31 extract. On 2026-11-20 the fee page (`https://jlcpcb.com/help/article/pcb-assembly-price`) still
read "Last updated on Oct 22, 2026", with the same Economic and Standard values.

| Item | USD | Basis |
| --- | ---: | --- |
| Components, 2 boards | 7.13 | Each line bought at max(need, first tier) |
| Components, with JLC attrition and minimum buy | 9.72 | `lossNumber` + `leastPatchNumber` from the JLC rows. The field meaning is not publicly documented |
| Economic PCBA setup | 8.18 | Fee page |
| Stencil (Economic) | 1.53 | Fee page |
| Extended-part feeder loading, 6 × 3.07 | 18.42 | Fee page |
| SMT joints, 72 × 2 × 0.0016 | 0.23 | Pad count |
| Manual THT joints, 10 × 2 × 0.0164, and hand-soldering labour 3.58 | 3.91 | Pad count: JOUT1 6 pins and the J1 shell 4 |
| Confirm parts placement | 0.45 | Fee page |
| **Parts and assembly** | **39.85 to 42.44** | Economic PCBA; the Standard single-side model gives 74.71 for assembly |
| PCB fabrication | **UNAVAILABLE** | The quote page is rendered client-side; the server HTML shows "$0.00" without login or upload |
| Shipping, duty | **UNKNOWN** | Needs a destination and the quote calculator |

The model does not include possible JLC options such as pre-reflow THT soldering ($0.016 per joint), X-ray or
packing. The historical USD 39.94 figure (2026-11-03 snapshot) is superseded by this estimate. It is not a quote
either.

## Order two assembled P15 and reuse the existing boards

| Item | Quantity | Source |
| --- | --- | --- |
| P15 r1, assembled (PCBA) | **2** | New. The JLCPCB PCBA minimum is 2 sets (owner rule 2026-11-03) |
| Board L | 0 new | Reuse the two 2026-09-19 boards (RS1 200 mΩ, MCU believed blank) |
| Board B | 0 new | Reuse the 2026-09-20 S3 board; its count and condition are not yet recorded |

There is no spare: the first P15 that passes NVM acceptance is also an LED unit. The PD15 build receives an accepted
P15 after the LED stack.

## Still NOT RUN or unavailable

- **Full historical package replay:** the original local-only `populated-stack.step` is absent.
- **Supplier quote, placement preview, order, delivery:** these are owner actions. No cart, upload or quote was made.
- **PCB fabrication price and shipping:** see the estimate above.
- **P15 programming and acceptance (P15-NVM-1 to -7):** no hardware.
- **Accepted residuals:** R2.3, R2.4 and R2.6 FAIL, and R2.5 UNKNOWN (no hardware voltage window or eFuse). These
  stay accepted prototype residuals, not passes.

## Run the arrival tests in this order (all NOT RUN)

1. **Incoming, unpowered, each unit:** D5 stripe and D9 band against the silk, U1 and J1 seating, and no bridges
   at U1.
2. **NVM provisioning:** use a current-limited 5 V-only source, with Board L and Board B disconnected. Run
   P15-NVM-1 to -5 and -7 in
   [Board P15 NVM Programming](../doc/src/content/docs/architecture/board-p15-programming.md). Pass is a power-cycle
   readback equal to SHA-256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`.
3. **No-load PD acceptance (P15-NVM-6):** use a PD source that also offers 20 V. Pass is a 15 V contract, with
   VBUS_OUT measured off during the 5 V phase of attach. The bit position is now supported by an official ST GUI export pair
   (`dec-pd20-nvm-power-only-gui`), but a programmed part's behavior is still only shown by this measurement.
4. **Mating:** only then mate a passing unit with a Board L or, later, with Board B.
   - Board L: complete zudo-led-lamp `firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md` first.
   - Board B: complete its unpowered check ([`manufacturing/board-b-unpowered-check.md`](board-b-unpowered-check.md))
     first. PD15 staged bring-up follows
     [renewal-bring-up](../doc/src/content/docs/verification/renewal-bring-up.md).

Record each result with the unit identity in the
[current-state page](../doc/src/content/docs/project/current-state.md).

## Read-only refresh — 2026-11-20

Commands, run on PD20 PR #307's merged head `dc1df18` in a shallow clone, with the following results (evidence in [`verification/p15-order-refresh-20261120/`](verification/p15-order-refresh-20261120/)):

- **`verify-shared-reference.py --rev HEAD`:** all 7 artifacts MATCH. The frozen source lock is 452/498 unchanged; the
  46 changes are not fabrication paths. The adoption-ancestry FAIL is a shallow-clone artifact: GitHub compare
  `4a0741f...9312dc6` returns `ahead`, `behind_by` 0.
- **`sha256sum -c SHA256SUMS`:** 150 OK, 0 mismatches, and 1 unreadable (the local-only STEP).
- **Board-p15-only, non-replay subset of the `verify-jlcpcb.py` checks:** PASS. Run with gerbonara, it covered BOM
  against the spec, CPL against BOM, CPL coordinates, side, rotation and LCSC against the package source PCB,
  DRC/ERC with 0 errors and 0 unconnected, ZIP integrity and equality with `gerbers/`, the Gerber and drill parse,
  2 copper layers plus PTH and NPTH, a 27.05 × 40.05 mm outline, and the HEAD PCB equal to its lock.

Hashes:

- **Files:** all four upload and review hashes above match, and so does the NVM image.
- **Lookups:** the 2026-11-20 lookups found no stock shortfall.

## Read-only refresh — 2026-11-22

On `main` `edfd690`, in a full clone (evidence in [`verification/pd20-order-day-20261122/p15/`](verification/pd20-order-day-20261122/README.md)):

- **`verify-shared-reference.py --rev HEAD`:** SOURCE IDENTITY MATCH, all 7 artifacts, with no ancestry error.
- **`sha256sum -c SHA256SUMS`:** 150 OK, 0 mismatches, 1 unreadable (the local-only STEP). The four `board-p15/` files
  and the NVM image (`76622e14…`) match the table above.
- **Board-p15 non-replay subset:** PASS, all 13 checks.
- **JLC lookups, 06:13:47–06:14:01 UTC:** all 14 lines found. Each has stock above two boards plus `lossNumber`, and
  no `minPurchaseNum` or `leastPatchNumber` above stock.

Full historical replay stays NOT RUN.
