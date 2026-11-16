#!/usr/bin/env python3
"""LED-variant protected-node bulk (C3) study for the r-next candidate. Desk arithmetic only.

Question: what effective capacitance does the LED product need on VBUS_P, and can C3
(RVT1H101M0810 100 uF 50 V, 8 x 8.3 mm can) become MLCCs or a smaller part for LED only?

Evidence classes: G = primary text (locator given), PA = project assumption, PROP = proposed.
Usage: python3 tools/bulk_study.py > checks/bulk-study.json
"""
import json
import math
import sys

SOURCES = {
    "usb-pd-r3.2-v1.2": {
        "url": "https://www.usb.org/sites/default/files/USB_PD_R3.2_V1.2%283%29.zip",
        "zip_sha256": "ccdb5b0fcb6af9ed787ba81d1781065772c7d15a816638137327ebbbf16f3bae",
        "member": "USB_PD_R3.2_V1.2/USB_PD_R3.2_V1.2_2026_08_19.pdf",
        "member_sha256": "1a041ab16c7ffcd39569809859fc59e569ade9cf155e4c314a46c9e9b1184027",
        "retrieved": "2026-10-31",
        "locators": {"sink_params": "Table 4.7 Sink Electrical Parameters, PDF page 83 (printed 83)",
                     "source_params": "Table 4.6 rows vSrcNew/vSrcValid/vSrcSlewPos, PDF page 82 (printed 82)",
                     "bulk_rule": "Section 4.2.2 text, PDF page 62 (printed 62)"},
    },
    "usb-pd-ecn-csnkbulkpd": {
        "member": "USB_PD_R3.2_V1.2/ECNs/USB PD R3.2 V1.1 ECN cSnkBulkPd Clarifications.pdf",
        "member_sha256": "ecfcb37657b3047c9e9d8503f4309d363c5fdfc194d7a0a6bae38a4ef204a5d1",
        "locators": {"rule": "ECN page 2, section 7.2.2 -> 4.2.2 replacement text"},
    },
    "ti-tps1663": {"note": "same PDF as owner bundle component-rnext-tps16630pwpr (sha256 8f91a0db...)",
                   "locators": {"dvdt": "section 8.3 Equation 1 and 2, PDF page 17; I(dVdT), GAIN(dVdT) PDF page 9",
                                "ovp_timing": "OVP_toff(dly) PDF page 9; I(OL) at 4.02 k, I(FASTRIP) = 2 x I(OL), I(SCP) PDF page 8; tFASTTRIP PDF page 10"}},
    "zudo-pd-l7-model": {"note": "zudo-pd 3ac13d46 scripts/pcb/calculate-input-ovp-20v.py (same charge model, reproduced here)"},
}

# USB PD R3.2 V1.2 (G)
C_SNK_BULK_PD_MAX_UF = 100.0         # after a successful negotiation; more only behind VBUS surge current limiting
V_SRC_SLEW_POS_V_PER_S = 30e-3 / 1e-6
I_SNK_STDBY_MAX_A = 0.5
V_SRC_NEW_TOL = 0.05
V_SRC_VALID_V = 0.5

# TI TPS1663 (G)
VOVPR = (1.176, 1.2, 1.224)
OVP_TOFF_MAX_S = 14e-6
IOL_MAX_4K02 = 4.815
IOL_MIN_4K02 = 4.185
FASTRIP_MULT = 2.0
ISCP_TYP_A = 45.0                    # TYP only: no maximum is given
TFASTRIP_TYP_S = 1e-6                # TYP only
TDVDT_K = 20.8e3                     # Equation 2: tdVdT = 20.8e3 x VIN x CdVdT

# Project values
C_DVDT_F = 100e-9                    # C5, r3 spec
DIVIDER_ERR = 0.002                  # two 0.1 % resistors (PA, as zudo-pd)
TRIP_GUARD_V = 0.5                   # PA, as zudo-pd
ABS_MAX_V = 28.0                     # STUSB4500 VDD / U4 IN
C3_RANGE_UF = (80.0, 120.0)          # RVT1H101M0810 100 uF +/-20 % (zudo-pd owner record)
C3_COURTYARD_MM2 = 95.69             # checks/placement-study.json
MLCC_C13585 = {"part": "CL31A106KBHNNNE C13585 (10 uF 50 V X5R 1206, LED inventory)", "nominal_uF": 10.0, "tol": 0.10,
               "courtyard_mm2": 15.06, "bias_retention": "UNSOURCED: Samsung curves are typical design reference only (fact-c13585-curve-caveat)"}
RETENTION_BRACKET = (0.3, 0.5, 0.7)  # PROP bracket for illustration only
ESR_CASES_OHM = {"MLCC bank, 0.005 ohm PROP": 0.005, "electrolytic 0.03 ohm PA": 0.03, "electrolytic 0.3 ohm": 0.3, "electrolytic 0.5 ohm": 0.5}
NODE_TARGET_V = 24.65                # zudo-pd T3 design row (100 uF, 30 mOhm): +3.35 V to 28 V; reused as the LED target (PROP)


