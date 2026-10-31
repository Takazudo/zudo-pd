# Board P r3 placement draft

**Unvalidated draft: power-path pours and ground only, signals unrouted. Not for fabrication
or ordering.** The as-built
`../board-p.kicad_pcb` is unchanged and remains the routed 15 V module.

`board-p-r3-draft.kicad_pcb` takes every footprint from the shared library named in
`scripts/schgen/board_p_spec.py`, with the spec nets. The outline, J1, JOUT1, J2, J3,
MH1–MH3 keep their as-built coordinates. R21 (RESET strap) and the D9–D11 local clamps sit
1.78–2.46 mm (pad to pad) from their STUSB4500 pins and D12 5.71 mm, and each pin corridor is
a footprint/via keep-out. Rebuild with `scripts/pcb/board-p-r3-draft/run.sh`.

Phase 11 floorplan (`floorplan.json`): the power-path parts are pre-placed along one chain,
J1 VBUS → D5 / Q3 (U3 beside) → U2 → VBUS_P to C3 and Q1 → VBUS_OUT to JOUT1.1/.2, and the 5 A
corridors are reserved. U1 moves 2.67 mm right of its as-built x so VBUS_P can pass on its left.

Fit result (`placement-report.json`): top-only placement still does not fit (best of 25 heuristic
restarts leaves 20 small parts unplaced; C3 cannot go to B.Cu, and no evidenced lower-profile
100 µF / 50 V part was found). The two-sided placement fits by courtyard, with 26 small two-terminal
parts on B.Cu. A heuristic miss is not a proof of infeasibility.

Routing (phase 11, `route-power.py`, `routing-report.json`): the power path is F.Cu copper pours of
VBUS_IN, EF_IN, VBUS_P and VBUS_OUT, with full-board GND pours on both layers and 80 stitching
vias. The width rule is IPC-2221 external layer, 1 oz (35 µm, board stackup), 5 A at an assumed
20 °C rise: 1.81 mm minimum. Every sampled corridor cross-section has a single filled run of
2.0–4.7 mm. Native KiCad 10.0.6 DRC: no clearance or courtyard errors; 72 unconnected items (133
before the pass), 17 of them on power nets (B.Cu decoupling, divider, clamp and sense branches
and J3.4). Signal nets are unrouted. Thermal, loop, ground-return, assembly-side, stack-height
and C3 height checks are OPEN.
