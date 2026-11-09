"""Phase 30 desk thermal screen of the B20 draft at the PD20 contract load cases (load_cases.py; nothing measured).

usage: python3 thermal-check.py [out.json] [board.kicad_pcb]

Per-stage loss from the TPS54560 dissipation estimate (SLVSBN0C section 8.2.2.13, equations 52-55), the catch
diode, the two inductors, the shunt and the back-to-back rail FETs; then the board mean surface rise for the same
still-air coefficient used for the 15 V Board B screen, and each TPS54560 junction from the datasheet's
standard-board theta-JA. A desk screen: switching edges, diode capacitance, core loss and the controller block are
an allowance, and the real board is not the JEDEC board.

PD20 layout review: the inverter's D3 anode and U3 PAD share one M12_RAW copper island. The `inverter_island` rows
replace the JEDEC theta-JA there with a node model read from the routed board's filled M12_RAW zones and vias.
"""
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'schgen'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sexp  # noqa: E402
from report_provenance import calculation_binding, digest

from load_cases import (CASES, CONTRACT_CASES, CONTROL_W, FSW, RDS, T_AMB, THETA_JA_STD, VIN,  # noqa: E402
                        case_record, stage)

H_RANGE = (10.0, 15.0)             # PA still-air convection + radiation, W/m2K, as in the Board B screen
AREA_M2 = 2 * 0.110 * 0.085        # both faces of the 110 x 85 mm outline


# inverter island node (PD20 layout review). All coefficients are project assumptions (PA), not measurements:
# through-plane FR4 0.3-0.4 W/mK; JLC7628 prepreg 0.2 mm and core 1.065 mm (apply-routes.py stackup); copper 385 W/mK;
# via barrel plating 20 um over a 1.6 mm board; spreading in the In1.Cu GND plane (17.5 um) plus 50-100 % of one 1 oz
# outer pour, to an assumed 25 mm radius. B560C junction to terminal 10 C/W (fact-c85100-theta-jt). The TPS54560
# junction-to-PAD resistance is not retained, so U3 gets only the island (PAD) temperature, a lower bound for TJ.
K_FR4 = (0.3, 0.4)
T_PP, T_CORE, T_BOARD, PLATING = 0.2e-3, 1.065e-3, 1.6e-3, 20e-6
K_CU, SPREAD_B_M = 385.0, 25e-3
KT_PLANE = (K_CU * (17.5e-6 + 0.5 * 35e-6), K_CU * (17.5e-6 + 35e-6))
THETA_JT_D3 = 10.0
D3_ANODE, U3_PAD = (31.15, 41.25), (30.0, 48.0)   # placement anchors used to pick the island polygons


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and sexp.atom(c[0]) == name]


def inside(pt, poly):
    hit = False
    for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]):
        if (ya > pt[1]) != (yb > pt[1]) and pt[0] < xa + (pt[1] - ya) * (xb - xa) / (yb - ya):
            hit = not hit
    return hit


def area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def island_geometry(pcb):
    """F.Cu M12_RAW fill polygons that reach the D3 anode or the U3 PAD, the B.Cu one under the PAD, and the through
    holes that join them (routed vias plus the PAD's own via pads)."""
    tree = sexp.load(pcb)
    polys = []
    for zone in kids(tree, 'zone'):
        if [sexp.atom(c[1]) for c in kids(zone, 'net')] != ['M12_RAW']:
            continue
        for fp in kids(zone, 'filled_polygon'):
            layer = sexp.atom(kids(fp, 'layer')[0][1])
            pts = [(float(sexp.atom(q[1])), float(sexp.atom(q[2]))) for q in kids(kids(fp, 'pts')[0], 'xy')]
            polys.append((layer, pts))

    def near(poly, c, r=1.6):
        return any(inside((c[0] + dx, c[1] + dy), poly) for dx in (-r, 0, r) for dy in (-r, 0, r))
    front = [q for l, q in polys if l == 'F.Cu' and (near(q, D3_ANODE) or near(q, U3_PAD, 2.6))]
    back = [q for l, q in polys if l == 'B.Cu' and inside(U3_PAD, q)]
    holes = []
    for via in kids(tree, 'via'):
        if [sexp.atom(c[1]) for c in kids(via, 'net')] == ['M12_RAW']:
            at = kids(via, 'at')[0]
            holes.append((float(sexp.atom(at[1])), float(sexp.atom(at[2]))))
    for fp in kids(tree, 'footprint'):
        props = {sexp.atom(q[1]): sexp.atom(q[2]) for q in kids(fp, 'property')}
        if props.get('Reference') != 'U3':
            continue
        ox, oy = (float(sexp.atom(v)) for v in kids(fp, 'at')[0][1:3])
        for pad in kids(fp, 'pad'):
            if sexp.atom(pad[1]) == '9' and sexp.atom(pad[2]) == 'thru_hole':
                at = kids(pad, 'at')[0]
                holes.append((ox + float(sexp.atom(at[1])), oy + float(sexp.atom(at[2]))))
    joined = [h for h in holes if any(inside(h, q) for q in back)
              and (any(inside(h, q) for q in front) or math.dist(h, U3_PAD) < 2.6)]
    return {'front_mm2': round(sum(area(q) for q in front), 1), 'back_mm2': round(sum(area(q) for q in back), 1),
            'joining_vias': len(joined)}


