# P15 r1 first prototype order: decision packet (2026-11-03)

This packet gathers what the owner needs to decide the first P15 r1 prototype order for the LED lamp (with the two
existing Board Ls) and for the 15 V zudo-pd (with Board B). It is desk work only. Nothing was ordered, quoted,
uploaded, programmed or energized. Every hardware row stays NOT RUN until a bench result exists.

## Order the fixed-revision package as is; it verifies in full with the original STEP

| Item | Value |
| --- | --- |
| Package | `manufacturing/releases/corner-support-review/` (development review files, not an order) |
| Source revision | manifest `git_base` `3b9821b`; sources unchanged through `6cb02c8` and `5a21ab9` |
| `manifest.json` sha256 | `7afcef99c3a0b0e83a8321aef4aca7a68fd13b901e087804d5931b2c866e13bb` |
| `SHA256SUMS` sha256 | `a72dedecc3b928870ee2eff4717521c96f70492610ad05fcf0c7ed6ba7ec27ac` (151 entries) |
| Source lock | board-p15 498 + Board B 622 paths, 0 mismatches at `5a21ab9` |
| NVM image | `boards/board-p15/nvm/stusb4500-15v.bin` sha256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` (PDO2 15 V / 3 A); desk image, never written |
| Local-only STEP | `populated-stack.step`, 158,591,651 bytes, sha256 `b2d5d8da200c4f4e989e33d4190912054475fb17d601f2f76c0b347ab3508167`, the original bytes, recovered unchanged from the session that exported them |

The package is a **fixed-revision snapshot**. It is verified at its own `git_base`, not at whatever HEAD the 20 V work
reaches later. If a package from a later HEAD is ever wanted, that is one new export at that HEAD, verified again.

Checks run on 2026-11-03 at `6cb02c8`/`5a21ab9` with the original STEP in place:

| Check | Result |
| --- | --- |
| `sha256sum -c SHA256SUMS` | PASS, 151/151 |
| `verify-jlcpcb.py` (unmodified, `--out` outside the package) | PASS for both boards: identity, coordinates, hashes, Gerber/drill parse |
| Manifest source lock against the tree | PASS, 498/622 match |
| `validate.py --strict` | PASS (128 lines, 16 candidates, 41 bundles) |
| `check_forward_tests.py --strict` | PASS |
| `check_decisions.py` | PASS (35 decisions, 269 refs) |
| `nvm-image.py --check` | PASS (file regeneration only, not a readback) |
| `circuit/scripts/run-python-gates.sh` (after the B20 courtyard cherry-pick) | PASS |

Earlier package results are kept, not repeated: fab content equals the earlier export apart from KiCad timestamps
(`manufacturing/readiness/p15-package-equivalence.json`), and DRC/ERC/parity are as recorded in the manifest
(board-p15 DRC 0 errors / 0 unconnected; Board B 0 / 0).

No output outside the approved package is needed for this order.

## P15 fits the LED enclosure and Board L stack in CAD

Run: the LED enclosure generator (`enclosure/generate.py`, LED `cfc8cb4`) in an isolated copy whose
`boards/board-p/board-p.kicad_pcb` is replaced by `boards/board-p15/board-p15-draft.kicad_pcb`
(sha256 `97acc5f4…`, a locked source), with the zudo-pd 3D models. KiCad 10.0.6 pinned image for the STEP exports.
The tracked LED outputs were not touched.

| Check | Result |
| --- | --- |
| Outline, three Ø3.2 holes, J1 (13.506, 5.0, 180°) and the shared pillar holes | PASS (generator assertions) |
| `check_stack`: JOUT1 ↔ Board L J2 six-pin alignment, RV1/SW2 courtyards clear of Board P + 1 mm | PASS |
| Every printed part against every P15 and Board L populated STEP body | PASS: largest intersection 0.0 mm³ (limit 0.02) |
| USB cable corridor (16 × 8 mm overmold, 8.4 × 2.6 mm nose) | PASS (open in CAD; real plug seating unverified) |
| P15 bodies against Board L bodies (separate board-to-board script) | PASS: the only overlap is JOUT1 into Board L J2 (1.79 mm³, the intended mate). Next tallest: J1 at 7.84 mm and D5 at 8.91 mm below Board L |

These are CAD results with nominal datums (11 mm board gap, 5 mm Board P supports). Printing, real seating and
screw fit remain unmeasured.

Evidence and scripts: zudo-led-lamp `candidates/p15-r1-enclosure-fit/`.

## D5 and D9 orientation is consistent locally; JLC's preview is still the check that counts

`manufacturing/readiness/p15-first-placement-orientation.json` records, per part, the CPL row, the pad nets, the
footprint marks, the 3D model mark and the owner pin map.

| Ref | Part | Local result | At the order step, confirm in JLC preview |
| --- | --- | --- | --- |
| board-p15 D5 | SMAJ16A C74561 | PASS: stripe, pad 1 and VBUS_IN agree | stripe on the VBUS_IN pad (smaller X) |
| board-p15 D9 | BZT52C18 C192739 | PASS: band, pad 1 and VDD_LOC agree | band on the VDD_LOC pad (smaller X) |
| Board B C11 | RVT1E471M0810 C696190 | PASS for footprint and pin map; model has no polarity mark | only if new Board Bs are assembled: + / chamfers on the GND pad |

JLC places with its own library footprint, so local agreement does not prove the placed orientation.

## Quantities: two P15 for LED, P15 for zudo-pd, and new Board Bs only if needed

The old "5 sets" figure was a cost basis, not a requirement. Needs per use:

| Use | Reused (on hand) | New |
| --- | --- | --- |
| LED lamp | 2 Board L from the 2026-09-19 order, unchanged (RS1 200 mΩ, MCU believed blank) | 2 × P15 r1 (one per Board L). The old LED Board Ps (#144) are not part of this path |
| 15 V zudo-pd | Board B from the 2026-09-20 order (S3 BOM), **count and condition not recorded here**; needs the D1 unpowered check first | 1–2 × P15 r1 for the first sets; new Board Bs only if more sets are wanted or the C11/R21/R27 substitute rows must be tested |
| Spare / first-article | — | 1 × P15 r1 to run the NVM procedure first and to keep for a destructive or repeat test |

Read-only catalog refresh 2026-11-03 19:12Z (`manufacturing/readiness/jlc-snapshot-2026-11-03-p15.json`, priced
by `scripts/pcb/p15-order-scenarios.py`). Parts plus assembly only; PCB fabrication, its minimum quantity, shipping
and duty are UNKNOWN. The assembly fee page still reads "Last updated on Oct 22, 2026".

| Scenario | P15 assembled | New Board B | Parts + assembly (USD) |
| --- | --- | --- | --- |
| A: LED only | 2 | 0 | 39.94 |
| **B: LED + zudo-pd on existing Board B (recommended)** | 5 | 0 | **51.62** |
| C: as B, plus 2 new Board B | 5 | 2 | 246.33 |
| D: reference, the old 5 sets | 5 | 5 | 357.84 |

Going from 2 to 5 assembled P15 adds about USD 11.7, because the Economic PCBA setup dominates.

Stock on the refresh date: every P15 line covers 5 boards (lowest: TYPE-C-31-M-17 C283540 at 1,165). For new Board
Bs, RT0603BRD0733RL C861332 (R24) has **10** and RT0603BRE07158KL C861679 has **12**: enough for 2 boards, not much
more. Re-check stock on the order day.

## First acceptance tests, in order (all NOT RUN)

1. **Incoming, unpowered (each P15):** D5 stripe and D9 band against the silk, U1 and J1 seating, no bridges at U1.
2. **NVM on a 5 V-only, current-limited source, Board L and Board B disconnected:** P15-NVM-1 to P15-NVM-5 and
   P15-NVM-7 (`doc/src/content/docs/architecture/board-p15-programming.md`). Pass = power-cycle readback equals
   `76622e14…`.
3. **First PD attach, no load (P15-NVM-6):** a PD test source that also offers 20 V. Pass = 15 V contract, VBUS_OUT off
   at 5 V. Only after this may the unit meet a Board L or Board B.
4. **LED:** Board L checklist first (`zudo-led-lamp` `firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md`): unpowered
   checks, first energizing on a current-limited bench source, option bytes, firmware with `CTRL_FULL_CCR` 2407.
   Then mate an accepted P15 and record contract, ATT/PDOK and input current.
5. **zudo-pd:** Board B D1 unpowered check (`manufacturing/board-b-unpowered-check.md`), then the P15 + Board B stack
   with a current-limited source: startup, rail set points, ripple, load steps and thermal from `ORDER-NOTES.md`.
   BB-R/BB-C apply only to new Board Bs.
6. **Mechanical:** LED enclosure fit print with an accepted P15; Board B legs (M3 × 5 mm) for zudo-pd.

## Residuals that stay as recorded

- R2.3, R2.4 and R2.6 are FAIL and R2.5 is UNKNOWN: P15 has no hardware voltage window or eFuse. Accepted for the
  prototype; NVM acceptance on every unit is the only mitigation.
- D9 cold-knee margin (+0.01 V), STUSB4500 current during PD communication, R29/R30 derating above 70 °C, and the
  C11 150 kHz ESR stay OPEN or UNKNOWN.
- The S3 Board B copper, silk and LED2 rotation are unconfirmed until the D1 check.

## Decisions for the owner

1. **Quantity:** scenario B (5 × P15 assembled, no new Board B now), or C if new Board Bs are wanted now.
2. **Existing Board B:** how many S3 Board Bs are on hand and usable, which decides whether B is enough.

Ordering, payment, quotes, uploads, programming and energizing all stay with the owner.
