"""Add the fit verdict and OPEN items to boards/board-p/r3-draft/placement-report.json (last step of run.sh).

Current native claims require a matching PCB/schematic/project/report receipt. Historical results remain historical.
"""
import json, sys
from pathlib import Path
from native_receipt import read_native_receipt
O = sys.argv[1].rstrip('/') + '/'
r = json.load(open(O + 'placement-report.json'))
top = json.load(open(O + 'search-top-only.json')); two = json.load(open(O + 'search-two-sided.json'))
route_data = json.load(open(O + 'routes.json'))
routes = route_data['report']
rr = json.load(open(O + 'routing-report.json'))
open_sig = routes['unrouted']
r['status'] = ('DEVELOPMENT REVIEW, GRID-ROUTED; independent desk review dated 2026-11-08 (power-path pours, ground pours and grid-routed signals; '
               f'{len(open_sig)} signal connection(s) open; route-power.py finds {len(rr["gnd_clusters_detached"])} detached GND cluster(s), '
               'native evidence is reported separately below). '
               'Not for fabrication or ordering. PD20: the routed draft is boards/board-p/board-p.kicad_pcb, the exported board-p; the routed 15 V as-built PCB it replaced is read from git history (run.sh AS_BUILT_REV).')
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
 "historical_native_drc_kicad_10_0_6_before_R1_R4_corrections": {
  "scope": "Historical November 8 review at main 6b08236, PCB SHA 67b0e0960c8d5590dec0efc6de22218d3f7a21fa098abcaffdd57433f3e0058d; not acceptance of a rebuild.",
  "courtyard_overlap": 0,
  "clearance_or_shorting_errors": 0,
  "items_not_allowed": "0 (PD20: the pin-corridor keep-outs forbid vias only; build-draft.py checks that only U1 and the protected owners touch a corridor)",
  "schematic_parity_pd20": "--schematic-parity against boards/board-p/board-p.kicad_sch: 0 errors; only extra_footprint MH1-MH3 (mechanical, excluded from BOM and CPL). The builder writes each LCSC field and the unconnected-(ref-pin-Pad) nets of the no-connect pins",
  "unconnected_items": 0,
  "dangling": "PD20 rebuild: 2 via_dangling and 1 track_dangling warnings (fixed fan-out vias and stub; phase 15 had 3)",
  "gnd_cluster_check_disagreement": "RESOLVED (phase 15): native DRC was right. route-power.py joined tracks to fills, vias and pads only at track endpoints; it missed track-to-track joints and track bodies crossing a fill, so the B.Cu track (16.95,22.15)-(16.95,23.25) that joins its neighbour track and touches B.Cu fill #8 left C34.2, R21.2 and C38.2 falsely detached, and the repeated join passes added duplicate tracks. The fixed union-find and the deduplicated rebuild find 0 detached GND clusters, in agreement with native DRC",
  "phase_14": "0 unconnected items; route-power.py listed 1 false detached GND cluster and the board held 20 duplicate join segments",
  "phase_13": "3 unconnected items (CC2 at U1.4, 2 GND zone items); phase 12: 8; phase 11: 72, 17 on power nets",
  "other": "PD20 rebuild: 69 silk_overlap, 34 silk_over_copper, 14 text_height, 2 silk_edge_clearance and 3 lib_footprint_issues warnings; no error"
 },
 "open": [
  "Independent desk/native review exists: independent-review.md, 2026-11-08, with dated corrective dispositions. R1–R4 implementation and acceptance are separate; layout-corrections.md records source ownership and manufacturing residuals. Current native results require the matching receipt below. The 5 A width uses IPC-2221 at an assumed 20 C rise (PA), not a measured thermal rating.",
  "Two-sided assembly changes the JLCPCB assembly scope; not decided here.",
  "B.Cu faces the enclosure floor in the installed stack (P is below B); bottom parts add to the 12.7 mm P envelope against the 18 mm printed-leg seating height. Exact envelope evidence and final pair assembly reports must establish the resulting clearances.",
  "C3 RVT1H101M0810 is 10.2 mm nominal (tolerance not stated) against the 11.1 mm nominal plane gap. The historical Board B collision motivated the adopted B20 r3 keepout. The valid PD20 pair is Board P plus B20; verify the final pair with fresh datum and assembly evidence.",
  "The library 0603 courtyard (3.37 x 1.91 mm) is larger than the as-built embedded lands; using compact lands would change geometry and needs layout review."
 ]
}
fit['top_only'].update(restarts=top['restarts'], best_unplaced=top['unplaced'])
fit['two_sided'].update(restarts=two['restarts'], bottom_side=two['bottom'])
fit['courtyard_utilisation_of_board_less_hole_courtyards'] = r['area_mm2']['utilisation_of_board_less_holes']
pcb = Path(O) / 'board-p-r3-draft.kicad_pcb'
if not pcb.exists():
    pcb = Path('boards/board-p/board-p.kicad_pcb')
