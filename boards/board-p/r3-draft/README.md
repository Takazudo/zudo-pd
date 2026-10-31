# Board P r3 placement draft

**Unvalidated, unrouted placement draft. Not for fabrication or ordering.** The as-built
`../board-p.kicad_pcb` is unchanged and remains the routed 15 V module.

`board-p-r3-draft.kicad_pcb` takes every footprint from the shared library named in
`scripts/schgen/board_p_spec.py`, with the spec nets. The outline, J1, JOUT1, J2, J3,
MH1–MH3 and U1 keep their as-built coordinates. R21 (RESET strap) and the D9–D12 local
clamps sit 1.65–2.49 mm (pad to pad) from their STUSB4500 pins, and each pin corridor is
a footprint/via keep-out. Rebuild with `scripts/pcb/board-p-r3-draft/run.sh`.

Fit result (`placement-report.json`): top-only placement did not fit in 40 heuristic
restarts, because C3 could not be placed. A two-sided placement fits by courtyard, with
20 small two-terminal parts on B.Cu. Routing, the assembly side, stack height and C3
height are OPEN.
