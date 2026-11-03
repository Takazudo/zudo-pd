#!/usr/bin/env python3
"""Supply-alternatives screen for manufacturing/supply-alternatives.md.

SCREENING ARITHMETIC ONLY. No simulation, bench, thermal, efficiency, ripple
or startup measurement exists for any option. Every converter efficiency below
is a PROJECT_ASSUMPTION (PA); exact-part limits are quoted with their class in
manufacturing/supply-alternatives.md. The output is deterministic and uses only
the Python standard library.

Inputs read (ROOT-relative): manufacturing/supply-capability.json, for the
OSC probe-point loads (canonical planning-normal is the basis; the Stage54
conditional row is printed only as a labeled comparison), the capability
pre-rail floors, and the per-rail ancillary currents (indicator and feedback
divider; LDO output minus external load) that the capability screen uses.

Usage: python3 scripts/pcb/calculate-supply-alternatives.py [--root PATH]
"""

import argparse
import json
import math
from pathlib import Path

RAILS = ("plus12", "minus12", "plus5")
VOUT = {"plus12": 12.0, "minus12": 12.0, "plus5": 5.0}  # magnitudes, DP

# Board-input screening points (V). 15 V points follow supply-capability.json;
# 20 V reuses the same 14.0/15 derate, plus an extra cable-drop case.
DERATE = 14.0 / 15.0
POINTS = {
    "15V": {"floor": 14.0, "ideal": 15.0},
    "20V": {"derated": round(20.0 * DERATE, 2), "cable": 18.4, "ideal": 20.0},
}
CONTRACT_A = {"15V/3A": 3.0, "20V/3A": 3.0, "20V/5A": 5.0}

# PA efficiency sets: (+12 buck, -12 inverting buck-boost, +5 buck)
ETA = {
    "base": {"plus12": 0.92, "minus12": 0.85, "plus5": 0.83},
    "-3pt": {"plus12": 0.89, "minus12": 0.82, "plus5": 0.80},
    "-5pt": {"plus12": 0.87, "minus12": 0.80, "plus5": 0.75},
}
# Rail-side series path outside the regulation loop: PTC R1max (G, Bourns
# MF-MSMF250/16X 0.100 ohm) plus 0.02 ohm filter/copper (PA).
R_PTC_MAX = 0.100
R_FILTER = 0.020

# Hybrid: +/-12 V LDOs at 0.7 V headroom (PA), LDO ground current 2 % (PA).
HYB_HEADROOM = 0.7
HYB_GND_FRAC = 0.02

# TPS54560 (G unless stated): high-side RDS(on) 92 mohm typ / 190 mohm max
# (VIN 12 V, BOOT-SW 6 V); current limit 6.3 A min; theta-JA 42 C/W (TYP,
# standard test board). L, f, Vf and switching loss are PA.
RDS_MAX = 0.190
ILIM_MIN = 6.3
THETA_JA = 42.0
L_H = 22e-6
F_SW = 400e3
VF = 0.5
P_SW_FIXED = 0.25  # PA switching + quiescent loss per stage, W

# PTC derating, Bourns MF-MSMF250/16X hold current vs ambient (G).
PTC_DERATE = [(-40, 3.90), (-20, 3.42), (0, 2.96), (23, 2.50), (40, 2.24),
              (50, 1.98), (60, 1.85), (70, 1.29), (85, 0.94)]


def load_probes(root):
    """Probe loads, ancillary currents and capability floors from the JSON.
    The canonical planning row is the basis; the Stage54 row is an unadopted
    conditional saving kept only as a labeled comparison."""
    data = json.loads((root / "manufacturing/supply-capability.json").read_text())
    res = data["probe_points"]["results"]
    names = {"osc_planning_normal_canonical": "planning",
             "osc_planning_normal_stage54_conditional": "stage54_cond",
             "osc_continuous": "continuous", "osc_transient": "transient"}
    probes, anc, floors = {}, {}, {}
    for key, short in names.items():
        r = res[key]
        probes[short] = {k: r["external_loads_a"][k] for k in RAILS}
        floors[short] = r["pre_rail_power_floor"]
        for k in RAILS:
            anc.setdefault(k, r["rails"][k]["ldo_output_a"] - r["external_loads_a"][k])
    return probes, anc, floors


