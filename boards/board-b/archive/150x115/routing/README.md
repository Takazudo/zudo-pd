# Board B routing inputs

These files preserve the placement, explicit netclass DSN and local Freerouting
session used for the renewed board. The PCB in the parent directory is the
editable final layout. The session alone is incomplete: the finishing script adds
reviewed capacitor connections, feedback clearance corrections and copper pours,
then synchronizes the final protection-diode lands and supplier fields.

With KiCad 10's bundled Python (including `pcbnew` and `wx`) and `kicad-cli`:

```sh
python3 scripts/pcb/finish-board-b.py boards/board-b/routing/placement.kicad_pcb boards/board-b/routing/board-b.ses tmp/board-b-review.kicad_pcb
kicad-cli pcb drc --refill-zones --save-board --format json -o tmp/board-b-review-drc.json tmp/board-b-review.kicad_pcb
```

The temporary-path check does not load the final project's netclasses or schematic.
Run `configure-board-b.py` and native DRC with `--schematic-parity` in the actual
Board B project before any release. The exporter repeats these checks on its
source snapshot. Use `verify-board-b.py` and `verify-power-layout.py` for the
connector, mounting, power-path and filled-copper checks.

For a new placement or routing session, review the explicit connections in the
finishing script again. They are tied to this placement. Do not reuse them after
moving components without updating and verifying the routes.
