#!/usr/bin/env python3
"""Paper screen for the Board B 20 V switcher-direct DRAFT (analysis only).

Reproduces the CALCULATED rows of manufacturing/board-b-20v-switcher-direct-draft.md
for scripts/schgen/board_b20_spec.py against the OSC-PD interface contract
(+12 / -12 / +5 V). Every input carries an evidence tag:

  G   guaranteed manufacturer limit from a retained primary datasheet extract
  T   typical manufacturer value (not a bound)
  PA  project assumption
  PROPOSED  draft design value with no owner record yet

Nothing here is a measurement, a simulation or an adopted value. A row that
needs unsourced data is reported OPEN, never PASS.
"""

import argparse
import json
import math

# ---- Contract (manager osc-pd-interface-20v.md, 2026-10-31) -----------------
SOURCE_BAND = {'+12': (12.00, 12.30), '-12': (12.00, 12.20), '+5': (5.05, 5.10)}
LOAD_BAND = {'+12': (11.53, 12.48), '-12': (11.74, 12.37), '+5': (4.81, 5.20)}
I_TRANSIENT_MIN = {'+12': 2.0, '-12': 1.9, '+5': 0.4}
I_MAX = {'+12': 2.1, '-12': 2.0, '+5': 0.5}
C_LOAD_MAX = {'+12': 180e-6, '-12': 180e-6, '+5': 120e-6}
RIPPLE_MAX_VPP = 1e-3
RAMP_MIN_S = 10e-3
SLOPE_MAX_V_PER_MS = {'+12': 1.23, '-12': 1.22, '+5': 0.51}
START_SKEW_MAX_S = 0.41e-3
BAND_ENTRY_SKEW_MAX_S = 2e-3            # PROPOSED in the contract
DISCHARGE_LEVEL = {'+12': 0.5, '-12': 0.6, '+5': 0.6}
DISCHARGE_TIME_MAX_S = 0.100            # PROPOSED in the contract
P5_ORDER_LEVEL = 0.8                    # +5 V must be <= 0.8 V before an analog rail is absent
M12_WHILE_P12_ABSENT_MAX = 6.0          # R-VEE: |-12| <= 6 V while +12 absent
OV_TRIP_MAX = {'+12': 12.48, '-12': 12.37, '+5': 5.20}   # PROPOSED trip = load-band maximum
REVERSE_CURRENT_MAX_A = 1e-3            # PROPOSED

# ---- Input (Board P VBUS_OUT) -----------------------------------------------
VIN_NOM, VIN_MIN, VIN_MAX = 20.0, 19.0, 21.0      # PA: USB PD 20 V fixed PDO +/-5 %
VIN_OVERSHOOT = 25.20785682388359                 # Board P hot/TCR OVP bound + overshoot (rules.json)

# ---- Primary datasheet values ------------------------------------------------
# TI TPS54560 SLVSBN0C (G unless tagged)
TPS_VIN_ABS = 65.0
TPS_VIN_OP_MAX = 60.0
TPS_VREF = (0.792, 0.800, 0.808)
TPS_EN_TH = (1.1, 1.2, 1.3)
TPS_EN_I1 = 1.2e-6           # T (-0.58..-1.8 uA band at threshold -50 mV)
TPS_EN_IHYS = 3.4e-6         # T (2.2..4.5 uA)
TPS_ILIM_MIN = 6.3
TPS_FSW_RT200K = (450e3, 500e3, 550e3)
# fsw(kHz) = 92471 x RT(kOhm)^-0.991 (T, datasheet Equation 8 curve fit)
# TI OPA2187 SBOS807E (G): section 6.8 (4.5 V to < 8 V) VOS 15 uV, swing 30 mV at 10 k over
# temperature, VCM (V-) - 0.1 V to (V+) - 2 V; section 6.7 (8 V to 36 V) VOS 10 uV, swing 125 mV
OPA_VOS_MAX = 15e-6
OPA_SWING_LV = 0.030
OPA_SWING_HV = 0.125
OPA_VCM_HEADROOM = 2.0
OPA_SUPPLY = (4.5, 36.0)
OPA_SR_V_PER_US = 0.2         # T
# TI REF5025AIDR SBOS410O (G): the AI suffix is the standard grade (Table 4-2)
REF_V = 2.5
REF_LOAD_MA_PA = 3.0          # PA: dividers about 1.6 mA plus OPA2187 input-diode loading of comparators (review finding 11)
REF_ACC = 0.001 + 30e-6 * REF_LOAD_MA_PA   # initial accuracy + 25 C load regulation 30 ppm/mA
REF_TC_PPM = 8.0
# TI INA301A3 SBOS713A (G)
INA_GAIN = 100.0
INA_GAIN_ERR = 0.002
INA_VOS = 35e-6
INA_CMP_VOS = 4.5e-3          # 25 C limit only
INA_TP_S = 1e-6
INA_ILIMIT = (79.2e-6, 80.0e-6, 80.8e-6)   # LIMIT pin source current (review finding 1)
INA_VS_MAX = 5.5
# YAGEO PE1206FRF470R02L product sheet (G)
SHUNT_R = 0.020
SHUNT_TOL = 0.01
SHUNT_TCR = 100e-6
# YAGEO RT0603 0.1 % (owner records; TCR 25 ppm/C assumed for the B tolerance class, PA)
R01_TOL = 0.001
R01_TCR = 25e-6
# TI CSD18543Q3A SLPS633 (G)
CSD_RDS_4V5_MAX = 15.6e-3
CSD_RDS_10V_MAX = 9.9e-3
CSD_VGS_MAX = 20.0
CSD_RDS_HOT_FACTOR_PA = 1.25   # PA: normalized RDS(on) at about 85 C junction, read from a typical curve (not a bound)
# Diodes BZT52C11-7-F DS18004 (G)
VZ11 = (10.4, 11.6)
# Diodes BSS138-7-F (G)
BSS_VGSTH_MAX = 1.5
BSS_VGSTH_MIN_PA = 0.5        # PA: the owner record carries no minimum
BSS_VGS_MAX = 20.0
DMP_VGSTH = (1.0, 2.5)        # |VGS(th)| (G max; min from the same table)
# Diodes AP63201WU-7 (owner record, G): VFB window
AP_VFB = (0.792, 0.808)
# Diodes DMP3036SFG-7 (G)
DMP_VGS_MAX = 25.0
# Abracon ASPI-0630LR-100M-T15 (T for Isat/Irms)
L_UH = 10e-6
L_DCR_MAX = 0.068
L_IRMS_T = 4.0
L_ISAT_T = 5.5
# Murata GRM32ER71H106KA12L effective-bank assumption (PA, owner record): 27.54 uF per 5 units
C_GRM32_EFF = 27.54e-6 / 5
# Panasonic 25SVPF47M (G)
C_POLY = 47e-6
C_POLY_ESR = 0.030
GRM_ESR_T = 0.003

