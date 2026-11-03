#!/usr/bin/env python3
"""Screen arithmetic for the 20 V Board P input-protection topologies (analysis only).

Reproduces the tables in manufacturing/input-protection-20v.md. Every input is
tagged with its evidence class; nothing here is a measurement or an adopted value.

Gate L7 is FAIL on guaranteed figures (phase 8, Board P r3: LM74700 + Q3, then TPS16630).
VBUS_P is fed only forward through Q3 and U2, so it cannot rise above VBUS_IN except by
PCB parasitic inductance, which is unquantified. VBUS_IN is bounded only by the TVS2200
clamp rows: 27.7 V (24 A, 27 C), 28.0 V (40 A, 27 C) and 28.35 V (35 A, 125 C), against
the STUSB4500 28 V absolute maximum. A tighter VBUS_P bound (trip plus let-through into
the bulk) needs a guaranteed peak current through U2 during OVP_toff(dly); SLVSET9G gives
the fast-trip threshold and I(SCP) as TYP only, so a guaranteed bulk ESR alone cannot
close the gate. The TYP let-through rows below are a sensitivity, never a bound.
"""

import argparse
import json
import math

# STUSB4500 DS12499 Rev 8 Table 20 (G-U, owner bundle mirror evidence).
STUSB_VBUS_ABS_MAX_V = 28.0
STUSB_CC_ABS_MAX_V = 22.0

# USB PD 20 V fixed PDO, project +/-5 % source range (PA; no primary PD text retained).
VBUS_20V_MAX_V = 21.0
# Project guard between the highest legitimate VBUS and the lowest OVP trip (PA).
TRIP_GUARD_V = 0.5

# TI TPS1663 SLVSET9G (G, retrieved 2026-10-31): the TPS16630 V(OVPR), OVP_toff, I(OL) and RON rows
# carry the same limits the r2 TPS26630 (SLVSE94G) analysis used.
VOVPR_MIN, VOVPR_TYP, VOVPR_MAX = 1.176, 1.2, 1.224
VOVPF_MIN, VOVPF_MAX = 1.09, 1.15
OVP_TOFF_MAX_S = 14e-6  # OVP rising to FLT low; FET-off coincidence is PA
IOL_MAX_A_4K02 = 4.815  # R(ILIM) = 4.02 kOhm row, G
IOL_MIN_A_4K02 = 4.185
FASTRIP_MULT = 2.0  # TPS16630: 2 x I(OL), TYP only (no tabulated min/max)
ISCP_TYP_A = 45.0  # TYP
TFASTRIP_TYP_S = 1e-6  # section 8.3, typical
TSOFTSHORT_MAX_S = 4.5e-6  # EC table: soft short response, I(FASTTRIP) < I(OUT) < I(SCP), max
RON_MAX_OHM = 0.053  # -40..125 C, G

# Divider ratio error with 0.1 % resistors (PA): both resistors at opposite limits.
DIVIDER_ERR = 0.002

# TI TVS2200 SLVSED5C (G): VBR at 1 mA and clamp points.
TVS2200_VBR_MIN_V = 24.6
TVS2200_VC_40A_27C_V = 28.0
TVS2200_VC_35A_125C_V = 28.35
TVS2200_VC_24A_27C_V = 27.7
# STUSB4500 DS12499 Table 21 operating maximum for VDD and the VBUS pins (G-U, mirror in the bundle).
STUSB_VDD_OPERATING_MAX_V = 22.0

# Board P r2 (dec-p-20v-front-end-r2): UVLO divider and single bulk part.
UVLO_R_TOP_OHM, UVLO_R_BOT_OHM = 11.5e3, 4.02e3  # Yageo 0.1 % (G)
OVP_R_TOP_OHM, OVP_R_BOT_OHM = 174e3, 10e3  # fitted OVP divider, Yageo 0.1 % (G)
VUVLOR_MIN, VUVLOR_MAX = 1.176, 1.224  # SLVSE94G V(UVLOR) (G)
VUVLOF_MIN, VUVLOF_MAX = 1.09, 1.15  # SLVSE94G V(UVLOF) (G)
PROJECT_VBUS_FLOOR_V = 4.5  # project 5 V attach floor (PA)
# RVT1H101M0810 C970687 100 uF +/-20 % (G); one part on VBUS_P after r2, two before.
BULK_R2_UF = (80.0, 120.0)
BULK_R1_MAX_UF = 240.0
# USB PD source transition slew ceiling 30 mV/us (G-U: no PD primary retained here).
PD_SLEW_V_PER_S = 30e3

