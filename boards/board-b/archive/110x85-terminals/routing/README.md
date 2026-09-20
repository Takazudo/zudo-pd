# Terminal revision routing

The active PCB is 110 ×85 mm with two C8465 screw-terminal blocks and a plain
rectangular edge. The four output rails keep their existing protection and load
budgets. J6.1=GND, J6.2=−12 V; J7.1=+5 V, J7.2=+12 V. Both blocks are on top,
rotated 90 degrees so their wire entries face left and pin2 is above pin1.

The archived guarded PCB supplies the reviewed power-stage placement and routing.
`update-output-terminals.py` accepts only that exact input hash, replaces the four
Faston footprints with two terminal footprints, replaces only their 12 outgoing
track segments with three 1 mm routes, restores a plain outline and places new
polarity markings. J6 ground joins both connected ground pours. Regulator loops,
thermal vias, feedback routing and the central ground stitches are preserved.

With KiCad 10's bundled Python (`pcbnew` and `wx`):

```sh
python3 scripts/pcb/update-output-terminals.py boards/board-b/archive/110x85-guarded/board-b.kicad_pcb tmp/terminal-new.kicad_pcb
python3 scripts/pcb/place-assembly-labels.py tmp/terminal-new.kicad_pcb tmp/terminal-labelled.kicad_pcb --project-dir boards/board-b --report tmp/terminal-labels.json
```

Use the current `.kicad_pro` beside temporary copies for DRC. After promotion,
restore explicit net classes with `configure-board-b.py`, refill/save copper, and
run native DRC with schematic parity in the active Board B project. Require
`verify-board-b.py` and `verify-power-layout.py` on that final filled board.

The retained `placement.kicad_pcb`, DSN and SES are historical routing inputs for
the guarded power-stage layout, preserved in `../archive/110x85-guarded/routing/`.
For a fresh route, `place-board-b.py` generates the current terminal placement,
`prepare-routing.py` applies explicit routing classes, and `finish-board-b.py`
imports a new session and adds pours. It never applies a previous session's
special completion paths. A new route requires the complete native and geometry
checks; a router's completion claim is insufficient.
