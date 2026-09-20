# Guarded compact Board B routing inputs

These are the placement, explicit-netclass DSN and local Freerouting session for
110 × 85 mm Board B. The editable final board is `../board-b.kicad_pcb`.
The superseded layouts and routing inputs are in `../archive/110x95/` and
`../archive/150x115/`.

The placement generator includes short switching loops, wide output trunks,
negative-stage reference straps and back-copper frames around 48 thermal vias.
The finishing script imports the reviewed session, completes the low-current
negative indicator and U7 feedback branches, completes seven ground stitches,
corrects one fiducial clearance, moves the TP voltage legend clear of R20, and
adds the copper pours and edge silkscreen.
The ground screen reports aggregate and largest contiguous cross-sections; it
does not claim that the aggregate is one continuous corridor or a current rating. A session hash prevents
those placement-specific completions from silently applying to a different route.
The reference-label postprocessor moves only reference labels into nearby clear
space; its report proves that copper, models and functional markings are unchanged.

The placement rotates the separate PD board under the upper-left corner, puts
all four Fastons on the bottom facing inward, and packs the lower power stages
10 mm closer to the upper stage. Seven pogo contacts share the top edge. Three
rounded T-shaped edge notches locate the printed terminal guard; their geometry
is generated from `3dp-files/faston-cover/pcb-contract.json`.

With KiCad 10's bundled Python (including `pcbnew` and `wx`) and `kicad-cli`:

```sh
python3 scripts/pcb/finish-board-b.py boards/board-b/routing/placement.kicad_pcb boards/board-b/routing/board-b.ses tmp/guarded-unlabelled.kicad_pcb
python3 scripts/pcb/place-assembly-labels.py tmp/guarded-unlabelled.kicad_pcb tmp/guarded-labelled.kicad_pcb --project-dir boards/board-b --report tmp/guarded-labels.json
```

Run `configure-board-b.py` after native PCB saves, and run native DRC with
`--refill-zones --save-board --schematic-parity` in the actual Board B project.
The exporter repeats DRC/ERC, model availability, mechanical identity, filled
thermal copper, ground connectivity and wide load-path checks on a source copy.
A temporary-path DRC without the project configuration is not the release check.

A new placement or routing session requires review of the explicit completion
paths and its session hash. `prepare-routing.py` rejects missing/duplicated nets
and missing or narrowed power classes; the router alone does not qualify a board.
