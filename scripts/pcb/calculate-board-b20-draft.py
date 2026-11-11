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
START_SKEW_MAX_S = 0.41e-3             # CALCULATED fastest-slope proxy for the voltage-form requirement
BAND_ENTRY_SKEW_MAX_S = 2e-3            # PROPOSED in the contract
DISCHARGE_LEVEL = {'+12': 0.5, '-12': 0.6, '+5': 0.6}
DISCHARGE_TIME_MAX_S = 0.100            # PROPOSED in the contract
P5_ORDER_LEVEL = 0.8                    # +5 V must be <= 0.8 V before an analog rail is absent
M12_WHILE_P12_ABSENT_MAX = 6.0          # R-VEE: |-12| <= 6 V while +12 absent
OV_TRIP_MAX = {'+12': 12.48, '-12': 12.37, '+5': 5.20}   # PROPOSED trip = load-band maximum
REVERSE_CURRENT_MAX_A = 1e-3            # PROPOSED upstream, adopted by PD; discharge/backdrive timing unresolved

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
# Per-rail current shunts. +5 V: YAGEO PE1206FRF470R02L 20 mOhm product sheet (G).
# +/-12 V: manufacturer E16009 V9 acquired 2026-11-09 confirms B/R010/M codes.
# TCR references +20 C, unlike the existing +25 C calculation convention.
# Supplier lot revision remains unknown: retain the historical 1 W / 10 A working bound.
SHUNT = {'+12': {'r': 0.010, 'tol': 0.001, 'tcr': 15e-6, 'temperature_reference_c': 20.0,
                  'evidence': 'PRIMARY-SPEC E16009 V9; supplier lot applicability unresolved; 1 W / 10 A working bound'},
         '-12': {'r': 0.010, 'tol': 0.001, 'tcr': 15e-6, 'temperature_reference_c': 20.0,
                  'evidence': 'PRIMARY-SPEC E16009 V9; supplier lot applicability unresolved; 1 W / 10 A working bound'},
         '+5': {'r': 0.020, 'tol': 0.01, 'tcr': 100e-6, 'temperature_reference_c': 25.0, 'evidence': 'G'}}
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
# common tracking reference: REF25 -> RRMP 20k -> RAMP, CRMP 1 uF + CRMP2 470 nF (phase 9), loaded by RT12NA 93.1k
RAMP_NET = {'R': 20e3, 'C': 1.47e-6, 'C_TOL': 0.10, 'LOAD': 93.1e3}
TRACK_K = {'+12': 1 + 69.8e3 / 10e3, '+5': 1 + 23.2e3 / 10e3, '-12': 750e3 / 93.1e3}
RAMP_RELEASE = {'R': 100e3, 'C': 470e-9}
PREBIAS_R, PREBIAS_CT = 10e6, 10e-9                # RT12O / RT5O / RT12NO 10M 1 %, CT12 / CT5 / CT12N 10 nF C0G
PREBIAS_M12_PRE_MIN_V = 12.0                       # PA: M12_PRE magnitude after the -12 V pre-regulator is up      # RRMD / CRMD from EN_N to the Q12 gate (phase 10: was 100 nF)
SERVO_CI = {'+12': 1.5e-9, '+5': 1.5e-9, '-12': 270e-12}   # PROPOSED C0G integrators
SERVO_RI = 100e3
RDY_NET = {'R': 200e3, 'C': 10e-6}            # two C25803 100k + C13585 10 uF
POR_NET = {'R': 100e3, 'C': 1e-6}             # C25803 100k + CP1 C15849 1 uF
# 25 C tolerance corners for the RDY / POR timing (2026-11-11, #235): fact-c25803-tolerance 1 %, fact-c13585-tolerance
# and fact-c15849-tolerance 10 %. DC bias is the TYPICAL curve (src-c13585-dcbias-20261111 / src-c15849-dcbias-20261111,
# linear interpolation of the hashed series at the 1.5 V maximum threshold: -1.149 % / -3.169 %) applied to the short
# corner as a conservative bound; that corner actually crosses at the 0.5 V PA minimum, where the curve shows no
# reduction. X5R +/-15 % TCC (fact-c13585-dielectric, fact-c15849-dielectric) and 100 ppm/C TCR (fact-c25803-tcr) are
# NOT applied; with -15 % the short RDY corner only falls further below the servo screen.
RDY_CORNER = {'R_TOL': 0.01, 'C_TOL': 0.10, 'DC_BIAS_TYP_AT_VTH': -0.011}
POR_CORNER = {'R_TOL': 0.01, 'C_TOL': 0.10, 'DC_BIAS_TYP_AT_VTH': -0.032}
HOLD_NET = {'R': 300e3, 'C': 1e-6, 'R_TOL': 0.01, 'C_EFF': (0.6, 1.1)}   # phase 12: RHO1+RHO2 2x C22807 150k, CHO C15849; effective C range is PA (DC bias + tolerance)
SUP_FB = (52.3e3, 10e3)                       # AP63201 feedback, PROPOSED top / C95204 bottom
FB_DIV = {'+12': (145e3, 10e3), '+5': (54.9e3, 10e3), '-12': (145e3, 10e3)}   # PROPOSED top 0.1 %, C95204 bottom
SERVO_RJ = {'+12': 1e6, '+5': 1e6, '-12': 4.7e6}     # PROPOSED 1 % injection resistors
FB_R_TOL, RJ_TOL = 0.001, 0.01
VIN_UV_RES = (226e3, 18e3)  # PROPOSED 0.1 %, compared with REF/2 from two C861589 8.2 k
VIN_UV_MAX_PA = VIN_MIN       # PA: trip must stay below the minimum operating VIN
DISCHARGE_R = {'+12': 100.0, '-12': 150.0, '+5': 33.0}     # PROPOSED 1206
HOLDUP = {'C': 10e-6, 'R_gate': 100e3, 'R_m12': 470e3 + 1e6, 'R_charge': 56e3}   # CDH, R60, R61 + R62, RDH
LIMIT_DIV = {  # INA301 LIMIT dividers from REF (0.1 %); LIMIT also carries ILIMIT x (top || bot)
    '+12': {'top': 649.0, 'bot': 2.74e3},
    '+5': {'top': 3.09e3, 'bot': 1.5e3},
}
M12_LIMIT_DIV = {'top': 10.2e3 + 10.1e3, 'bot': 33.0}     # GND -> node -> -12 pre (RL3A/RL3B, RL3C)
TA_SPAN = 20.0                 # PA: +/-20 C around the 25 C reference
# window dividers (PROPOSED E192 0.1 %): positive rails top/bottom to GND, -12 V REF-to-terminal
OV_RES = {'+12': (47.5e3, 12e3), '+5': (26.4e3, 24.9e3), '-12': (118e3, 24e3)}
UV_RES = {'+12': (172e3, 46.4e3), '+5': (10.4e3, 10.7e3), '-12': (301e3, 63.4e3)}


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


