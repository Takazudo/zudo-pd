"""Arithmetic screen of the V196 Board P voltage-qualification window.

Pure worst-case arithmetic; no simulation, no measurement. Datasheet limits are
copied from the official documents recorded in FAILOFF-WINDOW.md (TI SBVS240C
TPS3701 Table 6.5, TI SLVSFC9C TPS25947 Table 6.5, Yageo RT series V.17 Table 4).
"""
import itertools
import json
import sys

# TI SBVS240C 6.5, TJ -40..125 C, VDD 1.8..36 V.
TPS3701_INA_FALL = (0.397, 0.403)
TPS3701_INA_RISE = (0.400, 0.413)
TPS3701_IIN = 25e-9  # +/- at VINA = 6.5 V row (larger of the two rows)
# TI SLVSFC9C 6.5, TJ -40..125 C, VIN = 12 V.
EFUSE_UV_RISE = (1.183, 1.223)
EFUSE_UV_FALL = (1.076, 1.116)
EFUSE_OV_RISE = (1.183, 1.223)
EFUSE_OV_FALL = (1.076, 1.116)
EFUSE_PIN_LKG = 0.1e-6  # IENLKG / IOVLKG +/-
QINH_LKG_ASSUMED = 1e-6  # assumption carried from V15; NOT a manufacturer bound

# Per-resistor relative error budgets (Yageo RT0603BRD: B = 0.1 %, D = 25 ppm/K).
DT_K = 100  # assumed excursion from 25 C
TCR = 25e-6
LEVELS = {
    "L0_initial_plus_TCR": 0.001 + TCR * DT_K,
    "L1_plus_solder_heat_0p5pct": 0.001 + TCR * DT_K + 0.005,
    "L2_plus_endurance_0p5pct": 0.001 + TCR * DT_K + 0.005 + 0.005,
}

REJECT_MAX_V = 12.6  # 12 V fixed PDO +5 % (conditional, see report)


def trip_band(rtop, rbot, thr, e, ibias):
    """Return (min, max) RAW voltage at which pin = thr, all corners."""
    vals = []
    for t, et, eb, ib in itertools.product(thr, (-e, e), (-e, e), (-ibias, ibias)):
        rt, rb = rtop * (1 + et), rbot * (1 + eb)
        # pin = (Vraw - ib*rt) * rb/(rt+rb) ... solve: Vraw = t*(1+rt/rb) + ib*rt
        vals.append(t * (1 + rt / rb) + ib * rt)
    return min(vals), max(vals)


def monitor(rtop, rbot, e):
    fall = trip_band(rtop, rbot, TPS3701_INA_FALL, e, TPS3701_IIN)
    rise = trip_band(rtop, rbot, TPS3701_INA_RISE, e, TPS3701_IIN)
    return {"fall": fall, "rise": rise, "reject_margin_v": fall[0] - REJECT_MAX_V,
            "accept_floor_needed_v": rise[1]}


def efuse(rtop, rbot, rise, fall, e, extra_lkg=0.0):
    lk = EFUSE_PIN_LKG + extra_lkg
    return {"rise": trip_band(rtop, rbot, rise, e, lk), "fall": trip_band(rtop, rbot, fall, e, lk)}


def main():
    out = {"levels": LEVELS, "reject_max_v": REJECT_MAX_V, "cases": {}}
    for name, e in LEVELS.items():
        c = {
            "V196_monitor_313k_10k": monitor(313e3, 10e3, e),
            "V196_efuse_UV_97k6_10k": efuse(97.6e3, 10e3, EFUSE_UV_RISE, EFUSE_UV_FALL, e),
            "V196_efuse_UV_97k6_10k_with_QINH_1uA": efuse(97.6e3, 10e3, EFUSE_UV_RISE, EFUSE_UV_FALL, e, QINH_LKG_ASSUMED),
            "V196_efuse_OV_133k_10k": efuse(133e3, 10e3, EFUSE_OV_RISE, EFUSE_OV_FALL, e),
        }
        out["cases"][name] = c
    # Option O3: retune monitor top resistance (bottom 10k) so that the L2 falling
    # minimum clears 12.6 V by a margin, then report the resulting accept floor.
    o3 = []
    for rtop_k in (316, 318, 320, 324, 330):
        o3.append({"rtop_k": rtop_k, **{n: monitor(rtop_k * 1e3, 10e3, e) for n, e in LEVELS.items()}})
    out["option_O3_monitor_retune"] = o3
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