def board_input_power(loads, anc, eta, hybrid=False):
    """Power needed at the Board B input, W. Q1/cable loss is upstream of
    this point and is inside the board-input derate, so it is not added."""
    total = 0.0
    for k in RAILS:
        i = loads[k] + anc[k]
        p_rail = VOUT[k] * i + i * i * (R_PTC_MAX + R_FILTER)
        if hybrid and k != "plus5":
            v_pre = VOUT[k] + HYB_HEADROOM
            p_rail = v_pre * i * (1 + HYB_GND_FRAC) + i * i * (R_PTC_MAX + R_FILTER)
        total += p_rail / eta[k]
    return total


def ext_power(loads):
    return sum(VOUT[k] * loads[k] for k in RAILS)


def ancillary_power(loads, anc):
    return sum(VOUT[k] * anc[k] + (loads[k] + anc[k]) ** 2 * R_PTC_MAX for k in RAILS)


def max_continuous_scale(probe, anc, eta, vb, ilim, hybrid=False):
    lo, hi = 0.0, 4.0
    for _ in range(80):
        k = (lo + hi) / 2
        loads = {"plus12": probe["plus12"] * k, "minus12": probe["minus12"] * k,
                 "plus5": probe["plus5"]}
        if board_input_power(loads, anc, eta, hybrid) / vb <= ilim:
            lo = k
        else:
            hi = k
    return probe["plus12"] * lo, probe["minus12"] * lo


def holdup_c(deficit_w, v1, v2, t=0.020):
    return 2 * deficit_w * t / (v1 * v1 - v2 * v2)


def inverter(vin, iout):
    d = (VOUT["minus12"] + VF) / (vin + VOUT["minus12"] + VF)
    il = iout / (1 - d)
    di = vin * d / (L_H * F_SW)
    ipk = il + di / 2
    irms_sw = il * math.sqrt(d)
    p_cond = irms_sw ** 2 * RDS_MAX
    return d, il, di, ipk, p_cond, (p_cond + P_SW_FIXED) * THETA_JA


def buck(vin, vout, iout):
    d = (vout + VF) / (vin + VF)
    di = (vin - vout) * d / (L_H * F_SW)
    p_cond = iout ** 2 * d * RDS_MAX
    return d, iout + di / 2, p_cond, (p_cond + P_SW_FIXED) * THETA_JA


