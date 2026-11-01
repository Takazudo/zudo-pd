"""Add the fit verdict and OPEN items to boards/board-p/r3-draft/placement-report.json (last step of run.sh).

The DRC summary records the KiCad 10.0.6 result for the committed draft; re-run DRC after any rebuild.
"""
import json, sys
O = sys.argv[1].rstrip('/') + '/'
r = json.load(open(O + 'placement-report.json'))
top = json.load(open(O + 'search-top-only.json')); two = json.load(open(O + 'search-two-sided.json'))
routes = json.load(open(O + 'routes.json'))['report']
rr = json.load(open(O + 'routing-report.json'))
open_sig = routes['unrouted']
r['status'] = ('UNVALIDATED DRAFT, GRID-ROUTED WITHOUT LAYOUT REVIEW (power-path pours, ground pours and grid-routed signals; '
               f'{len(open_sig)} signal connection(s) open; route-power.py finds {len(rr["gnd_clusters_detached"])} detached GND cluster(s), '
               'see the native DRC summary under fit). '
               'Not for fabrication or ordering. The as-built boards/board-p/board-p.kicad_pcb is unchanged.')
fit = {
 "floorplan": "floorplan.json (phase 11): power-path parts pre-placed and 5 A corridors reserved; U1 moved 2.67 mm right of its as-built x.",
 "top_only": {
  "result": "DOES NOT FIT (heuristic search)",
  "note": "With the phase-11 floorplan the best restart leaves 20 small parts unplaced (phase 10 without reserved corridors: only C3). The single C3 cannot move to B.Cu and no evidenced lower-profile 100 uF / 50 V part was found. A heuristic miss is not a proof of infeasibility."
 },
 "two_sided": {
  "result": "FITS (courtyards)",
  "note": "Only two-terminal 0603/1206/SOD-123/SOD-523 parts may go on B.Cu."
 },
 "local_clamp_placement": "Phase 12: D12 (DISCH clamp) moves to B.Cu directly below U1.9 (0.05 mm pad-centre offset in plane, one via); R21 and D9-D11 stay on F.Cu at 1.78-2.46 mm.",
 "native_drc_kicad_10_0_6_after_routing": {
  "courtyard_overlap": 0,
  "clearance_or_shorting_errors": 0,
  "items_not_allowed": "5, the protected owners themselves (U1, R21, D9-D11) touching their own pin-corridor keep-outs",
  "unconnected_items": 0,
  "dangling": "3 warnings: the fixed SCL and ATT fan-out vias have no B.Cu track (their routes stay on F.Cu), and 0.65 mm of the fixed CC1 stub beyond the routed joint",
  "gnd_cluster_check_disagreement": "route-power.py's union-find still lists one GND cluster (C34.2, R21.2, C38.2) after four join passes, while native DRC reports every GND item connected; the native result is the oracle, and the disagreement is OPEN",
  "phase_13": "3 unconnected items (CC2 at U1.4, 2 GND zone items); phase 12: 8; phase 11: 72, 17 on power nets",
  "other": "silk/text-height and 3 lib_footprint_issues warnings only; see routing-report.json"
 },
 "open": [
  "Native DRC finds no open connection, but the router is a grid router with rip-up and fixed fan-outs, and its result has had no layout review. No thermal, loop-inductance or ground-return review exists. The 5 A width uses IPC-2221 at an assumed 20 C rise (PA).",
  "Two-sided assembly changes the JLCPCB assembly scope; not decided here.",
  "B.Cu faces the enclosure floor in the installed stack (P is below B); bottom parts add to the 12.7 mm P envelope against the 18 mm printed-leg seating height. Part heights are not in the bundles.",
  "C3 RVT1H101M0810 is 10.2 mm nominal (tolerance not stated) against the 11.1 mm nominal plane gap. Mapped onto the current Board B its base overlaps the U3 TO-263 courtyard by 3.31 x 4.05 mm; no shift inside the Board P outline clears it without moving J1 or MH2. The fix is a Board B side keep-out (B20 layout) or a U3 move on the current Board B; OPEN.",
  "The library 0603 courtyard (3.37 x 1.91 mm) is larger than the as-built embedded lands; using compact lands would change geometry and needs layout review."
 ]
}
fit['top_only'].update(restarts=top['restarts'], best_unplaced=top['unplaced'])
fit['two_sided'].update(restarts=two['restarts'], bottom_side=two['bottom'])
fit['courtyard_utilisation_of_board_less_hole_courtyards'] = r['area_mm2']['utilisation_of_board_less_holes']
r['fit'] = fit
open(O + 'placement-report.json', 'w').write(json.dumps(r, indent=1) + '\n')