# Highest legitimate board-input current at 20 V (calc, product-lineup.md, PA efficiencies).
I_IN_TRANSIENT_MAX_A = 3.38


def trip_window(v_nominal):
    lo = v_nominal * (VOVPR_MIN / VOVPR_TYP) * (1 - DIVIDER_ERR)
    hi = v_nominal * (VOVPR_MAX / VOVPR_TYP) * (1 + DIVIDER_ERR)
    rec_lo = v_nominal * (VOVPF_MIN / VOVPR_TYP) * (1 - DIVIDER_ERR)
    return lo, hi, rec_lo


def overshoot_charge():
    q_window = FASTRIP_MULT * IOL_MAX_A_4K02 * OVP_TOFF_MAX_S
    q_fastrip = ISCP_TYP_A * TFASTRIP_TYP_S
    return q_window, q_fastrip


# ---- Phase 9: STUSB4500 HV pins on local small-current clamps -----------------------------
# Diodes DS18004 Rev 38-2 (G, sha256 0fbd7d13...), 25 C, VZ at IZT 5 mA, ZZT max at IZT, TC at IZTC.
ZENER = {
    'BZT52C18': {'vz': (16.8, 19.1), 'izt': 5e-3, 'zzt': 45.0, 'tc': (12.4e-3, 16.0e-3), 'ir_ua_at_vr': (0.1, 12.6)},
    'BZT52C20': {'vz': (18.8, 21.2), 'izt': 5e-3, 'zzt': 55.0, 'tc': (14.4e-3, 18.0e-3), 'ir_ua_at_vr': (0.1, 14.0)},
}
# DS12499 Rev 7 copy (sha256 407ee676..., mirror; Rev 8 Table 22 not re-checked) - UNSOURCED class
STUSB_VDD_OP_MIN_V = 4.1
STUSB_IDD_IDLE_MAX_A = 210e-6       # Table 22, VDD 5.0 V, 25 C, idle sink (not connected, no communication)
STUSB_IDD_IDLE_TYP_A = 160e-6       # same row, typical
R_VDD_FEED = 1000.0 + 470.0         # phase 10: R29 1k C21190 + R30 470R C23179 (was 2 x 1k)
IDD_DESIGN_A = 2 * STUSB_IDD_IDLE_TYP_A   # project sizing target (PA): twice the idle typical
STUSB_VMONUSBL_20V = 20.0 * (1 - 0.05 - 0.15)   # default VSHUSBL 15 %
STUSB_TDISPAR_STEP_MIN_S = 70e-3    # TDISUSB0V min = 70 ms x TDISPAR0V
STUSB_TDISPAR0V_DEFAULT = 9
STUSB_VTH0V_MIN = 0.5
STUSB_VS_DISCH_I_MAX = 50e-3
R1_TOL = 0.01                        # 0603WAF 1 %
T_RANGE = (-40.0, 125.0)             # L7 hot row is 125 C; STUSB operating TA -40..105 C
TA_OP_MAX = 105.0
VBUS_ATTACH_MIN_V = 4.75 - 0.03      # vSafe5V minimum less the Q3 ideal-diode and U2 drops (PA)
C3_MAX_F = 120e-6


def _vz_bounds(z, t):
    lo, hi = z['vz']
    tcl, tch = z['tc']
    if t >= 25:
        return lo + tcl * (t - 25), hi + tch * (t - 25)
    return lo - tch * (25 - t), hi - tcl * (25 - t)


def local_clamp_pin(name, zener, r_nom, v_src_max, limit, leak_r=None):
    """Pin voltage bound across temperature: the source current through r (or leak_r) into the zener."""
    z = ZENER[zener]
    worst = None
    rows = []
    for t in (T_RANGE[0], 25.0, TA_OP_MAX, T_RANGE[1]):
        vmin, vmax = _vz_bounds(z, t)
        r_min = (leak_r if leak_r else r_nom) * (1 - R1_TOL)
        i = max(0.0, (v_src_max - vmin) / r_min)
        extra = max(0.0, i - z['izt']) * z['zzt']
        v = vmax + extra
        rows.append({'t_c': t, 'i_ma': round(i * 1e3, 3), 'beyond_izt_ma': round(max(0, i - z['izt']) * 1e3, 3),
                     'pin_max_v': round(v, 3)})
        worst = max(worst or 0, v)
    return {'pin': name, 'clamp': zener, 'series_ohm': leak_r or r_nom, 'rows': rows, 'pin_max_v': round(worst, 3),
            'limit_v': limit, 'margin_v': round(limit - worst, 3), 'status': 'PASS' if worst < limit else 'FAIL'}