def island(geom, p_d3, p_u3, mean_rise, worst):
    k = K_FR4[0] if worst else K_FR4[1]
    kt = KT_PLANE[0] if worst else KT_PLANE[1]
    a_f, a_b = geom['front_mm2'] * 1e-6, geom['back_mm2'] * 1e-6
    g_front = k * a_f / T_PP
    g_back = k * a_b / (T_PP + T_CORE)
    r_via = T_BOARD / (K_CU * math.pi * 0.3e-3 * PLATING)
    r_vias = r_via / geom['joining_vias'] if geom['joining_vias'] else math.inf
    g_b_path = 1 / (r_vias + 1 / g_back) if g_back and geom['joining_vias'] else 0.0
    r_spread = math.log(SPREAD_B_M / math.sqrt((a_f + a_b) / math.pi)) / (2 * math.pi * kt)
    r_node = 1 / (g_front + g_b_path) + r_spread
    t_island = T_AMB + mean_rise + (p_d3 + p_u3) * r_node
    return {'island_k_per_w': round(r_node, 1), 'island_c': round(t_island, 1),
            'd3_tj_c': round(t_island + p_d3 * THETA_JT_D3, 1), 'u3_pad_c_lower_bound_of_tj': round(t_island, 1)}


out = {'assumptions': {'vin_v': VIN, 'fsw_hz': FSW, 'ambient_c': T_AMB, 'h_w_per_m2k': H_RANGE, 'area_both_faces_m2': AREA_M2,
                       'control_allowance_w': CONTROL_W},
       'load_cases': {case: case_record(case) for case in CASES}, 'contract_cases': list(CONTRACT_CASES),
       'model_limit': ('Every case is a steady-state desk evaluation of an unvalidated draft. No case is a transient, '
                       'thermal simulation or measured result.')}
for case in CASES:
    loads = CASES[case]['loads']
    for corner in ('typ', 'max'):
        st = {r: stage(r, loads[r], VIN, RDS[corner]) for r in loads}
        loss = sum(s['stage_w'] for s in st.values()) + CONTROL_W
        pout = sum(s['output_w'] for s in st.values())
        out[f'{case}_{corner}_rds'] = {
            'stages': st, 'board_loss_w': round(loss, 2), 'output_w': round(pout, 2),
            'efficiency': round(pout / (pout + loss), 4), 'input_a_at_19v': round((pout + loss) / VIN, 3),
            'mean_rise_k': [round(loss / (h * AREA_M2), 1) for h in H_RANGE]}
pcb = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[3] / 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
geom = island_geometry(pcb)
rows = {}
for case in CASES:
    for corner in ('typ', 'max'):
        row = out[f'{case}_{corner}_rds']
        st = row['stages']['-12']
        p_d3, p_u3 = st['other_w']['diode'], st['ic_w']
        rows[f'{case}_{corner}_rds'] = {'p_d3_w': p_d3, 'p_u3_w': p_u3,
                                        'best': island(geom, p_d3, p_u3, row['mean_rise_k'][1], False),
                                        'worst': island(geom, p_d3, p_u3, row['mean_rise_k'][0], True)}
out['inverter_island'] = {'copper': geom, 'd3_tj_max_c': 150, 'cases': rows,
                          'method': 'desk node model: F.Cu island to In1 through the prepreg, B.Cu pour through the vias '
                                    'and the board to In1, In1 spreading, plus the board-mean rise (the island heat is '
                                    'counted in both, conservative). Nothing measured.'}
out['input_binding'] = calculation_binding(__file__, {'pcb': digest(pcb)})
json.dump(out, open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout, indent=1)