def shunt_temperature_span(shunt):
    # Preserve the original PA operating interval: 25 +/-20 C = 5..45 C.
    # Do not re-center that interval when the manufacturer's reference differs.
    return max(abs(t - shunt['temperature_reference_c']) for t in (25.0 - TA_SPAN, 25.0 + TA_SPAN))


def limiter():
    rows = {}
    for rail in ('+12', '+5'):
        d = LIMIT_DIV[rail]
        rth = d['top'] * d['bot'] / (d['top'] + d['bot'])
        vdiv = REF_V * d['bot'] / (d['top'] + d['bot'])
        vlim = vdiv + INA_ILIMIT[1] * rth
        sh = SHUNT[rail]
        rs = sh['r']
        itrip = vlim / (INA_GAIN * rs)
        vsense = itrip * rs
        err = sh['tol'] + sh['tcr'] * shunt_temperature_span(sh) + INA_GAIN_ERR + INA_VOS / vsense \
            + INA_CMP_VOS / vlim + (REF_ACC + 2 * R01_TOL) * vdiv / vlim \
            + (INA_ILIMIT[2] - INA_ILIMIT[1]) * rth / vlim
        lo, hi = itrip * (1 - err), itrip * (1 + err)
        rows[rail] = {'device': 'INA301A3 comparator, transparent mode', 'limit_v': round(vlim, 5),
                      'divider_v': round(vdiv, 5), 'ilimit_shift_v': round(INA_ILIMIT[1] * rth, 5),
                      'trip_nominal_a': round(itrip, 5), 'tolerance_pct': round(err * 100, 3),
                      'trip_min_a': round(lo, 5), 'trip_max_a': round(hi, 5),
                      'window': [I_TRANSIENT_MIN[rail], I_MAX[rail]],
                      'ina_out_at_trip_v': round(vlim, 4), 'shunt_evidence': sh['evidence'],
                      'status': status(lo > I_TRANSIENT_MIN[rail] and hi <= I_MAX[rail])}
    sp = setpoints()['-12']
    k = M12_LIMIT_DIV['bot'] / (M12_LIMIT_DIV['top'] + M12_LIMIT_DIV['bot'])
    vmag = sp['nominal_v']
    vref = vmag * k
    sh = SHUNT['-12']
    rs = sh['r']
    itrip = vref / rs
    err = sh['tol'] + sh['tcr'] * shunt_temperature_span(sh) + sp['tolerance_ratio'] + 2 * R01_TOL + OPA_VOS_MAX / vref \
        + I_MAX['-12'] * path_resistance('-12') / vmag
    lo, hi = itrip * (1 - err), itrip * (1 + err)
    rows['-12'] = {'device': 'OPA2187 comparator on the -12 V pre-node shunt', 'reference_v': round(vref, 6),
                   'trip_nominal_a': round(itrip, 5), 'tolerance_pct': round(err * 100, 3),
                   'trip_min_a': round(lo, 5), 'trip_max_a': round(hi, 5),
                   'window': [I_TRANSIENT_MIN['-12'], I_MAX['-12']], 'shunt_evidence': sh['evidence'],
                   'status': status(lo > I_TRANSIENT_MIN['-12'] and hi <= I_MAX['-12'])}
    for rail in ('+12', '-12'):
        sh = SHUNT[rail]
        delta = shunt_temperature_span(sh)
        rmax = sh['r'] * (1 + sh['tol'] + sh['tcr'] * delta)
        rows[rail]['shunt_temperature_screen'] = {
            'operating_interval_c': [25.0 - TA_SPAN, 25.0 + TA_SPAN],
            'reference_c': sh['temperature_reference_c'], 'maximum_delta_c': delta,
            'resistance_max_ohm': rmax,
            'power_at_contract_max_w': I_MAX[rail] ** 2 * rmax,
            'working_power_bound_w': 1.0,
            'limit': 'Arithmetic at contractual current only; no measured temperature, fault-current or let-through bound.'}
    rows['let_through'] = {
        'status': 'OPEN',
        'reason': 'The limiter trips and opens the rail; it does not regulate current. Fault current between detection '
                  '(INA301 tp <= 1 us; OPA2187 slew-limited, ~70 us typ) and switch-off is set by unsourced source, '
                  'wiring and load-side impedance, so the contract maximum cannot be shown to bound let-through. '
                  'A linear limiter in the tracking loop could not respond faster than the INA301 comparator either; '
                  'only a series current-limiting element sized for the fault energy would bound it.',
    }
    return rows