# ---- Draft design values (board_b20_spec.py; PROPOSED unless an owner record exists) --
RT_OHM = 174e3                 # C861163 (owner record)
FSW_T = 92471 * (RT_OHM / 1e3) ** -0.991 * 1e3     # Hz, typical
FSW = (FSW_T * 0.9, FSW_T, FSW_T * 1.1)            # PA: +/-10 % like the 200 k row

SENSE = {  # sense dividers on the post-filter nodes (0.1 % owner-record values)
    '+12': {'top': 11.5e3 + 4.02e3, 'bot': 4.02e3},
    '+5': {'top': 174e3 + 10e3, 'bot': 174e3 + 4.02e3},
    '-12': {'neg': 3 * 11.5e3, 'ref': 3.09e3 + 4.02e3},
}
UVLO = {'top': 470e3, 'bot': 39e3}   # PROPOSED, every converter EN divider
# common tracking reference (phase 7): REF25 -> RRMP 20k -> RAMP, CRMP 1 uF, loaded by RT12NA 100k
RAMP_NET = {'R': 20e3, 'C': 1e-6, 'C_TOL': 0.10, 'LOAD': 100e3}
TRACK_K = {'+12': 1 + 69.8e3 / 10e3, '+5': 1 + 23.2e3 / 10e3, '-12': 806e3 / 100e3}
RAMP_RELEASE = {'R': 100e3, 'C': 100e-9}      # RRMD / CRMD from EN_N to the Q12 gate
SERVO_CI = {'+12': 1.5e-9, '+5': 1.5e-9, '-12': 270e-12}   # PROPOSED C0G integrators
SERVO_RI = 100e3
RDY_NET = {'R': 200e3, 'C': 10e-6}            # two C25803 100k + C13585 10 uF
POR_NET = {'R': 100e3, 'C': 1e-6}
SUP_FB = (52.3e3, 10e3)                       # AP63201 feedback, PROPOSED top / C95204 bottom
FB_DIV = {'+12': (145e3, 10e3), '+5': (54.9e3, 10e3), '-12': (145e3, 10e3)}   # PROPOSED top 0.1 %, C95204 bottom
SERVO_RJ = {'+12': 1e6, '+5': 1e6, '-12': 4.7e6}     # PROPOSED 1 % injection resistors
FB_R_TOL, RJ_TOL = 0.001, 0.01
VIN_UV_RES = (221e3, 17.6e3)  # PROPOSED 0.1 %, compared with REF/2 from two C861589 8.2 k
VIN_UV_MAX_PA = VIN_MIN       # PA: trip must stay below the minimum operating VIN
DISCHARGE_R = {'+12': 100.0, '-12': 150.0, '+5': 33.0}     # PROPOSED 1206
HOLDUP = {'C': 10e-6, 'R_gate': 100e3, 'R_m12': 470e3 + 1e6, 'R_charge': 56e3}   # CDH, R60, R61 + R62, RDH
LIMIT_DIV = {  # INA301 LIMIT dividers from REF (0.1 %); LIMIT also carries ILIMIT x (top || bot)
    '+12': {'top': 680.0, 'bot': 2.74e3},
    '+5': {'top': 3.09e3, 'bot': 1.5e3},
}
M12_LIMIT_DIV = {'top': 10.5e3 + 10e3, 'bot': 33.0}       # GND -> node -> -12 pre
SHUNT_N = {'+12': 2, '-12': 2, '+5': 1}                  # parallel PE1206 20 mOhm
TA_SPAN = 20.0                 # PA: +/-20 C around the 25 C reference
# window dividers (PROPOSED E192 0.1 %): positive rails top/bottom to GND, -12 V REF-to-terminal
OV_RES = {'+12': (54.2e3, 13.7e3), '+5': (10.6e3, 10e3), '-12': (200e3, 40.7e3)}
UV_RES = {'+12': (232e3, 62.6e3), '+5': (10.4e3, 10.7e3), '-12': (198e3, 41.7e3)}


def _trip(rail, res):
    a, b = res[rail]
    return REF_V * a / b if rail == '-12' else REF_V * (1 + a / b)


