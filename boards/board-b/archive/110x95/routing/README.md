# Compact Board B routing inputs

These are the placement, explicit-netclass DSN and local Freerouting session for
110 × 95 mm Board B. The editable final board is `../board-b.kicad_pcb`.
The superseded 150 × 115 mm layout and inputs are in `../archive/150x115/`.

The placement generator includes short switching loops, wide output trunks,
negative-stage reference straps and back-copper frames around 48 thermal vias.
The finishing script imports the reviewed session, completes the low-current
negative indicator branch, stitches the central ground pour to the front plane,
and adds the copper pours and edge-specific silkscreen. A session hash prevents
those placement-specific completions from silently applying to a different route.
The reference-label postprocessor moves only reference labels into nearby clear
space; its report proves that copper, models and functional markings are unchanged.

With KiCad 10's bundled Python (including `pcbnew` and `wx`) and `kicad-cli`:

```sh
python3 scripts/pcb/finish-board-b.py boards/board-b/routing/placement.kicad_pcb boards/board-b/routing/board-b.ses tmp/compact-unlabelled.kicad_pcb
python3 scripts/pcb/place-assembly-labels.py tmp/compact-unlabelled.kicad_pcb tmp/compact-labelled.kicad_pcb --project-dir boards/board-b --report tmp/compact-labels.json
```

Run `configure-board-b.py` after native PCB saves, and run native DRC with
`--refill-zones --save-board --schematic-parity` in the actual Board B project.
The exporter repeats DRC/ERC, model availability, mechanical identity, filled
thermal copper, ground connectivity and wide load-path checks on a source copy.
A temporary-path DRC without the project configuration is not the release check.

A new placement or routing session requires review of the explicit completion
paths and its session hash. `prepare-routing.py` rejects missing/duplicated nets
and missing or narrowed power classes; the router alone does not qualify a board.