STARTUP_LOAD_REF_V = {'+12': 12.0, '-12': 12.0, '+5': 5.0}   # PA: transient-load minimum defined at nominal


def limiter_startup():
    """Resistive start into the full transient load: the peak draw is I_min x Vterm_max / Vnom.

    The servo time constant (~5 ms) is longer than the load RC, so charging does not add to the peak.
    """
    tb = terminal_band()
    lim = limiter()
    sp = setpoints()
    rows = {}
    floor = {r: I_TRANSIENT_MIN[r] * tb[r]['terminal_max_v'] / STARTUP_LOAD_REF_V[r] for r in I_MAX}
    for r in ('+12', '+5', '-12'):
        rows[r] = {'startup_floor_a': round(floor[r], 5), 'present_trip_min_a': lim[r]['trip_min_a'],
                   'present_status': status(lim[r]['trip_min_a'] > floor[r]),
                   'shunt_evidence': SHUNT[r]['evidence']}
    # Let-through: a series inductance that holds di/dt so the current cannot pass I_MAX before switch-off
    # needs L >= V x t_off / (I_MAX - trip_max); t_off is not guaranteed anywhere, 2 us is illustrative.
    t_off = 2e-6
    rows['let_through_series_l'] = {
        r: {'l_needed_h_at_2us': round(SOURCE_BAND[r][1] * t_off / (I_MAX[r] - lim[r]['trip_max_a']), 6)}
        for r in ('+12', '-12', '+5')}
    rows['let_through_series_l']['status'] = 'OPEN'
    rows['let_through_series_l']['reason'] = ('A series element that bounds a hard short to I_MAX needs millihenries '
                                              '(infeasible at 2 A) or a regulating current limit; switch-off time is not '
                                              'guaranteed by any retained source. No excess-current charge/time budget is adopted; '
                                              'the existing maximum still requires supported compliance or explicit contract agreement.')
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


ESL_MLCC_PA = 0.5e-9      # PA: per 1210 MLCC incl. vias; not a manufacturer bound
ESL_POLY_PA = 1.0e-9      # PA: polymer can incl. vias
EDGE_PA = 20e-9           # PA: inverter switch-node current edge time