OV_DIV = {r: (_trip(r, OV_RES), 'PROPOSED 0.1 %') for r in OV_RES}
UV_DIV = {r: (_trip(r, UV_RES),) for r in UV_RES}


def status(ok):
    return 'PASS' if ok else 'FAIL'


def setpoints():
    out = {}
    for rail in ('+12', '+5'):
        t, b = SENSE[rail]['top'], SENSE[rail]['bot']
        nom = REF_V * (1 + t / b)
        ratio = t / b
        tol = REF_ACC + 2 * R01_TOL * ratio / (1 + ratio) + REF_TC_PPM * 1e-6 * TA_SPAN \
            + 2 * R01_TCR * TA_SPAN * ratio / (1 + ratio)
        out[rail] = {'nominal_v': nom, 'tolerance_ratio': tol}
    neg, ref = SENSE['-12']['neg'], SENSE['-12']['ref']
    nom = REF_V * neg / ref
    tol = REF_ACC + 2 * R01_TOL + REF_TC_PPM * 1e-6 * TA_SPAN + 2 * R01_TCR * TA_SPAN
    out['-12'] = {'nominal_v': nom, 'tolerance_ratio': tol}
    return out


def path_resistance(rail, hot=False):
    # The servo senses the *_SH node, so only the switch pair is outside the loop. Every pair
    # is held at VGS >= 4.5 V (review finding 6: the zener knee is not relied on), so the
    # 4.5 V row bounds it at 25 C; hot=True applies the PA junction-temperature factor.
    return 2 * CSD_RDS_4V5_MAX * (CSD_RDS_HOT_FACTOR_PA if hot else 1.0)


def terminal_band():
    sp = setpoints()
    rows = {}
    for rail, (lo, hi) in SOURCE_BAND.items():
        nom, tol = sp[rail]['nominal_v'], sp[rail]['tolerance_ratio']
        drop_max = I_MAX[rail] * path_resistance(rail)
        drop_hot = I_MAX[rail] * path_resistance(rail, hot=True)
        vmax = nom * (1 + tol)
        vmin = nom * (1 - tol) - drop_max
        vmin_hot = nom * (1 - tol) - drop_hot
        rows[rail] = {
            'setpoint_nominal_v': round(nom, 5), 'setpoint_tolerance_pct': round(tol * 100, 4),
            'path_drop_max_v': round(drop_max, 5), 'terminal_min_v': round(vmin, 5),
            'terminal_max_v': round(vmax, 5), 'band': [lo, hi],
            'ripple_allowance_v': 0.0,
            'status': status(vmin >= lo and vmax <= hi),
            'terminal_min_hot_pa_v': round(vmin_hot, 5),
            'hot_status': 'OPEN' if vmin_hot < lo else 'PASS (PA factor)',
            'note': 'servo regulates the *_SH node; only 2 x CSD18543Q3A RDS(on) at the 4.5 V row is outside the loop',
        }
    return rows


def limiter():
    rows = {}
    for rail in ('+12', '+5'):
        d = LIMIT_DIV[rail]
        rth = d['top'] * d['bot'] / (d['top'] + d['bot'])
        vdiv = REF_V * d['bot'] / (d['top'] + d['bot'])
        vlim = vdiv + INA_ILIMIT[1] * rth
        rs = SHUNT_R / SHUNT_N[rail]
        itrip = vlim / (INA_GAIN * rs)
        vsense = itrip * rs
        err = SHUNT_TOL + SHUNT_TCR * TA_SPAN + INA_GAIN_ERR + INA_VOS / vsense \
            + INA_CMP_VOS / vlim + (REF_ACC + 2 * R01_TOL) * vdiv / vlim \
            + (INA_ILIMIT[2] - INA_ILIMIT[1]) * rth / vlim
        lo, hi = itrip * (1 - err), itrip * (1 + err)
        rows[rail] = {'device': 'INA301A3 comparator, transparent mode', 'limit_v': round(vlim, 5),
                      'divider_v': round(vdiv, 5), 'ilimit_shift_v': round(INA_ILIMIT[1] * rth, 5),
                      'trip_nominal_a': round(itrip, 5), 'tolerance_pct': round(err * 100, 3),
                      'trip_min_a': round(lo, 5), 'trip_max_a': round(hi, 5),
                      'window': [I_TRANSIENT_MIN[rail], I_MAX[rail]],
                      'ina_out_at_trip_v': round(vlim, 4),
                      'status': status(lo > I_TRANSIENT_MIN[rail] and hi <= I_MAX[rail])}
    sp = setpoints()['-12']
    k = M12_LIMIT_DIV['bot'] / (M12_LIMIT_DIV['top'] + M12_LIMIT_DIV['bot'])
    vmag = sp['nominal_v']
    vref = vmag * k
    rs = SHUNT_R / SHUNT_N['-12']
    itrip = vref / rs
    err = SHUNT_TOL + SHUNT_TCR * TA_SPAN + sp['tolerance_ratio'] + 2 * R01_TOL + OPA_VOS_MAX / vref \
        + I_MAX['-12'] * path_resistance('-12') / vmag
    lo, hi = itrip * (1 - err), itrip * (1 + err)
    rows['-12'] = {'device': 'OPA2187 comparator on the -12 V pre-node shunt', 'reference_v': round(vref, 6),
                   'trip_nominal_a': round(itrip, 5), 'tolerance_pct': round(err * 100, 3),
                   'trip_min_a': round(lo, 5), 'trip_max_a': round(hi, 5),
                   'window': [I_TRANSIENT_MIN['-12'], I_MAX['-12']],
                   'status': status(lo > I_TRANSIENT_MIN['-12'] and hi <= I_MAX['-12'])}
    rows['let_through'] = {
        'status': 'OPEN',
        'reason': 'The limiter trips and opens the rail; it does not regulate current. Fault current between detection '
                  '(INA301 tp <= 1 us; OPA2187 slew-limited, ~70 us typ) and switch-off is set by unsourced source, '
                  'wiring and load-side impedance, so the contract maximum cannot be shown to bound let-through. '
                  'A linear limiter in the tracking loop could not respond faster than the INA301 comparator either; '
                  'only a series current-limiting element sized for the fault energy would bound it.',
    }
    return rows


