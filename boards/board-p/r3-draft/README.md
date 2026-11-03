# Board P r3 placement draft

**Unvalidated draft: power-path and ground pours with grid-routed signals; native DRC finds no open connection, and no layout review exists.
Not for fabrication or ordering.** PD20: the routed r3 board is `../board-p.kicad_pcb`, the board the exporter's
`board-p` packages (paired only with `board-b20-draft`). The routed 15 V as-built module it replaced stays in git at
`6cb02c8`; `run.sh` reads its outline, connectors and holes from there. This folder keeps the placement inputs and the
routing and fit reports.

Native DRC with `--schematic-parity` against `../board-p.kicad_sch` (KiCad 10.0.6, PD20 rebuild): 0 errors, 0 unconnected
items, parity only `extra_footprint` MH1–MH3; warnings are silkscreen, text height, 3 library-footprint notes and 3
dangling fan-out items. The builder writes each LCSC field, marks bare-copper parts exclude-from-BOM/CPL, names the
no-connect pin nets and keeps the pin-corridor keep-outs to vias only.

The board takes every footprint from the shared library named in
`scripts/schgen/board_p_spec.py`, with the spec nets. The outline, J1, JOUT1, J2, J3,
MH1–MH3 keep their as-built coordinates. R21 (RESET strap) and the D9–D11 local clamps sit
1.78–2.46 mm (pad centre to pin pad centre) from their STUSB4500 pins on F.Cu, and each pin
corridor is a footprint/via keep-out. D12 (DISCH) sits on B.Cu directly below U1.9 (0.05 mm in plane,
one via; phase 11: 5.71 mm on F.Cu). Rebuild with `scripts/pcb/board-p-r3-draft/run.sh` (the committed placement is kept; `R3_SEARCH=1` re-runs the search).

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
- **Ground.** GND pours on both layers, 58 grid stitching vias and 1 island via. The router escapes
  GND pads to vias before the signals; join passes (up to four) then add a track or via for any GND
  cluster that `route-power.py` finds detached. Its union-find joins pours, vias, pads, track-to-track
  joints and track bodies that cross a fill. A join that
  displaces signals is kept, and the displaced nets go through rip-up again.
- **Fixed copper** (`pours.json` `tracks`/`vias`):
  - U1.7 SCL, U1.8 SDA, U1.9 DISCH and U1.11 ATT fan out to B.Cu through vias beside the QFN, because the
    VBUS_P pour had left one 0.1 mm channel for four pins.
  - U1.5 CC2DB runs between the R21 pads to a via at (13.9, 18.6).
  - U1.4 CC2 takes a via at (14.6, 20.4) in the band between R21.2 and the pins, and U1.2 CC1 steps
    right of R21.2.
  - U1.6 RESET is a straight strap to R21.1.
  - U2.7 EF_UVLO and U3.1 EF_VCAP have vias at (5.05, 14.05) and (2.2, 12.5).
  - U3.3 and U3.6 (VBUS_IN) are joined by a 0.4 mm track between the U3 rows.

  A fixed group that does not touch its net's pour joins the net only through a routed pad.
- **Signals.** The host-side grid router works on two layers. It uses 0.2 mm Default tracks, 0.4 mm on
  power-net branches and 0.5 mm signal vias. It runs 20 ordered passes, then 60 rounds of rip-up and
  reroute with congestion history and tabu; power-net branch tracks may be ripped. It placed 780 tracks
  and 85 vias, with identical join copies removed. It routes from a canonical pad order with `PYTHONHASHSEED=0`, so each seed is repeatable.
  `run.sh` runs seeds 12, 14, 16 and 20 and keeps the fewest open connections. Seed 12 leaves none.
- **DRC.** Native KiCad 10.0.6 DRC finds 0 unconnected items and no clearance, short or courtyard
  errors (phase 13: 3 unconnected; phase 12: 8; phase 11: 72). It reports these warnings:
  - The 5 `items_not_allowed` errors are the protected owners in their own corridors.
  - The fixed SCL and ATT vias raise 2 `via_dangling` warnings, because those routes stay on F.Cu.
  - 0.65 mm of the fixed CC1 stub lies beyond the routed joint, which raises 1 `track_dangling` warning.

  `route-power.py` now agrees: 0 detached GND clusters. In phase 14 it listed C34.2, R21.2 and C38.2
  as detached, which was wrong. It joined tracks only at their endpoints, so it missed the B.Cu track
  (16.95, 22.15)–(16.95, 23.25) that meets its neighbour track and touches B.Cu fill #8. Native DRC
  was right. The repeated join passes had also added 20 duplicate segments.

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