def ripple_injection():
    """Averaged + ripple-injection estimate (NOT a switching simulation).

    The converter is replaced by its averaged DC operating point plus an injected periodic switching
    current at FSW minimum: a buck inductor triangle (peak-to-peak from VIN_OVERSHOOT) or the inverter
    rectangular diode current (IL at VIN_MIN, I_MAX). The current drives the linear stage-1 MLCC bank,
    the 10 uH post filter (DCR max) and the polymer + MLCC output bank; the periodic steady state is the
    harmonic superposition of the injected spectrum times the network transfer impedance.
    """
    import numpy as np
    f0 = FSW[0]
    n = 8192
    t = np.arange(n) / (n * f0)
    w = 2 * np.pi * np.fft.rfftfreq(n, 1 / (n * f0))
    w[0] = 1.0
    def zc(c, esr, esl, k):
        return (1 / (1j * w * c) + esr + 1j * w * esl) / k
    rows = {}
    for rail, vo, n_c1 in (('+12', 12.15, 2), ('+5', 5.075, 2), ('-12', 12.1, 4)):
        rload = vo / I_MAX[rail]
        z1 = zc(C_GRM32_EFF, GRM_ESR_T, ESL_MLCC_PA, n_c1)
        z2 = 1 / (1 / zc(C_POLY, C_POLY_ESR, ESL_POLY_PA, 1) + 1 / zc(C_GRM32_EFF, GRM_ESR_T, ESL_MLCC_PA, 1)
                  + 1 / rload)
        zf = 1j * w * L_UH + L_DCR_MAX
        zin = 1 / (1 / z1 + 1 / (zf + z2))
        h_out = zin * z2 / (zf + z2)
        tt = t * f0
        if rail == '-12':
            d = vo / (VIN_MIN + vo)
            il = I_MAX[rail] / (1 - d)
            e = EDGE_PA * f0
            hi = np.clip((tt - d) / e, 0, 1) - np.clip((tt - 1 + e) / e, 0, 1)
            i = il * hi - I_MAX[rail]
            src = f'inverter diode current IL {il:.4f} A, D {d:.4f}, edges {EDGE_PA * 1e9:.0f} ns (PA)'
        else:
            d = vo / VIN_OVERSHOOT
            di = (VIN_OVERSHOOT - vo) * d / (L_UH * f0)
            i = np.where(tt < d, -di / 2 + di * tt / d, di / 2 - di * (tt - d) / (1 - d))
            src = f'buck triangle {di:.4f} App, D {d:.4f} at VIN {VIN_OVERSHOOT:.3f} V'
        spec = np.fft.rfft(i - i.mean())
        spec[0] = 0
        v1 = np.fft.irfft(spec * zin, n)
        v2 = np.fft.irfft(spec * h_out, n)
        vpp = float(v2.max() - v2.min())
        rows[rail] = {'method': 'AVERAGED + RIPPLE INJECTION (linear periodic steady state; not a switching simulation)',
                      'injected_current': src, 'fsw_hz': round(f0), 'stage1_vpp': round(float(v1.max() - v1.min()), 6),
                      'output_vpp': round(vpp, 9), 'limit_vpp': RIPPLE_MAX_VPP,
                      'margin_factor': round(RIPPLE_MAX_VPP / vpp, 1),
                      'status': 'OPEN',
                      'reason': 'Estimate only: MLCC/polymer ESL, inductor self-resonance, switch-node dv/dt coupling, '
                                'ground-return impedance and the measurement bandwidth are PA or unsourced, and no '
                                'switching transient model converged; PASS needs a bench measurement.'}
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
    out['historical_phase10_slope_sim_status'] = 'PASS (SIM) at the I_TRANSIENT_MIN load; FAIL (SIM) at no load'
    out['historical_phase10_slope_sim_note'] = ('Phase-10 ngspice runs (manufacturing/sim/board-b20-phase10, CRMD 470 nF): 0.322 / 0.134 / 0.322 V/ms in the '
                             'four completed loaded runs (all threshold shifts); at no load +5 V 0.85-0.90 V/ms and -12 V 1.21-1.47 V/ms '
                             '(adv fails the 1.22 row). Phase 9 (100 nF) gave +5 V 0.53-1.03 V/ms in every run. No-load cause: the '
                             'source-only pairs overshoot their pre-bias targets, cannot pull the output back without a load, and the '
                             'integrators wind to their rails again before RAMP moves. The owner recorded bounded exceptions '
                             '(2026-11-03, card cmsg_01Pv35emdXEU6gCRF3teSpo2GzmXCn8kfxsnNg5p6WdFzN: no load only, '
                             '+5 V <= 0.95 V/ms below 0.45 V at <=114 mA, -12 V <= 1.47 V/ms below 0.75 V at <=265 mA; '
                             'loaded starts keep the contract slopes). This historical average is not current compliance evidence.')
    out['slope_sim_status'] = 'OPEN (PRE-ORDER HOLD)'
    out['slope_sim_note'] = ('Actual phase33 adjacent-sample analysis and 2 us refinements on 2026-11-09 expose no-load '
                            'slope/current excess beyond those recorded exception ceilings. Small negative increments also '
                            'remain. See manufacturing/sim/board-b20-phase33/startup-refinement.md and its hash-bound '
                            'receipt. This calculator does not execute the solver or establish physical compliance.')
    out['start_skew_criterion_authority'] = 'CALCULATED fastest-slope proxy; keep the direct voltage-form requirements separate'
    out['band_entry_criterion_authority'] = 'PROPOSED upstream 2 ms criterion; not silently promoted to CONTRACT'
    out['start_skew_status'] = 'HISTORICAL SIM: CALCULATED proxy exceeded'
    out['start_skew_note'] = ('Arithmetic cannot bound the time-form start skew (loop dynamics and FET thresholds). '
                              'The phase-10 ngspice runs (CRMD 470 nF) give 2.24-3.93 ms against 0.41 ms (phase 9: 1.16-2.42 ms), '
                              'while the voltage forms it derives from pass in every completed run; see the draft page section 5d.')
    rr = RAMP_RELEASE['R'] * RAMP_RELEASE['C']
    vsup = REF_V * 0 + 4.98
    out['ramp_release_delay_s'] = [round(rr * math.log(vsup / BSS_VGSTH_MAX), 5), round(rr * math.log(vsup / BSS_VGSTH_MIN_PA), 5)]
    # Pre-bias climb (phase 10): after enable each tracking integrator leaves its rail at I = |M12_PRE| / 10M on its 10 nF
    # CT; RAMP must stay reset until every gate reaches conduction. CSD18543Q3A VGS(th) is not in its bundle, so the
    # climb available before the earliest release is stated, not compared with a threshold.
    climb = PREBIAS_M12_PRE_MIN_V / (PREBIAS_R * (1 + RJ_TOL)) / PREBIAS_CT
    out['prebias_gate_climb_v_per_s'] = round(climb, 3)
    out['prebias_gate_climb_before_release_min_v'] = round(climb * out['ramp_release_delay_s'][0], 3)
    out['prebias_status'] = 'UNSOURCED (CSD18543Q3A VGS(th) not in bundle); SIM: every loaded run reaches its pre-bias plateau before RAMP moves'
    return out