def converters():
    out = {}
    lo, typ, hi = FSW
    for rail, vo in (('+12', 12.15), ('+5', 5.075)):
        d_hi = vo / VIN_MIN
        di = (VIN_OVERSHOOT - vo) * (vo / VIN_OVERSHOOT) / (L_UH * lo)
        ipk = I_MAX[rail] + di / 2
        out[rail] = {'topology': 'buck', 'duty_at_vin_min': round(d_hi, 4), 'inductor_ripple_app_max': round(di, 4),
                     'switch_peak_a': round(ipk, 4), 'current_limit_min_a': TPS_ILIM_MIN,
                     'status': status(ipk < TPS_ILIM_MIN and ipk < L_ISAT_T)}
    vo = 12.1
    d = vo / (VIN_MIN + vo)
    il = I_MAX['-12'] / (1 - d)
    di = VIN_MIN * d / (L_UH * lo)
    ipk = il + di / 2
    vstress = VIN_OVERSHOOT + LOAD_BAND['-12'][1]
    out['-12'] = {'topology': 'inverting buck-boost (IC GND on -12 V)', 'duty_at_vin_min': round(d, 4),
                  'inductor_avg_a': round(il, 4), 'inductor_ripple_app': round(di, 4), 'switch_peak_a': round(ipk, 4),
                  'current_limit_min_a': TPS_ILIM_MIN, 'inductor_irms_typ_a': L_IRMS_T,
                  'vin_to_ic_gnd_max_v': round(vstress, 5), 'vin_operating_max_v': TPS_VIN_OP_MAX,
                  'vin_abs_max_v': TPS_VIN_ABS, 'margin_to_operating_v': round(TPS_VIN_OP_MAX - vstress, 5),
                  'status': status(ipk < TPS_ILIM_MIN and vstress < TPS_VIN_OP_MAX),
                  'note': 'U4 40 V margin issue: the old LT3015 path is removed; the inverter IC sees VIN + |Vout|'}
    out['fsw_typical_hz'] = round(typ)
    return out


def ripple():
    rows = {}
    lo = FSW[0]
    zl = 2 * math.pi * lo * L_UH
    zc_cer = 1 / (2 * math.pi * lo * C_GRM32_EFF) + GRM_ESR_T
    zc2 = 1 / (1 / C_POLY_ESR + 1 / zc_cer)
    att = zc2 / zl
    for rail, vo, n_c1 in (('+12', 12.15, 2), ('+5', 5.075, 2), ('-12', 12.1, 4)):
        c1 = n_c1 * C_GRM32_EFF
        if rail == '-12':
            d = vo / (VIN_MIN + vo)
            dv1 = I_MAX[rail] * d / (lo * c1)
        else:
            di = (VIN_OVERSHOOT - vo) * (vo / VIN_OVERSHOOT) / (L_UH * lo)
            dv1 = di / (8 * lo * c1)
        dv2 = dv1 * att
        rows[rail] = {'stage1_vpp': round(dv1, 6), 'post_filter_attenuation': round(att, 7),
                      'ideal_load_vpp': round(dv2, 9), 'limit_vpp': RIPPLE_MAX_VPP,
                      'status': 'OPEN',
                      'reason': 'Ideal LC arithmetic only. ESL, inductor self-resonance, switching-edge spikes, layout coupling '
                                'and ground return are unsourced and dominate above a few MHz; no simulation or measurement exists.'}
    return rows