def stusb_local_clamp(v_main_max):
    out = {'main_path_bound_v': v_main_max,
           'basis': 'VZ max at IZT and TC max (DS18004, G); resistor 1 %; source bound = TVS2200 35 A / 125 C row. '
                    'Where the clamp current exceeds IZT (VDD up to 1.36 mA, VS_DISCH 0.41 mA at -40 C only) ZZT max '
                    'is used as a linear slope (PA); that adds <= 0.06 V, and the >= 5 V margins would absorb a slope '
                    'of several kilohms'}
    vdd = local_clamp_pin('VDD (U1.24)', 'BZT52C18', R_VDD_FEED, v_main_max, STUSB_VBUS_ABS_MAX_V)
    vs = local_clamp_pin('VBUS_VS_DISCH (U1.18)', 'BZT52C20', 2.0e3, v_main_max, STUSB_VBUS_ABS_MAX_V)
    dis = local_clamp_pin('DISCH (U1.9)', 'BZT52C18', 4.7e3, v_main_max, STUSB_VBUS_ABS_MAX_V)
    ven = local_clamp_pin('VBUS_EN_SNK (U1.16) behind Q6 cascode', 'BZT52C18', None, v_main_max, STUSB_VBUS_ABS_MAX_V,
                          leak_r=150e3 + 4.7e3)
    out['pins'] = [vdd, vs, dis, ven]
    out['l7_status'] = 'PASS (guaranteed zener rows; STUSB limits are mirror-authority)' if all(
        p['status'] == 'PASS' for p in out['pins']) else 'FAIL'
    # VDD operating window
    z18 = ZENER['BZT52C18']
    vdd_hot = _vz_bounds(z18, TA_OP_MAX)[1]
    r_vdd_max = R_VDD_FEED * (1 + R1_TOL)
    i_div = VBUS_ATTACH_MIN_V / (2 * 100e3 * (1 - R1_TOL))
    vdd_attach = VBUS_ATTACH_MIN_V - r_vdd_max * (STUSB_IDD_IDLE_MAX_A + i_div + 0.1e-6)
    vdd_attach_design = VBUS_ATTACH_MIN_V - r_vdd_max * (IDD_DESIGN_A + i_div + 0.1e-6)
    z18c = ZENER['BZT52C18']
    i_clamp_max = (v_main_max - _vz_bounds(z18c, T_RANGE[0])[0]) / (R_VDD_FEED * (1 - R1_TOL))
    p_clamp_max = i_clamp_max * vdd['pin_max_v']
    out['vdd_operating'] = {
        'vdd_max_at_105c_v': round(vdd_hot, 3), 'limit_v': STUSB_VDD_OPERATING_MAX_V,
        'status_22v': 'PASS' if vdd_hot <= STUSB_VDD_OPERATING_MAX_V else 'FAIL',
        'vdd_min_at_5v_attach_v': round(vdd_attach, 3), 'vdd_op_min_v': STUSB_VDD_OP_MIN_V,
        'margin_v': round(vdd_attach - STUSB_VDD_OP_MIN_V, 3),
        'idd_allowed_max_a': round((VBUS_ATTACH_MIN_V - STUSB_VDD_OP_MIN_V) / r_vdd_max - i_div, 7),
        'feed_ohm': R_VDD_FEED,
        'vdd_min_at_5v_attach_2x_typ_idd_v': round(vdd_attach_design, 3),
        'design_idd_a': IDD_DESIGN_A, 'design_margin_v': round(vdd_attach_design - STUSB_VDD_OP_MIN_V, 3),
        'idd_allowed_over_idle_typ': round(((VBUS_ATTACH_MIN_V - STUSB_VDD_OP_MIN_V) / r_vdd_max - i_div) / STUSB_IDD_IDLE_TYP_A, 2),
        'zener_current_max_a_at_surge_row': round(i_clamp_max, 5), 'zener_power_max_w_at_surge_row': round(p_clamp_max, 3),
        'zener_pd_rating_w': 0.5,
        'status_attach': 'PASS at the idle maximum and at 2 x idle typical (sizing PA); active-communication IDD OPEN',
        'reason': 'DS12499 Rev 7 Table 22 gives only the idle 5 V / 25 C IDD (typ 160, max 210 uA, mirror copy); '
                  'no active-communication or temperature maximum exists, so the feed is sized for 2 x typical with margin'}
    # VBUS_VS_DISCH sense and discharge
    z20 = ZENER['BZT52C20']
    vs_cold_min = _vz_bounds(z20, T_RANGE[0])[0]
    vs_hot_max = _vz_bounds(z20, TA_OP_MAX)[1]
    tau = 2.0e3 * (1 + R1_TOL) * C3_MAX_F
    t_dis = tau * math.log(VBUS_20V_MAX_V / STUSB_VTH0V_MIN)
    tdispar_needed = math.ceil(t_dis / STUSB_TDISPAR_STEP_MIN_S)
    out['vs_disch'] = {
        'sense_min_when_clamping_v': round(vs_cold_min, 3), 'vmonusbl_20v_default_v': round(STUSB_VMONUSBL_20V, 3),
        'uv_margin_v': round(vs_cold_min - STUSB_VMONUSBL_20V, 3),
        'pin_max_at_105c_v': round(vs_hot_max, 3),
        'operating_22v_note': 'the pin follows min(VBUS_P, VZ): above 22 V it exceeds the 22 V operating row only at '
                              'TA above about 67 C with VBUS_P in the 22.0-22.56 V OVP band',
        'stusb_ov_monitor': 'the 22 V VMONUSBH (PDO 20 V +10 %) is no longer reliable behind the clamp; U2 OVP '
                            '(21.60-22.56 V) is the overvoltage protection',
        'discharge_current_max_a': round(VBUS_20V_MAX_V / (2.0e3 * (1 - R1_TOL)), 4), 'pin_limit_a': STUSB_VS_DISCH_I_MAX,
        'discharge_time_21v_to_vth0v_s': round(t_dis, 4),
        'tdisusb0v_default_min_s': round(STUSB_TDISPAR_STEP_MIN_S * STUSB_TDISPAR0V_DEFAULT, 3),
        'tdispar0v_needed': tdispar_needed,
        'discharge_status': 'FAIL with the default NVM (TDISPAR0V 9); PASS only with TDISPAR0V >= '
                            f'{tdispar_needed} in the factory image'}
    out['vben_cascode'] = {
        'q6_vgs_max_v': round(_vz_bounds(z18, T_RANGE[1])[1] * 101 / 200, 3), 'bss138_vgs_max_v': 20.0,
        'q6_vg_min_at_attach_v': round(vdd_attach * 0.99 / 2.0, 3), 'bss138_vgsth_max_v': 1.5,
        'gate_network_current_5v25_a': round(5.25 / ((150e3 + 4.7e3) * 0.99), 7),
        'note': 'Q6 (BSS138) source on the VBEN pin, drain on R12, gate at VDD_LOC / 2: the pin cannot rise above the '
                'gate, and the only current into D11 when Q6 is off is leakage, bounded by R11 + R12. Q1 off-state '
                'integrity at temperature depends on the hot IDSS, which is not in DS30144 (0.5 uA max at 25 C only).'}
    out['cc_pins'] = 'unchanged: CC abs max 22 V is a separate single-fault concern (GAP-2, section 2.2)'
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    v_min_required = VBUS_20V_MAX_V + TRIP_GUARD_V
    v_nominal = v_min_required / ((VOVPR_MIN / VOVPR_TYP) * (1 - DIVIDER_ERR))
    lo, hi, rec_lo = trip_window(v_nominal)
    q_window, q_fastrip = overshoot_charge()
    q_total = q_window + q_fastrip
    esr_ohm = 0.03  # PA bulk ESR; no RVT1H101M0810 ESR fact exists in the owner bundle
    i_peak = FASTRIP_MULT * IOL_MAX_A_4K02
    ovp_ratio = 1 + OVP_R_TOP_OHM / OVP_R_BOT_OHM
    ovp_fitted_hi = VOVPR_MAX * ovp_ratio * (1 + DIVIDER_ERR)

    rows = []
    for c_uf in (47, 100, 220):
        dv = q_total / (c_uf * 1e-6) + i_peak * esr_ohm
        node = min(ovp_fitted_hi + dv, TVS2200_VC_35A_125C_V)
        rows.append({"c_eff_uF": c_uf, "delta_v": round(dv, 2), "node_max_v": round(node, 2),
                     "margin_to_28v": round(STUSB_VBUS_ABS_MAX_V - node, 2)})

    ratio = 1 + UVLO_R_TOP_OHM / UVLO_R_BOT_OHM
    uvlo = {
        "rising_v": [round(VUVLOR_MIN * ratio * (1 - DIVIDER_ERR), 2), round(VUVLOR_MAX * ratio * (1 + DIVIDER_ERR), 2)],
        "falling_v": [round(VUVLOF_MIN * ratio * (1 - DIVIDER_ERR), 2), round(VUVLOF_MAX * ratio * (1 + DIVIDER_ERR), 2)],
        "floor_v": PROJECT_VBUS_FLOOR_V,
    }
    r2 = {
        "uvlo": uvlo,
        "ovp_fitted_trip_v": [round(VOVPR_MIN * ovp_ratio * (1 - DIVIDER_ERR), 2), round(ovp_fitted_hi, 2)],
        "transition_inrush_a_r1_max": round(BULK_R1_MAX_UF * 1e-6 * PD_SLEW_V_PER_S, 2),
        "transition_inrush_a_r2_max": round(BULK_R2_UF[1] * 1e-6 * PD_SLEW_V_PER_S, 2),
        "iol_min_a": IOL_MIN_A_4K02,
        "node_max_v_r2_min_bulk": round(ovp_fitted_hi + q_total / (BULK_R2_UF[0] * 1e-6) + i_peak * esr_ohm, 2),
    }
    r2["margin_to_28v_r2_min_bulk"] = round(STUSB_VBUS_ABS_MAX_V - r2["node_max_v_r2_min_bulk"], 2)
    c_min = BULK_R2_UF[0] * 1e-6
    sens = []
    for label, q, esr in (("TYP charge, ESR 0.03 ohm PA", q_total, 0.03),
                          ("TYP charge, ESR 0.3 ohm", q_total, 0.3),
                          ("TYP charge, ESR 0.5 ohm", q_total, 0.5),
                          ("soft-short 4.5 us max at I(SCP) TYP, ESR 0.03 ohm", q_window + ISCP_TYP_A * TSOFTSHORT_MAX_S, 0.03)):
        node = ovp_fitted_hi + q / c_min + i_peak * esr
        sens.append({"case": label, "node_v": round(node, 2), "margin_to_28v": round(STUSB_VBUS_ABS_MAX_V - node, 2)})
    r2["node_sensitivity_80uF"] = sens
    r2["l7_status"] = "superseded by front_end_r3_guaranteed (TYP rows are a sensitivity only)"
    r2["l7_guaranteed_bound"] = ("VBUS_IN <= TVS2200 clamp 28.0 V (27 C) / 28.35 V (125 C): margin "
                                 f"{STUSB_VBUS_ABS_MAX_V - TVS2200_VC_40A_27C_V:+.2f} / {STUSB_VBUS_ABS_MAX_V - TVS2200_VC_35A_125C_V:+.2f} V")

    # r3, guaranteed figures only (phase 8).
    clamp_rows = (("24 A 8/20 us, 27 C", TVS2200_VC_24A_27C_V), ("40 A 8/20 us, 27 C", TVS2200_VC_40A_27C_V),
                  ("35 A 8/20 us, 125 C", TVS2200_VC_35A_125C_V))
    tol, tcr_dt = 0.001, 25e-6 * 100
    def trip(vref, ratio, sign, drift=0.0):
        return vref * (1 + ratio * (1 + sign * (tol + drift)) / (1 - sign * (tol + drift)))
    ratio_fit = OVP_R_TOP_OHM / OVP_R_BOT_OHM
    # Largest divider ratio whose trip maximum stays at the 22 V operating ceiling, and the trip minimum it then gives.
    ratio_22 = (STUSB_VDD_OPERATING_MAX_V / VOVPR_MAX - 1) * (1 - tol) / (1 + tol)
    r3 = {
        "l7_status": "FAIL (guaranteed figures)",
        "vbus_p_bound": "VBUS_P <= VBUS_IN (forward-only Q3 + U2 path; PCB inductive overshoot unquantified) <= TVS2200 clamp row",
        "clamp_rows": [{"case": c, "vbus_p_max_v": v, "margin_to_28v": round(STUSB_VBUS_ABS_MAX_V - v, 2)} for c, v in clamp_rows],
        "let_through_bound": "NOT AVAILABLE: no guaranteed I(FASTTRIP) or I(SCP) maximum (SLVSET9G TYP only); a guaranteed bulk ESR does not supply the missing current term",
        "ovp_trip_fitted_v": [round(trip(VOVPR_MIN, ratio_fit, -1), 4), round(trip(VOVPR_MAX, ratio_fit, +1), 4),
                              round(trip(VOVPR_MAX, ratio_fit, +1, tcr_dt), 4)],
        "stusb_operating_gap_v": round(trip(VOVPR_MAX, ratio_fit, +1) - STUSB_VDD_OPERATING_MAX_V, 4),
        "ratio_for_22v_trip_max": round(ratio_22, 4),
        "trip_min_at_that_ratio_v": round(trip(VOVPR_MIN, ratio_22, -1), 4),
        "guard_over_21v_at_that_ratio_v": round(trip(VOVPR_MIN, ratio_22, -1) - VBUS_20V_MAX_V, 4),
    }
    # LED worker proposal (led-phase11 section a): OVP top 133k as a per-product common-block value.
    ratio_led = 133e3 / OVP_R_BOT_OHM
    r3["per_product_ovp_133k"] = {
        "trip_v": [round(trip(VOVPR_MIN, ratio_led, -1), 4), round(trip(VOVPR_MAX, ratio_led, +1), 4),
                   round(trip(VOVPR_MAX, ratio_led, +1, tcr_dt), 4)],
        "pd_product": "NOT APPLICABLE: the trip maximum is below the 19.0 V PD 20 V contract minimum, so PD would trip on its own contract",
        "led_product": "valid as a resistor-value-only per-product parameter (same footprint and net); it requires an NVM image whose "
                       "highest PDO is 15 V, because a 20 V contract trips OVP and the STUSB browns out",
        "l7_effect_guaranteed": "none: VBUS_P is still bounded only by the TVS2200 clamp row; an earlier trip shortens the TYP "
                                "overshoot window but no guaranteed current term exists to turn it into a bound",
        "l7_effect_typ": "LED sensitivity 29.6 V -> 24.6 V at 80 uF / 0.5 ohm (TYP charge, PA ESR): a sensitivity, not a bound",
        "stusb_vdd_22v_effect": "the trip maximum then sits well below the 22 V STUSB VDD operating maximum, which closes that gap for LED only",
    }
    r3["stusb_local_clamp"] = stusb_local_clamp(TVS2200_VC_35A_125C_V)
    result = {
        "ovp_nominal_v": round(v_nominal, 2),
        "ovp_trip_window_v": [round(lo, 2), round(hi, 2)],
        "ovp_recovery_min_v": round(rec_lo, 2),
        "charge_window_uC": round(q_window * 1e6, 1),
        "charge_fastrip_uC_typ": round(q_fastrip * 1e6, 1),
        "node_rows": rows,
        "iol_window_a": [IOL_MIN_A_4K02, IOL_MAX_A_4K02],
        "iol_min_margin_over_transient_a": round(IOL_MIN_A_4K02 - I_IN_TRANSIENT_MAX_A, 3),
        "efuse_loss_w_at_transient": round(I_IN_TRANSIENT_MAX_A ** 2 * RON_MAX_OHM, 2),
        "tvs2200_alone_margin_hot_v": round(STUSB_VBUS_ABS_MAX_V - TVS2200_VC_35A_125C_V, 2),
        "tvs2200_alone_margin_27c_v": round(STUSB_VBUS_ABS_MAX_V - TVS2200_VC_40A_27C_V, 2),
        "tvs2200_vbr_min_over_vbus_v": round(TVS2200_VBR_MIN_V - VBUS_20V_MAX_V, 2),
        "cc_single_fault_margin_v": round(STUSB_CC_ABS_MAX_V - VBUS_20V_MAX_V, 2),
        "front_end_r2_typ_sensitivity": r2,
        "front_end_r3_guaranteed": r3,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"OVP nominal {result['ovp_nominal_v']} V, trip {lo:.2f}-{hi:.2f} V, recovers above {rec_lo:.2f} V min")
    print(f"charge: window {result['charge_window_uC']} uC + fast-trip {result['charge_fastrip_uC_typ']} uC (TYP)")
    print("| C_eff (uF) | dV (V) | protected node max (V) | margin to 28 V |")
    print("|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['c_eff_uF']} | {r['delta_v']} | {r['node_max_v']} | {r['margin_to_28v']:+} |")
    print(f"I(OL) {IOL_MIN_A_4K02}-{IOL_MAX_A_4K02} A; min over 3.38 A: {result['iol_min_margin_over_transient_a']} A;"
          f" eFuse loss at 3.38 A: {result['efuse_loss_w_at_transient']} W")
    print(f"TVS2200 alone: {result['tvs2200_alone_margin_27c_v']} V at 27 C, {result['tvs2200_alone_margin_hot_v']} V hot;"
          f" CC single fault {result['cc_single_fault_margin_v']} V")
    print(f"r2 UVLO rising {uvlo['rising_v'][0]}-{uvlo['rising_v'][1]} V, falling {uvlo['falling_v'][0]}-{uvlo['falling_v'][1]} V"
          f" (floor {PROJECT_VBUS_FLOOR_V} V)")
    print(f"r2 5->20 V transition inrush at 30 V/ms: {r2['transition_inrush_a_r2_max']} A (r1 2x100 uF: {r2['transition_inrush_a_r1_max']} A)"
          f" vs I(OL) min {IOL_MIN_A_4K02} A")
    print(f"r2 fitted 174k/10k OVP trip {r2['ovp_fitted_trip_v'][0]}-{r2['ovp_fitted_trip_v'][1]} V")
    print(f"r2 protected node max at 80 uF: {r2['node_max_v_r2_min_bulk']} V; margin to 28 V {r2['margin_to_28v_r2_min_bulk']:+} V"
          " (TYP I(SCP)/t_FASTTRIP and PA ESR: not a bound)")
    for r in r2["node_sensitivity_80uF"]:
        print(f"  {r['case']}: {r['node_v']} V, margin {r['margin_to_28v']:+} V")
    print(f"r3 L7 {r3['l7_status']}: {r3['vbus_p_bound']}")
    for r in r3["clamp_rows"]:
        print(f"  TVS2200 {r['case']}: VBUS_P <= {r['vbus_p_max_v']} V, margin to 28 V {r['margin_to_28v']:+} V")
    print(f"  let-through bound: {r3['let_through_bound']}")
    print(f"r3 OVP trip {r3['ovp_trip_fitted_v'][0]}-{r3['ovp_trip_fitted_v'][1]} V ({r3['ovp_trip_fitted_v'][2]} V with TCR over 100 C);"
          f" above the 22 V STUSB operating maximum by up to {r3['stusb_operating_gap_v']} V")
    print(f"  ratio {r3['ratio_for_22v_trip_max']} would cap the trip at 22.0 V but its minimum {r3['trip_min_at_that_ratio_v']} V"
          f" leaves {r3['guard_over_21v_at_that_ratio_v']} V over the 21.0 V normal high (0.5 V guard wanted)")
    lc = r3["stusb_local_clamp"]
    print(f"phase-9 local clamps: L7 {lc['l7_status']}")
    for pin in lc["pins"]:
        print(f"  {pin['pin']}: {pin['clamp']} via {pin['series_ohm']:.0f} ohm, pin <= {pin['pin_max_v']} V, margin {pin['margin_v']} V")
    v = lc["vdd_operating"]
    print(f"  VDD <= {v['vdd_max_at_105c_v']} V at 105 C ({v['status_22v']} vs 22 V); at 5 V attach >= {v['vdd_min_at_5v_attach_v']} V"
          f" (margin {v['margin_v']} V, {v['status_attach']}: IDD allowed <= {v['idd_allowed_max_a'] * 1e6:.0f} uA)")
    d = lc["vs_disch"]
    print(f"  VS_DISCH sense >= {d['sense_min_when_clamping_v']} V vs VMONUSBL {d['vmonusbl_20v_default_v']} V; discharge"
          f" {d['discharge_time_21v_to_vth0v_s']} s vs {d['tdisusb0v_default_min_s']} s: {d['discharge_status']}")
    led = r3["per_product_ovp_133k"]
    print(f"per-product OVP 133k/10k (LED proposal): trip {led['trip_v'][0]}-{led['trip_v'][1]} V ({led['trip_v'][2]} V TCR);"
          f" PD {led['pd_product'].split(':')[0]}; L7 guaranteed effect {led['l7_effect_guaranteed'].split(':')[0]}")


if __name__ == "__main__":
    main()