# Start-sequence construction, DRAWN in board_b20_spec.py (phase 9) and simulated in
# manufacturing/sim/board-b20-phase9/. Each tracking target is the minimum of its RAMP term and a
# clamp from the other rails' actual output voltages (U15/U16 OPA2187, BSS138 body-diode clamps):
#   |-12| <= A_M12 x V(+12)             LVLM12 = P12_OUT x 10.2k / (64.9k + 10.2k), RAMP_M12 scale
#   V(+12) <= A_P12 x |-12| + OFF_P12   MABS = |-12| x 15k / 100k; LVL12 = 102k/9.76k gain, 30.1k/10k REF offset
#   V(+5) <= C_P5 x |-12|               MABS against RAMP_P5 (with |-12| <= A_M12 x V(+12), +5 also trails +12)
# Followers only lag their targets and the contract excludes overshoot, so every clamp inequality
# holds on the actual outputs; precision-clamp amplifier and diode errors are PA (CLAMP_TOL, not bounded).
SEQ = {'A_M12': 1.0947, 'A_P12': 1.0990, 'OFF_P12': 0.407, 'C_P5': 0.498,
       'OFF_P5': {'drawn': 0.0}, 'RAMP_C': RAMP_NET['C'], 'CLAMP_TOL': 0.01}
P59A_P12_AT = 5.2            # +12 V level below which |-12| must stay <= 6 V (P59-A)
P59A_M12_MAX = 6.0
ONE_RAIL_P12_MAX = 0.5       # unconditional: +12 V alone <= 0.5 V
ONE_RAIL_M12_MAX = 6.0       # unconditional: -12 V alone <= 6 V