def ramps():
    """Common tracking start: each output follows k x RAMP until its pair saturates."""
    rth = RAMP_NET['R'] * RAMP_NET['LOAD'] / (RAMP_NET['R'] + RAMP_NET['LOAD'])
    vf = REF_V * RAMP_NET['LOAD'] / (RAMP_NET['R'] + RAMP_NET['LOAD'])
    out = {'ramp_final_v': round(vf, 4)}
    cases = []
    for cf in (1 - RAMP_NET['C_TOL'], 1.0, 1 + RAMP_NET['C_TOL']):
        tau = rth * RAMP_NET['C'] * cf
        row = {'tau_s': round(tau, 5)}
        for rail in ('+12', '+5', '-12'):
            k = TRACK_K[rail]
            r_band = SOURCE_BAND[rail][0] / k
            row[rail] = {'slope0_v_per_ms': round(k * vf / tau / 1e3, 4),
                         'band_entry_s': round(tau * math.log(vf / (vf - r_band)), 5),
                         'saturates': k * vf > SOURCE_BAND[rail][1] + 0.5}
        entries = [row[r]['band_entry_s'] for r in ('+12', '+5', '-12')]
        row['band_entry_skew_s'] = round(max(entries) - min(entries), 5)
        row['p5_last'] = row['+5']['band_entry_s'] >= max(row['+12']['band_entry_s'], row['-12']['band_entry_s'])
        row['m12_before_p12'] = row['-12']['band_entry_s'] <= row['+12']['band_entry_s']
        cases.append(row)
    out['cases_c_tolerance'] = cases
    out['slope_status'] = status(all(c[r]['slope0_v_per_ms'] <= SLOPE_MAX_V_PER_MS[r] for c in cases for r in ('+12', '+5', '-12')))
    out['ramp_min_s'] = round(min(c[r]['band_entry_s'] for c in cases for r in ('+12', '+5', '-12')), 5)
    out['ramp_min_status'] = status(out['ramp_min_s'] >= RAMP_MIN_S)
    out['band_entry_skew_worst_s'] = round(max(c['band_entry_skew_s'] for c in cases), 5)
    out['band_entry_skew_status'] = status(out['band_entry_skew_worst_s'] <= BAND_ENTRY_SKEW_MAX_S)
    out['p5_last_status'] = status(all(c['p5_last'] for c in cases))
    out['start_skew_status'] = 'FAIL (SIM)'
    out['start_skew_note'] = ('Arithmetic cannot bound the start skew (it is set by loop dynamics and FET thresholds). '
                              'The phase-7 ngspice tracking runs give 0.55-2.26 ms against 0.41 ms '
                              '(+/-0.5 V threshold shifts, PA); see the draft page section 5.')
    rr = RAMP_RELEASE['R'] * RAMP_RELEASE['C']
    vsup = REF_V * 0 + 4.98
    out['ramp_release_delay_s'] = [round(rr * math.log(vsup / BSS_VGSTH_MAX), 5), round(rr * math.log(vsup / BSS_VGSTH_MIN_PA), 5)]
    return out


def timing():
    sup_lo = AP_VFB[0] * (1 + SUP_FB[0] * (1 - R01_TOL) / (SUP_FB[1] * (1 + R01_TOL)))
    sup_hi = AP_VFB[1] * (1 + SUP_FB[0] * (1 + R01_TOL) / (SUP_FB[1] * (1 - R01_TOL)))
    por = POR_NET['R'] * POR_NET['C']
    rdy = RDY_NET['R'] * RDY_NET['C']
    t_por = [por * math.log(sup_lo / (sup_lo - v)) for v in (BSS_VGSTH_MIN_PA, BSS_VGSTH_MAX)]
    t_rdy = [rdy * math.log(sup_lo / (sup_lo - v)) for v in (BSS_VGSTH_MIN_PA, BSS_VGSTH_MAX)]
    servo = {}
    beta = {'+12': 4.02 / (11.5 + 4.02 + 4.02), '+5': 178.02 / (184 + 178.02), '-12': 7.11 / (34.5 + 7.11)}
    for rail in ('+12', '+5', '-12'):
        g = FB_DIV[rail][0] / SERVO_RJ[rail]
        tau = SERVO_RI * SERVO_CI[rail] / (beta[rail] * g)
        servo[rail] = {'loop_tau_s': round(tau, 5), 'settle_to_0p1pct_s': round(tau * math.log(1000), 5)}
    settle = max(v['settle_to_0p1pct_s'] for v in servo.values())
    return {'p5_sup_v': [round(sup_lo, 4), round(sup_hi, 4)],
            'p5_sup_status': status(sup_lo >= OPA_SUPPLY[0] and sup_hi <= INA_VS_MAX),
            'por_s': [round(x, 5) for x in t_por], 'rdy_s': [round(x, 5) for x in t_rdy],
            'por_rdy_overlap_status': status(t_rdy[0] > t_por[1]),
            'servo': servo,
            'servo_settled_before_enable_status': status(t_rdy[0] > 5 * settle),
            'note': 'servo loop tau = RI x CI / (sense ratio x FB-top / RJ); wind-up while P5_SUP rises is bounded by the '
                    'integrator rails and recovers within the same settle time'}