def ptc_crossing(i):
    for (t1, h1), (t2, h2) in zip(PTC_DERATE, PTC_DERATE[1:]):
        if h1 >= i >= h2:
            return t1 + (h1 - i) * (t2 - t1) / (h1 - h2)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args().root)
    probes, anc, floors = load_probes(root)

    print("SCREENING ARITHMETIC ONLY - efficiencies PA; ripple/thermal/startup NOT RUN\n")
    print("Ancillary rail currents from supply-capability.json (A):",
          {k: round(v, 4) for k, v in anc.items()})

    for basis in ("planning", "stage54_cond"):
        f = floors[basis]
        e = f["required_weighted_converter_efficiency_at_3a"]
        print(f"Capability pre-rail floor, {basis}: {f['power_w']:.2f} W; required eta "
              f"14 V {e['14V'] * 100:.1f}%, 15 V {e['15V'] * 100:.1f}%")

    print("\n1. Required weighted end-to-end efficiency = Pout_ext / (Vb*3A - Pancillary)")
    for name, loads in probes.items():
        pa = ancillary_power(loads, anc)
        po = ext_power(loads)
        row = [f"{name:12s} Pout {po:6.2f} W  Panc {pa:4.2f} W"]
        for vb in (14.0, 15.0, POINTS["20V"]["derated"], 18.4):
            row.append(f"{vb:5.2f}V:{po / (vb * 3.0 - pa) * 100:6.1f}%")
        print("  " + "  ".join(row))

    print("\n2. Switcher-direct board input current (A) by board-input point and eta set")
    cases = [("15V floor", 14.0), ("15V ideal", 15.0),
             ("20V derated", POINTS["20V"]["derated"]), ("20V cable", 18.4)]
    for es in ETA:
        print(f"  eta {es} {ETA[es]}")
        for name, loads in probes.items():
            p = board_input_power(loads, anc, ETA[es])
            cells = "  ".join(f"{c}:{p / vb:5.2f}" for c, vb in cases)
            print(f"    {name:12s} Pin {p:6.2f} W  {cells}")

    print("\n3. Hybrid (20 V; +/-12 V LDO at 0.7 V headroom, +5 V direct)")
    for es in ETA:
        for name, loads in probes.items():
            p = board_input_power(loads, anc, ETA[es], hybrid=True)
            print(f"  {es:5s} {name:12s} Pin {p:6.2f} W  "
                  f"{POINTS['20V']['derated']}V:{p / POINTS['20V']['derated']:5.2f} A  "
                  f"18.4V:{p / 18.4:5.2f} A")

    print("\n4. Max continuous-shaped +12/-12 (A) with +5 V at 0.3 A")
    for es in ETA:
        for label, vb, ilim, hyb in [("15V/3A floor", 14.0, 3.0, False),
                                     ("15V/3A ideal", 15.0, 3.0, False),
                                     ("20V/3A derated", POINTS["20V"]["derated"], 3.0, False),
                                     ("20V/3A cable", 18.4, 3.0, False),
                                     ("20V/3A hybrid derated", POINTS["20V"]["derated"], 3.0, True),
                                     ("20V/5A derated", POINTS["20V"]["derated"], 5.0, False)]:
            a, b = max_continuous_scale(probes["continuous"], anc, ETA[es], vb, ilim, hyb)
            print(f"  {es:5s} {label:22s} +12 {a:5.3f}  -12 {b:5.3f}")

    print("\n5. 20 ms transient energy (input held at 3 A by a sink-side limit)")
    for es in ETA:
        for label, vb, v2 in [("15V floor", 14.0, 13.0),
                              ("20V derated", POINTS["20V"]["derated"], POINTS["20V"]["derated"] - 1.0),
                              ("20V cable", 18.4, 17.4)]:
            p = board_input_power(probes["transient"], anc, ETA[es])
            deficit = max(0.0, p - vb * 3.0)
            c = holdup_c(deficit, vb, v2)
            print(f"  {es:5s} {label:12s} Pin {p:6.2f} W  deficit {deficit:5.2f} W  "
                  f"energy {deficit * 0.02 * 1000:6.1f} mJ  hold-up {c * 1000:6.2f} mF "
                  f"({vb:.2f}->{v2:.2f} V)")

    print("\n6. TPS54560 stress (L 22 uH, 400 kHz, Vf 0.5 V, RDS 190 mohm max; PA)")
    for vin in (14.0, POINTS["20V"]["derated"]):
        for io in (1.6, 1.9):
            d, il, di, ipk, pc, rise = inverter(vin, io)
            print(f"  inverter Vin {vin:5.2f} Iout {io:.1f}: D {d:.3f} IL {il:.2f} dI {di:.2f} "
                  f"Ipk {ipk:.2f} A vs 6.3 A min, Pcond {pc:.2f} W, rise ~{rise:.0f} C")
        for io in (1.7, 2.0):
            d, ipk, pc, rise = buck(vin, 12.0, io)
            print(f"  +12 buck Vin {vin:5.2f} Iout {io:.1f}: D {d:.3f} Ipk {ipk:.2f} A, "
                  f"Pcond {pc:.2f} W, rise ~{rise:.0f} C")

    print("\n7. PTC MF-MSMF250/16X: drop at R1max and hold-current crossing ambient")
    for i in (1.6, 1.7, 1.9, 2.0):
        t = ptc_crossing(i)
        print(f"  {i:.1f} A: drop {i * R_PTC_MAX:.2f} V outside loop; hold = load at ~{t:.0f} C")

    print("\n8. J5 two-contact sharing (equal split, unverified)")
    for label, i in (("A1 at 3 A", 3.0), ("B1 continuous ~2.5 A", 2.5)):
        print(f"  {label}: {i / 2:.2f} A per contact vs 3 A rating")


if __name__ == "__main__":
    main()