def start_sequence_proposal():
    tb = terminal_band()
    rth = RAMP_NET['R'] * RAMP_NET['LOAD'] / (RAMP_NET['R'] + RAMP_NET['LOAD'])
    vf = REF_V * RAMP_NET['LOAD'] / (RAMP_NET['R'] + RAMP_NET['LOAD'])
    tau_max = rth * SEQ['RAMP_C'] * (1 + RAMP_NET['C_TOL'])
    tau_min = rth * SEQ['RAMP_C'] * (1 - RAMP_NET['C_TOL'])
    slope = {r: TRACK_K[r] * vf / tau_min / 1e3 for r in ('+12', '+5', '-12')}
    slope['-12_clamped'] = SEQ['A_M12'] * (1 + SEQ['CLAMP_TOL']) * slope['+12']
    slope['+12_clamped'] = SEQ['A_P12'] * (1 + SEQ['CLAMP_TOL']) * slope['-12']
    analog_slope = max(slope['+12'], slope['-12'], slope['-12_clamped'], slope['+12_clamped'])
    slope['+5_clamped'] = SEQ['C_P5'] * (1 + SEQ['CLAMP_TOL']) * analog_slope
    entries = {}
    for r in ('+12', '+5', '-12'):
        rb = SOURCE_BAND[r][0] / TRACK_K[r]
        entries[r] = [tau_min * math.log(vf / (vf - rb)), tau_max * math.log(vf / (vf - rb))]
    p12_alone = SEQ['OFF_P12'] * (1 + SEQ['CLAMP_TOL'])
    m12_at_p12_absent = SEQ['A_M12'] * (1 + SEQ['CLAMP_TOL']) * ONE_RAIL_P12_MAX
    m12_at_5v2 = SEQ['A_M12'] * (1 + SEQ['CLAMP_TOL']) * P59A_P12_AT
    sat = {'+12': min(TRACK_K['+12'] * vf, SEQ['A_P12'] * (1 - SEQ['CLAMP_TOL']) * tb['-12']['terminal_min_v'] + SEQ['OFF_P12'])
           - (SOURCE_BAND['+12'][1] + 0.5),
           '-12': min(TRACK_K['-12'] * vf, SEQ['A_M12'] * (1 - SEQ['CLAMP_TOL']) * tb['+12']['terminal_min_v'])
           - (SOURCE_BAND['-12'][1] + 0.5)}
    variants = {}
    for name, off in SEQ['OFF_P5'].items():
        amin = tb['-12']['terminal_min_v']
        sat5 = min(TRACK_K['+5'] * vf, SEQ['C_P5'] * (1 - SEQ['CLAMP_TOL']) * (amin - off)) - (SOURCE_BAND['+5'][1] + 0.5)
        hold = off + P5_ORDER_LEVEL / (SEQ['C_P5'] * (1 - SEQ['CLAMP_TOL']))
        variants[name] = {'off_p5_v': off, 'p5_le_0v8_until_absm12_v': round(hold, 3),
                          'p5_le_0v8_until_p12_v': round(hold / (SEQ['A_M12'] * (1 + SEQ['CLAMP_TOL'])), 3),
                          'p5_starts_after_both_analog_v': off,
                          'p5_start_lag_s_at_fastest_slope': round(off / analog_slope / 1e3, 5),
                          'p5_overdrive_v': round(sat5, 3)}
    rows = {
        'construction': 'DRAWN in board_b20_spec.py (phase 9); simulated in manufacturing/sim/board-b20-phase9 (SIM, not a bound)',
        'ramp_c_f': SEQ['RAMP_C'], 'slopes_v_per_ms': {k: round(v, 4) for k, v in slope.items()},
        'slope_status': status(slope['+12'] <= SLOPE_MAX_V_PER_MS['+12'] and slope['+12_clamped'] <= SLOPE_MAX_V_PER_MS['+12']
                               and max(slope['-12'], slope['-12_clamped']) <= SLOPE_MAX_V_PER_MS['-12']
                               and max(slope['+5'], slope['+5_clamped']) <= SLOPE_MAX_V_PER_MS['+5']),
        'first_band_entry_min_s': round(min(e[0] for e in entries.values()), 5),
        'band_entry_skew_max_s': round(max(e[1] for e in entries.values()) - min(e[1] for e in entries.values()), 5),
        'pair_overdrive_v': {k: round(v, 3) for k, v in sat.items()},
        'unconditional': {
            'p12_alone_max_v': round(p12_alone, 4), 'p12_alone_limit_v': ONE_RAIL_P12_MAX,
            'p12_alone_margin_v': round(ONE_RAIL_P12_MAX - p12_alone, 4),
            'm12_while_p12_le_0v5_max_v': round(m12_at_p12_absent, 4), 'm12_alone_limit_v': ONE_RAIL_M12_MAX,
            'm12_alone_margin_v': round(ONE_RAIL_M12_MAX - m12_at_p12_absent, 4),
            'start_skew_basis': 'The 0.41 ms row is the time form of +12 V alone <= 0.5 V at the fastest slope (A1); '
                                'the construction meets the voltage form directly, independent of FET thresholds.',
            'status': 'PASS (drawn construction, arithmetic, clamp errors PA)'
                      if p12_alone < ONE_RAIL_P12_MAX and m12_at_p12_absent < ONE_RAIL_M12_MAX else 'FAIL'},
        'p59a': {
            'm12_at_p12_5v2_max_v': round(m12_at_5v2, 4), 'limit_v': P59A_M12_MAX,
            'margin_v': round(P59A_M12_MAX - m12_at_5v2, 4),
            'm12_lead_time_s_at_6v': round((P59A_M12_MAX - P59A_M12_MAX / (SEQ['A_M12'] * (1 + SEQ['CLAMP_TOL']))) / slope['+12'] / 1e3, 5),
            'm12_lead_limit_s': round(0.069 * SOURCE_BAND['+12'][1] / slope['+12'] / 1e3, 5),
            'm12_lead_limit_basis': '0.069 x ramp time, ramp time = +12 V source-band maximum / steepest +12 V slope',
            'p12_lead': 'no R-VEE limit under P59-A; with +5 V present the single analog rail stays <= '
                        f'{p12_alone:.3f} V, far below 8 V (the 6.50 ms row)',
            'status': 'PASS (drawn construction, arithmetic, 25 C P59-A rows)' if m12_at_5v2 < P59A_M12_MAX else 'FAIL'},
        'p5_variants': variants,
        'p5_hold_conflict': ('Holding +5 V <= 0.8 V until both analog rails are inside their source bands is not '
                             'compatible with the common-ramp rows: +5 V then needs >= '
                             f"{(SOURCE_BAND['+5'][0] - P5_ORDER_LEVEL) / SLOPE_MAX_V_PER_MS['+5']:.2f} ms at 0.51 V/ms after "
                             'analog band entry, against the 2 ms band-entry skew (PROPOSED) and the one-common-ramp shape '
                             '(CONTRACT). The drawn clamp holds +5 V <= 0.8 V only until |-12| reaches about 1.6 V; OSC '
                             'must say which level "both analog rails up" means.'),
    }
    return rows


