"""Phase 30 desk thermal screen of the B20 draft at rated load and at the limiter maximum (nothing measured).

usage: python3 thermal-check.py [out.json]

Per-stage loss from the TPS54560 dissipation estimate (SLVSBN0C section 8.2.2.13, equations 52-55), the catch
diode, the two inductors, the shunt and the back-to-back rail FETs; then the board mean surface rise for the same
still-air coefficient used for the 15 V Board B screen, and each TPS54560 junction from the datasheet's
standard-board theta-JA. A desk screen: switching edges, diode capacitance, core loss and the controller block are
an allowance, and the real board is not the JEDEC board.
"""
import json
import sys

# TPS54560 SLVSBN0C (retained source src-c31966-primary): section 6.5 high-side on-resistance 92 mOhm typical,
# 190 mOhm maximum (VIN 12 V, BOOT-SW 6 V); section 6.4 theta-JA 42.0 C/W on the standard board; section 8.2.2.13
# trise = VIN x 0.16 ns/V + 3 ns, QG 3 nC and IQ 146 uA as used in the datasheet example.
RDS = {'typ': 0.092, 'max': 0.190}
QG, IQ, THETA_JA_STD = 3e-9, 146e-6, 42.0
FSW = 556.7e3                      # calculate-board-b20-draft.py fsw_typical_hz
VF = 0.52                          # SDT5A60SA fact-c3024223-vf-max-5a-25c (5 A, 25 C maximum; a bound at these currents)
DCR = 0.068                        # ASPI-0630LR-100M-T15 fact-aspi-0630lr-100m-t15-dcr-max
R_SHUNT = 0.010                    # PCSR2512 fact-c23067428-resistance
R_FET = 0.0156 * 1.25              # CSD18543Q3A 4.5 V maximum x the draft's 1.25 hot factor (PA)
RIPPLE_PP = {'+12': 1.2562, '+5': 0.809, '-12': 1.4754}   # calculate-board-b20-draft.py inductor ripple maxima
VOUT = {'+12': 12.15, '+5': 5.08, '-12': 12.13}           # setpoint_nominal_v
LOADS = {'rated': {'+12': 1.2, '-12': 0.8, '+5': 0.5}, 'limiter_max': {'+12': 2.1, '-12': 2.0, '+5': 0.5}}
CONTROL_W = 0.3                    # PA allowance: AP63201 supervisor supply, references, amplifiers, comparators, gate drive
H_RANGE = (10.0, 15.0)             # PA still-air convection + radiation, W/m2K, as in the Board B screen
AREA_M2 = 2 * 0.110 * 0.085        # both faces of the 110 x 85 mm outline
T_AMB = 40.0


def stage(rail, io, vin, rds):
    vo = VOUT[rail] + io * (R_SHUNT + DCR)          # raw node above the servo-regulated SH node
    di = RIPPLE_PP[rail]
    if rail == '-12':                                # inverting buck-boost: the IC switches VIN + |VOUT|
        d = (vo + VF) / (vin + vo + VF)
        il = io / (1 - d)
        vsw = vin + vo
    else:
        d = (vo + VF) / (vin + VF)
        il = io
        vsw = vin
    irms2 = il ** 2 + di ** 2 / 12
    ic = {'conduction': irms2 * rds * d, 'switching': vsw * FSW * il * (vsw * 0.16e-9 + 3e-9),
          'gate': vsw * QG * FSW, 'quiescent': vsw * IQ}
    rest = {'diode': VF * io if rail == '-12' else VF * io * (1 - d), 'inductor': irms2 * DCR,
            'post_filter': io ** 2 * DCR, 'shunt': io ** 2 * R_SHUNT, 'rail_fets': 2 * io ** 2 * R_FET}
    p_ic = sum(ic.values())
    return {'duty': round(d, 4), 'inductor_a': round(il, 3), 'ic_w': round(p_ic, 3),
            'ic_terms_w': {k: round(v, 4) for k, v in ic.items()}, 'other_w': {k: round(v, 3) for k, v in rest.items()},
            'stage_w': round(p_ic + sum(rest.values()), 3), 'output_w': round(VOUT[rail] * io, 3),
            'tj_std_board_c': round(T_AMB + THETA_JA_STD * p_ic, 1)}


out = {'assumptions': {'vin_v': 19.0, 'fsw_hz': FSW, 'ambient_c': T_AMB, 'h_w_per_m2k': H_RANGE, 'area_both_faces_m2': AREA_M2,
                       'control_allowance_w': CONTROL_W}}
for case, loads in LOADS.items():
    for corner in ('typ', 'max'):
        st = {r: stage(r, loads[r], 19.0, RDS[corner]) for r in loads}
        loss = sum(s['stage_w'] for s in st.values()) + CONTROL_W
        pout = sum(s['output_w'] for s in st.values())
        out[f'{case}_{corner}_rds'] = {
            'stages': st, 'board_loss_w': round(loss, 2), 'output_w': round(pout, 2),
            'efficiency': round(pout / (pout + loss), 4), 'input_a_at_19v': round((pout + loss) / 19.0, 3),
            'mean_rise_k': [round(loss / (h * AREA_M2), 1) for h in H_RANGE]}
json.dump(out, open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout, indent=1)