def discharge():
    c12, cn, c5 = C_LOAD_MAX['+12'], C_LOAD_MAX['-12'], C_LOAD_MAX['+5']
    r12, rn, r5 = DISCHARGE_R['+12'], DISCHARGE_R['-12'], DISCHARGE_R['+5']
    t12 = r12 * c12 * math.log(LOAD_BAND['+12'][1] / DISCHARGE_LEVEL['+12'])
    tn = rn * cn * math.log(LOAD_BAND['-12'][1] / DISCHARGE_LEVEL['-12'])
    t5 = r5 * c5 * math.log(LOAD_BAND['+5'][1] / DISCHARGE_LEVEL['+5'])
    t5_order = r5 * c5 * math.log(LOAD_BAND['+5'][1] / P5_ORDER_LEVEL)
    m12_at_t12 = LOAD_BAND['-12'][1] * math.exp(-t12 / (rn * cn))
    # capacitance-ratio window for the analog ordering at zero load
    a = r12 * math.log(LOAD_BAND['+12'][1] / DISCHARGE_LEVEL['+12'])
    b = rn * math.log(LOAD_BAND['-12'][1] / DISCHARGE_LEVEL['-12'])
    c = rn * math.log(LOAD_BAND['-12'][1] / M12_WHILE_P12_ABSENT_MAX)
    ratio_hi = b / a
    ratio_lo = c / a
    p5_ratio_max = a / (r5 * math.log(LOAD_BAND['+5'][1] / P5_ORDER_LEVEL))
    en_e = 4.98 * 100e3 / 104.7e3
    v0 = en_e - 0.6                       # PA body-diode drop of Q57
    rload = 1 / (1 / HOLDUP['R_gate'] + 1 / HOLDUP['R_m12'])
    tau_h = HOLDUP['C'] * rload
    window = [tau_h * math.log(v0 / max(DMP_VGSTH[1], BSS_VGSTH_MAX)), tau_h * math.log(v0 / max(DMP_VGSTH[0], BSS_VGSTH_MIN_PA))]
    charge_tau = HOLDUP['C'] * HOLDUP['R_charge']
    q55_vgs = (v0 + LOAD_BAND['-12'][1]) * 1e6 / HOLDUP['R_m12']
    peak = {r: LOAD_BAND[r][1] / DISCHARGE_R[r] for r in DISCHARGE_R}
    return {
        'times_at_ceiling_zero_load_s': {'+12': round(t12, 5), '-12': round(tn, 5), '+5': round(t5, 5)},
        'time_limit_s': DISCHARGE_TIME_MAX_S,
        'time_status': status(max(t12, tn, t5) <= DISCHARGE_TIME_MAX_S and window[0] >= max(t12, tn, t5)),
        'holdup_window_s': [round(window[0], 5), round(window[1], 5)],
        'holdup_charge_tau_s': round(charge_tau, 5),
        'holdup_note': 'CDH is charged from EN_E only while enabled, so the window is independent of P5_SUP after a '
                       'disable, fault or unplug (review finding 8); a disable within about 3 x RDH x CDH of enable '
                       'shortens it',
        'q55_vgs_max_v': round(q55_vgs, 3),
        'p5_to_0v8_s': round(t5_order, 5), 'p12_absent_s': round(t12, 5), 'm12_absent_s': round(tn, 5),
        'm12_when_p12_absent_v': round(m12_at_t12, 4),
        'order_status_equal_ceiling_c': status(t5_order <= min(t12, tn) and t12 <= tn and m12_at_t12 <= M12_WHILE_P12_ABSENT_MAX),
        'analog_c_ratio_window': [round(ratio_lo, 4), round(ratio_hi, 4)],
        'p5_c_ratio_max_vs_p12': round(p5_ratio_max, 3),
        'loaded_order_status': 'OPEN',
        'loaded_order_reason': 'Disconnect-then-discharge leaves each rail to its own load: a rail carrying I amps on C '
                               'falls at I/C (2.0 A on 180 uF is 11 V/ms) and only the discharge resistors set the zero-load '
                               'order. Any OSC load asymmetry can make an analog rail absent first. Guaranteeing the order '
                               'needs a tracked ramp-down (RAMP falling while the pairs stay in tracking), which is a '
                               'contract change (disconnect then discharge) and is proposed, not drawn.',
        'loaded_fall_rate_v_per_ms': {r: round(I_MAX[r] / C_LOAD_MAX[r] / 1e3, 3) for r in C_LOAD_MAX},
        'discharge_peak_current_a': {r: round(v, 4) for r, v in peak.items()},
        'pulse_rating_status': 'OPEN',
        'pulse_rating_reason': 'No PROPOSED discharge resistor has an owner record. YAGEO RC1206 candidates (C137392 100R, '
                               'C137308 33R; manufacturer sheets read) give 0.25 W at 70 C and 400 V overload but no '
                               'pulse-energy curve.',
        'pulse_energy_j': {r: round(0.5 * C_LOAD_MAX[r] * LOAD_BAND[r][1] ** 2, 5) for r in C_LOAD_MAX},
        'reverse_current_after_window_status': 'OPEN',
        'reverse_current_reason': 'During the one-shot window the discharge path draws up to the peak currents above from an '
                                  'externally held inlet, above the PROPOSED 1 mA; after it, leakage plus the terminal '
                                  'sense dividers remain (calculated below). The contract pair (discharge vs 1 mA reverse) '
                                  'needs joint agreement.',
    }


def reverse_current():
    out = {}
    for rail in ('+12', '+5', '-12'):
        vmax = LOAD_BAND[rail][1]
        ov = OV_DIV[rail][0]
        if rail == '-12':
            i_div = sum((vmax + REF_V) / (x[0] + x[1]) for x in (OV_RES[rail], UV_RES[rail]))
        else:
            i_div = sum(vmax / (x[0] + x[1]) for x in (OV_RES[rail], UV_RES[rail]))
        out[rail] = {'sense_divider_current_a': round(i_div, 7), 'limit_a': REVERSE_CURRENT_MAX_A,
                     'status': 'OPEN', 'reason': 'Divider current is CALCULATED; FET and BSS138 leakage at the held voltage '
                                                 'and temperature are not retained as guaranteed values.'}
    return out


def windows():
    rows = {}
    for rail in ('+12', '+5', '-12'):
        ov = OV_DIV[rail][0]
        uv = UV_DIV[rail][0]
        tol = REF_ACC + 2 * R01_TOL + REF_TC_PPM * 1e-6 * TA_SPAN + 2 * R01_TCR * TA_SPAN
        cmp = OPA_VOS_MAX / REF_V
        ov_lo, ov_hi = ov * (1 - tol - cmp), ov * (1 + tol + cmp)
        uv_lo, uv_hi = uv * (1 - tol - cmp), uv * (1 + tol + cmp)
        src_lo, src_hi = SOURCE_BAND[rail]
        rows[rail] = {'ov_trip_v': [round(ov_lo, 4), round(ov_hi, 4)], 'ov_limit': [src_hi, OV_TRIP_MAX[rail]],
                      'uv_trip_v': [round(uv_lo, 4), round(uv_hi, 4)], 'uv_limit': [LOAD_BAND[rail][0], src_lo],
                      'tolerance_pct': round((tol + cmp) * 100, 4),
                      'status': status(ov_lo > src_hi and ov_hi <= OV_TRIP_MAX[rail] and uv_lo >= LOAD_BAND[rail][0] and uv_hi < src_lo),
                      'note': 'OPA2187 comparators against REF5025 with 0.1 % dividers (PROPOSED values); TPS3700 at +/-1 % fails the +12 V OV window'}
    return rows


