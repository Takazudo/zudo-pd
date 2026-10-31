"""Add the fit verdict and OPEN items to boards/board-p/r3-draft/placement-report.json (last step of run.sh).

The DRC summary records the KiCad 10.0.6 result for the committed draft; re-run DRC after any rebuild.
"""
import json, sys
O = sys.argv[1].rstrip('/') + '/'
r = json.load(open(O + 'placement-report.json'))
top = json.load(open(O + 'search-top-only.json')); two = json.load(open(O + 'search-two-sided.json'))
r['status'] = 'UNVALIDATED PLACEMENT DRAFT, UNROUTED. Not for fabrication or ordering. The as-built boards/board-p/board-p.kicad_pcb is unchanged.'
fit = {
 "top_only": {
  "result": "DOES NOT FIT (heuristic search)",
  "restarts": 40,
  "best_unplaced": [
   "C3"
  ],
  "note": "Greedy net-affinity placement with perturbed big-first orders; 8 of 40 restarts left only C3 (100 uF, 10.77 x 9.05 mm library courtyard) unplaced, the rest left more. A heuristic miss is not a proof of infeasibility."
 },
 "two_sided": {
  "result": "FITS (courtyards, before routing)",
  "restarts": 25,
  "bottom_side": [
   "C1",
   "C2",
   "C35",
   "D6",
   "D7",
   "R12",
   "R13",
   "R14",
   "R17",
   "R18",
   "R19",
   "R20",
   "R23",
   "R24",
   "R25",
   "R27",
   "R28",
   "R29",
   "R30",
   "R31"
  ],
  "note": "Only two-terminal 0603/1206/SOD-123/SOD-523 parts may go on B.Cu; 20 of them are needed."
 },
 "courtyard_utilisation_of_board_less_hole_courtyards": 0.84,
 "native_drc_kicad_10_0_6": {
  "courtyard_overlap": 0,
  "items_not_allowed": "6, all the protected owners themselves (U1, R21, D9-D12) touching their own pin-corridor keep-outs",
  "unconnected_items": 131,
  "other": "silk/text-height and lib_footprint_issues (library not resolved inside the DRC container) only; no copper rule run is meaningful before routing"
 },
 "open": [
  "Routing not started: no copper, clearance, current-capacity, thermal or ground-return check exists.",
  "Two-sided assembly changes the JLCPCB assembly scope; not decided here.",
  "B.Cu faces the enclosure floor in the installed stack (P is below B); bottom parts add to the 12.7 mm P envelope against the 18 mm printed-leg seating height. Part heights are not in the bundles.",
  "C3 RVT1H101M0810 height is not a bundle fact; it faces Board B across the 11.1 mm nominal plane gap and needs a stack check.",
  "The library 0603 courtyard (3.37 x 1.91 mm) is larger than the as-built embedded lands; using compact lands would change geometry and needs layout review."
 ]
}
fit['top_only'].update(restarts=top['restarts'], best_unplaced=top['unplaced'])
fit['two_sided'].update(restarts=two['restarts'], bottom_side=two['bottom'])
fit['courtyard_utilisation_of_board_less_hole_courtyards'] = r['area_mm2']['utilisation_of_board_less_holes']
r['fit'] = fit
open(O + 'placement-report.json', 'w').write(json.dumps(r, indent=1) + '\n')
