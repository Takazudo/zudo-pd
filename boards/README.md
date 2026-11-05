# Board projects

| Stream | Active PCB | Connectivity / inventory owner |
| --- | --- | --- |
| Shared P15 input | `board-p15/board-p15-draft.kicad_pcb` | `scripts/schgen/board_p15_spec.py` |
| PD15 conversion | `board-b/board-b.kicad_pcb` | `scripts/schgen/board_b_spec.py` |
| PD20 input r3 | `board-p/board-p.kicad_pcb` | `scripts/schgen/board_p_spec.py` |
| PD20 four-layer conversion | `board-b20-draft/board-b20-draft.kicad_pcb` | `scripts/schgen/board_b20_spec.py`; inventory `board_b20_components.py` |
| Historical Board A | `board-a/` | `scripts/schgen/board_a_spec.py` |

Valid pairs are **board-p15 + board-b** and **board-p + board-b20-draft**.
P15 is shared LED-first input hardware, not another product. Current `board-p` is 20 V r3;
the retired 15 V PCB remains in Git at `6cb02c8`. Root combined-board v0.4.0 is historical.

Use [current state](../doc/src/content/docs/project/current-state.md),
[board contract](../doc/src/content/docs/architecture/board-contract.md) and
[release gates](../doc/src/content/docs/architecture/release-readiness.md).
Received S3 Board B is distinct from development source; PD-specific retired P was never built.

## Generated schematics

Edit executable specs and regenerate only the intended board. See [hardware workflow](../doc/src/content/docs/project/hardware-workflow.md)
and `scripts/schgen/README.md`. The inventory provider has five inputs A/B/P/P15/B20; the pure-Python schematic
regeneration gate covers A/B/P/P15. PCB layouts remain separate review owners.

## Libraries resolve from each board directory

Open each paired `.kicad_pro` with its board-local library tables. For projects two levels below root,
shared paths use `${KIPRJMOD}/../../symbols/zudo-pd.kicad_sym` and
`${KIPRJMOD}/../../footprints/kicad/zudo-power.pretty`. Active models use
`${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/`. Export snapshot paths are rebased for their deeper location;
do not copy them into active boards. Merge only intended symbols into the shared library.

## Connector and mounting changes

[PD15](../doc/src/content/docs/architecture/pd15.md) and [PD20](../doc/src/content/docs/architecture/pd20.md)
own interfaces and scope. B20 P1 is NC/PDOK/GND/NC; PD15 retains ATT. Shared mechanical positions do not imply
electrical interchangeability. Assembly previews and support/model reports retain revision-specific evidence;
nominal geometry does not establish physical fit.