def servo_authority():
    """Injection range needed to hold each pre node at its setpoint across TPS54560 VREF."""
    sp = setpoints()
    p5_lo = sp['+5']['nominal_v'] * (1 - sp['+5']['tolerance_ratio'])
    rows = {}
    for rail in ('+12', '+5', '-12'):
        rt, rb = FB_DIV[rail]
        v = sp[rail]['nominal_v']
        need = []
        for vref in (TPS_VREF[0], TPS_VREF[2]):
            for k in (1 - FB_R_TOL, 1 + FB_R_TOL):
                rt_k = rt * k
                need.append((vref * (1 + rt_k / rb) - v) / rt_k)   # current into FB, A
        if rail == '-12':
            # U5 runs from P5_PRE to M12_PRE (>= 8 V: section 6.7 swing); FB sits at -(|V| - VREF)
            sv = (-v + OPA_SWING_HV, p5_lo - OPA_SWING_HV)
            lo = sv[0] + v - TPS_VREF[0]
            avail = [lo / (SERVO_RJ[rail] * (1 + RJ_TOL if lo < 0 else 1 - RJ_TOL)),
                     (sv[1] + v - TPS_VREF[2]) / (SERVO_RJ[rail] * (1 + RJ_TOL))]
        else:
            sv = (OPA_SWING_LV, p5_lo - OPA_SWING_LV)
            avail = [(sv[0] - TPS_VREF[2]) / (SERVO_RJ[rail] * (1 - RJ_TOL)),
                     (sv[1] - TPS_VREF[2]) / (SERVO_RJ[rail] * (1 + RJ_TOL))]
        rows[rail] = {'needed_ua': [round(min(need) * 1e6, 3), round(max(need) * 1e6, 3)],
                      'available_ua': [round(avail[0] * 1e6, 3), round(avail[1] * 1e6, 3)],
                      'status': status(avail[0] < min(need) and avail[1] > max(need)),
                      'note': 'static trim range only; loop stability and startup wind-up are NOT RUN'}
    return rows


def opa_input_range():
    """OPA2187 inputs on the 5 V-only amplifiers (U4, U6, U7) must stay <= (V+) - 2 V."""
    sp = setpoints()
    p5_lo = sp['+5']['nominal_v'] * (1 - sp['+5']['tolerance_ratio'])
    vcm_max = p5_lo - OPA_VCM_HEADROOM
    worst = REF_V * (1 + REF_ACC + REF_TC_PPM * 1e-6 * TA_SPAN)
    return {'vcm_max_v': round(vcm_max, 4), 'worst_input_at_setpoint_v': round(worst, 4),
            'status': status(worst <= vcm_max),
            'note': 'at the setpoint and at window thresholds every input is at REF; a divider node above '
                    'the range during a gross overvoltage relies on the documented no-phase-reversal behaviour (T)'}


def vin_uv():
    a, b = VIN_UV_RES
    ref_half = REF_V / 2
    tol = REF_ACC + REF_TC_PPM * 1e-6 * TA_SPAN + 2 * R01_TOL + 2 * R01_TOL + OPA_VOS_MAX / ref_half
    nom = ref_half * (1 + a / b)
    lo, hi = nom * (1 - tol), nom * (1 + tol)
    sp = setpoints()
    vcm_max = sp['+5']['nominal_v'] * (1 - sp['+5']['tolerance_ratio']) - OPA_VCM_HEADROOM
    node_at_overshoot = VIN_OVERSHOOT * b / (a + b)
    return {'trip_v': [round(lo, 4), round(hi, 4)], 'trip_max_allowed_v': VIN_UV_MAX_PA,
            'node_at_vin_overshoot_v': round(node_at_overshoot, 4), 'vcm_max_v': round(vcm_max, 4),
            'status': status(hi < VIN_UV_MAX_PA and node_at_overshoot <= vcm_max)}


