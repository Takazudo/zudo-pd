# P15 r1 in the LED enclosure stack: CAD fit check (2026-11-03)

Desk CAD check for the current path (zudo-pd P15 r1 + the two existing Board Ls). Nothing was printed, built or
measured. Nominal datums only: 5 mm Board P supports, 11 mm board gap.

## Inputs

| Input | Identity |
| --- | --- |
| LED repo | `cfc8cb4` (`enclosure/generate.py` sha256 `926d5757…`, `boards/board-l/board-l.kicad_pcb` sha256 `1d9dc7a7…`) |
| P15 PCB | zudo-pd `boards/board-p15/board-p15-draft.kicad_pcb`, sha256 `97acc5f4…`, a path in the P15 package source lock (`git_base` `3b9821b`) |
| 3D models | zudo-pd `footprints/kicad/zudo-pd.3dshapes/` STEP siblings |
| KiCad | 10.0.6, pinned image `kicad/kicad@sha256:18693567…` |

## Method

1. `git archive` of the LED repo into a scratch directory; the P15 PCB copied over `boards/board-p/board-p.kicad_pcb`
   and the zudo-pd model folder copied beside the LED one. The tracked enclosure outputs in this repository were not
   regenerated.
2. `uv run enclosure/generate.py` in that copy, with `kicad-cli` resolving to the pinned image. Result:
   [`generator-run.json`](generator-run.json).
3. [`board-to-board-check.py`](board-to-board-check.py): the generator does not test Board P bodies against Board L
   bodies, so this script exports both boards' populated STEP the same way, places them at the generator datums
   (Board P bottom 13.4 mm, Board L bottom 26.0 mm), screens every P15 body against every Board L body by bounding
   box, and intersects the overlapping pairs exactly. Result: [`board-to-board-result.json`](board-to-board-result.json).

## Results

| Check | Result |
| --- | --- |
| Generator assertions (outline, three Ø3.2 holes, J1 at (13.506, 5.0, 180°), shared pillar holes) | PASS |
| `check_stack` (JOUT1 ↔ J2 six-pin alignment; RV1/SW2 courtyards clear of Board P + 1 mm) | PASS |
| Printed parts against every P15 and Board L STEP body | PASS, 65 pairs checked, maximum 0.0 mm³ |
| USB plug corridor | Open in CAD; real plug seating unverified |
| P15 bodies against Board L bodies | Only JOUT1 ↔ J2 overlap (1.79 mm³): the intended header-into-socket mate. No other pair overlaps |
| Tallest P15 bodies below Board L | JOUT1 (mating), then J1 USB-C at 7.84 mm, D5 SMAJ16A at 8.91 mm below the Board L bottom face |

Status: CAD PASS at nominal datums. Physical fit, header seating depth and the real board gap are NOT RUN.