def timing():
    sup_lo = AP_VFB[0] * (1 + SUP_FB[0] * (1 - R01_TOL) / (SUP_FB[1] * (1 + R01_TOL)))
    sup_hi = AP_VFB[1] * (1 + SUP_FB[0] * (1 + R01_TOL) / (SUP_FB[1] * (1 - R01_TOL)))
    por = POR_NET['R'] * POR_NET['C']
    rdy = RDY_NET['R'] * RDY_NET['C']
    t_por_nom = [por * math.log(sup_lo / (sup_lo - v)) for v in (BSS_VGSTH_MIN_PA, BSS_VGSTH_MAX)]
    t_rdy_nom = [rdy * math.log(sup_lo / (sup_lo - v)) for v in (BSS_VGSTH_MIN_PA, BSS_VGSTH_MAX)]

    def short(c):
        return (1 - c['R_TOL']) * (1 - c['C_TOL']) * (1 + c['DC_BIAS_TYP_AT_VTH'])

    def long_(c):
        return (1 + c['R_TOL']) * (1 + c['C_TOL'])
    # The short corner takes the high supply (earlier crossing); t_*_nom keeps the recorded low-supply history.
    early = math.log(sup_hi / (sup_hi - BSS_VGSTH_MIN_PA))
    t_por = [por * early * short(POR_CORNER), t_por_nom[1] * long_(POR_CORNER)]
    t_rdy = [rdy * early * short(RDY_CORNER), t_rdy_nom[1] * long_(RDY_CORNER)]
    servo = {}
    beta = {'+12': 4.02 / (11.5 + 4.02 + 4.02), '+5': 178.02 / (184 + 178.02), '-12': 7.11 / (34.5 + 7.11)}
    for rail in ('+12', '+5', '-12'):
        g = FB_DIV[rail][0] / SERVO_RJ[rail]
        tau = SERVO_RI * SERVO_CI[rail] / (beta[rail] * g)
        servo[rail] = {'loop_tau_s': round(tau, 5), 'settle_to_0p1pct_s': round(tau * math.log(1000), 5)}
    settle = max(v['settle_to_0p1pct_s'] for v in servo.values())
    # phase 12 minimum-off interlock: EN_HO charges from P5_SUP after a disable; Q66 completes the set path at its VGS(th)
    h = HOLD_NET
    hold = [h['R'] * (1 - h['R_TOL']) * h['C'] * h['C_EFF'][0] * math.log(sup_hi / (sup_hi - BSS_VGSTH_MIN_PA)),
            h['R'] * (1 + h['R_TOL']) * h['C'] * h['C_EFF'][1] * math.log(sup_lo / (sup_lo - BSS_VGSTH_MAX))]
    rr = RAMP_RELEASE['R'] * RAMP_RELEASE['C']
    reset_engaged_max = rr * math.log(sup_lo / (sup_lo - BSS_VGSTH_MAX))
    nominal = {'por_s': [round(x, 5) for x in t_por_nom], 'rdy_s': [round(x, 5) for x in t_rdy_nom],
               'min_off_hold_status': status(hold[0] >= reset_engaged_max and hold[1] < t_rdy_nom[0]),
               'por_rdy_overlap_status': status(t_rdy_nom[0] > t_por_nom[1]),
               'servo_settled_before_enable_status': status(t_rdy_nom[0] > 5 * settle),
               'note': 'historical nominal-RC result (no R/C tolerance); superseded 2026-11-11 by the corner rows'}
    return {'p5_sup_v': [round(sup_lo, 4), round(sup_hi, 4)],
            'corner_basis': ('por_s / rdy_s are 25 C tolerance [short, long] corners: short = high P5_SUP, 0.5 V PA '
                             'threshold, R -1 %, C -10 %, TYPICAL DC bias at the 1.5 V maximum threshold as a conservative '
                             'bound; long = low P5_SUP, R +1 %, C +10 %. X5R TCC and resistor TCR are not applied. '
                             'The servo 5x settle margin is a PROJECT screen.'),
            'nominal': nominal,
            'min_off_hold_s': [round(x, 5) for x in hold], 'ramp_reset_engaged_by_s': round(reset_engaged_max, 5),
            'min_off_hold_status': status(hold[0] >= reset_engaged_max and hold[1] < t_rdy[0]),
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
                               'order. OSC load asymmetry can make an analog rail absent first. Guaranteed order '
                               'is not established. Tracked ramp-down while the pairs stay in tracking is only one proposal; '
                               'it changes the accepted disconnect-before-discharge contract and requires explicit agreement. '
                               'Loaded asymmetric discharge remains a pre-order gate.',
        'loaded_fall_rate_v_per_ms': {r: round(I_MAX[r] / C_LOAD_MAX[r] / 1e3, 3) for r in C_LOAD_MAX},
        'discharge_peak_current_a': {r: round(v, 4) for r, v in peak.items()},
        'pulse_rating_status': 'OPEN',
        'pulse_rating_reason': 'The installed UNI-ROYAL 1206W4F1000T5E/C17901, 1206W4F1500T5E/C17917 and '
                               '1206W4F330JT5E/C18005 have exact owner records. The retained V.7 short-time overload '
                               'test bounds the recorded single-event screen only; repetitive discharge endurance is '
                               'UNSOURCED. See manufacturing/pd20-evidence-research.md; no substitute is adopted.',
        'pulse_energy_j': {r: round(0.5 * C_LOAD_MAX[r] * LOAD_BAND[r][1] ** 2, 5) for r in C_LOAD_MAX},
        'reverse_current_after_window_status': 'OPEN',
        'reverse_current_reason': 'During the one-shot window the discharge path draws up to the peak currents above from an '
                                  'externally held inlet, above the upstream-proposed, PD-adopted 1 mA; after it, leakage plus the terminal '
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
        'limiter_startup': limiter_startup(),
        'converters': converters(),
        'ripple': ripple(),
        'ripple_injection': ripple_injection(),
        'ramp': ramps(),
        'start_sequence_proposal': start_sequence_proposal(),
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
    ls = res['limiter_startup']
    for rail in ('+12', '-12', '+5'):
        r = ls[rail]
        line(f'startup into full load {rail}', r['present_status'], f"floor {r['startup_floor_a']} A vs trip min {r['present_trip_min_a']} A")
    line('let-through series L', 'OPEN', ', '.join(f"{k} {v['l_needed_h_at_2us'] * 1e3:.2f} mH" for k, v in ls['let_through_series_l'].items() if isinstance(v, dict)))
    for rail in ('+12', '+5', '-12'):
        r = res['converters'][rail]
        line(f'converter {rail}', r['status'], f"switch peak {r['switch_peak_a']} A")
    line('U4 margin (-12 inverter VIN to IC GND)', res['converters']['-12']['status'],
         f"{res['converters']['-12']['vin_to_ic_gnd_max_v']} V vs {TPS_VIN_OP_MAX} V operating")
    for rail, r in res['ripple'].items():
        line(f'ripple {rail}', r['status'], f"ideal {r['ideal_load_vpp'] * 1e6:.2f} uVpp")
    for rail, r in res['ripple_injection'].items():
        line(f'ripple injection {rail}', r['status'], f"{r['output_vpp'] * 1e6:.2f} uVpp at output, stage 1 {r['stage1_vpp'] * 1e3:.2f} mVpp (averaged + injection, labelled)")
    rp = res['ramp']
    line('ramp slope', rp['slope_status'], ', '.join(f"{r} {max(c[r]['slope0_v_per_ms'] for c in rp['cases_c_tolerance'])} V/ms" for r in ('+12', '+5', '-12')))
    line('ramp duration', rp['ramp_min_status'], f"first band entry >= {rp['ramp_min_s'] * 1e3:.2f} ms")
    line('band-entry skew', rp['band_entry_skew_status'], f"{rp['band_entry_skew_worst_s'] * 1e3:.3f} ms (+5 last: {rp['p5_last_status']})")
    line('start skew', rp['start_skew_status'], rp['start_skew_note'])
    line('ramp slope (sim)', rp['slope_sim_status'], rp['slope_sim_note'])
    sq = res['start_sequence_proposal']
    line('start sequence (drawn) slopes', sq['slope_status'], str(sq['slopes_v_per_ms']))
    line('start sequence (drawn) ramp / band skew', status(sq['first_band_entry_min_s'] >= RAMP_MIN_S and sq['band_entry_skew_max_s'] <= BAND_ENTRY_SKEW_MAX_S),
         f"first entry {sq['first_band_entry_min_s'] * 1e3:.2f} ms, skew {sq['band_entry_skew_max_s'] * 1e3:.3f} ms, overdrive {sq['pair_overdrive_v']}")
    u = sq['unconditional']
    line('start sequence unconditional', u['status'].split()[0], f"+12 alone <= {u['p12_alone_max_v']} V (margin {u['p12_alone_margin_v']} V), |-12| while +12 <= 0.5 V <= {u['m12_while_p12_le_0v5_max_v']} V")
    q = sq['p59a']
    line('start sequence P59-A', q['status'].split()[0], f"|-12| at +12 = 5.2 V <= {q['m12_at_p12_5v2_max_v']} V (margin {q['margin_v']} V); lead at 6 V {q['m12_lead_time_s_at_6v'] * 1e3:.3f} ms vs {q['m12_lead_limit_s'] * 1e3:.2f} ms")
    for k, v in sq['p5_variants'].items():
        line(f'+5 hold ({k})', 'INFO', f"+5 <= 0.8 V until |-12| >= {v['p5_le_0v8_until_absm12_v']} V (+12 >= {v['p5_le_0v8_until_p12_v']} V), start lag {v['p5_start_lag_s_at_fastest_slope'] * 1e3:.2f} ms, overdrive {v['p5_overdrive_v']} V")
    line('RAMP release delay', 'INFO', f"{rp['ramp_release_delay_s']} s after enable")
    line('Pre-bias gate climb before RAMP release', 'INFO', f"{rp['prebias_gate_climb_v_per_s']} V/s, >= {rp['prebias_gate_climb_before_release_min_v']} V by the earliest release; {rp['prebias_status']}")
    tm = res['timing']
    line('P5_SUP', tm['p5_sup_status'], f"{tm['p5_sup_v']} V")
    line('POR vs RDY', tm['por_rdy_overlap_status'], f"POR {tm['por_s']} s, RDY {tm['rdy_s']} s")
    line('Minimum-off interlock', tm['min_off_hold_status'], f"hold {tm['min_off_hold_s']} s after a disable; RAMP reset engaged by {tm['ramp_reset_engaged_by_s']} s; before RDY {tm['rdy_s'][0]} s")
    five_settle = 5 * max(v['settle_to_0p1pct_s'] for v in tm['servo'].values())
    line('servo settle before enable', tm['servo_settled_before_enable_status'],
         f"RDY short corner {tm['rdy_s'][0]} s vs 5 x settle {five_settle:.5f} s (PROJECT screen); "
         + ', '.join(f"{r} tau {v['loop_tau_s'] * 1e3:.2f} ms" for r, v in tm['servo'].items()))
    line('servo settle before enable (nominal RC, historical)', tm['nominal']['servo_settled_before_enable_status'],
         f"RDY {tm['nominal']['rdy_s'][0]} s; superseded by the corner row")
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