def gate_stress():
    vgs5 = VIN_OVERSHOOT - 5.05
    m12_pre = -(SOURCE_BAND['-12'][1] + 0.1)
    q25 = (4.98 * 1.01 - m12_pre) * 100e3 / 156e3
    return {
        '+12_vgs_max_v': round(VIN_OVERSHOOT - 12.0, 4), '+5_vgs_unclamped_v': round(vgs5, 4),
        '+5_vgs_clamped_v': VZ11[1], 'csd_vgs_max_v': CSD_VGS_MAX,
        '+12_vgs_min_at_vin_uv_v': round(16.95 - SOURCE_BAND['+12'][1] - OPA_SWING_HV, 4),
        'q25_vgs_v': round(q25, 3), 'bss_vgs_max_v': BSS_VGS_MAX,
        'status': status(VIN_OVERSHOOT - 12.0 <= CSD_VGS_MAX and VZ11[1] <= CSD_VGS_MAX and q25 <= BSS_VGS_MAX
                         and 16.95 - SOURCE_BAND['+12'][1] - OPA_SWING_HV >= 4.5),
        'note': 'BZT52C11 (cathode gate, anode common source) clamps each pair; tracking amplifiers drive the gates '
                'through 10k, so the clamp current stays below 1 mA and the 4.5 V RDS row is used throughout.',
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--json', action='store_true', help='print the full result as JSON')
    args = ap.parse_args()
    res = {
        'status_note': 'UNVALIDATED DRAFT paper screen; PASS means the arithmetic closes on the tagged inputs only',
        'setpoints_and_terminal_band': terminal_band(),
        'limiter': limiter(),
        'converters': converters(),
        'ripple': ripple(),
        'ramp': ramps(),
        'timing': timing(),
        'discharge': discharge(),
        'reverse_current': reverse_current(),
        'windows': windows(),
        'switch_gate_stress': gate_stress(),
        'servo_authority': servo_authority(),
        'opa_input_range': opa_input_range(),
        'vin_uv': vin_uv(),
    }
    if args.json:
        print(json.dumps(res, indent=2))
        return
    def line(name, st, detail):
        print(f'{st:6s} {name}: {detail}')
    for rail, r in res['setpoints_and_terminal_band'].items():
        line(f'terminal band {rail}', r['status'], f"{r['terminal_min_v']}..{r['terminal_max_v']} V in {r['band']}")
        line(f'terminal band {rail} hot (PA)', r['hot_status'].split()[0], f"min {r['terminal_min_hot_pa_v']} V")
    for rail in ('+12', '+5', '-12'):
        r = res['limiter'][rail]
        line(f'limiter {rail}', r['status'], f"trip {r['trip_min_a']}..{r['trip_max_a']} A in {r['window']}")
    line('limiter let-through', 'OPEN', 'not bounded')
    for rail in ('+12', '+5', '-12'):
        r = res['converters'][rail]
        line(f'converter {rail}', r['status'], f"switch peak {r['switch_peak_a']} A")
    line('U4 margin (-12 inverter VIN to IC GND)', res['converters']['-12']['status'],
         f"{res['converters']['-12']['vin_to_ic_gnd_max_v']} V vs {TPS_VIN_OP_MAX} V operating")
    for rail, r in res['ripple'].items():
        line(f'ripple {rail}', r['status'], f"ideal {r['ideal_load_vpp'] * 1e6:.2f} uVpp")
    rp = res['ramp']
    line('ramp slope', rp['slope_status'], ', '.join(f"{r} {max(c[r]['slope0_v_per_ms'] for c in rp['cases_c_tolerance'])} V/ms" for r in ('+12', '+5', '-12')))
    line('ramp duration', rp['ramp_min_status'], f"first band entry >= {rp['ramp_min_s'] * 1e3:.2f} ms")
    line('band-entry skew', rp['band_entry_skew_status'], f"{rp['band_entry_skew_worst_s'] * 1e3:.3f} ms (+5 last: {rp['p5_last_status']})")
    line('start skew', rp['start_skew_status'], rp['start_skew_note'])
    line('RAMP release delay', 'INFO', f"{rp['ramp_release_delay_s']} s after enable")
    tm = res['timing']
    line('P5_SUP', tm['p5_sup_status'], f"{tm['p5_sup_v']} V")
    line('POR vs RDY', tm['por_rdy_overlap_status'], f"POR {tm['por_s']} s, RDY {tm['rdy_s']} s")
    line('servo settle before enable', tm['servo_settled_before_enable_status'], ', '.join(f"{r} tau {v['loop_tau_s'] * 1e3:.2f} ms" for r, v in tm['servo'].items()))
    d = res['discharge']
    line('discharge time', d['time_status'], f"{d['times_at_ceiling_zero_load_s']}, hold-up {d['holdup_window_s']} s")
    line('discharge order', d['order_status_equal_ceiling_c'], f"+5 at 0.8 V {d['p5_to_0v8_s']} s, +12 absent {d['p12_absent_s']} s, -12 absent {d['m12_absent_s']} s, |-12| {d['m12_when_p12_absent_v']} V; C+/C- window {d['analog_c_ratio_window']}")
    line('discharge with load', 'OPEN', d['loaded_order_reason'])
    for rail, r in res['windows'].items():
        line(f'OV/UV {rail}', r['status'], f"OV {r['ov_trip_v']} in {r['ov_limit']}, UV {r['uv_trip_v']} in {r['uv_limit']}")
    g = res['switch_gate_stress']
    line('switch VGS', g['status'], f"+12 {g['+12_vgs_max_v']} V, +5 clamped {g['+5_vgs_clamped_v']} V, +12 min {g['+12_vgs_min_at_vin_uv_v']} V, Q25 {g['q25_vgs_v']} V")
    for rail, r in res['servo_authority'].items():
        line(f'servo authority {rail}', r['status'], f"need {r['needed_ua']} uA, available {r['available_ua']} uA")
    o = res['opa_input_range']
    line('OPA2187 input range (5 V amps)', o['status'], f"worst {o['worst_input_at_setpoint_v']} V <= {o['vcm_max_v']} V")
    u = res['vin_uv']
    line('VIN UV (U5B)', u['status'], f"trip {u['trip_v']} V < {u['trip_max_allowed_v']} V; node {u['node_at_vin_overshoot_v']} V at VIN overshoot <= {u['vcm_max_v']} V")
    line('converter loop stability', 'SIM', 'TPS54560 average-model AC runs (see the draft page)')


if __name__ == '__main__':
    main()
