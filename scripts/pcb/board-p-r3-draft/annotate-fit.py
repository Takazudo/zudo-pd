"""Add the fit verdict and OPEN items to boards/board-p/r3-draft/placement-report.json (last step of run.sh).

The DRC summary records the KiCad 10.0.6 result for the committed draft; re-run DRC after any rebuild.
"""
import json, sys
O = sys.argv[1].rstrip('/') + '/'
r = json.load(open(O + 'placement-report.json'))
top = json.load(open(O + 'search-top-only.json')); two = json.load(open(O + 'search-two-sided.json'))
r['status'] = ('UNVALIDATED DRAFT, PARTLY ROUTED (power-path pours and ground only; signal nets unrouted). Not for fabrication '
               'or ordering. The as-built boards/board-p/board-p.kicad_pcb is unchanged.')
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
 "native_drc_kicad_10_0_6_after_power_pass": {
  "courtyard_overlap": 0,
  "clearance_or_shorting_errors": 0,
  "items_not_allowed": "6, all the protected owners themselves (U1, R21, D9-D12) touching their own pin-corridor keep-outs",
  "unconnected_items": 72,
  "unconnected_before_power_pass": 133,
  "unconnected_power_nets": "17 (VBUS_IN 8, VBUS_P 6, VBUS_OUT 2, EF_IN 1): B.Cu decoupling, divider, clamp and sense branches and J3.4; the F.Cu 5 A path J1 -> D5/Q3 -> U2 -> C3/Q1 -> JOUT1 is connected",
  "other": "silk/text-height and 3 lib_footprint_issues warnings only; see routing-report.json"
 },
 "open": [
  "Signal nets, the B.Cu power branches and J3.4 are unrouted; no thermal, loop-inductance or ground-return review exists. The 5 A width uses IPC-2221 at an assumed 20 C rise (PA).",
  "Two-sided assembly changes the JLCPCB assembly scope; not decided here.",
  "B.Cu faces the enclosure floor in the installed stack (P is below B); bottom parts add to the 12.7 mm P envelope against the 18 mm printed-leg seating height. Part heights are not in the bundles.",
  "C3 RVT1H101M0810 is 10.2 mm nominal (8 x 10.2 series row of the retained datasheet; tolerance not stated) against the 11.1 mm nominal plane gap, and its mapped footprint on Board B touches the U3 TO-263 courtyard corner; stack check OPEN.",
  "The library 0603 courtyard (3.37 x 1.91 mm) is larger than the as-built embedded lands; using compact lands would change geometry and needs layout review."
 ]
}
fit['top_only'].update(restarts=top['restarts'], best_unplaced=top['unplaced'])
fit['two_sided'].update(restarts=two['restarts'], bottom_side=two['bottom'])
fit['courtyard_utilisation_of_board_less_hole_courtyards'] = r['area_mm2']['utilisation_of_board_less_holes']
r['fit'] = fit
open(O + 'placement-report.json', 'w').write(json.dumps(r, indent=1) + '\n')
