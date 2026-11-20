"""Issue #52 desk calculation: hottest-branch LED peak current vs RS1 and CTRL ceiling.

Pure arithmetic over retained facts; prints JSON. No measured data.
Usage: python3 -I led_margin.py > led_margin.json
"""
import json

VSENSE_MAX = 0.104          # V, DS39014 Rev 8-2 EC table, TA = 25 C only
HYS_TYP = 0.20              # +/-20 % typ (no max published) -> peak = mean * (1 + h)
RS_TOL = 0.01               # RLP25 F
RS_TCR = 50e-6              # RLP25 +/-50 ppm/K
RS_DT = 100.0               # K, 25 C -> 125 C board/part temperature assumption (proposed)
RB, RB_TOL, RB_TCR = 33.0, 0.01, 100e-6   # FOJAN 2512 33R0 F, +/-100 ppm/K
N = 8
SPREAD = 0.30               # V, locked assembled-string Vf spread (#35/#47)
IF_MAX = 0.090              # A, LED absolute maximum (TS <= ~65 C per derating curve, graph-read)
TARGET = 0.081              # A, proposed design limit = 90 % of 90 mA (10 % margin)

V3P3_MAX = 3.33             # AP63203 fact-ap63203-vout-max
R20, R21, RTOL = 10e3, 33e3, 0.01
C21, C21_TOL = 100e-9, 0.10 # proposed tolerance assumption for ripple estimate
F_PWM = 20e3
CTRL_ACC = 0.05             # "Typical 5% Output Current Accuracy" (typical, not a limit)


def hot_branch(i_total, rb_dev):
    rmin, rmax = RB * (1 - rb_dev), RB * (1 + rb_dev)
    vd = (i_total + (N - 1) * SPREAD / rmax) / (1 / rmin + (N - 1) / rmax)
    return vd / rmin


def rs_case(rs, hys, rb_dev, rs_dt=RS_DT):
    rs_min = rs * (1 - RS_TOL) * (1 - RS_TCR * rs_dt)
    i_mean = VSENSE_MAX / rs_min
    i_peak = i_mean * (1 + hys)
    hot = hot_branch(i_peak, rb_dev)
    return {"rs": rs, "hys": hys, "rb_dev": rb_dev, "i_nom_mean": 0.1 / rs,
            "i_max_mean": i_mean, "i_max_peak": i_peak, "hot_peak_mA": hot * 1e3,
            "pct_of_90mA": hot / IF_MAX * 100, "meets_81mA": hot <= TARGET + 1e-12}


def ctrl_ceiling(hys=HYS_TYP, rb_dev=RB_TOL):
    """Largest duty keeping the hot branch <= TARGET with RS1 = 0.200 ohm.
    Transfer is TYPICAL only: bounded here by I/I_FS = V/2.5 (>= (V-0.3)/2.2 on 0.3..2.5 V)
    times (1 + CTRL_ACC)."""
    i_fs = VSENSE_MAX / (0.2 * (1 - RS_TOL) * (1 - RS_TCR * RS_DT))
    lo, hi = 0.0, TARGET * 2 * N
    for _ in range(80):
        mid = (lo + hi) / 2
        (lo, hi) = (mid, hi) if hot_branch(mid, rb_dev) <= TARGET else (lo, mid)
    k_max = lo / (i_fs * (1 + hys)) / (1 + CTRL_ACC)
    r20, r21 = R20 * (1 - RTOL), R21 * (1 + RTOL)
    vth = V3P3_MAX * r21 / (r20 + r21)
    tau = (r20 * r21 / (r20 + r21)) * C21 * (1 - C21_TOL)
    ripple_pp = vth / (4 * tau * F_PWM)       # worst case at 50 % duty, T << tau
    v_ctrl_max = 2.5 * k_max - ripple_pp / 2
    return {"k_max_typ": k_max, "vctrl_max": v_ctrl_max, "vth_worst_high": vth,
            "ripple_pp_20kHz": ripple_pp, "duty_ceiling": v_ctrl_max / vth,
            "nominal_light_fraction": (v_ctrl_max / vth * 3.3 * 33 / 43 - 0.3) / 2.2}


rows = [rs_case(rs, h, d) for rs in (0.200, 0.220, 0.240, 0.250, 0.270)
        for h in (0.20, 0.25, 0.30) for d in (RB_TOL, RB_TOL + RB_TCR * RS_DT)]
print(json.dumps({"rs_options": rows, "ctrl_ceiling_rs200": ctrl_ceiling(),
                  "ctrl_ceiling_rs200_hys30": ctrl_ceiling(hys=0.30),
                  # Firmware default CTRL_FULL_CCR: h = 30 % with ballast +-2 % (1 % + TCR).
                  "ctrl_ceiling_rs200_hys30_rb2": ctrl_ceiling(hys=0.30, rb_dev=RB_TOL + RB_TCR * RS_DT)},
                 indent=1))