def trip(rtop, rbot=10e3):
    ratio = 1 + rtop / rbot
    return VOVPR[0] * ratio * (1 - DIVIDER_ERR), VOVPR[2] * ratio * (1 + DIVIDER_ERR)


def main():
    q_total = FASTRIP_MULT * IOL_MAX_4K02 * OVP_TOFF_MAX_S + ISCP_TYP_A * TFASTRIP_TYP_S
    i_peak = FASTRIP_MULT * IOL_MAX_4K02
    v15_legit_max = 15.0 * (1 + V_SRC_NEW_TOL) + V_SRC_VALID_V
    dividers = {"common 174k/10k (fitted, 20 V capable)": 174e3, "LED-only 133k/10k (15 V-only, not adopted)": 133e3}
    ovp = {}
    for name, rtop in dividers.items():
        lo, hi = trip(rtop)
        rows = []
        for c_uf in (10, 22, 33, 47, 68, 80, 100):
            for esr_name, esr in ESR_CASES_OHM.items():
                node = hi + q_total / (c_uf * 1e-6) + i_peak * esr
                rows.append({"c_eff_uF": c_uf, "esr_case": esr_name, "node_v": round(node, 2), "margin_to_28v": round(ABS_MAX_V - node, 2)})
        need = {esr_name: round(q_total / (NODE_TARGET_V - hi - i_peak * esr) * 1e6, 1) if NODE_TARGET_V - hi - i_peak * esr > 0 else None
                for esr_name, esr in ESR_CASES_OHM.items()}
        ovp[name] = {"trip_v": [round(lo, 3), round(hi, 3)],
                     "guard_over_15v_legit_max_v": round(lo - v15_legit_max, 3),
                     "c_eff_needed_for_node_target_uF": need, "rows": rows}
    mlcc = []
    for target_name, target in (("common OVP, MLCC", ovp["common 174k/10k (fitted, 20 V capable)"]["c_eff_needed_for_node_target_uF"]["MLCC bank, 0.005 ohm PROP"]),
                                ("LED OVP, MLCC", ovp["LED-only 133k/10k (15 V-only, not adopted)"]["c_eff_needed_for_node_target_uF"]["MLCC bank, 0.005 ohm PROP"])):
        for r in RETENTION_BRACKET:
            n = math.ceil(target / (MLCC_C13585["nominal_uF"] * (1 - MLCC_C13585["tol"]) * r))
            mlcc.append({"case": target_name, "c_eff_needed_uF": target, "retention_PROP": r, "parts": n,
                         "courtyard_mm2": round(n * MLCC_C13585["courtyard_mm2"], 1), "vs_C3_mm2": C3_COURTYARD_MM2})
    attach_inrush = {f"{c}uF": round(c * 1e-6 / (TDVDT_K * C_DVDT_F), 4) for c in (C3_RANGE_UF[1], 47, 22)}
    out = {
        "status": "desk arithmetic, UNADOPTED; L7 stays BLOCKING (TYP I(SCP)/tFASTTRIP, no guaranteed bound below the TVS2200 clamp)",
        "sources": SOURCES,
        "usb_pd_limits": {
            "cSnkBulkPd_max_uF": C_SNK_BULK_PD_MAX_UF,
            "rule": "total Sink bulk on VBUS <= cSnkBulk/cSnkBulkPd; more is permitted only if isolated from VBUS through current-limiting circuitry ([USB3]); cSnkBulk itself is 'See [USB3]' and that document is not retained (gap)",
            "vSrcSlewPos_mV_per_us": 30, "iSnkStdby_max_A": I_SNK_STDBY_MAX_A,
            "v15_highest_legit_v": v15_legit_max,
            "transition_charge_current_A": {f"{c}uF": round(c * 1e-6 * V_SRC_SLEW_POS_V_PER_S, 2) for c in (C3_RANGE_UF[1], 100, 47, 22)},
            "reading": "U2 is fully on after attach, so C3 is charged at the source slew during 5 V -> 15 V; the spec sizes vSrcSlewPos on 3 A and 100 uF Sink bulk, so <=100 uF nominal keeps within it; 120 uF (+20 %) is 3.6 A, below I(OL) min 4.185 A",
        },
        "attach_inrush_through_U2_dvdt_A": attach_inrush,
        "led_load": "Board L draws about 0.41-0.5 A at 15 V behind Q1 and U4 (U4 dVdT limited); the load sets no bulk requirement on VBUS_P",
        "surge_charge_uC": round(q_total * 1e6, 1),
        "ovp_cases": ovp,
        "mlcc_substitution": {"part": MLCC_C13585, "rows": mlcc},
        "conclusion": [
            "C3 is sized by the L7 surge-charge model (179.8 uC TYP), not by the LED load or by USB PD rules.",
            "With the common 174k OVP an MLCC bank needs C_eff about 88 uF for the 24.65 V node target: 15-33 C13585 parts (226-497 mm2) against the 95.7 mm2 can.",
            "With an LED-only 133k OVP the need falls to about 25.5 uF: 5-10 C13585 parts (75-151 mm2), depending on unsourced DC-bias retention; the area gain is at best 20 mm2 and not established.",
            "Keep C3 for LED. Offer the LED-only OVP retune to PD as an L7 margin improvement, not as an area fix.",
        ],
    }
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
