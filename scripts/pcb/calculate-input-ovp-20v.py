#!/usr/bin/env python3
"""Screen arithmetic for the 20 V Board P input-protection topologies (analysis only).

Reproduces the tables in manufacturing/input-protection-20v.md. Every input is
tagged with its evidence class; nothing here is a measurement or an adopted value.
"""

import argparse
import json

# STUSB4500 DS12499 Rev 8 Table 20 (G-U, owner bundle mirror evidence).
STUSB_VBUS_ABS_MAX_V = 28.0
STUSB_CC_ABS_MAX_V = 22.0

# USB PD 20 V fixed PDO, project +/-5 % source range (PA; no primary PD text retained).
VBUS_20V_MAX_V = 21.0
# Project guard between the highest legitimate VBUS and the lowest OVP trip (PA).
TRIP_GUARD_V = 0.5

# TI TPS2663 SLVSE94G (G, retrieved 2026-10-31): OVP comparator and timing.
VOVPR_MIN, VOVPR_TYP, VOVPR_MAX = 1.176, 1.2, 1.224
VOVPF_MIN, VOVPF_MAX = 1.09, 1.15
OVP_TOFF_MAX_S = 14e-6  # OVP rising to FLT low; FET-off coincidence is PA
IOL_MAX_A_4K02 = 4.815  # R(ILIM) = 4.02 kOhm row, G
IOL_MIN_A_4K02 = 4.185
FASTRIP_MULT = 2.0  # TPS26630/TPS26632: 2 x I(OL), TYP column
ISCP_TYP_A = 45.0  # TYP
TFASTRIP_TYP_S = 1e-6  # section 8.3, typical
RON_MAX_OHM = 0.053  # -40..125 C, G

# Divider ratio error with 0.1 % resistors (PA): both resistors at opposite limits.
DIVIDER_ERR = 0.002

# TI TVS2200 SLVSED5C (G): VBR at 1 mA and clamp points.
TVS2200_VBR_MIN_V = 24.6
TVS2200_VC_40A_27C_V = 28.0
TVS2200_VC_35A_125C_V = 28.35

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    v_min_required = VBUS_20V_MAX_V + TRIP_GUARD_V
    v_nominal = v_min_required / ((VOVPR_MIN / VOVPR_TYP) * (1 - DIVIDER_ERR))
    lo, hi, rec_lo = trip_window(v_nominal)
    q_window, q_fastrip = overshoot_charge()
    q_total = q_window + q_fastrip
    esr_ohm = 0.03  # PA bulk ESR
    i_peak = FASTRIP_MULT * IOL_MAX_A_4K02

    rows = []
    for c_uf in (47, 100, 220):
        dv = q_total / (c_uf * 1e-6) + i_peak * esr_ohm
        node = min(hi + dv, TVS2200_VC_35A_125C_V)
        rows.append({"c_eff_uF": c_uf, "delta_v": round(dv, 2), "node_max_v": round(node, 2),
                     "margin_to_28v": round(STUSB_VBUS_ABS_MAX_V - node, 2)})

    ratio = 1 + UVLO_R_TOP_OHM / UVLO_R_BOT_OHM
    uvlo = {
        "rising_v": [round(VUVLOR_MIN * ratio * (1 - DIVIDER_ERR), 2), round(VUVLOR_MAX * ratio * (1 + DIVIDER_ERR), 2)],
        "falling_v": [round(VUVLOF_MIN * ratio * (1 - DIVIDER_ERR), 2), round(VUVLOF_MAX * ratio * (1 + DIVIDER_ERR), 2)],
        "floor_v": PROJECT_VBUS_FLOOR_V,
    }
    ovp_ratio = 1 + OVP_R_TOP_OHM / OVP_R_BOT_OHM
    ovp_fitted_hi = VOVPR_MAX * ovp_ratio * (1 + DIVIDER_ERR)
    r2 = {
        "uvlo": uvlo,
        "ovp_fitted_trip_v": [round(VOVPR_MIN * ovp_ratio * (1 - DIVIDER_ERR), 2), round(ovp_fitted_hi, 2)],
        "transition_inrush_a_r1_max": round(BULK_R1_MAX_UF * 1e-6 * PD_SLEW_V_PER_S, 2),
        "transition_inrush_a_r2_max": round(BULK_R2_UF[1] * 1e-6 * PD_SLEW_V_PER_S, 2),
        "iol_min_a": IOL_MIN_A_4K02,
        "node_max_v_r2_min_bulk": round(ovp_fitted_hi + q_total / (BULK_R2_UF[0] * 1e-6) + i_peak * esr_ohm, 2),
    }
    r2["margin_to_28v_r2_min_bulk"] = round(STUSB_VBUS_ABS_MAX_V - r2["node_max_v_r2_min_bulk"], 2)

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
        "front_end_r2": r2,
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
    print(f"r2 protected node max at 80 uF: {r2['node_max_v_r2_min_bulk']} V; margin to 28 V {r2['margin_to_28v_r2_min_bulk']:+} V")


if __name__ == "__main__":
    main()
