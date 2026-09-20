# Front-stack routing

The active PCB is 110 × 85 mm. J5 is on the front at (37.7,12.9),270 degrees.
Board P faces Board B with P(x,y) mapping to B(y,x); its nominal CAD face plane is
11.1 mm above B. In the installed orientation B faces down on legs and its back
silkscreen is visible from above. Nominal CAD spacing is not a qualified spacer.

C5 moves to (7,34). J6/J7 move to (7,48)/(7,61), and R1/R2 move 0.5 mm to the
right for the front header courtyard. The input feed and affected terminal/
status/test-point routes are replaced; conversion-stage loops, thermal vias and
central ground stitching remain. New full input routes are at least 1.5 mm; load
output routes remain at least 1 mm. The TP5 measurement branch is 0.25 mm and is
excluded from all current-path proofs.

The source snapshot in `../archive/110x85-terminals/` also preserves the user's
interim C36/C37 reference placement, top TP legend and backside rev1 marking.
`update-front-stack.py` accepts only that exact input SHA and applies the reviewed
placement, routes, PTC model-node corrections and two-sided terminal labels.

With KiCad 10's bundled Python (`pcbnew` and `wx`):

```sh
python3 scripts/pcb/update-front-stack.py boards/board-b/archive/110x85-terminals/board-b.kicad_pcb tmp/front-stack-new.kicad_pcb
```

Copy the active `.kicad_pro` beside a temporary PCB after generation, because a
native pcbnew save can reset project defaults. Refill and check the candidate,
then promote only after native DRC and mechanical/power checks pass. Run parity
against the actual matching schematic and project. Use `configure-board-b.py`
after native project changes to restore the reviewed routing/manufacturing rules.

For a fresh route, `place-board-b.py` generates current placement,
`prepare-routing.py` applies explicit net classes, and `finish-board-b.py`
imports the new session and adds pours. Do not apply a prior session's special
completion paths. Every new route requires native and geometry checks.

The old Faston and underside-terminal scripts/inputs are historical and remain
in their matching archive directories. They do not describe the active layout.