fit['current_native_drc'] = read_native_receipt(O, pcb, 'boards/board-p/board-p.kicad_sch', 'boards/board-p/board-p.kicad_pro')
r['fit'] = fit
open(O + 'placement-report.json', 'w').write(json.dumps(r, indent=1) + '\n')

# The board README is a live view of the same receipts, not a second hard-coded
# DRC summary. Historical findings remain in the dated independent review.
import hashlib
pcb_hash = hashlib.sha256(pcb.read_bytes()).hexdigest()
native = fit['current_native_drc']
if native['status'].startswith('EXECUTED'):
    native_text = (f"KiCad {native['kicad_version']} native DRC: **{native['errors']} errors, "
                   f"{native['unconnected_items']} unconnected items**. The complete parity findings "
                   "and warning objects are in [native-drc.json](native-drc.json); their source/tool identity "
                   "is in [native-drc-receipt.json](native-drc-receipt.json).")
    warning_lines = '\n'.join(f"| `{kind}` | {count} |" for kind, count in native['warning_counts'].items())
else:
    native_text = '**Current native DRC: NOT RUN.** ' + native['reason']
    warning_lines = '| Current native warning inventory | NOT RUN |'
proof_path = Path(O)/'layout-correction-check.json'
proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
if proof.get('pcb_sha256') == pcb_hash:
    dec = proof['decoupling']; back = proof['connected_back_copper']; returns = proof['local_returns']
    correction_text = (
        'R1–R4 native geometry is implemented and checked for these PCB bytes. '
        'The dated implementation dispositions and remaining process/thermal limits are in '
        '[independent-review.md](independent-review.md) and [layout-corrections.md](layout-corrections.md).\n\n'
        f"- R1: four U2 thermal vias contact {back['U2.21']['connected_area_mm2']:.3f} mm² of connected B.Cu GND.\n"
        f"- R2: four Q1 drain vias contact {back['Q1.9']['connected_area_mm2']:.3f} mm² of B.Cu VBUS_OUT.\n"
        f"- R3: three Q3 drain vias contact {back['Q3.9']['connected_area_mm2']:.3f} mm² of B.Cu EF_IN.\n"
        f"- R4: C30/C34 pad distances are {dec['C30']['actual_distance_mm']:.3f}/{dec['C34']['actual_distance_mm']:.3f} mm; "
        f"planar supply paths are {dec['C30']['routed_path']['routed_centerline_mm']:.3f}/{dec['C34']['routed_path']['routed_centerline_mm']:.3f} mm "
        f"with {dec['C30']['routed_path']['via_transitions']}/{dec['C34']['routed_path']['via_transitions']} via transitions. "
        f"Direct cap-to-return-via tracks are {returns['C30']['direct_return_length_mm']:.3f}/{returns['C34']['direct_return_length_mm']:.3f} mm.\n\n"
        'Via barrels are excluded from planar path length. Filled area is geometry, not an installed thermal resistance or current rating. '
        'R1–R3 stencil/via-process approval and the shared land/paste adaptations remain pre-order manufacturing holds. '
        'R5 and R7 physical/conditional limitations remain open; no lower current ceiling is adopted.')
else:
    correction_text = '**Current R1–R4 geometry proof: NOT RUN or stale.** Rebuild and run the pinned native correction verifier before claiming acceptance.'
label_path = Path(O)/'probe-silk-check.json'
labels = json.loads(label_path.read_text()) if label_path.exists() else {}
label_text = ('Functional probe silk uses front contact ordinals and indexed reverse-side role maps, including J3.4 VBUS and J3.5 GND. Q3/D13 reference fields are retained on Fab to expose D5/D8 polarity cues; D5 has one checked printable pin1 marker. The matching artwork-only proof is [probe-silk-check.json](probe-silk-check.json); native DRC status is reported above. Text is 1.0 mm with 0.15 mm strokes and conservative mask-opening clearance ≥0.15 mm. This is a CAD/mask screen; supplier tenting and printed legibility remain unobserved.'
              if labels.get('pcb_sha256') == pcb_hash else
              'Functional probe-silk correction remains pending: the generic J3 footprint labels VDD/RST do not describe the current J3.4 VBUS_IN/J3.5 GND contract. The electrical pad roles are unchanged; an owner-local artwork correction is under review.')
