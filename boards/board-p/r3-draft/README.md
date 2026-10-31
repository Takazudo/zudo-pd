# Board P r3 placement draft

**Unvalidated draft: power-path and ground pours with grid-routed signals, 8 connections open.
Not for fabrication or ordering.** The as-built
`../board-p.kicad_pcb` is unchanged and remains the routed 15 V module.

`board-p-r3-draft.kicad_pcb` takes every footprint from the shared library named in
`scripts/schgen/board_p_spec.py`, with the spec nets. The outline, J1, JOUT1, J2, J3,
MH1–MH3 keep their as-built coordinates. R21 (RESET strap) and the D9–D11 local clamps sit
1.78–2.46 mm (pad centre to pin pad centre) from their STUSB4500 pins on F.Cu, and each pin
corridor is a footprint/via keep-out. D12 (DISCH) sits on B.Cu directly below U1.9 (0.05 mm in plane,
one via; phase 11: 5.71 mm on F.Cu). Rebuild with `scripts/pcb/board-p-r3-draft/run.sh`.

Phase 11 floorplan (`floorplan.json`): the power-path parts are pre-placed along one chain,
J1 VBUS → D5 / Q3 (U3 beside) → U2 → VBUS_P to C3 and Q1 → VBUS_OUT to JOUT1.1/.2, and the 5 A
corridors are reserved. U1 moves 2.67 mm right of its as-built x so VBUS_P can pass on its left.

Fit result (`placement-report.json`): top-only placement still does not fit (best of 25 heuristic
restarts leaves 20 small parts unplaced; C3 cannot go to B.Cu, and no evidenced lower-profile
100 µF / 50 V part was found). The two-sided placement fits by courtyard, with 26 small two-terminal
parts on B.Cu. A heuristic miss is not a proof of infeasibility.

Routing (`pours.json`, `route-signals.py`, `apply-tracks.py`, `route-power.py`; reports in
`routes.json` and `routing-report.json`):

- **Power path.** F.Cu pours of VBUS_IN, EF_IN, VBUS_P and VBUS_OUT. The width rule is IPC-2221
  external layer, 1 oz (35 µm, board stackup), 5 A at an assumed 20 °C rise: 1.82 mm minimum. Every
  sampled cross-section has a single filled run of 1.85–4.7 mm. The narrowest is the C3 riser beside
  U1, which carries the C3 branch, not the 5 A DC path.
- **Ground.** GND pours on both layers, 69 grid stitching vias and 2 island vias.
- **Signals.** A host-side grid router (two layers, 0.2 mm Default tracks, 0.4 mm on power-net
  branches, 0.5 mm signal vias, no rip-up, 20 ordered passes) placed 428 tracks and 44 vias.
- **DRC.** Native KiCad 10.0.6 DRC finds no clearance, short or courtyard errors. It reports 8
  unconnected items: CC1, ATT, PDOK and SCL at the U1 QFN, and four F.Cu GND islands without a via.
  No power-net connection is open (phase 11: 17).

Thermal, loop, ground-return, assembly-side and stack-height checks are OPEN.

**Stack conflict with Board B (OPEN).** Mapped onto the current Board B, C3's 8.3 × 8.3 mm base covers
B x 8.35–16.65, y 26.0–34.3 mm. That overlaps the U3 TO-263-5 courtyard (x 13.34–29.95, y 30.25–41.75)
by 3.31 × 4.05 mm, over the U3 tab.

- C3 is 10.2 mm nominal. The U3 3D model is named H4.5, a model attribute, not a datasheet fact.
  Together they exceed the 11.1 mm plane gap.
- No shift inside the Board P outline clears U3. The C3 centre would need P y ≤ 9.44 (into J1 and MH2)
  or P x ≤ 13.85 (into U1 and the power path).
- The fix is on the Board B side. Either the B20 layout keeps x 7.74–17.25, y 24.54–35.77 mm free of
  parts, or U3 on the current Board B moves at least 3.91 mm in +x (not checked against the other
  Board B parts).
