"""Source-bound B20 load cases and the per-stage desk loss model shared by the B20 desk screens (nothing measured).

Every load case names where its currents come from. thermal-check.py, current-check.py, loop-check.py and
power-report.py read this table, so a rail current, a VIN branch current or an inductor current cannot drift between
reports. All cases are evaluated by the same steady-state desk model; none is a transient or measured result.
"""
import math

CONTRACT_SOURCE = 'manufacturing/pd20-status.md, fixed decision "OSC current contract"'
RAILS = ('+12', '-12', '+5')

# Currents in A per rail. `evidence` is the class of the currents, not of any result computed from them.
CASES = {
    'continuous': {
        'loads': {'+12': 1.7, '-12': 1.6, '+5': 0.3},
        'source': CONTRACT_SOURCE + ': continuous 1.7 / 1.6 / 0.3 A, all rails at once',
        'evidence': 'CONTRACT',
        'model_limit': 'Steady-state desk evaluation at the continuous contract current.',
    },
    'transient_20ms': {
        'loads': {'+12': 2.0, '-12': 1.9, '+5': 0.4},
        'source': CONTRACT_SOURCE + ': 20 ms transient 2.0 / 1.9 / 0.4 A',
        'evidence': 'CONTRACT',
        'model_limit': ('Steady-state desk evaluation held at the 20 ms transient current. It is not a transient model: '
                        'a 20 ms event is far shorter than the board and part thermal time constants, so the copper '
                        'and junction temperatures shown overstate one event; no hold-up, slope or limiter timing is '
                        'covered.'),
    },
    'let_through_max': {
        'loads': {'+12': 2.1, '-12': 2.0, '+5': 0.5},
        'source': CONTRACT_SOURCE + ': let-through maximum 2.1 / 2.0 / 0.5 A including tolerance',
        'evidence': 'CONTRACT',
        'model_limit': ('Steady-state desk evaluation held at the let-through maximum (the case earlier records call '
                        'the limiter maximum). The limiter trips; it does not regulate current, so this level is a '
                        'bound, not an operating point. Let-through is not simulated or measured.'),
    },
    'legacy_pd15_budget': {
        'loads': {'+12': 1.2, '-12': 0.8, '+5': 0.5},
        'source': ('LEGACY: the PD15 Board B output budget (CLAUDE.md), which phase 30-33 B20 reports mislabelled '
                   '"rated". It is not a PD20 contract case and not a B20 rating'),
        'evidence': 'LEGACY_COMPARISON_ONLY',
        'model_limit': 'Kept only so earlier phase records can be compared; no PD20 acceptance reads it.',
    },
}
CONTRACT_CASES = tuple(k for k, v in CASES.items() if v['evidence'] == 'CONTRACT')

# Desk input: the PD 20 V contract with 1 V of cable/input drop, as used since phase 30 (an assumption, not low line).
VIN = 19.0

# TPS54560 SLVSBN0C (retained source src-c31966-primary): section 6.5 high-side on-resistance 92 mOhm typical,
# 190 mOhm maximum (VIN 12 V, BOOT-SW 6 V); section 6.4 theta-JA 42.0 C/W on the standard board; section 8.2.2.13
# trise = VIN x 0.16 ns/V + 3 ns, QG 3 nC and IQ 146 uA as used in the datasheet example.
RDS = {'typ': 0.092, 'max': 0.190}
QG, IQ, THETA_JA_STD = 3e-9, 146e-6, 42.0
FSW = 556.7e3                      # calculate-board-b20-draft.py fsw_typical_hz
# catch-diode forward voltage per rail (5 A, 25 C maxima; bounds at these currents): the bucks keep SDT5A60SA
# (fact-c3024223-vf-max-5a-25c), the inverter has B560C-13-F since phase 33 (fact-c85100-vf-max-5a-25c)
VF_RAIL = {'+12': 0.52, '+5': 0.52, '-12': 0.70}
DCR = 0.068                        # ASPI-0630LR-100M-T15 fact-aspi-0630lr-100m-t15-dcr-max
R_SHUNT = 0.010                    # PCSR2512 fact-c23067428-resistance
R_FET = 0.0156 * 1.25              # CSD18543Q3A 4.5 V maximum x the draft's 1.25 hot factor (PA)
RIPPLE_PP = {'+12': 1.2562, '+5': 0.809, '-12': 1.4754}   # calculate-board-b20-draft.py inductor ripple maxima
VOUT = {'+12': 12.15, '+5': 5.08, '-12': 12.13}           # setpoint_nominal_v
CONTROL_W = 0.3                    # PA allowance: AP63201 supervisor supply, references, amplifiers, comparators, gate drive
T_AMB = 40.0


def stage(rail, io, vin=VIN, rds=RDS['max']):
    vo = VOUT[rail] + io * (R_SHUNT + DCR)          # raw node above the servo-regulated SH node
    vf = VF_RAIL[rail]
    di = RIPPLE_PP[rail]
    if rail == '-12':                                # inverting buck-boost: the IC switches VIN + |VOUT|
        d = (vo + vf) / (vin + vo + vf)
        il = io / (1 - d)
        vsw = vin + vo
    else:
        d = (vo + vf) / (vin + vf)
        il = io
        vsw = vin
    irms2 = il ** 2 + di ** 2 / 12
    ic = {'conduction': irms2 * rds * d, 'switching': vsw * FSW * il * (vsw * 0.16e-9 + 3e-9),
          'gate': vsw * QG * FSW, 'quiescent': vsw * IQ}
    rest = {'diode': vf * io if rail == '-12' else vf * io * (1 - d), 'inductor': irms2 * DCR,
            'post_filter': io ** 2 * DCR, 'shunt': io ** 2 * R_SHUNT, 'rail_fets': 2 * io ** 2 * R_FET}
    p_ic = sum(ic.values())
    stage_w = p_ic + sum(rest.values())
    return {'duty': round(d, 4), 'inductor_a': round(il, 3), 'inductor_rms_a': round(math.sqrt(irms2), 3),
            'ic_w': round(p_ic, 3), 'ic_terms_w': {k: round(v, 4) for k, v in ic.items()},
            'other_w': {k: round(v, 3) for k, v in rest.items()}, 'stage_w': round(stage_w, 3),
            'output_w': round(VOUT[rail] * io, 3), 'input_a': round((VOUT[rail] * io + stage_w) / vin, 3),
            'tj_std_board_c': round(T_AMB + THETA_JA_STD * p_ic, 1)}


def case_currents(case, rds=RDS['max']):
    """Rail, inductor and VIN branch currents of one case at VIN, from the same stage model as the loss screen.
    The VIN branches carry each stage's input current at the maximum-RDS corner; J5 also carries the control allowance."""
    loads = CASES[case]['loads']
    st = {r: stage(r, loads[r], VIN, rds) for r in RAILS}
    total = sum(s['output_w'] + s['stage_w'] for s in st.values()) + CONTROL_W
    return {'rail_a': dict(loads), 'inductor_a': {r: st[r]['inductor_a'] for r in RAILS},
            'inductor_rms_a': {r: st[r]['inductor_rms_a'] for r in RAILS},
            'stage_input_a': {r: st[r]['input_a'] for r in RAILS}, 'vin_total_a': round(total / VIN, 3)}


def case_record(case):
    c = CASES[case]
    return {'loads_a': dict(c['loads']), 'source': c['source'], 'evidence': c['evidence'], 'model_limit': c['model_limit']}