minimum = min(row['largest_run_mm'] for row in rr['cross_sections'])
maximum = max(row['largest_run_mm'] for row in rr['cross_sections'])
readme = f'''# Board P r3 development review

Generated by `scripts/pcb/board-p-r3-draft/annotate-fit.py` from the current routing and native receipts.

**DEVELOPMENT REVIEW — not fabrication/order qualification.** The valid PD20 pair is
`board-p` + `board-b20-draft`. The 20 V / 5 A contract is preserved. Native CAD,
interface/electrical acceptance, supplier preview and measured performance are separate gates.
See [prototype order readiness](../../../manufacturing/prototype-order-readiness.md).

PCB SHA-256: `{pcb_hash}`.

{native_text}

| Native warning category | Count |
| --- | ---: |
{warning_lines}

The only retained parity exceptions are the specifically reviewed mechanical-only
MH1–MH3 footprints, excluded from BOM/CPL. Warning classifications and functional
annular-junction details are in [layout-corrections.md](layout-corrections.md).
Warnings are not automatically accepted for manufacturing merely because they are warnings.

## Corrective layout and remaining holds

{correction_text}

{label_text}

## Rebuild and evidence ownership

Use the [owned native workflow](../../../scripts/pcb/board-p-r3-draft/README.md).
The committed `search-two-sided.json` is the placement owner; do not enable
`R3_SEARCH=1` for an ordinary rebuild. Only C30/C34 placement differs from the
November 8 reviewed baseline; footprint identities, outline, connectors and
mounting geometry are checked separately by the native correction verifier.

`pours.json` owns fixed power/ground copper, thermal vias and short regulator
escapes. The current routed artifact contains {len(route_data['tracks'])} tracks and
{len(route_data['vias'])} routing/fixed vias; the fill stage adds {len(rr['stitching_vias'])}
grid stitching vias and {len(rr['island_vias'])} island vias. Routing reports
{len(open_sig)} open signal connections and {len(rr['gnd_clusters_detached'])}
detached GND clusters. These are routing results, not substitutes for native DRC.

All sampled power-path cuts have single filled runs of {minimum:.2f}–{maximum:.2f} mm.
The 1.82 mm target uses IPC-2221, 1 oz copper and an assumed 20 °C rise; it is
conditioned arithmetic, not a measured 5 A thermal rating. The two-sided build
has {len(r['bottom'])} bottom-side parts; final pair mechanical evidence is separate.

The default seeds are 12, 14, 16 and 20. Actual completion, selected seed and
fresh-builder/saved-route replay identity are retained in
[native-full-builder-replay-20261110.json](native-full-builder-replay-20261110.json).
The final artwork-only stage replay is recorded separately in
[native-replay.json](native-replay.json); it preserves that checked filled copper
and does not rerun heuristic routing. Stable generated UUIDs and explicit
canonical project copies prevent native object ordering/default-project drift
from silently changing filled copper. A successful replay does not establish
supplier process approval or electrical order readiness.

## Historical findings

The [November 8 independent review](independent-review.md) retains the original
R1–R8 findings and baseline hash, followed by dated corrective dispositions.
Historical phase-13/14/15 DRC and ground-cluster results remain explicitly
historical in `placement-report.json`; they are not reused as current acceptance.
The old top-only heuristic search left 20 parts unplaced in 25 restarts. That
search result is not proof of infeasibility and is not rerun by this correction.

The old r3 + PD15 Board B stack is an invalid pair. Its C3/U3 conflict motivated
the B20 r3 keepout; it does not require redesigning the received S3 Board B.
Historically, C3's 8.3 × 8.3 mm base overlapped that Board B U3 courtyard by
3.31 × 4.05 mm. The 10.2 mm nominal C3 and the old H4.5 model exceeded the
11.1 mm nominal plane gap; the H4.5 value was a model attribute, not a datasheet
fact. The current valid P/B20 pair requires its own fresh datum/assembly evidence.
'''
(Path(O)/'README.md').write_text(readme)
